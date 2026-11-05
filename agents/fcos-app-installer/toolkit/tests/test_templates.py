import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from render import load_values, render  # noqa: E402

TEMPLATES = ROOT / "templates"
FIXTURES = ROOT / "tests" / "fixtures"


def values(fixture: str) -> dict[str, str]:
    return load_values(str(FIXTURES / f"{fixture}.values"))


def rendered(template: str, fixture: str = "ai-vm") -> str:
    return render((TEMPLATES / template).read_text(), values(fixture))


def unit_block(text: str, name: str) -> str:
    """Return the Butane systemd unit entry for `name` (up to the next entry)."""
    match = re.search(rf"- name: {re.escape(name)}\n(.*?)(?=\n\s*- name: |\Z)", text, re.S)
    if not match:
        raise AssertionError(f"unit {name} not found")
    return match.group(1)


class BaseConfigTests(unittest.TestCase):
    def test_butane_version(self):
        for template in ("base/config.bu.tmpl", "base/base-config.bu.tmpl"):
            with self.subTest(template=template):
                self.assertIn("version: 1.7.0", rendered(template))

    def test_admin_groups(self):
        text = rendered("base/base-config.bu.tmpl")
        self.assertIn("- name: " + values("ai-vm")["ADMIN_USER"], text)
        groups = re.search(r"groups:\s*\[([^\]]*)\]", text)
        self.assertIsNotNone(groups)
        self.assertEqual({g.strip() for g in groups.group(1).split(",")}, {"wheel", "sudo"})

    def test_data_disk_never_wiped(self):
        text = rendered("base/base-config.bu.tmpl")
        filesystems = text.split("filesystems:", 1)[1].split("\n  directories:", 1)[0]
        entries = re.split(r"\n\s*- device:", filesystems)[1:]
        self.assertTrue(entries, "no filesystem entries")
        for entry in entries:
            self.assertIn("/dev/disk/by-id/scsi-0QEMU_QEMU_HARDDISK_drive-scsi1", entry)
            self.assertIn("label: appdata", entry)
            self.assertIn("path: /var/lib/appdata", entry)
            self.assertIn("wipe_filesystem: false", entry)
            self.assertNotIn("wipe_filesystem: true", entry)

    def test_zincati_periodic(self):
        text = rendered("base/base-config.bu.tmpl")
        self.assertIn("/etc/zincati/config.d/", text)
        self.assertIn('strategy = "periodic"', text)
        self.assertIn("[[updates.periodic.window]]", text)

    def test_autoupdate_dropin(self):
        text = rendered("base/base-config.bu.tmpl")
        self.assertIn("/etc/systemd/system/podman-auto-update.timer.d/", text)
        self.assertIn("/etc/systemd/user/podman-auto-update.timer.d/", text)
        self.assertIn("/etc/systemd/user/timers.target.wants/podman-auto-update.timer", text)
        self.assertNotIn("- name: podman-auto-update.service", text)
        self.assertNotIn("contents: |\n            [Unit]\n            Description=Podman auto-update", text)

    def test_merge_entries(self):
        text = rendered("base/config.bu.tmpl")
        self.assertIn("merge:", text)
        self.assertIn("local: igns/base-config.ign", text)


class NfsShareTests(unittest.TestCase):
    def test_only_automount_enabled(self):
        text = rendered("base/nfs-share.bu.tmpl")
        name = values("ai-vm")["NFS_MOUNT_NAME"]
        mount = unit_block(text, f"var-mnt-{name}.mount")
        automount = unit_block(text, f"var-mnt-{name}.automount")
        self.assertNotIn("enabled: true", mount)
        self.assertIn("enabled: true", automount)
        self.assertIn("_netdev", mount)
        self.assertIn("Type=nfs4", mount)

    def test_virt_use_nfs(self):
        text = rendered("base/nfs-share.bu.tmpl")
        block = unit_block(text, "virt-use-nfs.service")
        self.assertIn("enabled: true", block)
        self.assertIn("setsebool -P virt_use_nfs 1", block)
        self.assertIn("ConditionPathExists=!", block)


class FirewallTests(unittest.TestCase):
    def test_firewall_only_edge(self):
        text = rendered("base/firewall.bu.tmpl")
        v = values("ai-vm")
        self.assertIn("- name: nftables.service", text)
        self.assertIn("enabled: true", unit_block(text, "nftables.service"))
        self.assertIn("policy drop;", text)
        self.assertNotIn("flush ruleset", text)
        # Networks are a comma-separated list, written into an nftables set.
        self.assertIn(f"tcp dport 22 ip saddr {{ {v['ADMIN_LAN_CIDR']} }} accept", text)
        self.assertIn(f"tcp dport @edge_tcp ip saddr {v['EDGE_IP']} accept", text)
        self.assertIn(f"tcp dport @lan_tcp ip saddr {{ {v['LAN_CIDR']} }} accept", text)
        accepts = [l.strip() for l in text.splitlines() if "tcp dport" in l and "accept" in l]
        self.assertEqual(len(accepts), 3, accepts)
        self.assertIn('include "/etc/nftables.d/*.nft"', text)

    def test_firewall_takes_several_networks(self):
        # The web ports open to two networks.
        two = dict(values("ai-vm"), LAN_CIDR="192.0.2.0/24, 198.51.100.0/24")
        text = render((TEMPLATES / "base" / "firewall.bu.tmpl").read_text(), two)
        self.assertIn("tcp dport @lan_tcp ip saddr { 192.0.2.0/24, 198.51.100.0/24 } accept", text)
        # validate.sh runs nft -c on lists: LAN_CIDR in the edge fixture, ADMIN_LAN_CIDR in ai-vm.
        self.assertEqual(values("edge")["LAN_CIDR"].count(","), 1)
        self.assertEqual(values("ai-vm")["ADMIN_LAN_CIDR"].count(","), 1)

    def test_edge_accepts_lan_https(self):
        text = rendered("base/edge-ports.bu.tmpl", "edge")
        self.assertIn("add element inet host_filter lan_tcp { 80, 443 }", text)
        self.assertIn("net.ipv4.ip_unprivileged_port_start=80", text)


class RequireMountsTests(unittest.TestCase):
    def test_require_mounts_script(self):
        text = rendered("base/base-config.bu.tmpl")
        self.assertIn("- path: /usr/local/bin/require-mounts", text)
        self.assertIn("mode: 0755", text)
        self.assertIn("findmnt -n -o FSTYPE --mountpoint", text)
        self.assertIn('""|autofs)', text)


class ReviewFixTests(unittest.TestCase):
    def test_no_nested_volume_targets(self):
        # A bind mounted read-only can't hold another mountpoint inside it.
        for fixture in ("ai-vm", "edge"):
            for path in sorted(TEMPLATES.rglob("*.tmpl")):
                text = render(path.read_text(), values(fixture))
                for block in text.split("[Container]")[1:]:
                    block = block.split("[Service]", 1)[0]
                    targets = [v.split(":")[1] for v in re.findall(r"Volume=(\S+)", block)]
                    for a in targets:
                        for b in targets:
                            with self.subTest(template=path.name, outer=a, inner=b):
                                self.assertFalse(a != b and b.startswith(a.rstrip("/") + "/"))

    def test_firewall_safe_reload(self):
        text = rendered("base/firewall.bu.tmpl")
        self.assertIn("/etc/systemd/system/nftables.service.d/10-own-table.conf", text)
        self.assertIn("ExecReload=/sbin/nft -f /etc/sysconfig/nftables.conf", text)
        self.assertIn("ExecStop=/sbin/nft delete table inet host_filter", text)
        self.assertNotIn("flush ruleset", text)

    def test_firewall_forward_dnat(self):
        text = rendered("base/firewall.bu.tmpl")
        edge = values("ai-vm")["EDGE_IP"]
        self.assertIn("type filter hook forward priority 0; policy accept;", text)
        self.assertIn(f"ct status dnat ct state new ip saddr != {edge} drop", text)


class ExampleConfigTests(unittest.TestCase):
    def test_example_config_covers_keys(self):
        config = (ROOT / "site.example.yaml").read_text()
        groups = re.findall(r"maps to: ([A-Z][A-Z0-9_]*(?:, [A-Z][A-Z0-9_]*)*)\b", config)
        mapped = {k.strip() for group in groups for k in group.split(",")}
        keys = set()
        for path in TEMPLATES.rglob("*.tmpl"):
            keys |= set(re.findall(r"\{\{([A-Z][A-Z0-9_]*)\}\}", path.read_text()))
        self.assertEqual(sorted(keys - mapped), [], "template keys missing from site.example.yaml")

    def test_example_config_has_no_secret_values(self):
        config = (ROOT / "site.example.yaml").read_text()
        self.assertNotRegex(config, r"(?im)^\s*(token|password|secret|api_key)\s*:\s*\S")


class RebuildSafetyTests(unittest.TestCase):
    """Ignition fails on an existing file unless overwrite: true. Files on the
    data disk already exist after a rebuild, so they must all overwrite."""

    def test_data_disk_files_overwrite(self):
        for fixture in ("ai-vm", "edge"):
            for path in sorted(TEMPLATES.rglob("*.bu.tmpl")):
                text = render(path.read_text(), values(fixture))
                files = text.split("\n  files:\n", 1)
                if len(files) < 2:
                    continue
                for entry in re.split(r"\n    - path: ", "\n" + files[1])[1:]:
                    target = entry.split("\n", 1)[0]
                    if target.startswith("/var/lib/appdata/"):
                        with self.subTest(fixture=fixture, template=path.name, file=target):
                            self.assertIn("overwrite: true", entry.split("\n    - path:", 1)[0])


if __name__ == "__main__":
    unittest.main()
