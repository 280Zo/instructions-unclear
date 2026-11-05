#!/usr/bin/env python3
"""The agent's only way to talk to Proxmox VE.

Usage:
  pve.py check  [--host KEY]                    validate the token, show its permissions
  pve.py list   [--host KEY]                    VMs in the fcos-agent pool
  pve.py create <vm.yaml> [--dry-run] [--host KEY]   (ignition.method nocloud-iso also uploads
                                                a config ISO built by tools/make_cidata_iso.sh)
  pve.py start  <vm> [--host KEY]               <vm>: name under vms/ or a VMID
  pve.py status <vm> [--host KEY]

Runs on the owner's desktop. It reads the API token from
<workspace>/secrets/proxmox-<host>.token itself (one line,
"fcos-agent@pve!fcos-bootstrap=<secret>", file mode 0600, folder mode 0700) and
never prints it. It only acts on VMs in the pool "fcos-agent" and has no
delete, destroy, rebuild, disk-swap or pool-move verb: those stay owner steps.

TLS is always verified: the system CAs, or hosts.<key>.ca_file from site.yaml.
There is no switch to turn that off. The API endpoint comes only from
hosts.<key>.address in site.yaml; no environment variable or flag changes it
(so the token can never be pointed at another listener).
"""

import argparse
import json
import os
import re
import ssl
import stat
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import workspace
from workspace import WorkspaceError

POOL = "fcos-agent"
AGENT_PRINCIPAL = "fcos-agent@pve!fcos-bootstrap"
API_PREFIX = "/api2/json"
TIMEOUT = 30
POLL_SECONDS = 1.0
TASK_TIMEOUT = 900
MAX_RESPONSE = 4 * 1024 * 1024
MAX_ISO = 64 * 1024 * 1024
BUILD_TIMEOUT = 600
ISO_SCRIPT = Path(__file__).resolve().parent / "make_cidata_iso.sh"

HOST_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
NODE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]*$")
VM_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")
VOLUME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@+-]*$")
STORAGE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
UPLOAD_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.iso$")
FIELD_WORD = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
UPID = re.compile(r"^UPID:[A-Za-z0-9:._@!-]+$")
UUID_SHAPE = re.compile(r"^[0-9A-Za-z-]{8,64}$")
ADDRESS = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.:-]*$")
LOOPBACK = ("127.0.0.1", "localhost")


class PveError(Exception):
    pass


_to_hide: set[str] = set()


def scrub(text) -> str:
    """Remove any token secret (and the auth header value) from text."""
    out = str(text)
    for hidden in sorted(_to_hide, key=len, reverse=True):
        out = out.replace(hidden, "***")
    return re.sub(r"PVEAPIToken=\S+", "PVEAPIToken=***", out)


def _oneline(text, limit: int = 200) -> str:
    return " ".join(scrub(text).split())[:limit]


def _check_base_url(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    if parts.username or parts.password or not parts.hostname:
        raise PveError("API URL must be scheme://host[:port]/path without credentials")
    if parts.scheme == "https":
        return url.rstrip("/")
    if parts.scheme == "http" and parts.hostname in LOOPBACK:
        return url.rstrip("/")
    raise PveError("API URL must be https:// (plain http:// only to 127.0.0.1 or localhost, for tests)")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """urllib would forward the Authorization header to a redirect target."""

    def redirect_request(self, *args, **kwargs):
        return None


class PveClient:
    """Minimal Proxmox API client. GET, POST and PUT only: there is no delete."""

    def __init__(self, base_url: str, token_id: str, token_secret: str, verify="system"):
        if verify is False or verify is None:
            raise PveError("TLS verification cannot be turned off")
        if not token_id or not token_secret:
            raise PveError("token id and secret are required")
        self.base_url = _check_base_url(base_url)
        self.principal = token_id
        self._auth = "PVEAPIToken=" + token_id + "=" + token_secret
        _to_hide.add(token_secret)
        try:
            if isinstance(verify, (str, os.PathLike)) and verify != "system":
                context = ssl.create_default_context(cafile=str(verify))
                # The node's own pinned CA (Proxmox's self-signed root) has no
                # keyUsage extension, which Python 3.13+ rejects in strict mode.
                # Relax only that format check; the chain and the hostname are
                # still verified against this one CA.
                context.verify_flags &= ~getattr(ssl, "VERIFY_X509_STRICT", 0)
            else:
                context = ssl.create_default_context()
        except (OSError, ssl.SSLError) as exc:
            raise PveError(f"cannot load the CA file ({_oneline(exc)})") from None
        self._opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), _NoRedirect,
            urllib.request.HTTPHandler, urllib.request.HTTPSHandler(context=context))

    def get(self, path: str) -> dict:
        return self._request("GET", path)

    def post(self, path: str, data: dict | None = None) -> dict:
        return self._request("POST", path, data or {})

    def put(self, path: str, data: dict | None = None) -> dict:
        return self._request("PUT", path, data or {})

    def upload(self, path: str, fields: dict, filename: str, data: bytes) -> dict:
        """POST multipart/form-data: simple text fields plus the file as the part named "filename"."""
        if not UPLOAD_NAME.match(filename):
            raise PveError(f"unsafe upload file name {filename!r}")
        for key, value in fields.items():
            if not isinstance(key, str) or not isinstance(value, str) \
                    or not FIELD_WORD.match(key) or not FIELD_WORD.match(value):
                raise PveError("unsafe upload field")
        boundary = "fcosagent" + os.urandom(12).hex()
        while boundary.encode() in data:
            boundary = "fcosagent" + os.urandom(12).hex()
        pieces = []
        for key, value in fields.items():
            pieces.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
        pieces.append((f'--{boundary}\r\nContent-Disposition: form-data; name="filename"; filename="{filename}"\r\n'
                       "Content-Type: application/octet-stream\r\n\r\n").encode())
        pieces.append(data)
        pieces.append(f"\r\n--{boundary}--\r\n".encode())
        return self._request("POST", path, raw=(f"multipart/form-data; boundary={boundary}", b"".join(pieces)))

    def _request(self, method: str, path: str, data: dict | None = None,
                 raw: tuple[str, bytes] | None = None) -> dict:
        if method not in ("GET", "POST", "PUT"):
            raise PveError(f"method {method} is not allowed")
        if not path.startswith("/") or re.search(r"[\s\\]|//|\.\.", path):
            raise PveError(f"invalid API path {path!r}")
        shown = path.split("?", 1)[0]
        headers = {"Authorization": self._auth, "Accept": "application/json"}
        body = None
        if raw is not None:
            headers["Content-Type"], body = raw
        elif data is not None:
            body = urllib.parse.urlencode(data).encode("ascii")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        request = urllib.request.Request(self.base_url + path, data=body, method=method, headers=headers)
        try:
            with self._opener.open(request, timeout=TIMEOUT) as response:
                raw = response.read(MAX_RESPONSE + 1)
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                message = json.loads(exc.read(MAX_RESPONSE)).get("message")
                if isinstance(message, str) and message.strip():
                    detail = f": {_oneline(message)}"
            except (ValueError, AttributeError, OSError):
                pass
            finally:
                exc.close()
            if 300 <= exc.code < 400:
                raise PveError(f"{method} {shown}: unexpected redirect (HTTP {exc.code}); not followed") from None
            raise PveError(f"{method} {shown}: HTTP {exc.code}{detail}") from None
        except (urllib.error.URLError, OSError, ssl.SSLError) as exc:
            reason = getattr(exc, "reason", exc)
            raise PveError(f"{method} {shown}: cannot reach the API ({_oneline(reason)})") from None
        if len(raw) > MAX_RESPONSE:
            raise PveError(f"{method} {shown}: response too large")
        try:
            decoded = json.loads(raw)
        except ValueError:
            raise PveError(f"{method} {shown}: response is not JSON") from None
        if not isinstance(decoded, dict):
            raise PveError(f"{method} {shown}: unexpected response")
        return decoded


def load_token(ws: Path, host: str) -> tuple[str, str]:
    if not HOST_KEY.match(host):
        raise PveError(f"invalid host name {host!r}")
    vault = Path(ws) / "secrets"
    path = vault / f"proxmox-{host}.token"
    try:
        info = vault.lstat()
    except OSError:
        raise PveError(f"no secrets folder at {vault}; create the workspace first") from None
    if not stat.S_ISDIR(info.st_mode):
        raise PveError(f"{vault} must be a real folder")
    if stat.S_IMODE(info.st_mode) != 0o700:
        raise PveError(f"{vault} has mode {stat.S_IMODE(info.st_mode):04o}; run: chmod 700 {vault}")
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except FileNotFoundError:
        raise PveError(f"token file {path} is missing; store the token there (guide: host setup)") from None
    except OSError:
        raise PveError(f"token file {path} cannot be opened (is it a symlink?)") from None
    with os.fdopen(fd, "r", encoding="utf-8", errors="replace") as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise PveError(f"token file {path} must be a regular file")
        if stat.S_IMODE(info.st_mode) != 0o600:
            raise PveError(f"token file {path} has mode {stat.S_IMODE(info.st_mode):04o}; run: chmod 600 {path}")
        if info.st_uid != os.getuid():
            raise PveError(f"token file {path} is owned by another user")
        text = handle.read(4096)
    lines = text.strip().splitlines()
    who, sep, material = lines[0].strip().partition("=") if len(lines) == 1 else ("", "", "")
    if not sep or not UUID_SHAPE.match(material):
        raise PveError(f"token file {path} must hold one line: {AGENT_PRINCIPAL}=<secret>")
    _to_hide.add(material)
    if who != AGENT_PRINCIPAL:
        raise PveError(f"token file {path} must be for {AGENT_PRINCIPAL}")
    return who, material


def _positive_int(spec: dict, key: str) -> int:
    value = spec.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise PveError(f"vm.yaml: {key} must be a positive whole number")
    return value


def _volume(value, label: str) -> str:
    if not isinstance(value, str) or not VOLUME.match(value) or ".." in value:
        raise PveError(f"vm.yaml: {label} is missing or has unsupported characters")
    return value


# Every VM setting the agent must decide and explain (owner rule 2026-10-31):
# vm.yaml `settings:` holds each as {use, why, source}; none may be left out,
# and each is sent to Proxmox explicitly. Values are checked here.
# CPU flags allowed for a VM (Proxmox VM chapter, "VM-specific flags must be
# from the following set for security reasons").
CPU_FLAGS = {"aes", "amd-no-ssb", "amd-ssbd", "hv-evmcs", "hv-tlbflush", "ibpb", "md-clear", "nested-virt",
             "pcid", "pdpe1gb", "spec-ctrl", "ssbd", "virt-ssbd"}
CPU_TYPE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
TAG = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,63}$")
HOTPLUG = ("network", "disk", "cpu", "memory", "usb", "cloudinit")
SETTING_KEYS = ("cpu", "cpu_flags", "sockets", "numa", "cpuunits", "cpulimit", "balloon", "allow_ksm", "bios",
                "machine", "disk_cache", "disk_aio", "discard", "ssd", "nic_model", "nic_queues", "nic_firewall",
                "rng", "tablet", "hotplug", "startup_order", "startup_up", "onboot", "protection", "agent",
                "watchdog", "acpi", "kvm", "localtime", "tags", "description")


def _settings(spec: dict) -> dict:
    """The `use` value of every setting, checked: all present, none extra, each explained."""
    raw = spec.get("settings")
    if not isinstance(raw, dict):
        raise PveError("vm.yaml: settings is missing; every VM setting must be decided (see guide 2.3)")
    missing = [k for k in SETTING_KEYS if k not in raw]
    extra = sorted(set(raw) - set(SETTING_KEYS))
    if missing or extra:
        raise PveError("vm.yaml settings: " + "; ".join(
            ([f"missing {', '.join(missing)}"] if missing else []) + ([f"unknown {', '.join(extra)}"] if extra else [])))
    out = {}
    for key in SETTING_KEYS:
        entry = raw[key]
        if not isinstance(entry, dict) or set(entry) != {"use", "why", "source"}:
            raise PveError(f"vm.yaml settings: {key} must be {{use, why, source}}")
        for part in ("why", "source"):
            if not isinstance(entry[part], str) or not entry[part].strip() or "\n" in entry[part]:
                raise PveError(f"vm.yaml settings: {key} needs a one-line {part}")
        out[key] = entry["use"]
    return out


def _bool(s: dict, key: str) -> int:
    if not isinstance(s[key], bool):
        raise PveError(f"vm.yaml settings: {key} must be true or false")
    return 1 if s[key] else 0


def _int(s: dict, key: str, low: int, high: int, allow_none: bool = False):
    value = s[key]
    if value is None and allow_none:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise PveError(f"vm.yaml settings: {key} must be a whole number from {low} to {high}"
                       + (" or null" if allow_none else ""))
    return value


def _choice(s: dict, key: str, options: tuple) -> str:
    if s[key] not in options:
        raise PveError(f"vm.yaml settings: {key} must be one of {', '.join(options)}")
    return s[key]


def settings_params(s: dict, cores: int, ram: int) -> tuple[dict, str, str]:
    """(top-level params, disk options, NIC options) for the checked settings."""
    if not isinstance(s["cpu"], str) or not CPU_TYPE.match(s["cpu"]):
        raise PveError("vm.yaml settings: cpu must be a CPU type name (e.g. host)")
    if s["cpu"].startswith("custom-"):  # needs Mapping.Use on /mapping/cpu/<name> (check_cpu_model_access)
        raise PveError("vm.yaml settings: cpu custom models need a mapping right this token doesn't have")
    flags = s["cpu_flags"]
    if not isinstance(flags, list) or not all(isinstance(f, str) and len(f) > 1 and f[0] in "+-"
                                              and f[1:] in CPU_FLAGS for f in flags):
        raise PveError(f"vm.yaml settings: cpu_flags must be a list of +flag/-flag from {', '.join(sorted(CPU_FLAGS))}")
    sockets = _int(s, "sockets", 1, 4)
    params = {
        "cpu": s["cpu"] + (f",flags={';'.join(flags)}" if flags else ""),
        "sockets": sockets,
        "numa": _bool(s, "numa"),
        "cpuunits": _int(s, "cpuunits", 1, 10000),
        "cpulimit": _int(s, "cpulimit", 0, 128),
        "allow-ksm": _bool(s, "allow_ksm"),
        "bios": _choice(s, "bios", ("seabios",)),  # ovmf would need an EFI disk the tool doesn't create yet
        "machine": _choice(s, "machine", ("pc", "q35")),
        "tablet": _bool(s, "tablet"),
        "onboot": _bool(s, "onboot"),
        "protection": _bool(s, "protection"),
        "agent": _bool(s, "agent"),
        "acpi": _bool(s, "acpi"),
        "kvm": _bool(s, "kvm"),
        "localtime": _bool(s, "localtime"),
    }
    # balloon: "on" keeps the device with no minimum (balloon = memory, fixed size); "off" removes it.
    params["balloon"] = ram if _choice(s, "balloon", ("on", "off")) == "on" else 0
    hot = s["hotplug"]
    if not isinstance(hot, str) or not (hot == "0" or all(h in HOTPLUG for h in hot.split(","))):
        raise PveError(f"vm.yaml settings: hotplug must be 0 or a comma list of {', '.join(HOTPLUG)}")
    if any(h in ("memory", "cpu") for h in hot.split(",")) and not s["numa"]:
        raise PveError("vm.yaml settings: hotplug of memory or cpu needs numa true (Proxmox VM chapter)")
    params["hotplug"] = hot
    if _choice(s, "rng", ("urandom", "none")) == "urandom":
        params["rng0"] = "source=/dev/urandom"
    _choice(s, "watchdog", ("none",))
    order = _int(s, "startup_order", 0, 10000, allow_none=True)
    up = _int(s, "startup_up", 0, 3600, allow_none=True)
    if order is not None:
        params["startup"] = f"order={order}" + (f",up={up}" if up is not None else "")
    elif up is not None:
        raise PveError("vm.yaml settings: startup_up needs a startup_order")
    tags = s["tags"]
    if not isinstance(tags, list) or not all(isinstance(t, str) and TAG.match(t) for t in tags):
        raise PveError("vm.yaml settings: tags must be a list of lowercase names")
    if tags:
        params["tags"] = ";".join(tags)
    desc = s["description"]
    if not isinstance(desc, str) or "\n" in desc or len(desc) > 200:
        raise PveError("vm.yaml settings: description must be one line, at most 200 characters")
    params["description"] = desc
    if s["disk_aio"] == "native" and s["disk_cache"] not in ("none", "directsync"):
        raise PveError("vm.yaml settings: disk_aio native needs disk_cache none or directsync (direct I/O)")
    disk = (f"iothread=1,cache={_choice(s, 'disk_cache', ('none', 'writethrough', 'writeback', 'directsync'))}"
            f",aio={_choice(s, 'disk_aio', ('io_uring', 'native', 'threads'))}"
            f",discard={'on' if _bool(s, 'discard') else 'ignore'}" + (",ssd=1" if _bool(s, "ssd") else ""))
    _choice(s, "nic_model", ("virtio",))
    queues = _int(s, "nic_queues", 1, 64)
    if queues > sockets * cores:
        raise PveError(f"vm.yaml settings: nic_queues {queues} is more than the VM's {sockets * cores} vCPUs")
    nic = f"firewall={_bool(s, 'nic_firewall')}" + (f",queues={queues}" if queues > 1 else "")
    return params, disk, nic


# Sent by the tool for every VM (not a choice in vm.yaml): (value, why, source).
FIXED_SETTINGS = {
    "scsihw": ("virtio-scsi-single", "recommended with IO threads for performance", "Proxmox VM chapter"),
    "ostype": ("l26", "Linux 2.6+ kernel (FCOS)", "Proxmox VM chapter"),
    "serial0": ("socket", "serial console", "FCOS Proxmox guide"),
    "vga": ("serial0", "display on the serial console", "FCOS Proxmox guide"),
    "boot": ("order=scsi0", "boot the system disk", "FCOS Proxmox guide"),
}
# Not sent: Proxmox's own value applies, stated here so nothing is left silently.
DEFAULT_SETTINGS = {
    "vmgenid": ("generated", "VM generation ID, set automatically on create", "Proxmox VM chapter"),
    "smbios1": ("generated UUID", "machine identity, set automatically", "Proxmox API schema"),
    "shares": ("1000", "only used by auto-ballooning, which balloon on (no minimum) doesn't do", "Proxmox API schema"),
    "reboot": ("1", "a reboot inside the VM restarts it (needed for FCOS updates)", "Proxmox API schema"),
    "hugepages": ("off", "not needed at this size", "Proxmox VM chapter"),
    "vcpus": ("all", "no CPU hotplug", "Proxmox API schema"),
    "affinity": ("none", "no pinning to host cores", "Proxmox API schema"),
    "keyboard": ("none", "serial console, no VNC keyboard", "Proxmox API schema"),
    "start": ("0", "created stopped: the address is reserved before the first start", "Proxmox API schema"),
    "template": ("0", "an ordinary VM, not a template", "Proxmox API schema"),
}


# Settings whose Proxmox permission check goes beyond the VM's own rights
# (qemu-server PVE/API2/Qemu.pm check_vm_modify_config_perm): param -> (path, privilege, vm.yaml key).
SETTING_RIGHTS = {"startup": ("/", "Sys.Modify", "startup_order")}


def check_setting_rights(client: "PveClient", params: dict) -> None:
    """Refuse before any write when a setting needs a right this token doesn't have."""
    for param, (path, priv, key) in SETTING_RIGHTS.items():
        if param not in params:
            continue
        data = _data(client.get(f"/access/permissions?path={urllib.parse.quote(path, safe='/')}"))
        privs = data.get(path) if isinstance(data, dict) else None
        if not isinstance(privs, dict) or not privs.get(priv):
            raise PveError(f"settings {key} needs {priv} on {path}, which this token deliberately doesn't have; "
                           f"use null for {key} (an owner step can set it in Proxmox); nothing was sent")


def settings_table(spec: dict) -> list[tuple[str, str, str, str]]:
    """(setting, value, why, source) for every setting, for the owner to review."""
    _settings(spec)
    return [(k, json.dumps(spec["settings"][k]["use"]) if not isinstance(spec["settings"][k]["use"], str)
             else spec["settings"][k]["use"], spec["settings"][k]["why"], spec["settings"][k]["source"])
            for k in SETTING_KEYS]


def iso_file_name(vm_name: str) -> str:
    return f"fcos-{vm_name}-ign.iso"


def plan_create(spec: dict, existing: set[int], node: str | None = None,
                snippets_storage: str | None = None,
                iso_storage: str | None = None) -> list[tuple[str, str, dict]]:
    """Ordered (method, path, params) for creating the VM. Pure: sends nothing.

    The Ignition snippet is always <snippets_storage>:snippets/<name>.ign, with
    snippets_storage from the host's site.yaml entry. With nocloud-iso the plan
    starts with an UPLOAD step and the ISO is <iso_storage>:iso/fcos-<name>-ign.iso."""
    if not isinstance(spec, dict):
        raise PveError("vm.yaml must be a mapping")
    name = spec.get("name")
    if not isinstance(name, str) or not VM_NAME.match(name):
        raise PveError("vm.yaml: name must be lowercase letters, digits and hyphens")
    node = node or spec.get("node") or spec.get("host")
    if not isinstance(node, str) or not NODE_NAME.match(node):
        raise PveError("vm.yaml: cannot tell which Proxmox node to use")
    vmid = _positive_int(spec, "vmid")
    if vmid < 100 or vmid > 999999999:
        raise PveError("vm.yaml: vmid must be 100 or higher")
    if vmid in existing:
        raise PveError(f"VMID {vmid} is already in use; choose another")
    cores = _positive_int(spec, "cores")
    ram = _positive_int(spec, "ram_mib")
    os_gib = _positive_int(spec, "os_disk_gib")
    data_gib = _positive_int(spec, "data_disk_gib")
    storage = _volume(spec.get("storage"), "storage")
    bridge = _volume(spec.get("bridge"), "bridge")
    image = _volume(spec.get("image_volume"), "image_volume")
    net = f"virtio,bridge={bridge}"
    tag = spec.get("vlan_tag")
    if tag is not None:
        if isinstance(tag, bool) or not isinstance(tag, int) or not 1 <= tag <= 4094:
            raise PveError("vm.yaml: vlan_tag must be 1-4094 or null")
        net += f",tag={tag}"
    mtu = spec.get("mtu")
    if mtu is not None:
        # Proxmox: 1 = use the bridge's MTU, otherwise 576-65520.
        if isinstance(mtu, bool) or not isinstance(mtu, int) or not (mtu == 1 or 576 <= mtu <= 65520):
            raise PveError("vm.yaml: mtu must be 1 (use the bridge's MTU), 576-65520, or null")
        net += f",mtu={mtu}"
    for old in ("ssd", "ballooning"):
        if old in spec:
            raise PveError(f"vm.yaml: {old} moved under settings (with use, why, source)")
    # Every setting is decided in vm.yaml settings and sent explicitly.
    chosen, disk_opts, nic_opts = settings_params(_settings(spec), cores, ram)
    net += "," + nic_opts

    params = dict(chosen, **{k: v[0] for k, v in FIXED_SETTINGS.items()}, **{
        "vmid": vmid, "name": name, "pool": POOL,
        "cores": cores, "memory": ram,
        "scsi0": f"{storage}:0,import-from={image},{disk_opts}",
        "scsi1": f"{storage}:{data_gib},{disk_opts}",
        "net0": net,
    })
    steps: list[tuple[str, str, dict]] = []
    ignition = spec.get("ignition")
    method = ignition.get("method") if isinstance(ignition, dict) else None
    if method == "snippet":
        if not isinstance(snippets_storage, str) or not STORAGE_ID.match(snippets_storage):
            raise PveError("the host's snippets_storage is missing or invalid in site.yaml")
        volume = f"{snippets_storage}:snippets/{name}.ign"
        given = ignition.get("volume")
        if given is not None and given != volume:
            raise PveError(f"vm.yaml: ignition.volume must be {volume} (or left out); got a different value")
        params["ide2"] = f"{storage}:cloudinit"
        params["cicustom"] = f"vendor={volume}"
        params["ciupgrade"] = 0
    elif method == "nocloud-iso":
        if not isinstance(iso_storage, str) or not STORAGE_ID.match(iso_storage):
            raise PveError("ignition method nocloud-iso needs the host's iso_storage in site.yaml "
                           "(a storage that holds ISO images); it is missing or invalid")
        volume = f"{iso_storage}:iso/{iso_file_name(name)}"
        given = ignition.get("volume")
        if given is not None and given != volume:
            raise PveError(f"vm.yaml: ignition.volume must be {volume} (or left out); got a different value")
        params["ide2"] = f"{volume},media=cdrom"
        steps.append(("UPLOAD", f"/nodes/{node}/storage/{iso_storage}/upload",
                      {"content": "iso", "filename": iso_file_name(name)}))
    else:
        raise PveError("vm.yaml: ignition.method must be snippet or nocloud-iso")
    # Tags go in an update once the VM is in its pool: qemu-server checks them on
    # /vms/<vmid> before the create adds the VM to the pool, where this token's rights are.
    tags = params.pop("tags", None)
    return steps + [
        ("POST", f"/nodes/{node}/qemu", params),
        ("PUT", f"/nodes/{node}/qemu/{vmid}/resize", {"disk": "scsi0", "size": f"{os_gib}G"}),
    ] + ([("PUT", f"/nodes/{node}/qemu/{vmid}/config", {"tags": tags})] if tags else [])


LINUX_DEFAULT_MTU = 1500
MAC = re.compile(r"^[A-Za-z0-9]+=([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5})$")


def _truthy(value) -> bool:
    return value in (1, True, "1", "yes", "on")


UNREADABLE = "unreadable"


def _vlan_ranges(text):
    """bridge_vids (API format pve-vlan-id-or-range-list, e.g. "2 4 100-200") as
    [(low, high)]; None when not reported, UNREADABLE when it doesn't parse."""
    if text is None or (isinstance(text, str) and not text.strip()):
        return None
    if not isinstance(text, str):
        return UNREADABLE
    ranges = []
    for part in re.split(r"[\s,]+", text.strip()):
        match = re.fullmatch(r"(\d{1,4})(?:-(\d{1,4}))?", part)
        if not match:
            return UNREADABLE
        low, high = int(match.group(1)), int(match.group(2) or match.group(1))
        if low > high:
            return UNREADABLE
        ranges.append((low, high))
    return ranges


def check_network(spec: dict, host: str, cfg: dict, interfaces: list) -> tuple[list[str], list[str]]:
    """(problems, warnings) for the VM's NIC against the node's network, read
    with GET /nodes/{node}/network (open to every API user). Pure: sends nothing.
    Messages are plain words for the owner, the setting in parentheses at the end.

    Refused: no hosts.<host>.bridge (nothing says which network is allowed); a
    bridge other than it, or listed in hosts.<host>.forbidden_bridges; a bridge
    that doesn't exist; a VLAN tag on a Linux bridge that isn't VLAN-aware
    (Proxmox would then create <port>.<tag> and <bridge>v<tag> on the server,
    a change to the owner's network: wiki "Network Configuration", VLAN); a tag
    outside the bridge's allowed VLANs, or allowed VLANs that can't be read; a
    NIC MTU above the bridge's (none reported: the Linux default 1500 is assumed,
    which errs on the safe side). Warned: a
    VLAN-aware bridge that doesn't report its allowed VLANs (the owner's network
    stays as it is, so the owner checks); an inactive bridge; a tag other than
    the host's usual one. forbidden_bridges is optional (not asked)."""
    problems: list[str] = []
    warnings: list[str] = []
    name = spec.get("bridge")
    allowed_bridge = cfg.get("bridge")
    # forbidden_bridges is optional and never asked (owner decision 2026-10-31):
    # hosts.<host>.bridge plus the token's one-bridge grant already refuse every
    # other network. A list that is saved is still honored.
    forbidden = cfg.get("forbidden_bridges") or []
    if not isinstance(forbidden, list):
        problems.append(f"the list of networks never to use on {host} is not a list (hosts.{host}.forbidden_bridges)")
        forbidden = []
    if name in forbidden:
        problems.append(f"network {name} must never get a machine on {host} (hosts.{host}.forbidden_bridges)")
    if not allowed_bridge:
        problems.append(f"nothing says which network machines on {host} may use (hosts.{host}.bridge)")
    elif name != allowed_bridge:
        problems.append(f"network {name} is not the one machines on {host} may use, {allowed_bridge} "
                        f"(hosts.{host}.bridge)")
    bridges = {i.get("iface"): i for i in interfaces
               if isinstance(i, dict) and i.get("type") in ("bridge", "OVSBridge")}
    found = bridges.get(name)
    if found is None:
        problems.append(f"network {name} does not exist on the server; networks there: "
                        f"{', '.join(sorted(b for b in bridges if isinstance(b, str))) or 'none'} (bridge)")
        return problems, warnings
    # API schema: active is optional, "set to true if the interface is active".
    if not _truthy(found.get("active")):
        warnings.append(f"network {name} is not active on the server right now")
    tag = spec.get("vlan_tag")
    usual = cfg.get("vlan_tag")
    if tag is not None and usual is not None and tag != usual:
        warnings.append(f"this machine goes on VLAN {tag}, not the server's usual VLAN {usual}; "
                        "confirm with the owner (vlan_tag)")
    if tag is not None and found.get("type") == "bridge":
        if not _truthy(found.get("bridge_vlan_aware")):
            port = str(found.get("bridge_ports") or "<port>").split()[0]
            problems.append(f"network {name} doesn't handle VLANs itself, so for VLAN {tag} Proxmox would "
                            f"create new interfaces on the server ({port}.{tag} and {name}v{tag}); that "
                            "changes your network, so it is refused (vlan_tag)")
        else:
            ranges = _vlan_ranges(found.get("bridge_vids"))
            if ranges is None:
                warnings.append(f"network {name} doesn't say which VLANs it lets through; check on the "
                                f"server that VLAN {tag} passes (bridge-vids)")
            elif ranges == UNREADABLE:
                problems.append(f"can't read which VLANs network {name} lets through "
                                f"({found.get('bridge_vids')!r}); check it on the server (bridge-vids)")
            elif not any(low <= tag <= high for low, high in ranges):
                problems.append(f"network {name} doesn't let VLAN {tag} through; it allows "
                                f"{found.get('bridge_vids')} (vlan_tag)")
    mtu = spec.get("mtu")
    if isinstance(mtu, int) and not isinstance(mtu, bool) and mtu != 1:
        raw = found.get("mtu")
        limit = int(raw) if str(raw or "").strip().isdigit() else None
        if limit is None and mtu > LINUX_DEFAULT_MTU:
            problems.append(f"network {name} doesn't report its packet size, so a machine packet size of "
                            f"{mtu} can't be confirmed; use mtu 1 (the network's own size) or ask the owner (mtu)")
        elif limit is not None and mtu > limit:
            problems.append(f"the machine's packet size {mtu} is larger than network {name}'s {limit}; "
                            "the machine would not start (mtu)")
    return problems, warnings


def mac_from_net(net) -> str | None:
    """The MAC in a net0 value such as "virtio=BC:24:11:00:00:01,bridge=vmbr9"."""
    if not isinstance(net, str):
        return None
    match = MAC.match(net.split(",", 1)[0])
    return match.group(1).upper() if match else None


def vm_mac(client: "PveClient", node: str, vmid: int) -> str | None:
    """The VM's MAC, or None when it can't be read (never fails the caller:
    after a create the VM exists, and a retry would only hit "already exists")."""
    try:
        config = _data(client.get(f"/nodes/{node}/qemu/{vmid}/config"))
    except PveError:
        return None
    return mac_from_net(config.get("net0")) if isinstance(config, dict) else None


def wait_task(client: PveClient, node: str, upid: str) -> None:
    if not UPID.match(upid):
        raise PveError("the API returned an unexpected task id")
    path = f"/nodes/{node}/tasks/{urllib.parse.quote(upid, safe=':@!')}/status"
    deadline = time.monotonic() + TASK_TIMEOUT
    while True:
        status = client.get(path).get("data")
        status = status if isinstance(status, dict) else {}
        if status.get("status") == "stopped":
            if status.get("exitstatus") != "OK":
                raise PveError(f"task failed on {node}: {_oneline(status.get('exitstatus'))}")
            return
        if time.monotonic() > deadline:
            raise PveError(f"task on {node} did not finish in {TASK_TIMEOUT} seconds")
        time.sleep(POLL_SECONDS)


def _data(response: dict):
    return response.get("data")


def vm_resources(client: PveClient) -> list[dict]:
    data = _data(client.get("/cluster/resources?type=vm"))
    return [item for item in data if isinstance(item, dict)] if isinstance(data, list) else []


def pool_members(client: PveClient) -> dict[int, dict]:
    """The pool's own member list (guests only), keyed by vmid.

    The authority for membership. A guest's `pool` field in /cluster/resources
    is only shown to callers with Pool.Audit, so it is not relied on. Without
    Pool.Audit the pool listing comes back empty: refuse rather than guess.
    """
    data = _data(client.get(f"/pools?poolid={POOL}"))
    entry = next((p for p in data if isinstance(p, dict) and p.get("poolid") == POOL), None) \
        if isinstance(data, list) else None
    if entry is None or not isinstance(entry.get("members"), list):
        raise PveError(f"this token cannot read pool {POOL}'s member list (it needs Pool.Audit on "
                       f"/pool/{POOL}); re-run .agents/skills/adapter-proxmox/scripts/setup-agent-access.sh")
    members = {}
    for item in entry["members"]:
        if isinstance(item, dict) and item.get("type") == "qemu" and isinstance(item.get("vmid"), int):
            members[item["vmid"]] = item
    return members


def require_in_pool(client: PveClient, vmid: int) -> dict:
    """The pool member entry for vmid, or PveError unless it is in the pool."""
    item = pool_members(client).get(vmid)
    if item is None:
        raise PveError(f"VM {vmid} is not in pool {POOL}; refusing")
    node = item.get("node")
    if not isinstance(node, str) or not NODE_NAME.match(node):
        raise PveError(f"VM {vmid} has no usable node")
    return item


def run_task(client: PveClient, method: str, node: str, path: str, params: dict | None = None) -> None:
    response = client.post(path, params) if method == "POST" else client.put(path, params)
    data = _data(response)
    if isinstance(data, str) and data.startswith("UPID:"):
        wait_task(client, node, data)


def build_iso(ign: Path, out: Path) -> None:
    """Build the cidata ISO with tools/make_cidata_iso.sh (xorriso in a throwaway container)."""
    try:
        result = subprocess.run(["bash", str(ISO_SCRIPT), str(ign), str(out)],
                                capture_output=True, text=True, timeout=BUILD_TIMEOUT)
    except (OSError, subprocess.SubprocessError) as exc:
        raise PveError(f"cannot run the config ISO builder ({_oneline(exc)})") from None
    if result.returncode != 0:
        tail = " ".join((result.stderr or "").strip().splitlines()[-3:])
        raise PveError(f"building the config ISO failed: {_oneline(tail, 400) or 'no details'}")


def check_iso_upload(client: PveClient, node: str, storage: str, volume_name: str) -> None:
    """Refuse before any write unless this token may upload an ISO there and the name is free."""
    path = f"/storage/{storage}"
    data = _data(client.get(f"/access/permissions?path={urllib.parse.quote(path, safe='/')}"))
    privs = data.get(path) if isinstance(data, dict) else None
    privs = privs if isinstance(privs, dict) else {}
    if "Datastore.AllocateTemplate" not in privs:
        raise PveError(f"the token lacks Datastore.AllocateTemplate on {path}, which uploading an ISO needs; "
                       "the owner must grant it, or use ignition.method: snippet")
    if "Datastore.Audit" not in privs and "Datastore.AllocateSpace" not in privs:
        raise PveError(f"the token lacks Datastore.Audit (or Datastore.AllocateSpace) on {path}, "
                       "which listing the ISOs already there needs")
    listing = _data(client.get(f"/nodes/{node}/storage/{storage}/content?content=iso"))
    if not isinstance(listing, list):
        raise PveError(f"storage {storage} returned a listing this tool cannot read; "
                       "refusing, and nothing was uploaded")
    volid = f"{storage}:iso/{volume_name}"
    if any(isinstance(v, dict) and v.get("volid") == volid for v in listing):
        raise PveError(f"{volid} already exists; not overwriting it. Removing it is an owner step "
                       "(this tool cannot delete), or pick another VM name")


def _verify_for(ws: Path, cfg: dict):
    ca = cfg.get("ca_file")
    if not ca:
        return "system"
    path = Path(str(ca)).expanduser()
    if not path.is_absolute():
        path = Path(ws) / path
    if not path.is_file():
        raise PveError(f"ca_file {path} does not exist")
    return str(path)


def _api_base(host: str, cfg: dict) -> str:
    address = cfg.get("address")
    if not isinstance(address, str) or not ADDRESS.match(address):
        raise PveError(f"set hosts.{host}.address in site.yaml (the server's IP or DNS name)")
    if ":" in address:
        address = f"[{address}]"
    return _check_base_url(f"https://{address}:8006{API_PREFIX}")


def _pick_host(site: dict, requested: str | None, from_spec: str | None = None) -> tuple[str, dict]:
    hosts = site.get("hosts")
    if not isinstance(hosts, dict) or not hosts:
        raise PveError("site.yaml has no hosts")
    if requested and from_spec and requested != from_spec:
        raise PveError(f"--host {requested} does not match the VM's host {from_spec}")
    key = requested or from_spec
    if not key:
        if len(hosts) != 1:
            raise PveError("several hosts in site.yaml; pass --host <key>")
        key = next(iter(hosts))
    cfg = hosts.get(key)
    if not isinstance(cfg, dict):
        raise PveError(f"host {key!r} is not in site.yaml")
    return key, cfg


def _node(host: str, cfg: dict) -> str:
    node = cfg.get("node") or host
    if not isinstance(node, str) or not NODE_NAME.match(node):
        raise PveError(f"hosts.{host}.node is not a valid node name")
    return node


def _connect(ws: Path, host: str, cfg: dict) -> PveClient:
    who, material = load_token(ws, host)
    return PveClient(_api_base(host, cfg), who, material, _verify_for(ws, cfg))


def _load_yaml_mapping(path: Path) -> dict:
    yaml = workspace._yaml()
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        raise PveError(f"cannot read {path} as YAML") from None
    if not isinstance(data, dict):
        raise PveError(f"{path} must be a mapping")
    return data


def _spec_path(ws: Path, arg: str) -> Path:
    path = Path(arg).expanduser()
    if not path.is_absolute():
        path = Path(ws) / path
    path = path.resolve()
    vms = (Path(ws) / "vms").resolve()
    if path.name != "vm.yaml" or vms not in path.parents:
        raise PveError(f"VM spec must be {vms}/<vm>/vm.yaml")
    if not path.is_file():
        raise PveError(f"no VM spec at {path}")
    return path


def _resolve_vm(ws: Path, site: dict, arg: str, requested: str | None):
    """(host key, host cfg, vmid, expected name or None) for a name or VMID."""
    if arg.isdigit():
        host, cfg = _pick_host(site, requested)
        return host, cfg, int(arg), None
    if not VM_NAME.match(arg):
        raise PveError(f"{arg!r} is neither a VM name nor a VMID")
    spec = _load_yaml_mapping(_spec_path(ws, f"vms/{arg}/vm.yaml"))
    vmid = spec.get("vmid")
    if isinstance(vmid, bool) or not isinstance(vmid, int):
        raise PveError(f"vms/{arg}/vm.yaml has no vmid")
    host_from_spec = spec.get("host") if isinstance(spec.get("host"), str) else None
    host, cfg = _pick_host(site, requested, host_from_spec)
    return host, cfg, vmid, arg


def cmd_check(ws: Path, site: dict, args) -> int:
    host, cfg = _pick_host(site, args.host)
    client = _connect(ws, host, cfg)
    version = _data(client.get("/version"))
    if isinstance(version, dict):
        print(f"Proxmox VE {version.get('version', '?')} reachable; token {client.principal}")
    permissions = _data(client.get("/access/permissions"))
    if not isinstance(permissions, dict) or not permissions:
        raise PveError("the token has no permissions at all")
    for path in sorted(permissions):
        privs = permissions[path]
        names = sorted(privs) if isinstance(privs, dict) else []
        print(f"{path}: {' '.join(names) if names else '(none)'}")
    if f"/pool/{POOL}" not in permissions:
        print(f"warning: the token has no rights on /pool/{POOL}", file=sys.stderr)
        return 1
    return 0


def cmd_list(ws: Path, site: dict, args) -> int:
    host, cfg = _pick_host(site, args.host)
    client = _connect(ws, host, cfg)
    rows = list(pool_members(client).values())
    for item in sorted(rows, key=lambda r: r.get("vmid", 0)):
        print(f"{item.get('vmid')}\t{item.get('name', '')}\t{item.get('node', '')}\t{item.get('status', '')}")
    if not rows:
        print(f"no VMs in pool {POOL}")
    return 0


def cmd_create(ws: Path, site: dict, args) -> int:
    spec_path = _spec_path(ws, args.spec)
    spec = _load_yaml_mapping(spec_path)
    from_spec = spec.get("host") if isinstance(spec.get("host"), str) else None
    host, cfg = _pick_host(site, args.host, from_spec)
    node = _node(host, cfg)
    ignition = spec.get("ignition")
    use_iso = isinstance(ignition, dict) and ignition.get("method") == "nocloud-iso"
    iso_storage = cfg.get("iso_storage")
    ign_file = spec_path.parent / f"{spec.get('name')}.ign"
    if use_iso:
        if not isinstance(iso_storage, str) or not STORAGE_ID.match(iso_storage):
            raise PveError(f"ignition method nocloud-iso needs hosts.{host}.iso_storage in site.yaml "
                           "(a storage that holds ISO images); it is not set")
        if not ign_file.is_file():
            raise PveError(f"no Ignition file at {ign_file}; build the VM first")
    for key, limit_key in (("cores", "max_cores"), ("ram_mib", "max_ram_mib")):
        limit = cfg.get(limit_key)
        if isinstance(limit, int) and not isinstance(limit, bool) and isinstance(spec.get(key), int) \
                and spec[key] > limit:
            raise PveError(f"{key} {spec[key]} is above {limit_key} {limit} for host {host}")
    client = _connect(ws, host, cfg)
    members = pool_members(client)  # before any write: refuses without Pool.Audit
    visible = vm_resources(client)
    existing = {item["vmid"] for item in visible if isinstance(item.get("vmid"), int)}
    vmid = spec.get("vmid")
    if isinstance(vmid, int) and not isinstance(vmid, bool) and vmid not in existing:
        try:
            client.get(f"/cluster/nextid?vmid={vmid}")
        except PveError as exc:
            if "HTTP 400" not in str(exc):
                raise
            existing.add(vmid)
    if any(item.get("name") == spec.get("name") for item in members.values()):
        raise PveError(f"a VM named {spec.get('name')} already exists in pool {POOL}")
    plan = plan_create(spec, existing, node, cfg.get("snippets_storage"), iso_storage)
    check_setting_rights(client, next(p for m, _, p in plan if m == "POST"))
    interfaces = _data(client.get(f"/nodes/{node}/network"))
    problems, warnings = check_network(spec, host, cfg, interfaces if isinstance(interfaces, list) else [])
    for line in warnings:
        print(f"warning: {line}", file=sys.stderr)
    if problems:
        raise PveError("network check failed, nothing was sent:\n  " + "\n  ".join(problems))
    if args.dry_run:
        # The owner reviews every setting with its reason before anything is sent.
        print("| Setting | Will use | Why | Source |\n|---|---|---|---|")
        for row in settings_table(spec):
            print("| " + " | ".join(cell.replace("|", "/") for cell in row) + " |")
        for title, rows in (("Fixed by the tool", FIXED_SETTINGS), ("Left at Proxmox's default (those that matter for this VM)", DEFAULT_SETTINGS)):
            print(f"\n{title}:\n\n| Setting | Value | Why | Source |\n|---|---|---|---|")
            for key, (value, why, source) in rows.items():
                print(f"| {key} | {value} | {why} | {source} |")
        print()
        for method, path, params in plan:
            note = ("  (tags: sent after the create; if it fails the VM stays, untagged)"
                    if method == "PUT" and set(params) == {"tags"} else "")
            print(f"{method} {path} {json.dumps(params, sort_keys=True)}{note}")
    iso_bytes = b""
    if use_iso:
        check_iso_upload(client, node, iso_storage, iso_file_name(spec["name"]))
        if not args.dry_run:
            with tempfile.TemporaryDirectory(prefix="pve-iso-") as scratch:
                built = Path(scratch) / "ign.iso"
                build_iso(ign_file, built)
                if built.stat().st_size > MAX_ISO:
                    raise PveError(f"the config ISO is larger than {MAX_ISO} bytes; refusing")
                iso_bytes = built.read_bytes()
    if args.dry_run:
        print("dry run: nothing was sent")
        return 0
    for method, path, params in plan:
        if method == "UPLOAD":
            response = client.upload(path, {"content": params["content"]}, params["filename"], iso_bytes)
            task = _data(response)
            if isinstance(task, str) and task.startswith("UPID:"):
                wait_task(client, node, task)
        elif method == "PUT" and set(params) == {"tags"}:
            # Tags only: the VM already exists, so a failure here must not hide it or its MAC.
            try:
                run_task(client, method, node, path, params)
            except PveError as exc:
                print(f"warning: tags were not set ({exc}); the VM was created. Add them in Proxmox "
                      "(VM > Summary > Tags) or check the datacenter's tag settings", file=sys.stderr)
                continue
        else:
            run_task(client, method, node, path, params)
        print(f"done: {method} {path}")
    require_in_pool(client, spec["vmid"])
    print(f"VM {spec['vmid']} ({spec['name']}) created in pool {POOL}; not started")
    mac = vm_mac(client, node, spec["vmid"])
    if mac:
        print(f"MAC address: {mac} (reserve its address in DHCP before pve.py start, "
              "if the network only serves reserved addresses)")
    else:
        print("MAC address: not reported; read it in Proxmox (VM > Hardware > Network Device)")
    return 0


def cmd_start(ws: Path, site: dict, args) -> int:
    host, cfg, vmid, name = _resolve_vm(ws, site, args.vm, args.host)
    client = _connect(ws, host, cfg)
    item = require_in_pool(client, vmid)
    if name and item.get("name") != name:
        raise PveError(f"VM {vmid} in the pool is not named {name}; refusing")
    node = item["node"]
    run_task(client, "POST", node, f"/nodes/{node}/qemu/{vmid}/status/start")
    print(f"VM {vmid} started")
    return 0


def cmd_status(ws: Path, site: dict, args) -> int:
    host, cfg, vmid, name = _resolve_vm(ws, site, args.vm, args.host)
    client = _connect(ws, host, cfg)
    item = require_in_pool(client, vmid)
    if name and item.get("name") != name:
        raise PveError(f"VM {vmid} in the pool is not named {name}; refusing")
    node = item["node"]
    current = _data(client.get(f"/nodes/{node}/qemu/{vmid}/status/current"))
    current = current if isinstance(current, dict) else {}
    print(f"{vmid}\t{current.get('name', item.get('name', ''))}\t{current.get('status', '?')}"
          f"\tuptime={current.get('uptime', 0)}\tmac={vm_mac(client, node, vmid) or '?'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pve.py", allow_abbrev=False,
                                     description="Create and start FCOS VMs in the fcos-agent pool.")
    common = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    common.add_argument("--host", help="host key from site.yaml")
    common.add_argument("--workspace", help="workspace path (default: FCOS_WORKSPACE or the remembered one)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", parents=[common], allow_abbrev=False, help="validate the token and show its permissions")
    sub.add_parser("list", parents=[common], allow_abbrev=False, help="list VMs in the pool")
    create = sub.add_parser("create", parents=[common], allow_abbrev=False, help="create a VM from vms/<vm>/vm.yaml")
    create.add_argument("spec")
    create.add_argument("--dry-run", action="store_true", help="print the plan; send no changes")
    for name, text in (("start", "start a VM in the pool"), ("status", "show a VM's state")):
        one = sub.add_parser(name, parents=[common], allow_abbrev=False, help=text)
        one.add_argument("vm", help="VM name under vms/, or a VMID")
    return parser


COMMANDS = {"check": cmd_check, "list": cmd_list, "create": cmd_create,
            "start": cmd_start, "status": cmd_status}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        ws = workspace.resolve_workspace(args.workspace)
        site = workspace.load_site(ws)
        return COMMANDS[args.command](ws, site, args)
    except (PveError, WorkspaceError) as exc:
        print(f"pve: {scrub(exc)}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - never show a traceback that could carry the token
        print(f"pve: unexpected {type(exc).__name__}: {_oneline(exc)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
