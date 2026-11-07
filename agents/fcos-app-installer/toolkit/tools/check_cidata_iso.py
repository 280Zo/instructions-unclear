#!/usr/bin/env python3
"""Check that a NoCloud config ISO holds exactly the Ignition file it was built from.

Usage: check_cidata_iso.py <iso> <ign>

tools/make_cidata_iso.sh builds the ISO in a container that installs its tool at run time, and the ISO becomes the
VM's first-boot configuration. This reads the finished file back on the desktop, with nothing but the standard
library, and fails unless all of this holds:

- the first 16 sectors (where boot code would sit) are empty, and the volume descriptors are exactly one primary,
  one Joliet and the end marker, each once;
- the volume label is "cidata", in both the primary and the Joliet descriptor;
- the Joliet tree holds exactly "user-data" and "meta-data", no folders; user-data is byte for byte the input and
  meta-data is empty;
- the primary tree, which a machine may read instead, has Rock Ridge names (with the SP marker that makes a
  reader use them, and with files that are plain files) and leads to the same bytes under the same names as
  Joliet: same start and size for every file. An image without Rock Ridge names is refused, because its short
  primary names could not be matched to the Joliet ones; xorriso -r always writes them;
- no file is hidden, split over several pieces, interleaved or given an extended attribute area (each of those
  changes which bytes a machine reads), and no Rock Ridge entry points elsewhere (CE, SL, CL, PL, RE).

Sectors that no file or folder points at are not looked at: nothing reads them. Exit 0 if the ISO passes, 1 with
the reason if not, 2 for a wrong command line.
"""
import sys
from pathlib import Path

SECTOR = 2048
MAX_BYTES = 16 * 1024 * 1024
MAX_DESCRIPTORS = 8
JOLIET_ESCAPES = (b"%/@", b"%/C", b"%/E")
ROCK_RIDGE_KEPT = {"SP", "RR", "ER", "PX", "TF", "NM", "PD"}  # no ST: a reader stops reading entries at it
ROCK_RIDGE_LEAVING = {"CE", "SL", "CL", "PL", "RE"}


class IsoError(Exception):
    pass


def _both(buf: bytes, offset: int, size: int) -> int:
    """A both-endian number of an ISO 9660 record; the two halves must agree."""
    little = int.from_bytes(buf[offset:offset + size], "little")
    if little != int.from_bytes(buf[offset + size:offset + 2 * size], "big"):
        raise IsoError("a number in the ISO is stored two different ways")
    return little


def _descriptors(iso: bytes) -> tuple[bytes, bytes]:
    if len(iso) < 19 * SECTOR:
        raise IsoError("the ISO is too short to be an ISO 9660 image")
    if any(iso[:16 * SECTOR]):
        raise IsoError("the system area of the ISO (its first 16 sectors) is not empty; it could hold boot code")
    primary, joliet, ended = [], [], False
    for number in range(16, 16 + MAX_DESCRIPTORS):
        block = iso[number * SECTOR:(number + 1) * SECTOR]
        if len(block) < SECTOR or block[1:6] != b"CD001" or block[6] != 1:
            raise IsoError("not an ISO 9660 image (no valid volume descriptor)")
        kind = block[0]
        if kind == 255:
            ended = True
            break
        if kind == 1:
            primary.append(block)
        elif kind == 2 and block[88:91] in JOLIET_ESCAPES:
            joliet.append(block)
        else:
            raise IsoError(f"the ISO has a volume descriptor of type {kind} that is neither primary nor Joliet")
    if not ended:
        raise IsoError("the ISO has no end-of-descriptors marker")
    if len(primary) != 1:
        raise IsoError("the ISO must have exactly one primary volume descriptor")
    if len(joliet) != 1:
        raise IsoError("the ISO must have exactly one Joliet tree, so the file names can be checked")
    return primary[0], joliet[0]


def _system_use(area: bytes, iso: bytes | None = None) -> list[tuple[str, bytes]]:
    """The Rock Ridge (SUSP) entries of a record as (signature, data). With iso given, one CE entry is
    followed into its continuation area, which xorriso uses for the root folder's long ER entry; the entries
    there are held to the same rules and may not continue again."""
    entries, position = [], 0
    while position < len(area):
        if area[position] == 0 and not any(area[position:]):
            break  # padding
        if position + 4 > len(area):
            raise IsoError("a Rock Ridge entry in the ISO is damaged")
        signature = area[position:position + 2].decode("ascii", "replace")
        size = area[position + 2]
        if size < 4 or position + size > len(area):
            raise IsoError("a Rock Ridge entry in the ISO is damaged")
        if signature == "CE" and iso is not None:
            data = area[position + 4:position + size]
            if len(data) != 24:
                raise IsoError("a Rock Ridge CE entry in the ISO is damaged")
            start, offset, length = _both(data, 0, 4) * SECTOR, _both(data, 8, 4), _both(data, 16, 4)
            if offset + length > SECTOR or start + offset + length > len(iso):
                raise IsoError("a Rock Ridge continuation area lies outside the image")
            entries += _system_use(iso[start + offset:start + offset + length])
            position += size
            continue
        if signature in ROCK_RIDGE_LEAVING:
            raise IsoError(f"a Rock Ridge {signature} entry sends a reader elsewhere; not allowed")
        if signature not in ROCK_RIDGE_KEPT:
            raise IsoError(f"a Rock Ridge entry {signature!r} is not one this check knows")
        entries.append((signature, area[position + 4:position + size]))
        position += size
    return entries


def _rock_ridge_name(entries: list[tuple[str, bytes]]) -> str | None:
    name, found = b"", False
    for signature, data in entries:
        if signature != "NM":
            continue
        if not data or data[0] & 0b1110:  # current/parent/network-node names are not file names
            raise IsoError("a Rock Ridge name in the ISO is damaged")
        found = True
        name += data[1:]
    return name.decode("utf-8", "replace") if found else None


def _entries(iso: bytes, descriptor: bytes, joliet: bool) -> list[tuple[str, int, int]]:
    """(name, size, first sector) of every entry in the root folder, without . and ..  A folder, a hidden or
    split file, a file unit, an interleave or an extended attribute area is an error."""
    root = descriptor[156:190]
    if len(root) < 34 or root[1] != 0 or root[25] != 2:
        raise IsoError("the root folder record of the ISO is damaged")
    if _both(descriptor, 128, 2) != SECTOR:
        raise IsoError("the ISO does not use 2048-byte blocks")
    start, length = _both(root, 2, 4) * SECTOR, _both(root, 10, 4)
    if start + length > len(iso) or length > SECTOR * 64:
        raise IsoError("the root folder of the ISO lies outside the file")
    data, position, found, root_rock = iso[start:start + length], 0, [], []
    while position < len(data):
        size = data[position]
        if size == 0:  # records never straddle a sector: the rest of this one is padding
            position = (position // SECTOR + 1) * SECTOR
            continue
        record = data[position:position + size]
        if size < 34 or len(record) != size or 33 + record[32] > size:
            raise IsoError("a folder record in the ISO is damaged")
        position += size
        name = record[33:33 + record[32]]
        padding = 1 if record[32] % 2 == 0 else 0
        first = position == size and name == b"\0"  # the root folder's own "." record (position is already past it)
        rock = (_system_use(record[33 + record[32] + padding:], iso if first else None) if not joliet else [])
        extent, file_length = _both(record, 2, 4), _both(record, 10, 4)
        if file_length and (extent * SECTOR + file_length > len(iso)):
            raise IsoError("a file or folder in the ISO lies outside the image")
        if first:
            root_rock = rock
        if name in (b"\0", b"\1"):
            continue
        if record[1] != 0:
            raise IsoError("a file in the ISO has an extended attribute area, which shifts where its data starts")
        if record[25] != 0:
            raise IsoError("a file in the ISO is a folder, hidden or in several pieces")
        if record[26] or record[27]:
            raise IsoError("a file in the ISO is interleaved")
        try:
            text = name.decode("utf-16-be" if joliet else "ascii")
        except UnicodeDecodeError:
            raise IsoError("a file name in the ISO cannot be read") from None
        shown = _rock_ridge_name(rock) if not joliet else None
        if joliet:
            found.append((text.split(";")[0], file_length, extent))
            continue
        if shown is None:
            raise IsoError("a file in the primary tree of the ISO has no Rock Ridge name, so its name cannot be "
                           "checked against the Joliet tree")
        for signature, payload in rock:
            if signature == "PX" and (len(payload) < 32 or _both(payload, 0, 4) & 0o170000 != 0o100000):
                raise IsoError("a Rock Ridge entry in the ISO says a file is not a plain file")
        found.append((shown, file_length, extent))
    if not joliet:
        marker = [payload for signature, payload in root_rock if signature == "SP"]
        if not marker or marker[0] != bytes([0xBE, 0xEF, 0]):
            raise IsoError("the primary tree of the ISO lacks the Rock Ridge marker (SP), so a reader would not "
                           "use its Rock Ridge names")
    return found


def verify(iso: bytes, ign: bytes) -> None:
    primary, joliet = _descriptors(iso)
    label = primary[40:72].decode("ascii", "replace").strip()
    joliet_label = joliet[40:72].decode("utf-16-be", "replace").strip()
    if label != "cidata" or joliet_label != "cidata":
        raise IsoError(f"the volume label is {label!r} (Joliet {joliet_label!r}), not 'cidata'")
    for descriptor in (primary, joliet):
        if _both(descriptor, 80, 4) * SECTOR > len(iso):
            raise IsoError("the ISO is shorter than it says")
    tree = _entries(iso, joliet, True)
    flat = _entries(iso, primary, False)
    if sorted(name for name, *_ in tree) != ["meta-data", "user-data"]:
        raise IsoError("the ISO must hold exactly user-data and meta-data, found: "
                       + ", ".join(sorted(name for name, *_ in tree)))
    if sorted(flat) != sorted(tree):
        raise IsoError("the two file trees of the ISO disagree about names, sizes or where the files are")
    by_name = {name: (size, extent) for name, size, extent in tree}
    size, extent = by_name["user-data"]
    if size != len(ign) or iso[extent * SECTOR:extent * SECTOR + size] != ign:
        raise IsoError("user-data in the ISO is not the input Ignition file, byte for byte")
    if by_name["meta-data"][0] != 0:
        raise IsoError("meta-data in the ISO must be empty")


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        iso_path, ign_path = Path(argv[1]), Path(argv[2])
        if iso_path.stat().st_size > MAX_BYTES:
            raise IsoError(f"the ISO is larger than {MAX_BYTES} bytes")
        verify(iso_path.read_bytes(), ign_path.read_bytes())
    except (IsoError, OSError) as error:
        print(f"check_cidata_iso: {error}", file=sys.stderr)
        return 1
    print("check_cidata_iso: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
