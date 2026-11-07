"""tools/check_cidata_iso.py: the ISO built in a container is read back and must hold exactly the Ignition file.

The ISOs here are written by a small stand-in (ISO 9660 with a Joliet tree, like xorriso -J -r makes), so the
tests need no container and no xorriso."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import check_cidata_iso  # noqa: E402
from check_cidata_iso import IsoError, verify  # noqa: E402

SECTOR = 2048


def both(value: int, size: int) -> bytes:
    return value.to_bytes(size, "little") + value.to_bytes(size, "big")


def record(extent: int, length: int, name: bytes, directory: bool = False) -> bytes:
    body = (b"\0" + both(extent, 4) + both(length, 4) + bytes(7)  # starts with the extended-attribute length
            + bytes([2 if directory else 0, 0, 0]) + both(1, 2) + bytes([len(name)]) + name)
    if (len(body) + 1) % 2:
        body += b"\0"
    return bytes([len(body) + 1]) + body


def build(files: dict[str, bytes], label: str = "cidata", subdir: bool = False, extra_primary: int = 0,
          joliet: bool = True) -> bytes:
    """Sectors: 0-15 system area, 16 primary descriptor, 17 Joliet descriptor, 18 terminator, 19 primary
    root, 20 Joliet root, 21 and on the file data."""
    data, extents, at = b"", {}, 21
    for name, content in files.items():
        extents[name] = (at, len(content))
        sectors = max(1, -(-len(content) // SECTOR)) if content else 0
        data += content.ljust(sectors * SECTOR, b"\0")
        at += sectors
    dot = record(19, SECTOR, b"\0", True) + record(19, SECTOR, b"\1", True)
    primary = dot + b"".join(record(e, n, name.upper().replace("-", "_").encode() + b";1")
                             for name, (e, n) in extents.items())
    primary += b"".join(record(21, 1, f"X{i}".encode() + b";1") for i in range(extra_primary))
    if subdir:
        primary += record(19, SECTOR, b"SUB", True)
    jdot = record(20, SECTOR, b"\0", True) + record(20, SECTOR, b"\1", True)
    jroot = jdot + b"".join(record(e, n, name.encode("utf-16-be")) for name, (e, n) in extents.items())
    if subdir:
        jroot += record(20, SECTOR, "sub".encode("utf-16-be"), True)

    def descriptor(kind: int, root: int, escapes: bytes = b"") -> bytes:
        d = bytearray(SECTOR)
        d[0:7] = bytes([kind]) + b"CD001" + b"\1"
        d[40:72] = label.encode().ljust(32, b" ")
        d[80:88] = both(at, 4)
        d[88:88 + len(escapes)] = escapes
        d[128:132] = both(SECTOR, 2)
        d[156:190] = record(root, SECTOR, b"\0", True)
        return bytes(d)

    terminator = bytes([255]) + b"CD001" + b"\1" + bytes(SECTOR - 7)
    parts = [bytes(16 * SECTOR), descriptor(1, 19), descriptor(2, 20, b"%/E") if joliet else bytes(SECTOR),
             terminator, primary.ljust(SECTOR, b"\0"), jroot.ljust(SECTOR, b"\0"), data]
    return b"".join(parts)


IGN = b'{"ignition":{"version":"3.6.0"}}'
GOOD = {"user-data": IGN, "meta-data": b""}


class VerifyTests(unittest.TestCase):
    def test_an_iso_with_exactly_the_input_passes(self):
        verify(build(GOOD), IGN)

    def test_changed_content_is_refused(self):
        evil = b'{"ignition":{"version":"3.6.0"},"x":1}'
        with self.assertRaisesRegex(IsoError, "user-data"):
            verify(build({"user-data": evil, "meta-data": b""}), IGN)

    def test_extra_or_missing_files_are_refused(self):
        for files in ({**GOOD, "extra.sh": b"#!/bin/sh"}, {"user-data": IGN}, {"meta-data": b""},
                      {"user-data": IGN, "meta-data": b"instance-id: x"}):
            with self.subTest(files=sorted(files)), self.assertRaises(IsoError):
                verify(build(files), IGN)

    def test_a_folder_a_wrong_label_or_a_hidden_primary_entry_is_refused(self):
        for iso in (build(GOOD, subdir=True), build(GOOD, label="other"), build(GOOD, extra_primary=1)):
            with self.assertRaises(IsoError):
                verify(iso, IGN)

    def test_a_missing_joliet_tree_a_truncated_or_empty_file_is_refused(self):
        full = build(GOOD)
        for iso in (build(GOOD, joliet=False), full[: 20 * SECTOR], b"", b"not an iso at all" * 4000):
            with self.assertRaises(IsoError):
                verify(iso, IGN)

    def test_a_directory_record_that_points_outside_the_file_is_refused(self):
        data = bytearray(build(GOOD))
        data[19 * SECTOR + 2: 19 * SECTOR + 10] = both(9999999, 4)  # the primary root's first record
        with self.assertRaises(IsoError):
            verify(bytes(data), IGN)


class CommandLineTests(unittest.TestCase):
    def run_tool(self, iso: bytes, ign: bytes):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "x.iso").write_bytes(iso)
            (Path(tmp) / "x.ign").write_bytes(ign)
            return subprocess.run([sys.executable, str(ROOT / "tools" / "check_cidata_iso.py"),
                                   str(Path(tmp) / "x.iso"), str(Path(tmp) / "x.ign")],
                                  capture_output=True, text=True)

    def test_exit_codes_and_messages(self):
        good = self.run_tool(build(GOOD), IGN)
        self.assertEqual((good.returncode, good.stderr), (0, ""))
        bad = self.run_tool(build({"user-data": b"{}", "meta-data": b""}), IGN)
        self.assertEqual(bad.returncode, 1)
        self.assertIn("check_cidata_iso:", bad.stderr)
        self.assertNotIn("Traceback", bad.stderr)
        usage = subprocess.run([sys.executable, str(ROOT / "tools" / "check_cidata_iso.py")],
                               capture_output=True, text=True)
        self.assertEqual(usage.returncode, 2)

    def test_the_build_script_runs_the_check_before_it_moves_the_iso_into_place(self):
        script = (ROOT / "tools" / "make_cidata_iso.sh").read_text()
        self.assertIn("check_cidata_iso.py", script)
        self.assertLess(script.index("check_cidata_iso.py"), script.index('mv -n -- "$tmp_out" "$out"'))

    def test_module_has_no_third_party_import(self):
        text = Path(check_cidata_iso.__file__).read_text()
        for line in text.splitlines():
            if line.startswith(("import ", "from ")):
                self.assertIn(line.split()[1].split(".")[0], {"sys", "struct", "pathlib", "__future__"}, line)


if __name__ == "__main__":
    unittest.main()
