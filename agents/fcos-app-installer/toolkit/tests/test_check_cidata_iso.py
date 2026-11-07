"""tools/check_cidata_iso.py: the ISO built in a container is read back and must hold exactly the Ignition file.

The ISOs here are written by a small stand-in (ISO 9660 with a Joliet tree and optional Rock Ridge names, like
xorriso -J -r makes), so the tests need no container and no xorriso. Each way found to make an image that this
check passes but a machine reads differently has a test."""
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


def record(extent: int, length: int, name: bytes, directory: bool = False, xar: int = 0, flags: int | None = None,
           unit: int = 0, gap: int = 0, su: bytes = b"") -> bytes:
    flags = (2 if directory else 0) if flags is None else flags
    body = (bytes([xar]) + both(extent, 4) + both(length, 4) + bytes(7)
            + bytes([flags, unit, gap]) + both(1, 2) + bytes([len(name)]) + name)
    if (len(body) + 1) % 2:
        body += b"\0"
    body += su
    if (len(body) + 1) % 2:
        body += b"\0"
    return bytes([len(body) + 1]) + body


def nm(name: bytes, flags: int = 0) -> bytes:
    return b"NM" + bytes([5 + len(name), 1, flags]) + name


def susp(signature: bytes, payload: bytes = b"") -> bytes:
    return signature + bytes([4 + len(payload), 1]) + payload


SP = susp(b"SP", bytes([0xBE, 0xEF, 0]))


def build(files: dict[str, bytes], label: str = "cidata", subdir: bool = False, extra_primary: int = 0,
          joliet: bool = True, rock: bool = False, primary_edit: dict | None = None, joliet_edit: dict | None = None,
          system: bytes | None = None, extra_descriptors: tuple = (), spare: bytes = b"",
          root_su: bytes | None = None) -> bytes:
    """Sectors: 0-15 system area, 16 primary descriptor, 17 Joliet descriptor, then any extra descriptors, the
    terminator, the primary root, the Joliet root, the file data and last the spare data a test may point at."""
    primary_edit, joliet_edit = primary_edit or {}, joliet_edit or {}
    p_root = 19 + len(extra_descriptors)
    j_root = p_root + 1
    data, extents, at = b"", {}, p_root + 2
    for name, content in files.items():
        extents[name] = (at, len(content))
        sectors = max(1, -(-len(content) // SECTOR)) if content else 0
        data += content.ljust(sectors * SECTOR, b"\0")
        at += sectors
    data += spare.ljust(-(-len(spare) // SECTOR) * SECTOR, b"\0")
    at += -(-len(spare) // SECTOR)

    def entry(name: str, extent: int, size: int, edit: dict, text: bool) -> bytes:
        shown = name.encode("utf-16-be") if text else name.upper().replace("-", "_").encode() + b";1"
        fields = {"extent": extent, "size": size, "su": nm(name.encode()) if rock and not text else b""}
        fields.update(edit.get(name, {}))
        return record(fields["extent"], fields["size"], shown, xar=fields.get("xar", 0), flags=fields.get("flags"),
                      unit=fields.get("unit", 0), gap=fields.get("gap", 0), su=fields["su"])

    dot_su = root_su if root_su is not None else (SP if rock else b"")
    dot = record(p_root, SECTOR, b"\0", True, su=dot_su) + record(p_root, SECTOR, b"\1", True)
    primary = dot + b"".join(entry(n, e, s, primary_edit, False) for n, (e, s) in extents.items())
    primary += b"".join(record(p_root + 2, 1, f"X{i}".encode() + b";1") for i in range(extra_primary))
    if subdir:
        primary += record(p_root, SECTOR, b"SUB", True)
    jdot = record(j_root, SECTOR, b"\0", True) + record(j_root, SECTOR, b"\1", True)
    jroot = jdot + b"".join(entry(n, e, s, joliet_edit, True) for n, (e, s) in extents.items())
    if subdir:
        jroot += record(j_root, SECTOR, "sub".encode("utf-16-be"), True)

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
    parts = [system if system is not None else bytes(16 * SECTOR), descriptor(1, p_root),
             descriptor(2, j_root, b"%/E") if joliet else bytes(SECTOR), *extra_descriptors, terminator,
             primary.ljust(SECTOR, b"\0"), jroot.ljust(SECTOR, b"\0"), data]
    return b"".join(parts)


IGN = b'{"ignition":{"version":"3.6.0"}}'
EVIL = b'{"ignition":{"version":"3.6.0"},"x":1}'[: len(IGN)].ljust(len(IGN), b" ")
GOOD = {"user-data": IGN, "meta-data": b""}
SPARE = 22  # the first sector after GOOD's data: user-data at 21, meta-data holds none


def block(kind: int, escapes: bytes = b"") -> bytes:
    d = bytearray(SECTOR)
    d[0:7] = bytes([kind]) + b"CD001" + b"\1"
    d[88:88 + len(escapes)] = escapes
    return bytes(d)


class VerifyTests(unittest.TestCase):
    def test_an_iso_with_exactly_the_input_passes_with_or_without_rock_ridge(self):
        verify(build(GOOD), IGN)
        verify(build(GOOD, rock=True), IGN)

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


class TwoReadersTests(unittest.TestCase):
    """A machine reads either the primary tree (with its Rock Ridge names) or the Joliet tree, so both must
    lead to the same bytes under the same names."""

    def test_the_primary_tree_pointing_at_other_bytes_is_refused(self):
        for rock in (False, True):
            with self.subTest(rock=rock), self.assertRaisesRegex(IsoError, "disagree"):
                verify(build(GOOD, rock=rock, spare=EVIL, primary_edit={"user-data": {"extent": SPARE}}), IGN)

    def test_the_joliet_tree_pointing_at_other_bytes_is_refused(self):
        with self.assertRaises(IsoError):
            verify(build(GOOD, spare=IGN, joliet_edit={"user-data": {"extent": SPARE}}), IGN)

    def test_an_extended_attribute_length_shifts_the_data_and_is_refused(self):
        for edit in ({"primary_edit": {"user-data": {"xar": 1}}}, {"joliet_edit": {"user-data": {"xar": 1}}},
                     {"primary_edit": {"user-data": {"xar": 1}}, "joliet_edit": {"user-data": {"xar": 1}}}):
            with self.subTest(edit=edit), self.assertRaises(IsoError):
                verify(build(GOOD, **edit), IGN)

    def test_hidden_multi_extent_and_interleaved_files_are_refused(self):
        for field in ({"flags": 1}, {"flags": 0x80}, {"unit": 1}, {"gap": 1}):
            for tree in ("primary_edit", "joliet_edit"):
                with self.subTest(field=field, tree=tree), self.assertRaises(IsoError):
                    verify(build(GOOD, **{tree: {"user-data": field}}), IGN)

    def test_rock_ridge_names_that_differ_from_the_joliet_names_are_refused(self):
        renamed = {"user-data": {"su": nm(b"evil")}}
        swapped = {"user-data": {"su": nm(b"meta-data")}, "meta-data": {"su": nm(b"user-data")}}
        for edit in (renamed, swapped):
            with self.subTest(edit=edit), self.assertRaises(IsoError):
                verify(build(GOOD, rock=True, primary_edit=edit), IGN)

    def test_a_name_split_over_two_entries_is_put_together(self):
        split = {"user-data": {"su": nm(b"user-", 1) + nm(b"data")}}
        verify(build(GOOD, rock=True, primary_edit=split), IGN)
        broken = {"user-data": {"su": nm(b"user-", 1) + nm(b"evil")}}
        with self.assertRaises(IsoError):
            verify(build(GOOD, rock=True, primary_edit=broken), IGN)

    def test_some_names_with_rock_ridge_and_some_without_is_refused(self):
        with self.assertRaises(IsoError):
            verify(build(GOOD, rock=True, primary_edit={"meta-data": {"su": b""}}), IGN)

    def test_rock_ridge_entries_that_leave_the_record_are_refused(self):
        for signature in (b"CE", b"SL", b"CL", b"PL", b"RE", b"ZZ"):
            with self.subTest(signature=signature), self.assertRaises(IsoError):
                verify(build(GOOD, rock=True,
                             primary_edit={"user-data": {"su": nm(b"user-data") + susp(signature, bytes(8))}}), IGN)

    def test_the_root_folders_own_continuation_area_is_followed_once_and_checked(self):
        def ce(extent, length, offset=0):
            return susp(b"CE", both(extent, 4) + both(offset, 4) + both(length, 4))

        ident = susp(b"ER", bytes(10))
        verify(build(GOOD, rock=True, spare=ident, root_su=SP + ce(SPARE, len(ident))), IGN)  # as xorriso writes it
        for label, cont, pointer in (("leaving", susp(b"CL", bytes(8)), ce(SPARE, 12)),
                                     ("nested", ce(SPARE, 12), ce(SPARE, 12)),
                                     ("outside the image", ident, ce(99999, len(ident))),
                                     ("longer than a sector", ident, ce(SPARE, 5000)),
                                     ("unknown", susp(b"ZZ", bytes(8)), ce(SPARE, 12))):
            with self.subTest(label), self.assertRaises(IsoError):
                verify(build(GOOD, rock=True, spare=cont, root_su=SP + pointer), IGN)

    def test_a_damaged_system_use_area_is_refused(self):
        with self.assertRaises(IsoError):
            verify(build(GOOD, rock=True, primary_edit={"user-data": {"su": b"NM\xff\x01\x00user-data"}}), IGN)


class DescriptorTests(unittest.TestCase):
    def test_a_system_area_that_is_not_empty_is_refused(self):
        for first in (b"\x01", b"MZ", b"\0" * 100 + b"\x7f"):
            area = first.ljust(16 * SECTOR, b"\0")
            with self.subTest(first=first), self.assertRaisesRegex(IsoError, "system area"):
                verify(build(GOOD, system=area), IGN)
        tail = bytes(16 * SECTOR - 1) + b"\x01"
        with self.assertRaises(IsoError):
            verify(build(GOOD, system=tail), IGN)

    def test_descriptors_other_than_one_primary_and_one_joliet_are_refused(self):
        for extra in ((block(0),), (block(1),), (block(2, b"%/E"),), (block(2),), (block(3),), (block(9),)):
            with self.subTest(kind=extra[0][0]), self.assertRaises(IsoError):
                verify(build(GOOD, extra_descriptors=extra), IGN)

    def test_a_descriptor_that_is_not_iso_9660_is_refused(self):
        bad = bytearray(block(2, b"%/E"))
        bad[1:6] = b"XXXXX"
        with self.assertRaises(IsoError):
            verify(build(GOOD, extra_descriptors=(bytes(bad),)), IGN)

    def test_no_terminator_is_refused(self):
        iso = bytearray(build(GOOD))
        iso[18 * SECTOR] = 2  # the terminator becomes another descriptor
        iso[18 * SECTOR + 88:18 * SECTOR + 91] = b"%/E"
        with self.assertRaises(IsoError):
            verify(bytes(iso), IGN)


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

    def test_the_build_script_checks_the_iso_in_a_private_folder_and_places_it_without_overwriting(self):
        script = (ROOT / "tools" / "make_cidata_iso.sh").read_text()
        self.assertIn("mktemp -d", script)
        self.assertIn("check_cidata_iso.py", script)
        self.assertNotIn("mv -n", script)
        self.assertLess(script.index("check_cidata_iso.py"), script.index('ln -- "$tmp_out" "$out"'))

    def test_module_has_no_third_party_import(self):
        text = Path(check_cidata_iso.__file__).read_text()
        for line in text.splitlines():
            if line.startswith(("import ", "from ")):
                self.assertIn(line.split()[1].split(".")[0], {"sys", "pathlib", "__future__"}, line)


if __name__ == "__main__":
    unittest.main()
