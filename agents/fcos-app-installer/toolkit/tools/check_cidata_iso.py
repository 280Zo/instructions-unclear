#!/usr/bin/env python3
"""Check that a NoCloud config ISO holds exactly the Ignition file it was built from.

Usage: check_cidata_iso.py <iso> <ign>

tools/make_cidata_iso.sh builds the ISO in a container that installs its tool at run time, and the ISO becomes the
VM's first-boot configuration. This reads the finished file back on the desktop, with nothing but the standard
library, and fails unless: the volume label is "cidata"; the Joliet tree holds exactly "user-data" and "meta-data",
no folders; user-data is byte for byte the input; meta-data is empty; and the primary tree lists the same files
with the same sizes (so nothing is hidden in one tree and not the other). Exit 0 if so, 1 with the reason if not,
2 for a wrong command line.
"""
import sys
from pathlib import Path

SECTOR = 2048
MAX_BYTES = 16 * 1024 * 1024
JOLIET_ESCAPES = (b"%/@", b"%/C", b"%/E")


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
    primary = joliet = None
    for number in range(16, 40):
        block = iso[number * SECTOR:(number + 1) * SECTOR]
        if len(block) < SECTOR or block[1:6] != b"CD001" or block[6] != 1:
            raise IsoError("not an ISO 9660 image (no valid volume descriptor)")
        if block[0] == 255:
            break
        if block[0] == 1:
            primary = block
        elif block[0] == 2 and block[88:91] in JOLIET_ESCAPES:
            joliet = block
    else:
        raise IsoError("the ISO has no end-of-descriptors marker")
    if primary is None:
        raise IsoError("the ISO has no primary volume descriptor")
    if joliet is None:
        raise IsoError("the ISO has no Joliet tree, so the file names cannot be checked")
    return primary, joliet


def _entries(iso: bytes, descriptor: bytes, joliet: bool) -> list[tuple[str, int, int, bool]]:
    """(name, size, first byte, is a folder) of every entry in the root folder, without . and .."""
    root = descriptor[156:190]
    start, length = _both(root, 2, 4) * SECTOR, _both(root, 10, 4)
    if start + length > len(iso) or length > SECTOR * 64:
        raise IsoError("the root folder of the ISO lies outside the file")
    data, position, found = iso[start:start + length], 0, []
    while position < len(data):
        size = data[position]
        if size == 0:  # records never straddle a sector: the rest of this one is padding
            position = (position // SECTOR + 1) * SECTOR
            continue
        record = data[position:position + size]
        if size < 34 or len(record) != size or 33 + record[32] > size:
            raise IsoError("a folder record in the ISO is damaged")
        position += size
        extent, file_length = _both(record, 2, 4) * SECTOR, _both(record, 10, 4)
        if extent + file_length > len(iso):
            raise IsoError("a file in the ISO lies outside the image")
        name = record[33:33 + record[32]]
        if name in (b"\0", b"\1"):
            continue
        try:
            text = name.decode("utf-16-be" if joliet else "ascii")
        except UnicodeDecodeError:
            raise IsoError("a file name in the ISO cannot be read") from None
        found.append((text.split(";")[0], file_length, extent, bool(record[25] & 2)))
    return found


def verify(iso: bytes, ign: bytes) -> None:
    primary, joliet = _descriptors(iso)
    label = primary[40:72].decode("ascii", "replace").strip()
    if label != "cidata":
        raise IsoError(f"the volume label is {label!r}, not 'cidata'")
    if _both(primary, 80, 4) * SECTOR > len(iso):
        raise IsoError("the ISO is shorter than it says")
    tree = _entries(iso, joliet, True)
    flat = _entries(iso, primary, False)
    if any(is_folder for *_rest, is_folder in tree + flat):
        raise IsoError("the ISO holds a folder; it may hold only user-data and meta-data")
    if sorted(name for name, *_ in tree) != ["meta-data", "user-data"]:
        raise IsoError("the ISO must hold exactly user-data and meta-data, found: "
                       + ", ".join(sorted(name for name, *_ in tree)))
    if sorted(size for _name, size, *_ in tree) != sorted(size for _name, size, *_ in flat):
        raise IsoError("the two file trees of the ISO disagree about what it holds")
    by_name = {name: (size, extent) for name, size, extent, _folder in tree}
    size, extent = by_name["user-data"]
    if iso[extent:extent + size] != ign or size != len(ign):
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
