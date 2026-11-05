import contextlib
import io
import os
import ssl
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

import pve  # noqa: E402
from fake_pve import FakePve  # noqa: E402
from pve import PveClient, PveError, load_token, plan_create  # noqa: E402

REAL_API_BASE = pve._api_base
REAL_BUILD_ISO = pve.build_iso
# The old test-only override; production code must ignore it.
TEST_URL = "FCOS_PVE_TEST_BASE_URL"
# The fixed fake token tests/run_pve_against_fake.py uses (never a real one).
WRAPPER_SECRET = "-".join(["00000000", "0000", "0000", "0000", "000000000000"])
# Built at runtime so this file never holds a secret-looking literal.
SECRET = "-".join(["1a2b3c4d", "5e6f", "7a8b", "9c0d", "1e2f3a4b5c6d"])
PRINCIPAL = "fcos-agent@pve!fcos-bootstrap"

SITE = """\
hosts:
  host-a:
    name: pve-a
    node: pve-a
    address: 192.0.2.21
    ca_file: null
    storage: local-lvm
    snippets_storage: coreos
    iso_storage: isos
    bridge: vmbr0
    max_cores: 4
    max_ram_mib: 8192
"""

SPEC_ISO = """\
name: edge
host: host-a
vmid: 201
cores: 2
ram_mib: 4096
os_disk_gib: 20
data_disk_gib: 10
storage: local-lvm
bridge: vmbr0
vlan_tag: null
image_volume: local:import/fedora-coreos-test.qcow2
ignition:
  method: nocloud-iso
"""

IGN_BYTES = b'{"ignition":{"version":"3.6.0"}}'
ISO_PRIVS = {"Datastore.AllocateTemplate": 1, "Datastore.Audit": 1, "Datastore.AllocateSpace": 1}

SPEC = """\
name: edge
host: host-a
vmid: 201
cores: 2
ram_mib: 4096
os_disk_gib: 20
data_disk_gib: 10
storage: local-lvm
bridge: vmbr0
vlan_tag: null
image_volume: local:import/fedora-coreos-test.qcow2
ignition:
  method: snippet
  volume: coreos:snippets/edge.ign
"""


def setting(value):
    return {"use": value, "why": "example reason", "source": "example source"}


# Every VM setting the agent must decide (owner rule 2026-10-31), example values.
SETTINGS = {
    "cpu": "host", "cpu_flags": [], "sockets": 1, "numa": False, "cpuunits": 100, "cpulimit": 0,
    "balloon": "on", "allow_ksm": True, "bios": "seabios", "machine": "pc", "disk_cache": "none",
    "disk_aio": "io_uring", "discard": True, "ssd": True, "nic_model": "virtio", "nic_queues": 2,
    "nic_firewall": False, "rng": "urandom", "tablet": False, "hotplug": "network,disk,usb",
    "startup_order": None, "startup_up": None, "onboot": True, "protection": True, "agent": False,
    "watchdog": "none", "acpi": True, "kvm": True, "localtime": False, "tags": ["fcos-agent"],
    "description": "Example VM",
}


def fixture_spec(settings=None, **changes):
    spec = {
        "name": "edge", "host": "host-a", "vmid": 201, "cores": 2, "ram_mib": 4096,
        "os_disk_gib": 20, "data_disk_gib": 10, "storage": "local-lvm", "bridge": "vmbr0",
        "vlan_tag": None, "image_volume": "local:import/fedora-coreos-test.qcow2",
        "ignition": {"method": "snippet", "volume": "coreos:snippets/edge.ign"},
        "settings": {k: setting(v) for k, v in dict(SETTINGS, **(settings or {})).items()},
    }
    spec.update(changes)
    return spec


import yaml  # noqa: E402

SETTINGS_YAML = yaml.safe_dump({"settings": {k: setting(v) for k, v in SETTINGS.items()}}, sort_keys=False)
SPEC = SPEC + SETTINGS_YAML
SPEC_ISO = SPEC_ISO + SETTINGS_YAML


class SettingsTests(unittest.TestCase):
    """Every VM setting is decided, explained, checked and sent explicitly."""

    def params(self, **settings):
        return plan_create(fixture_spec(settings), set(), snippets_storage="coreos")[0][2]

    def test_every_setting_reaches_proxmox(self):
        p = self.params()
        for key, value in {"cpu": "host", "sockets": 1, "numa": 0, "cpuunits": 100, "cpulimit": 0,
                           "balloon": 4096, "allow-ksm": 1, "bios": "seabios", "machine": "pc",
                           "rng0": "source=/dev/urandom", "tablet": 0, "hotplug": "network,disk,usb",
                           "onboot": 1, "protection": 1, "agent": 0, "acpi": 1,
                           "kvm": 1, "localtime": 0, "description": "Example VM"}.items():
            self.assertEqual(p[key], value, key)
        for disk in ("scsi0", "scsi1"):
            self.assertIn("iothread=1,cache=none,aio=io_uring,discard=on,ssd=1", p[disk])
        self.assertEqual(p["net0"], "virtio,bridge=vmbr0,firewall=0,queues=2")
        self.assertNotIn("watchdog", p)

    def test_values_map_correctly(self):
        p = self.params(cpu_flags=["+pcid", "-md-clear"], balloon="off", numa=True, rng="none",
                        startup_order=None, ssd=False, discard=False, startup_up=None, tags=["a", "b"])
        self.assertEqual(p["cpu"], "host,flags=+pcid;-md-clear")
        self.assertEqual(p["balloon"], 0)
        self.assertEqual(p["numa"], 1)
        self.assertNotIn("rng0", p)
        self.assertNotIn("startup", p)
        self.assertIn("discard=ignore", p["scsi1"])
        self.assertNotIn("ssd=1", p["scsi1"])
        tags_step = plan_create(fixture_spec({"tags": ["a", "b"]}), set(), snippets_storage="coreos")[-1]
        self.assertEqual(tags_step, ("PUT", "/nodes/host-a/qemu/201/config", {"tags": "a;b"}))
        self.assertNotIn("tags", p)
        self.assertEqual(self.params(startup_order=3, startup_up=60)["startup"], "order=3,up=60")

    def test_missing_or_unexplained_settings_refused(self):
        spec = fixture_spec()
        del spec["settings"]["rng"]
        with self.assertRaisesRegex(PveError, "rng"):
            plan_create(spec, set(), snippets_storage="coreos")
        spec = fixture_spec()
        spec["settings"]["tablet"]["why"] = ""
        with self.assertRaisesRegex(PveError, "tablet"):
            plan_create(spec, set(), snippets_storage="coreos")
        spec = fixture_spec()
        spec["settings"]["surprise"] = setting(1)
        with self.assertRaisesRegex(PveError, "surprise"):
            plan_create(spec, set(), snippets_storage="coreos")
        with self.assertRaisesRegex(PveError, "settings"):
            plan_create(fixture_spec(ssd=True), set(), snippets_storage="coreos")  # old top-level key

    def test_bad_values_refused(self):
        for key, bad in (("cpu_flags", ["+evil"]), ("cpu_flags", ["pcid"]), ("cpu", "host,flags=+x"), ("cpu", "custom-mine"),
                         ("balloon", "maybe"), ("bios", "ovmf"), ("machine", "pc;x"), ("disk_cache", "unsafe"),
                         ("disk_aio", "x"), ("nic_model", "e1000"), ("nic_queues", 0), ("nic_queues", 9),
                         ("rng", "/dev/random"), ("hotplug", "network;x"), ("startup_order", -1),
                         ("cpuunits", 0), ("tags", ["bad tag"]), ("description", "a\nb"), ("watchdog", "x"),
                         ("numa", "yes"), ("sockets", 0)):
            with self.subTest(key=key, bad=bad), self.assertRaisesRegex(PveError, key):
                self.params(**{key: bad})

    def test_combinations_proxmox_or_qemu_refuse(self):
        # VM chapter: NUMA is required to hot-plug cores or RAM; QEMU's aio=native needs direct I/O.
        for bad in ({"hotplug": "network,memory"}, {"hotplug": "cpu"}):
            with self.subTest(bad=bad), self.assertRaisesRegex(PveError, "numa"):
                self.params(**bad)
        self.params(hotplug="network,memory", numa=True)
        for cache in ("writeback", "writethrough"):
            with self.subTest(cache=cache), self.assertRaisesRegex(PveError, "disk_aio"):
                self.params(disk_aio="native", disk_cache=cache)
        self.params(disk_aio="native", disk_cache="none")

    def test_guide_example_passes_the_checks(self):
        text = (ROOT / "docs" / "guide" / "02-build-a-vm.md").read_text()
        block = text.split("```yaml\nname: <vm>", 1)[1].split("```", 1)[0]
        example = yaml.safe_load("name: <vm>" + block)
        spec = fixture_spec(settings={k: v["use"] for k, v in example["settings"].items()})
        spec["settings"] = example["settings"]
        self.assertEqual(sorted(example["settings"]), sorted(pve.SETTING_KEYS))
        plan_create(spec, set(), snippets_storage="coreos")

    def test_table_lists_every_setting_with_reason_and_source(self):
        rows = pve.settings_table(fixture_spec())
        self.assertEqual(len(rows), len(SETTINGS))
        self.assertIn(("rng", "urandom", "example reason", "example source"), rows)


class PveCase(unittest.TestCase):
    """A throwaway HOME and workspace, a fake Proxmox, a token file."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()
        home = self.tmp / "home"
        home.mkdir()
        self.ws = self.tmp / "ws"
        (self.ws / "secrets").mkdir(parents=True)
        (self.ws / "secrets").chmod(0o700)
        (self.ws / "vms" / "edge").mkdir(parents=True)
        (self.ws / "site.yaml").write_text(SITE)
        (self.ws / "vms" / "edge" / "vm.yaml").write_text(SPEC)
        self.token = self.ws / "secrets" / "proxmox-host-a.token"
        self.write_token(SECRET)

        self.fake = FakePve(SECRET).start()
        self.addCleanup(self.fake.stop)
        env = {k: v for k, v in os.environ.items() if k not in ("FCOS_WORKSPACE", TEST_URL)}
        env.update({"HOME": str(home), "FCOS_WORKSPACE": str(self.ws)})
        patcher = mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        # The only way to reach the fake: patch the base-URL resolver in this process.
        patcher = mock.patch.object(pve, "_api_base", lambda host, cfg: self.fake.url + "/api2/json")
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch.object(pve, "POLL_SECONDS", 0)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.env = env

    def write_token(self, secret, mode=0o600):
        self.token.write_text(f"{PRINCIPAL}={secret}\n")
        self.token.chmod(mode)

    def fake_accepts(self, value):
        self.fake.secret = value

    def client(self, material=None):
        return PveClient(self.fake.url + "/api2/json", PRINCIPAL, material or SECRET, True)

    def run_pve(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = pve.main(list(argv))
        return code, out.getvalue(), err.getvalue()


def bridge(iface="vmbr0", **extra):
    entry = {"iface": iface, "type": "bridge", "active": 1}
    entry.update(extra)
    return entry


LAN = bridge("vmbr9", bridge_vlan_aware=1, bridge_vids="2-4094", mtu=9000, comments="LAN")
WAN = bridge("vmbr0", comments="WAN")
HOST = {"bridge": "vmbr9", "forbidden_bridges": ["vmbr0"]}


class NetworkCheckTests(unittest.TestCase):
    """pve.check_network: refuse what qemu-server or the owner's network would reject."""

    def check(self, spec_changes, host=None, interfaces=None):
        spec = fixture_spec(**dict({"bridge": "vmbr9"}, **spec_changes))
        return pve.check_network(spec, "host-a", HOST if host is None else host,
                                 [WAN, LAN] if interfaces is None else interfaces)

    def test_matching_bridge_tag_and_mtu_pass(self):
        self.assertEqual(self.check({"vlan_tag": 30, "mtu": 9000}), ([], []))
        self.assertEqual(self.check({"mtu": 1}), ([], []))  # 1 = use the bridge's MTU

    def test_forbidden_bridge_refused(self):
        problems, _ = self.check({"bridge": "vmbr0"}, host={"bridge": "vmbr0", "forbidden_bridges": ["vmbr0"]})
        self.assertTrue(any("forbidden" in p and "vmbr0" in p for p in problems), problems)

    def test_host_without_a_bridge_refuses(self):
        # Without hosts.<key>.bridge the agent can't tell which network is allowed.
        problems, warnings = self.check({"bridge": "vmbr0"}, host={})
        self.assertTrue(any("which network" in p for p in problems), problems)
        # Owner decision 2026-10-31: no "never use" question; its absence is no warning.
        self.assertEqual(self.check({}, host={"bridge": "vmbr9"}), ([], []))

    def test_messages_are_plain_with_the_key_at_the_end(self):
        problems, _ = self.check({"bridge": "vmbr0"}, host={"bridge": "vmbr0", "forbidden_bridges": ["vmbr0"]})
        message = next(p for p in problems if "forbidden" in p)
        self.assertTrue(message.startswith("network vmbr0 must never get a machine"), message)
        self.assertTrue(message.endswith("(hosts.host-a.forbidden_bridges)"), message)

    def test_tag_on_a_plain_bridge_is_refused_for_the_right_reason(self):
        # Proxmox would create <port>.<tag> and <bridge>v<tag> on the server (wiki,
        # Network Configuration, VLAN): a change to the owner's network.
        problems, _ = self.check({"vlan_tag": 30}, interfaces=[WAN, bridge("vmbr9", mtu=9000, bridge_ports="enp2s0")])
        message = next(p for p in problems if "VLAN 30" in p)
        self.assertIn("vmbr9v30", message)
        self.assertIn("enp2s0.30", message)
        self.assertIn("changes your network", message)

    def test_unreadable_allowed_vlans_refused(self):
        problems, _ = self.check({"vlan_tag": 30}, interfaces=[WAN, dict(LAN, bridge_vids="2-4094;x")])
        self.assertTrue(any("can't read" in p for p in problems), problems)
        # The full VLAN range is accepted.
        self.assertEqual(self.check({"vlan_tag": 30}, interfaces=[WAN, dict(LAN, bridge_vids="1-4094")])[0], [])

    def test_mtu_may_come_back_as_text(self):
        self.assertEqual(self.check({"mtu": 9000}, interfaces=[WAN, dict(LAN, mtu="9000")]), ([], []))
        problems, _ = self.check({"mtu": 9000}, interfaces=[WAN, dict(LAN, mtu="1500")])
        self.assertTrue(problems)

    def test_inactive_bridge_and_other_vlan_warn(self):
        _, warnings = self.check({"vlan_tag": 30}, interfaces=[WAN, dict(LAN, active=0)])
        self.assertTrue(any("not active" in w for w in warnings), warnings)
        down = {k: v for k, v in LAN.items() if k != "active"}  # the API leaves it out when down
        _, warnings = self.check({"vlan_tag": 30}, interfaces=[WAN, down])
        self.assertTrue(any("not active" in w for w in warnings), warnings)
        _, warnings = self.check({"vlan_tag": 40}, host=dict(HOST, vlan_tag=30))
        self.assertTrue(any("VLAN 40" in w and "30" in w for w in warnings), warnings)

    def test_bridge_must_be_the_hosts_bridge(self):
        problems, _ = self.check({"bridge": "vmbr7"}, interfaces=[WAN, LAN, bridge("vmbr7")])
        self.assertTrue(any("hosts.host-a.bridge" in p for p in problems), problems)

    def test_missing_bridge_lists_the_bridges(self):
        problems, _ = self.check({}, interfaces=[WAN])
        self.assertTrue(any("vmbr9" in p and "does not exist" in p and "vmbr0" in p for p in problems), problems)

    def test_vlan_tag_needs_a_vlan_aware_bridge(self):
        problems, _ = self.check({"vlan_tag": 30}, interfaces=[WAN, bridge("vmbr9", mtu=9000)])
        self.assertTrue(any("VLAN 30" in p and "refused" in p for p in problems), problems)

    def test_vlan_tag_must_be_allowed(self):
        lan = dict(LAN, bridge_vids="10 20-29,40")
        for tag, ok in ((10, True), (25, True), (40, True), (30, False), (1, False)):
            with self.subTest(tag=tag):
                problems, _ = self.check({"vlan_tag": tag}, interfaces=[WAN, lan])
                self.assertEqual(problems == [], ok, problems)

    def test_unknown_allowed_vlans_only_warn(self):
        lan = {k: v for k, v in LAN.items() if k != "bridge_vids"}
        problems, warnings = self.check({"vlan_tag": 30}, interfaces=[WAN, lan])
        self.assertEqual(problems, [])
        self.assertTrue(any("bridge-vids" in w for w in warnings), warnings)

    def test_ovs_bridge_carries_tags_without_vlan_aware(self):
        ovs = {"iface": "vmbr9", "type": "OVSBridge", "mtu": 9000, "active": 1}
        self.assertEqual(self.check({"vlan_tag": 30}, interfaces=[WAN, ovs]), ([], []))

    def test_nic_mtu_not_above_the_bridge(self):
        problems, _ = self.check({"mtu": 9000}, interfaces=[WAN, dict(LAN, mtu=1500)])
        self.assertTrue(any("9000" in p and "1500" in p for p in problems), problems)
        # A bridge that reports no MTU: a size above the Linux default can't be confirmed.
        lan = {k: v for k, v in LAN.items() if k != "mtu"}
        problems, _ = self.check({"mtu": 9000}, interfaces=[WAN, lan])
        self.assertTrue(any("doesn't report" in p and "mtu 1" in p for p in problems), problems)
        self.assertEqual(self.check({"mtu": 1500}, interfaces=[WAN, lan])[0], [])

    def test_mac_from_net0(self):
        self.assertEqual(pve.mac_from_net("virtio=BC:24:11:00:00:01,bridge=vmbr9,tag=30"), "BC:24:11:00:00:01")
        self.assertIsNone(pve.mac_from_net("virtio,bridge=vmbr9"))
        self.assertIsNone(pve.mac_from_net(None))


class PlanTests(unittest.TestCase):
    def test_plan_create_settings(self):
        plan = plan_create(fixture_spec(), set(), snippets_storage="coreos")
        (method, path, params), resize, _tags = plan
        self.assertEqual((method, path), ("POST", "/nodes/host-a/qemu"))
        for key, value in {
            "cpu": "host", "scsihw": "virtio-scsi-single", "pool": "fcos-agent", "protection": 1,
            "agent": 0, "onboot": 1, "serial0": "socket", "vga": "serial0", "vmid": 201,
            "name": "edge", "cores": 2, "memory": 4096, "boot": "order=scsi0",
        }.items():
            self.assertEqual(params[key], value, key)
        opts = "iothread=1,cache=none,aio=io_uring,discard=on,ssd=1"
        self.assertEqual(params["scsi0"], f"local-lvm:0,import-from=local:import/fedora-coreos-test.qcow2,{opts}")
        self.assertEqual(params["scsi1"], f"local-lvm:10,{opts}")
        self.assertEqual(params["net0"], "virtio,bridge=vmbr0,firewall=0,queues=2")
        self.assertEqual(params["cicustom"], "vendor=coreos:snippets/edge.ign")
        self.assertEqual(params["ide2"], "local-lvm:cloudinit")
        self.assertEqual(params["ciupgrade"], 0)
        self.assertEqual(resize, ("PUT", "/nodes/host-a/qemu/201/resize", {"disk": "scsi0", "size": "20G"}))

    def test_plan_uses_node_and_vlan(self):
        plan = plan_create(fixture_spec(vlan_tag=30), set(), node="pve-a", snippets_storage="coreos")
        self.assertEqual(plan[0][1], "/nodes/pve-a/qemu")
        self.assertEqual(plan[0][2]["net0"], "virtio,bridge=vmbr0,tag=30,firewall=0,queues=2")

    def test_plan_sets_nic_mtu(self):
        plan = plan_create(fixture_spec(vlan_tag=30, mtu=9000), set(), node="pve-a",
                           snippets_storage="coreos")
        self.assertEqual(plan[0][2]["net0"], "virtio,bridge=vmbr0,tag=30,mtu=9000,firewall=0,queues=2")
        plan = plan_create(fixture_spec(mtu=1), set(), snippets_storage="coreos")
        self.assertEqual(plan[0][2]["net0"], "virtio,bridge=vmbr0,mtu=1,firewall=0,queues=2")
        plan = plan_create(fixture_spec(mtu=None), set(), snippets_storage="coreos")
        self.assertEqual(plan[0][2]["net0"], "virtio,bridge=vmbr0,firewall=0,queues=2")

    def test_nic_queues_never_exceed_the_vcpus(self):
        # Proxmox VM chapter: multiqueue equal to the number of vCPUs (sockets x cores).
        with self.assertRaisesRegex(PveError, "nic_queues"):
            plan_create(fixture_spec({"nic_queues": 3}), set(), snippets_storage="coreos")

    def test_plan_rejects_bad_mtu(self):
        for mtu in (0, 2, 575, 65521, True, "9000", 9000.0, "9000,firewall=0"):
            with self.subTest(mtu=mtu), self.assertRaisesRegex(PveError, "mtu"):
                plan_create(fixture_spec(mtu=mtu), set(), snippets_storage="coreos")

    def test_plan_refuses_existing_vmid(self):
        with self.assertRaisesRegex(PveError, "201.*in use"):
            plan_create(fixture_spec(), {201}, snippets_storage="coreos")

    def test_plan_rejects_bad_values(self):
        for changes in ({"storage": "a,b"}, {"bridge": "vmbr0,firewall=0"}, {"name": "Bad Name"},
                        {"cores": 0}, {"cores": True}, {"vlan_tag": 5000}, {"vmid": 5},
                        {"image_volume": "../x"}, {"ignition": {"method": "bogus"}}):
            with self.subTest(changes=changes), self.assertRaises(PveError):
                plan_create(fixture_spec(**changes), set(), snippets_storage="coreos")

    def test_cicustom_derived_from_snippets_storage_and_vm_name(self):
        spec = fixture_spec(ignition={"method": "snippet"})
        params = plan_create(spec, set(), snippets_storage="snipstore")[0][2]
        self.assertEqual(params["cicustom"], "vendor=snipstore:snippets/edge.ign")

    def test_spec_volume_that_matches_is_accepted(self):
        params = plan_create(fixture_spec(), set(), snippets_storage="coreos")[0][2]
        self.assertEqual(params["cicustom"], "vendor=coreos:snippets/edge.ign")

    def test_spec_volume_that_differs_is_refused(self):
        spec = fixture_spec(ignition={"method": "snippet", "volume": "other:snippets/edge.ign"})
        with self.assertRaisesRegex(PveError, "ignition.volume.*coreos:snippets/edge.ign"):
            plan_create(spec, set(), snippets_storage="coreos")

    def test_snippets_storage_required_and_checked(self):
        for bad in (None, "", "a,b", "a:b"):
            with self.subTest(bad=bad), self.assertRaisesRegex(PveError, "snippets_storage"):
                plan_create(fixture_spec(), set(), snippets_storage=bad)

    def test_nocloud_iso_plan_uploads_then_attaches_a_cdrom(self):
        spec = fixture_spec(ignition={"method": "nocloud-iso"})
        upload, (method, path, params), resize, _tags = plan_create(spec, set(), iso_storage="isos")
        self.assertEqual(upload, ("UPLOAD", "/nodes/host-a/storage/isos/upload",
                                  {"content": "iso", "filename": "fcos-edge-ign.iso"}))
        self.assertEqual((method, path), ("POST", "/nodes/host-a/qemu"))
        self.assertEqual(params["ide2"], "isos:iso/fcos-edge-ign.iso,media=cdrom")
        for key in ("cicustom", "ciupgrade", "ciuser", "cipassword", "sshkeys", "ipconfig0"):
            self.assertNotIn(key, params)
        self.assertNotIn("cloudinit", " ".join(str(v) for v in params.values()))
        snippet = plan_create(fixture_spec(), set(), snippets_storage="coreos")[0][2]
        differing = {k for k in set(snippet) | set(params) if snippet.get(k) != params.get(k)}
        self.assertEqual(differing, {"ide2", "cicustom", "ciupgrade"})
        self.assertEqual(resize, ("PUT", "/nodes/host-a/qemu/201/resize", {"disk": "scsi0", "size": "20G"}))

    def test_nocloud_iso_upload_uses_the_node(self):
        spec = fixture_spec(ignition={"method": "nocloud-iso"})
        plan = plan_create(spec, set(), node="pve-a", iso_storage="isos")
        self.assertEqual(plan[0][1], "/nodes/pve-a/storage/isos/upload")

    def test_nocloud_iso_needs_iso_storage(self):
        spec = fixture_spec(ignition={"method": "nocloud-iso"})
        for bad in (None, "", "a,b", "a:b"):
            with self.subTest(bad=bad), self.assertRaisesRegex(PveError, "iso_storage"):
                plan_create(spec, set(), snippets_storage="coreos", iso_storage=bad)

    def test_nocloud_iso_volume_that_differs_is_refused(self):
        spec = fixture_spec(ignition={"method": "nocloud-iso", "volume": "isos:iso/other.iso"})
        with self.assertRaisesRegex(PveError, "ignition.volume.*isos:iso/fcos-edge-ign.iso"):
            plan_create(spec, set(), iso_storage="isos")
        spec = fixture_spec(ignition={"method": "nocloud-iso", "volume": "isos:iso/fcos-edge-ign.iso"})
        self.assertEqual(plan_create(spec, set(), iso_storage="isos")[1][2]["ide2"],
                         "isos:iso/fcos-edge-ign.iso,media=cdrom")


class SafetyTests(PveCase):
    def test_refuses_existing_vmid(self):
        self.fake.add_vm(201, "other", pool="fcos-agent")
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml")
        self.assertEqual(code, 1)
        self.assertIn("201", err)
        self.assertEqual(self.fake.writes(), [])

    def test_refuses_vmid_taken_outside_the_pool(self):
        self.fake.taken.add(201)
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml")
        self.assertEqual(code, 1)
        self.assertIn("201", err)
        self.assertEqual(self.fake.writes(), [])

    def test_refuses_vm_outside_pool(self):
        self.fake.add_vm(300, "stranger", pool="other")
        for command in ("start", "status"):
            for target in ("300", "301"):  # 300 in another pool, 301 not visible at all
                with self.subTest(command=command, target=target):
                    code, out, err = self.run_pve(command, target)
                    self.assertEqual(code, 1)
                    self.assertIn("refusing", err)
        self.assertEqual(self.fake.writes(), [])
        with self.assertRaises(PveError):
            pve.require_in_pool(self.client(), 300)

    def test_start_by_name_checks_pool_and_starts(self):
        self.fake.add_vm(201, "edge")
        code, out, err = self.run_pve("start", "edge")
        self.assertEqual(code, 0, err)
        posts = [r["path"] for r in self.fake.writes()]
        self.assertEqual(posts, ["/api2/json/nodes/pve-a/qemu/201/status/start"])
        self.assertIn("started", out)
        code, out, err = self.run_pve("status", "edge")
        self.assertEqual(code, 0, err)
        self.assertIn("running", out)

    def test_membership_comes_from_the_pool_member_list(self):
        # Real PVE 9.2: /cluster/resources may carry no `pool` field. The
        # pool's own member list is the authority.
        self.fake.hide_resource_pool = True
        self.fake.add_vm(201, "edge")
        self.fake.add_vm(300, "stranger", pool="other")
        code, out, err = self.run_pve("start", "edge")
        self.assertEqual(code, 0, err)
        code, out, err = self.run_pve("list")
        self.assertEqual(code, 0, err)
        self.assertIn("201", out)
        self.assertNotIn("stranger", out)
        code, out, err = self.run_pve("status", "300")
        self.assertEqual(code, 1)
        self.assertIn("refusing", err)

    def test_refuses_without_pool_audit(self):
        del self.fake.permissions["/pool/fcos-agent"]["Pool.Audit"]
        self.fake.add_vm(201, "edge")
        for args in (("start", "edge"), ("status", "edge"), ("list",)):
            with self.subTest(args=args):
                code, out, err = self.run_pve(*args)
                self.assertEqual(code, 1)
                self.assertIn("Pool.Audit", err)
                self.assertIn("setup-agent-access.sh", err)
        self.assertEqual(self.fake.writes(), [])

    def test_create_checks_pool_audit_before_any_write(self):
        del self.fake.permissions["/pool/fcos-agent"]["Pool.Audit"]
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml")
        self.assertEqual(code, 1)
        self.assertIn("Pool.Audit", err)
        self.assertEqual(self.fake.writes(), [])

    def test_start_refuses_when_name_differs(self):
        self.fake.add_vm(201, "somebody-else")
        code, out, err = self.run_pve("start", "edge")
        self.assertEqual(code, 1)
        self.assertEqual(self.fake.writes(), [])

    def test_no_delete_verbs(self):
        self.assertFalse(hasattr(PveClient, "delete"))
        with self.assertRaises(PveError):
            self.client()._request("DELETE", "/nodes/pve-a/qemu/201")
        self.assertEqual(self.fake.log, [])
        for verb in ("delete", "destroy", "rebuild", "move"):
            with self.subTest(verb=verb), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as caught:
                    pve.main([verb, "201"])
                self.assertEqual(caught.exception.code, 2)

    def test_tls_verification_cannot_be_disabled(self):
        with self.assertRaises(PveError):
            PveClient("https://192.0.2.21:8006/api2/json", PRINCIPAL, SECRET, False)
        self.assertNotIn("insecure", pve.build_parser().format_help().lower())

    def _contexts_for(self, verify):
        """Build a client and return the SSLContext it would use."""
        made = []
        real = ssl.create_default_context

        def record(*args, **kwargs):
            context = real()  # no cafile: the test only inspects the settings
            made.append(context)
            return context

        with mock.patch.object(pve.ssl, "create_default_context", side_effect=record):
            PveClient("https://192.0.2.21:8006/api2/json", PRINCIPAL, SECRET, verify)
        self.assertEqual(len(made), 1)
        return made[0]

    def test_pinned_ca_relaxes_only_x509_strict(self):
        # Proxmox's self-signed root CA has no keyUsage extension, which
        # Python 3.13+ rejects in strict mode. With the node's own pinned CA,
        # only that strict-format check is relaxed: chain and hostname are
        # still verified.
        context = self._contexts_for("/tmp/opencode/pinned-ca.pem")
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(context.check_hostname)
        if hasattr(ssl, "VERIFY_X509_STRICT"):
            self.assertFalse(context.verify_flags & ssl.VERIFY_X509_STRICT)

    def test_system_cas_keep_x509_strict(self):
        context = self._contexts_for("system")
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(context.check_hostname)
        default = ssl.create_default_context()
        self.assertEqual(context.verify_flags, default.verify_flags)

    def test_plain_http_only_to_loopback(self):
        PveClient("http://127.0.0.1:1/api2/json", PRINCIPAL, SECRET, True)
        PveClient("http://localhost:1/api2/json", PRINCIPAL, SECRET, True)
        for url in ("http://192.0.2.21:8006/api2/json", "http://example.org/api2/json",
                    "http://127.0.0.1" "@" "evil.example/api2/json", "ftp://127.0.0.1/x"):
            with self.subTest(url=url), self.assertRaises(PveError):
                PveClient(url, PRINCIPAL, SECRET, True)

    def test_no_environment_override_of_the_endpoint(self):
        source = (ROOT / "tools" / "pve.py").read_text()
        self.assertNotIn("FCOS_PVE_TEST", source)
        self.assertNotIn("os.environ", source)
        self.assertNotIn("getenv", source)

    def test_env_var_cannot_redirect_the_real_cli_to_loopback(self):
        # Undo the in-process patch: this is the production resolver.
        seen = []

        def blocked(opener, request, *args, **kwargs):
            seen.append(request.full_url)
            raise pve.urllib.error.URLError("blocked in test")

        env = {TEST_URL: self.fake.url}
        with mock.patch.object(pve, "_api_base", REAL_API_BASE), \
                mock.patch.dict(os.environ, env), \
                mock.patch.object(pve.urllib.request.OpenerDirector, "open", blocked):
            code, out, err = self.run_pve("check")
        self.assertEqual(code, 1)
        self.assertEqual(self.fake.log, [])
        self.assertEqual(seen, ["https://192.0.2.21:8006/api2/json/version"])
        self.assertNotIn(SECRET, out + err)

    def test_env_var_cannot_redirect_a_subprocess_either(self):
        env = dict(self.env)
        env[TEST_URL] = self.fake.url
        code = (
            "import sys\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "import pve\n"
            "def blocked(opener, request, *a, **k):\n"
            "    print('ATTEMPT', request.full_url)\n"
            "    raise pve.urllib.error.URLError('blocked in test')\n"
            "pve.urllib.request.OpenerDirector.open = blocked\n"
            "sys.exit(pve.main(['check']))\n")
        result = subprocess.run([sys.executable, "-c", code, str(ROOT / "tools")],
                                env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.fake.log, [])
        self.assertIn("ATTEMPT https://192.0.2.21:8006/api2/json/version", result.stdout)
        self.assertNotIn(SECRET, result.stdout + result.stderr)

    def test_redirects_are_not_followed(self):
        with self.assertRaisesRegex(PveError, "redirect"):
            self.client().get("/redirect")
        self.assertEqual([r["path"] for r in self.fake.log], ["/api2/json/redirect"])

    def test_bodies_are_form_encoded(self):
        self.fake.add_vm(201, "edge")
        self.client().post("/nodes/pve-a/qemu/201/status/start")
        self.assertEqual(self.fake.log[-1]["content_type"], "application/x-www-form-urlencoded")


class TokenTests(PveCase):
    def test_token_file_permissions(self):
        self.write_token(SECRET, 0o644)
        with self.assertRaises(PveError) as caught:
            load_token(self.ws, "host-a")
        message = str(caught.exception)
        self.assertIn(str(self.token), message)
        self.assertIn("chmod 600", message)
        self.assertNotIn(SECRET, message)
        code, out, err = self.run_pve("check")
        self.assertEqual(code, 1)
        self.assertIn("chmod 600", err)
        self.assertNotIn(SECRET, out + err)
        self.assertEqual(self.fake.log, [])

    def test_token_file_missing(self):
        self.token.unlink()
        with self.assertRaisesRegex(PveError, "proxmox-host-a.token.*missing"):
            load_token(self.ws, "host-a")

    def test_secrets_dir_must_be_private(self):
        (self.ws / "secrets").chmod(0o755)
        with self.assertRaisesRegex(PveError, "chmod 700"):
            load_token(self.ws, "host-a")

    def test_token_file_symlink_refused(self):
        real = self.tmp / "elsewhere"
        real.write_text(self.token.read_text())
        real.chmod(0o600)
        self.token.unlink()
        self.token.symlink_to(real)
        with self.assertRaises(PveError):
            load_token(self.ws, "host-a")

    def test_token_file_wrong_shape(self):
        for text in ("just-a-secret-value-without-id\n", f"{PRINCIPAL}={SECRET}\nsecond line\n",
                     f"root@pam!other={SECRET}\n", f"{PRINCIPAL}=\n", ""):
            with self.subTest(text=text[:12]):
                self.token.write_text(text)
                self.token.chmod(0o600)
                with self.assertRaises(PveError) as caught:
                    load_token(self.ws, "host-a")
                self.assertNotIn(SECRET, str(caught.exception))

    def test_load_token_ok(self):
        self.assertEqual(load_token(self.ws, "host-a"), (PRINCIPAL, SECRET))

    def test_host_key_is_validated(self):
        with self.assertRaises(PveError):
            load_token(self.ws, "../host-a")


class CommandTests(PveCase):
    def test_check_reports_permissions(self):
        code, out, err = self.run_pve("check")
        self.assertEqual(code, 0, err)
        self.assertIn("8.4.1", out)
        self.assertIn("/pool/fcos-agent: Pool.Audit VM.Allocate VM.Audit VM.Config.CPU VM.PowerMgmt", out)
        self.assertIn("/storage/local-lvm: Datastore.AllocateSpace Datastore.Audit", out)
        self.assertNotIn(SECRET, out + err)

    def test_check_warns_without_pool_rights(self):
        del self.fake.permissions["/pool/fcos-agent"]
        code, out, err = self.run_pve("check")
        self.assertEqual(code, 1)
        self.assertIn("/pool/fcos-agent", err)

    def test_list_shows_only_the_pool(self):
        self.fake.add_vm(201, "edge")
        self.fake.add_vm(300, "stranger", pool="other")
        code, out, err = self.run_pve("list")
        self.assertEqual(code, 0, err)
        self.assertIn("201", out)
        self.assertNotIn("stranger", out)

    def test_dry_run_sends_nothing(self):
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml", "--dry-run")
        self.assertEqual(code, 0, err)
        self.assertIn("POST /nodes/pve-a/qemu", out)
        self.assertIn("PUT /nodes/pve-a/qemu/201/resize", out)
        self.assertTrue(self.fake.log)
        self.assertEqual({r["method"] for r in self.fake.log}, {"GET"})
        self.assertEqual(self.fake.resources, [])

    def test_dry_run_shows_every_setting_with_reason(self):
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml", "--dry-run")
        self.assertEqual(code, 0, err)
        self.assertIn("| Setting | Will use | Why | Source |", out)
        for key in SETTINGS:
            self.assertIn(f"| {key} |", out)
        self.assertIn("| rng | urandom | example reason | example source |", out)
        # Nothing is set or left silently: the tool's fixed values and Proxmox's own defaults are listed too.
        self.assertIn("Fixed by the tool", out)
        for key in ("scsihw", "ostype", "vga", "serial0", "boot"):
            self.assertIn(f"| {key} |", out)
        self.assertIn("Left at Proxmox's default", out)
        for key in ("vmgenid", "smbios1", "shares", "reboot", "hugepages", "vcpus", "affinity", "keyboard",
                    "start", "template"):
            self.assertIn(f"| {key} |", out)

    def test_tags_are_set_after_the_vm_is_in_its_pool(self):
        # qemu-server checks tags on /vms/<vmid> before add_vm_to_pool, so they go in a later update.
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml")
        self.assertEqual(code, 0, err)
        create = next(w for w in self.fake.writes() if w["method"] == "POST")
        self.assertNotIn("tags", create["body"])
        self.assertEqual(self.fake.config_updates[201], [{"tags": "fcos-agent"}])
        writes = [(w["method"], w["path"].removeprefix("/api2/json")) for w in self.fake.writes()]
        self.assertEqual(writes[-1], ("PUT", "/nodes/pve-a/qemu/201/config"))

    def test_failed_tags_update_still_reports_the_created_vm_and_mac(self):
        # The VM exists by then; the owner still needs the MAC before the first start.
        self.fake.fail[("PUT", "/nodes/pve-a/qemu/201/config")] = (500, False)
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml")
        self.assertEqual(code, 0, out + err)
        self.assertIn("tags were not set", out + err)
        self.assertIn("created in pool", out)
        self.assertIn("MAC address:", out)

    def test_dry_run_marks_the_tags_step_as_after_the_create(self):
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml", "--dry-run")
        self.assertEqual(code, 0, err)
        self.assertIn("after the create", out)

    def test_rights_a_setting_needs_are_checked_before_any_write(self):
        # qemu-server check_vm_modify_config_perm: 'startup' needs Sys.Modify on / (trial run 2026-10-31:
        # the create was refused after the config disc had been uploaded).
        spec = SPEC_ISO.replace("startup_order:\n    use: null", "startup_order:\n    use: 2")
        self.assertNotEqual(spec, SPEC_ISO)
        (self.ws / "vms" / "edge" / "vm.yaml").write_text(spec)
        (self.ws / "vms" / "edge" / "edge.ign").write_bytes(IGN_BYTES)
        self.fake.permissions["/storage/isos"] = dict(ISO_PRIVS)
        for extra in ((), ("--dry-run",)):
            code, out, err = self.run_pve("create", "vms/edge/vm.yaml", *extra)
            self.assertEqual(code, 1, out + err)
            self.assertIn("Sys.Modify", err)
            self.assertIn("startup_order", err)
            self.assertEqual(self.fake.writes(), [])
        self.fake.permissions["/"] = {"Sys.Modify": 1}
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml", "--dry-run")
        self.assertEqual(code, 0, err)

    def test_create_runs_plan_in_order_without_starting(self):
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml")
        self.assertEqual(code, 0, err)
        writes = [(r["method"], r["path"].removeprefix("/api2/json")) for r in self.fake.writes()]
        self.assertEqual(writes, [("POST", "/nodes/pve-a/qemu"), ("PUT", "/nodes/pve-a/qemu/201/resize"),
                                  ("PUT", "/nodes/pve-a/qemu/201/config")])
        create = self.fake.writes()[0]["body"]
        self.assertEqual(create["pool"], "fcos-agent")
        self.assertEqual(create["protection"], "1")
        self.assertEqual(self.fake.writes()[1]["body"], {"disk": "scsi0", "size": "20G"})
        task_polls = [r for r in self.fake.log if "/tasks/" in r["path"]]
        self.assertGreaterEqual(len(task_polls), 2)
        self.assertEqual(self.fake.resources[0]["status"], "stopped")
        self.assertIn("not started", out)

    def test_create_prints_the_mac_to_reserve(self):
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml")
        self.assertEqual(code, 0, err)
        mac = self.fake.macs[201]
        self.assertIn(f"MAC address: {mac}", out)
        self.assertIn("reserve", out)
        code, out, err = self.run_pve("status", "edge")
        self.assertEqual(code, 0, err)
        self.assertIn(f"mac={mac}", out)

    def test_create_refuses_a_bad_network_before_any_write(self):
        cases = {
            "forbidden": (SPEC, {"forbidden_bridges": ["vmbr0"]}, None),
            "vlan": (SPEC.replace("vlan_tag: null", "vlan_tag: 30"), {},
                     [{"iface": "vmbr0", "type": "bridge", "mtu": 1500}]),
            "mtu": (SPEC + "mtu: 9000\n", {}, None),
        }
        for label, (spec, host_extra, interfaces) in cases.items():
            with self.subTest(case=label):
                self.fake.log.clear()
                site = SITE + "".join(f"    {k}: {v}\n" for k, v in host_extra.items())
                (self.ws / "site.yaml").write_text(site)
                (self.ws / "vms" / "edge" / "vm.yaml").write_text(spec)
                if interfaces is not None:
                    self.fake.interfaces = interfaces
                for extra in ((), ("--dry-run",)):
                    code, out, err = self.run_pve("create", "vms/edge/vm.yaml", *extra)
                    self.assertEqual(code, 1, out + err)
                    self.assertIn("network", err)
                    self.assertEqual(self.fake.writes(), [])
                self.fake.interfaces = [dict(self.fake.DEFAULT_BRIDGE)]

    def test_mac_read_failure_after_create_still_succeeds(self):
        self.fake.fail[("GET", "/nodes/pve-a/qemu/201/config")] = (500, False)
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml")
        self.assertEqual(code, 0, err)
        self.assertIn("MAC address: not reported", out)
        code, out, err = self.run_pve("status", "edge")
        self.assertEqual(code, 0, err)
        self.assertIn("mac=?", out)

    def test_create_stops_when_task_fails(self):
        self.fake.task_exit = "storage 'local-lvm' does not exist"
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml")
        self.assertEqual(code, 1)
        self.assertIn("does not exist", err)
        self.assertEqual([r["method"] for r in self.fake.writes()], ["POST"])

    def test_create_enforces_host_limits(self):
        (self.ws / "vms" / "edge" / "vm.yaml").write_text(SPEC.replace("cores: 2", "cores: 16"))
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml")
        self.assertEqual(code, 1)
        self.assertIn("max_cores", err)
        self.assertEqual(self.fake.writes(), [])

    def test_create_spec_must_live_under_vms(self):
        other = self.tmp / "vm.yaml"
        other.write_text(SPEC)
        code, out, err = self.run_pve("create", str(other))
        self.assertEqual(code, 1)
        self.assertEqual(self.fake.log, [])

    def test_host_mismatch_refused(self):
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml", "--host", "host-b")
        self.assertEqual(code, 1)
        self.assertEqual(self.fake.log, [])

    def test_ca_file_used_for_verification(self):
        ca = self.tmp / "ca.pem"
        ca.write_text("not a cert")
        self.assertEqual(pve._verify_for(self.ws, {"ca_file": str(ca)}), str(ca))
        self.assertEqual(pve._verify_for(self.ws, {"ca_file": None}), "system")
        with self.assertRaises(PveError):
            pve._verify_for(self.ws, {"ca_file": str(self.tmp / "missing.pem")})
        with self.assertRaises(PveError):  # an unreadable CA file is an error, never "no verification"
            PveClient("https://192.0.2.21:8006/api2/json", PRINCIPAL, SECRET, str(ca))

    def test_api_url_comes_from_site_address(self):
        base = REAL_API_BASE("host-a", {"address": "192.0.2.21"})
        self.assertEqual(base, "https://192.0.2.21:8006/api2/json")
        self.assertEqual(REAL_API_BASE("h", {"address": "fe80::1"}), "https://[fe80::1]:8006/api2/json")
        for bad in (None, "", "evil.example/x", "a@b", "h:8006/../x"):
            with self.subTest(bad=bad), self.assertRaises(PveError):
                REAL_API_BASE("host-a", {"address": bad})

    def test_create_derives_cicustom_from_site_and_refuses_mismatch(self):
        spec_file = self.ws / "vms" / "edge" / "vm.yaml"
        spec_file.write_text(SPEC.replace("  volume: coreos:snippets/edge.ign\n", ""))
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml", "--dry-run")
        self.assertEqual(code, 0, err)
        self.assertIn("vendor=coreos:snippets/edge.ign", out)
        spec_file.write_text(SPEC.replace("coreos:snippets/edge.ign", "elsewhere:snippets/edge.ign"))
        self.fake.log.clear()
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml")
        self.assertEqual(code, 1)
        self.assertIn("ignition.volume", err)
        self.assertEqual(self.fake.writes(), [])



class NoCloudIsoTests(PveCase):
    """ignition.method: nocloud-iso. The ISO builder is replaced; the container script has its own tests."""

    def setUp(self):
        super().setUp()
        (self.ws / "vms" / "edge" / "vm.yaml").write_text(SPEC_ISO)
        (self.ws / "vms" / "edge" / "edge.ign").write_bytes(IGN_BYTES)
        self.fake.permissions["/storage/isos"] = dict(ISO_PRIVS)
        self.built = []

        def fake_build(ign, out):
            self.built.append(Path(ign))
            Path(out).write_bytes(b"ISO:" + Path(ign).read_bytes())

        patcher = mock.patch.object(pve, "build_iso", fake_build)
        patcher.start()
        self.addCleanup(patcher.stop)

    def uploads(self):
        return [r for r in self.fake.log if r["method"] == "POST" and r["path"].endswith("/upload")]

    def test_create_uploads_the_iso_then_creates_the_vm(self):
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml")
        self.assertEqual(code, 0, err)
        writes = [(r["method"], r["path"].removeprefix("/api2/json")) for r in self.fake.writes()]
        self.assertEqual(writes, [("POST", "/nodes/pve-a/storage/isos/upload"),
                                  ("POST", "/nodes/pve-a/qemu"),
                                  ("PUT", "/nodes/pve-a/qemu/201/resize"),
                                  ("PUT", "/nodes/pve-a/qemu/201/config")])
        upload = self.uploads()[0]
        self.assertTrue(upload["content_type"].startswith("multipart/form-data; boundary="))
        self.assertEqual(upload["multipart"]["fields"], {"content": "iso"})
        self.assertEqual(upload["multipart"]["file"],
                         {"name": "filename", "filename": "fcos-edge-ign.iso", "data": b"ISO:" + IGN_BYTES})
        self.assertEqual(self.built, [self.ws / "vms" / "edge" / "edge.ign"])
        create = self.fake.writes()[1]["body"]
        self.assertEqual(create["ide2"], "isos:iso/fcos-edge-ign.iso,media=cdrom")
        self.assertNotIn("cicustom", create)
        self.assertEqual(create["pool"], "fcos-agent")
        self.assertEqual(create["protection"], "1")
        self.assertIn("not started", out)
        self.assertNotIn(SECRET, out + err)

    def test_checks_permission_and_existing_volume_before_any_write(self):
        self.run_pve("create", "vms/edge/vm.yaml")
        reads = [r["path"].removeprefix("/api2/json") for r in self.fake.log if r["method"] == "GET"]
        first_write = next(i for i, r in enumerate(self.fake.log) if r["method"] != "GET")
        before = [r["path"].removeprefix("/api2/json") for r in self.fake.log[:first_write]]
        self.assertIn("/access/permissions", before)
        self.assertIn("/nodes/pve-a/storage/isos/content", before)
        self.assertTrue(reads)

    def test_dry_run_shows_the_upload_and_sends_nothing(self):
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml", "--dry-run")
        self.assertEqual(code, 0, err)
        self.assertIn("UPLOAD /nodes/pve-a/storage/isos/upload", out)
        self.assertIn("fcos-edge-ign.iso", out)
        self.assertIn("ide2", out)
        self.assertIn("dry run: nothing was sent", out)
        self.assertEqual({r["method"] for r in self.fake.log}, {"GET"})
        self.assertEqual(self.built, [])
        self.assertEqual(self.fake.volumes, {})

    def test_refuses_without_allocate_template_privilege(self):
        self.fake.permissions["/storage/isos"] = {"Datastore.Audit": 1, "Datastore.AllocateSpace": 1}
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml")
        self.assertEqual(code, 1)
        self.assertIn("Datastore.AllocateTemplate", err)
        self.assertIn("/storage/isos", err)
        self.assertEqual(self.fake.writes(), [])
        self.assertEqual(self.built, [])

    def test_refuses_when_the_storage_has_no_rights_at_all(self):
        del self.fake.permissions["/storage/isos"]
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml")
        self.assertEqual(code, 1)
        self.assertIn("Datastore.AllocateTemplate", err)
        self.assertEqual(self.fake.writes(), [])

    def test_dry_run_also_reports_the_missing_privilege(self):
        del self.fake.permissions["/storage/isos"]
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml", "--dry-run")
        self.assertEqual(code, 1)
        self.assertIn("UPLOAD", out)
        self.assertIn("Datastore.AllocateTemplate", err)
        self.assertEqual(self.fake.writes(), [])

    def test_refuses_without_a_way_to_list_the_storage(self):
        self.fake.permissions["/storage/isos"] = {"Datastore.AllocateTemplate": 1}
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml")
        self.assertEqual(code, 1)
        self.assertIn("Datastore.Audit", err)
        self.assertEqual(self.fake.writes(), [])

    def test_refuses_to_overwrite_an_existing_volume(self):
        self.fake.volumes["isos"] = [{"volid": "isos:iso/fcos-edge-ign.iso", "format": "iso", "size": 1}]
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml")
        self.assertEqual(code, 1)
        self.assertIn("isos:iso/fcos-edge-ign.iso", err)
        self.assertIn("already exists", err)
        self.assertEqual(self.fake.writes(), [])
        self.assertEqual(self.built, [])

    def test_unexpected_storage_listing_fails_closed(self):
        for reply in ({"data": None}, {"data": {"volid": "isos:iso/fcos-edge-ign.iso"}},
                      {"data": "oops"}, {"message": "error-shaped"}):
            with self.subTest(reply=reply):
                self.fake.content_reply = reply
                self.fake.log.clear()
                code, out, err = self.run_pve("create", "vms/edge/vm.yaml")
                self.assertEqual(code, 1)
                self.assertIn("isos", err)
                self.assertIn("nothing was uploaded", err)
                self.assertEqual(self.fake.writes(), [])
                self.assertEqual(self.built, [])

    def test_other_volumes_in_the_storage_do_not_block(self):
        self.fake.volumes["isos"] = [{"volid": "isos:iso/fcos-edge2-ign.iso", "format": "iso", "size": 1},
                                     {"volid": "isos:iso/debian.iso", "format": "iso", "size": 1}]
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml")
        self.assertEqual(code, 0, err)

    def test_missing_iso_storage_names_the_site_key(self):
        site = (self.ws / "site.yaml").read_text().replace("    iso_storage: isos\n", "")
        (self.ws / "site.yaml").write_text(site)
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml", "--dry-run")
        self.assertEqual(code, 1)
        self.assertIn("hosts.host-a.iso_storage", err)
        self.assertNotIn("Task", err)
        self.assertEqual(self.fake.writes(), [])

    def test_missing_ignition_file_stops_before_any_write(self):
        (self.ws / "vms" / "edge" / "edge.ign").unlink()
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml")
        self.assertEqual(code, 1)
        self.assertIn("edge.ign", err)
        self.assertEqual(self.fake.writes(), [])

    def test_iso_build_failure_stops_before_any_write(self):
        with mock.patch.object(pve, "build_iso", side_effect=PveError("building the ISO failed")):
            code, out, err = self.run_pve("create", "vms/edge/vm.yaml")
        self.assertEqual(code, 1)
        self.assertIn("building the ISO failed", err)
        self.assertEqual(self.fake.writes(), [])

    def test_failed_upload_task_creates_no_vm(self):
        self.fake.task_exit = "upload failed"
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml")
        self.assertEqual(code, 1)
        self.assertIn("upload failed", err)
        self.assertEqual([r["path"].removeprefix("/api2/json") for r in self.fake.writes()],
                         ["/nodes/pve-a/storage/isos/upload"])
        self.assertEqual(self.fake.resources, [])

    def test_existing_vmid_is_refused_before_the_upload(self):
        self.fake.add_vm(201, "other")
        code, out, err = self.run_pve("create", "vms/edge/vm.yaml")
        self.assertEqual(code, 1)
        self.assertEqual(self.fake.writes(), [])

    def test_the_upload_cannot_be_used_as_a_delete_or_overwrite_verb(self):
        self.assertFalse(hasattr(PveClient, "delete"))
        self.assertFalse(hasattr(PveClient, "put_file"))
        with self.assertRaises(PveError):
            self.client()._request("DELETE", "/nodes/pve-a/storage/isos/content/isos:iso/x.iso")
        self.assertEqual(self.fake.log, [])

    def test_upload_body_is_well_formed_multipart(self):
        self.client().upload("/nodes/pve-a/storage/isos/upload", {"content": "iso"},
                             "fcos-x-ign.iso", b"a\r\n--b\r\nbinary\x00\xff")
        entry = self.uploads()[0]
        self.assertEqual(entry["multipart"]["file"]["data"], b"a\r\n--b\r\nbinary\x00\xff")
        self.assertEqual(entry["multipart"]["file"]["name"], "filename")
        self.assertEqual(entry["auth"], "PVEAPIToken=" + PRINCIPAL + "=" + SECRET)

    def test_upload_rejects_unsafe_names(self):
        for bad in ('a"b.iso', "a\r\nb.iso", "../x.iso", "a b.iso", ""):
            with self.subTest(bad=bad), self.assertRaises(PveError):
                self.client().upload("/nodes/pve-a/storage/isos/upload", {"content": "iso"}, bad, b"x")
        self.assertEqual(self.fake.log, [])

    def test_build_iso_runs_the_script_without_a_shell(self):
        ign, out = self.ws / "a.ign", self.ws / "a.iso"
        completed = subprocess.CompletedProcess([], 0, "", "")
        with mock.patch.object(pve, "build_iso", REAL_BUILD_ISO), \
                mock.patch.object(pve.subprocess, "run", return_value=completed) as run:
            pve.build_iso(ign, out)
        argv = run.call_args.args[0]
        self.assertEqual(argv, ["bash", str(ROOT / "tools" / "make_cidata_iso.sh"), str(ign), str(out)])
        self.assertFalse(run.call_args.kwargs.get("shell", False))

    def test_build_iso_failure_is_reported_without_a_traceback(self):
        failed = subprocess.CompletedProcess([], 1, "", f"boom {SECRET}\nimage is not pulled")
        pve.load_token(self.ws, "host-a")
        with mock.patch.object(pve, "build_iso", REAL_BUILD_ISO), \
                mock.patch.object(pve.subprocess, "run", return_value=failed):
            with self.assertRaises(PveError) as caught:
                pve.build_iso(self.ws / "a.ign", self.ws / "a.iso")
        self.assertIn("image is not pulled", str(caught.exception))
        self.assertNotIn(SECRET, str(caught.exception))


class SecretScrubbingTests(PveCase):
    def assert_clean(self, code, out, err, exc_text=""):
        self.assertEqual(code, 1)
        for text in (out, err, exc_text):
            self.assertNotIn(SECRET, text)
            self.assertNotIn("PVEAPIToken=" + PRINCIPAL, text)

    def test_http_401_never_leaks_secret(self):
        wrong = "ffffffff-0000-0000-0000-000000000000"
        self.write_token(wrong)
        code, out, err = self.run_pve("check")
        self.assert_clean(code, out, err)
        self.assertNotIn(wrong, out + err)
        self.assertIn("401", err)
        with self.assertRaises(PveError) as caught:
            self.client(wrong).get("/version")
        self.assertIn("401", str(caught.exception))
        self.assertNotIn(wrong, str(caught.exception))
        self.assertIsNone(caught.exception.__cause__)

    def test_http_500_that_echoes_the_header_is_scrubbed(self):
        self.fake.fail[("GET", "/version")] = (500, True)
        code, out, err = self.run_pve("check")
        self.assert_clean(code, out, err)
        self.assertIn("500", err)
        with self.assertRaises(PveError) as caught:
            self.client().get("/version")
        self.assertIn("500", str(caught.exception))
        self.assert_clean(1, "", "", str(caught.exception))

    def test_unreachable_server_message(self):
        self.fake.stop()
        code, out, err = self.run_pve("check")
        self.assert_clean(code, out, err)
        self.assertIn("cannot reach", err)

    def test_unexpected_exception_is_scrubbed(self):
        load_token(self.ws, "host-a")  # registers the secret, as every command does
        boom = mock.Mock(side_effect=RuntimeError(f"boom {SECRET}"))
        with mock.patch.dict(pve.COMMANDS, {"check": boom}):
            code, out, err = self.run_pve("check")
        self.assert_clean(code, out, err)
        self.assertIn("boom", err)
        self.assertNotIn("Traceback", err)

    def test_subprocess_end_to_end_output_is_clean(self):
        self.fake_accepts(WRAPPER_SECRET)
        self.fake.fail[("GET", "/version")] = (500, True)
        env = dict(self.env, FCOS_TEST_FAKE_URL=self.fake.url)
        result = subprocess.run([sys.executable, str(ROOT / "tests" / "run_pve_against_fake.py"), "check"],
                                env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn(SECRET, result.stdout + result.stderr)
        self.assertNotIn(WRAPPER_SECRET, result.stdout + result.stderr)
        self.assertIn("500", result.stderr)


class WrapperTests(PveCase):
    """tests/run_pve_against_fake.py must never read an owner's workspace or token."""

    WRAPPER = str(ROOT / "tests" / "run_pve_against_fake.py")

    def run_wrapper(self, *argv, env=None):
        env = dict(self.env if env is None else env, FCOS_TEST_FAKE_URL=self.fake.url)
        return subprocess.run([sys.executable, self.WRAPPER, *argv], env=env,
                              capture_output=True, text=True, timeout=60)

    def test_wrapper_uses_its_own_fake_token_not_the_owners(self):
        self.fake_accepts(WRAPPER_SECRET)
        remembered = Path(self.env["HOME"]) / ".config" / "fcos-agent" / "workspace"
        remembered.parent.mkdir(parents=True)
        remembered.write_text(f"{self.ws}\n")
        without_env = {k: v for k, v in self.env.items() if k != "FCOS_WORKSPACE"}
        for label, env in (("FCOS_WORKSPACE and remembered", self.env), ("remembered only", without_env)):
            with self.subTest(label):
                self.fake.log.clear()
                result = self.run_wrapper("check", env=env)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(self.fake.log)
                expected = "PVEAPIToken=" + PRINCIPAL + "=" + WRAPPER_SECRET
                self.assertEqual({r["auth"] for r in self.fake.log}, {expected})
                everything = result.stdout + result.stderr + repr(self.fake.log)
                self.assertNotIn(SECRET, everything)

    def test_wrapper_refuses_to_be_pointed_elsewhere(self):
        for argv in (("check", "--workspace", str(self.ws)), ("check", f"--workspace={self.ws}"),
                     ("list", "--host", "host-b")):
            with self.subTest(argv=argv):
                result = self.run_wrapper(*argv)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertTrue(result.stderr.strip())
                self.assertNotIn(SECRET, result.stdout + result.stderr)
                self.assertEqual(self.fake.log, [])

    def test_wrapper_removes_its_temp_workspace(self):
        self.fake_accepts(WRAPPER_SECRET)
        before = set(Path(tempfile.gettempdir()).glob("pve-fake-ws-*"))
        result = self.run_wrapper("check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(set(Path(tempfile.gettempdir()).glob("pve-fake-ws-*")), before)


if __name__ == "__main__":
    unittest.main()
