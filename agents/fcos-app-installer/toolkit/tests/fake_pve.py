"""A fake of the Proxmox endpoints tools/pve.py uses, with a request log.

Plain HTTP on 127.0.0.1, random port. Test-only.
"""

import json
import threading
from email import policy as email_policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlsplit

PREFIX = "/api2/json"
PRINCIPAL = "fcos-agent@pve!fcos-bootstrap"

PERMISSIONS = {
    "/pool/fcos-agent": {"VM.Allocate": 1, "VM.Audit": 1, "VM.PowerMgmt": 1, "VM.Config.CPU": 1,
                         "Pool.Audit": 1},
    "/storage/local-lvm": {"Datastore.AllocateSpace": 1, "Datastore.Audit": 1},
    "/sdn/zones/localnetwork/vmbr0": {"SDN.Use": 1},
}


def parse_multipart(content_type: str, raw: bytes) -> dict:
    """{"fields": {name: text}, "file": {"name", "filename", "data"} or None}."""
    message = BytesParser(policy=email_policy.HTTP).parsebytes(
        b"Content-Type: " + content_type.encode() + b"\r\n\r\n" + raw)
    result = {"fields": {}, "file": None}
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        filename = part.get_filename()
        data = part.get_payload(decode=True) or b""
        if filename is None:
            result["fields"][name] = data.decode()
        else:
            result["file"] = {"name": name, "filename": filename, "data": data}
    return result


class FakePve:
    # GET /nodes/{node}/network fields as the API schema lists them.
    DEFAULT_BRIDGE = {"iface": "vmbr0", "type": "bridge", "active": 1, "bridge_vlan_aware": 1,
                      "bridge_vids": "2-4094", "mtu": 1500}

    def __init__(self, secret: str):
        self.secret = secret
        self.interfaces: list[dict] = [dict(self.DEFAULT_BRIDGE)]
        self.macs: dict[int, str] = {}
        self.config_updates: dict[int, list] = {}
        self.net0: dict[int, str] = {}
        self.log: list[dict] = []
        self.volumes: dict[str, list[dict]] = {}
        self.content_reply: dict | None = None  # raw reply for the storage content listing
        self.resources: list[dict] = []
        self.hide_resource_pool = False  # drop `pool` from /cluster/resources entirely
        self.taken: set[int] = set()
        self.permissions = json.loads(json.dumps(PERMISSIONS))
        self.fail: dict[tuple[str, str], tuple[int, bool]] = {}
        self.task_exit = "OK"
        self._tasks: dict[str, int] = {}
        self._lock = threading.Lock()
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _reply(self, code, payload, headers=None):
                body = json.dumps(payload).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                for key, value in (headers or {}).items():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(body)

            def _handle(self, method):
                parts = urlsplit(self.path)
                length = int(self.headers.get("Content-Length") or 0)
                raw_bytes = self.rfile.read(length) if length else b""
                content_type = self.headers.get("Content-Type") or ""
                multipart = None
                body = {}
                if content_type.startswith("multipart/form-data"):
                    multipart = parse_multipart(content_type, raw_bytes)
                else:
                    body = {k: v[0] for k, v in parse_qs(raw_bytes.decode()).items()}
                path = unquote(parts.path)
                query = {k: v[0] for k, v in parse_qs(parts.query).items()}
                with fake._lock:
                    fake.log.append({"method": method, "path": path, "query": query, "body": body,
                                     "multipart": multipart,
                                     "content_type": self.headers.get("Content-Type"),
                                     "auth": self.headers.get("Authorization")})
                if path.endswith("/redirect"):
                    return self._reply(302, {}, {"Location": f"http://127.0.0.1:{fake.port}{PREFIX}/version"})
                auth = self.headers.get("Authorization")
                if auth != "PVEAPIToken=" + PRINCIPAL + "=" + fake.secret:
                    return self._reply(401, {"data": None, "message": "authentication failure"})
                if not path.startswith(PREFIX):
                    return self._reply(404, {"data": None})
                route = path[len(PREFIX):]
                if (method, route) in fake.fail:
                    code, echo = fake.fail[(method, route)]
                    message = f"internal error, request carried {auth}" if echo else "internal error"
                    return self._reply(code, {"data": None, "message": message})
                with fake._lock:
                    code, payload = fake.route(method, route, query, body, multipart)
                self._reply(code, payload)

            def do_GET(self):
                self._handle("GET")

            def do_POST(self):
                self._handle("POST")

            def do_PUT(self):
                self._handle("PUT")

            def do_DELETE(self):
                self._handle("DELETE")

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, args=(0.02,), daemon=True)

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def start(self):
        self.thread.start()
        return self

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def add_vm(self, vmid, name, pool="fcos-agent", node="pve-a", status="stopped"):
        self.resources.append({"vmid": vmid, "name": name, "pool": pool, "node": node,
                               "status": status, "type": "qemu"})

    def writes(self):
        return [r for r in self.log if r["method"] != "GET"]

    def _pool_audit(self, pool):
        return bool(pool) and bool(self.permissions.get(f"/pool/{pool}", {}).get("Pool.Audit"))

    def _vm(self, vmid):
        return next((r for r in self.resources if r["vmid"] == vmid), None)

    def _upid(self, node, kind, vmid):
        upid = f"UPID:{node}:0000A1B2:0001C3D4:6720F00D:{kind}:{vmid}:{PRINCIPAL}:"
        self._tasks[upid] = 0
        return upid

    def route(self, method, route, query, body, multipart=None):
        segs = route.strip("/").split("/")
        if method == "GET" and route == "/version":
            return 200, {"data": {"version": "8.4.1", "release": "8.4"}}
        if method == "GET" and route == "/access/permissions":
            if "path" in query:
                return 200, {"data": {query["path"]: self.permissions.get(query["path"], {})}}
            return 200, {"data": self.permissions}
        if segs[0] == "nodes" and len(segs) == 5 and segs[2] == "storage":
            storage, leaf = segs[3], segs[4]
            privs = self.permissions.get(f"/storage/{storage}", {})
            if method == "GET" and leaf == "content":
                if "Datastore.Audit" not in privs and "Datastore.AllocateSpace" not in privs:
                    return 403, {"data": None, "message": "Permission check failed"}
                if self.content_reply is not None:
                    return 200, self.content_reply
                wanted = query.get("content")
                return 200, {"data": [v for v in self.volumes.get(storage, [])
                                      if wanted in (None, v.get("content", "iso"))]}
            if method == "POST" and leaf == "upload":
                if "Datastore.AllocateTemplate" not in privs:
                    return 403, {"data": None, "message": "Permission check failed"}
                file = (multipart or {}).get("file")
                if not file or file["name"] != "filename" or (multipart["fields"].get("content") != "iso"):
                    return 400, {"data": None, "message": "parameter verification failed"}
                self.volumes.setdefault(storage, []).append(
                    {"volid": f"{storage}:iso/{file['filename']}", "format": "iso", "content": "iso",
                     "size": len(file["data"])})
                return 200, {"data": self._upid(segs[1], "imgcopy", "")}
        if method == "GET" and route == "/cluster/resources":
            # As on a real PVE 9.2 node: a guest's `pool` field is only shown
            # to callers with Pool.Audit on that pool.
            rows = []
            for r in self.resources:
                row = dict(r)
                if self.hide_resource_pool or not self._pool_audit(row.get("pool")):
                    row.pop("pool", None)
                rows.append(row)
            return 200, {"data": rows}
        if method == "GET" and route == "/pools":
            # Listing is filtered to pools the caller may audit.
            wanted = query.get("poolid")
            pools = sorted({r["pool"] for r in self.resources if r.get("pool")} | {"fcos-agent"})
            out = []
            for pool in pools:
                if (wanted and pool != wanted) or not self._pool_audit(pool):
                    continue
                members = [dict(r, id=f"qemu/{r['vmid']}") for r in self.resources if r.get("pool") == pool]
                out.append({"poolid": pool, "members": members})
            return 200, {"data": out}
        if method == "GET" and route == "/cluster/nextid":
            vmid = int(query.get("vmid", 0))
            if vmid in self.taken or self._vm(vmid):
                return 400, {"data": None, "message": f"VM {vmid} already exists"}
            return 200, {"data": str(vmid)}
        if method == "GET" and segs[0] == "nodes" and len(segs) == 3 and segs[2] == "network":
            return 200, {"data": self.interfaces}  # schema: open to every user
        if segs[0] == "nodes" and len(segs) >= 3 and segs[2] == "qemu":
            node = segs[1]
            if method == "POST" and len(segs) == 3:
                vmid = int(body["vmid"])
                # As qemu-server: tags are checked on /vms/<vmid> before the VM joins its
                # pool, so a pool-scoped token can't set them on create.
                if "tags" in body:
                    return 500, {"data": None, "message": f"Permission check failed (/vms/{vmid}, VM.Config.Options)"}
                if vmid in self.taken or self._vm(vmid):
                    return 500, {"data": None, "message": f"unable to create VM {vmid}: already exists"}
                self.add_vm(vmid, body["name"], body.get("pool", ""), node)
                # Proxmox generates the MAC and stores net0 as <model>=<MAC>,...
                mac = f"BC:24:11:00:{vmid // 256 % 256:02X}:{vmid % 256:02X}"
                model, _, rest = body.get("net0", "virtio").partition(",")
                self.macs[vmid] = mac
                self.net0[vmid] = f"{model}={mac}" + (f",{rest}" if rest else "")
                return 200, {"data": self._upid(node, "qmcreate", vmid)}
            if len(segs) >= 4:
                vmid = int(segs[3])
                rest = "/".join(segs[4:])
                vm = self._vm(vmid)
                if method == "PUT" and rest == "config" and vm:
                    self.config_updates.setdefault(vmid, []).append(body)
                    return 200, {"data": None}
                if method == "PUT" and rest == "resize":
                    return 200, {"data": None}
                if method == "POST" and rest == "status/start" and vm:
                    vm["status"] = "running"
                    return 200, {"data": self._upid(node, "qmstart", vmid)}
                if method == "GET" and rest == "config" and vm:
                    return 200, {"data": {"name": vm["name"], "net0": self.net0.get(vmid, "virtio,bridge=vmbr0")}}
                if method == "GET" and rest == "status/current" and vm:
                    return 200, {"data": {"vmid": vmid, "name": vm["name"], "status": vm["status"],
                                          "uptime": 0}}
        if method == "GET" and segs[0] == "nodes" and len(segs) == 5 and segs[2] == "tasks":
            upid = segs[3]
            if upid in self._tasks:
                self._tasks[upid] += 1
                if self._tasks[upid] == 1:
                    return 200, {"data": {"status": "running"}}
                return 200, {"data": {"status": "stopped", "exitstatus": self.task_exit}}
        return 404, {"data": None, "message": "no such endpoint"}
