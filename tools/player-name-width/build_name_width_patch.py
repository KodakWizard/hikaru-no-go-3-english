"""Build a standalone player-name width patch for the GHTJA4 DOL."""
import argparse
import hashlib
import struct
from pathlib import Path

from name_width_routines import CODE_BASE, RESERVED_END, branch, code

STOCK_TEXT = {
    0: "0c3bc5335708c2d4632ef43967fc4869e9618cf9f8858ac250a86c7c869c9cd8",
    1: "70c4c41d48ab19aec82343485c74c2a7b1f3a740481daa35f078f3e3aad5a9da",
}

def patch_dol(original):
    if len(original) < 0x100:
        raise ValueError("Input is too small to be a DOL")
    sections = {}
    for index in range(18):
        offset, address, size = (
            struct.unpack_from(">I", original, table + 4 * index)[0]
            for table in (0, 0x48, 0x90)
        )
        if offset or address or size:
            if offset < 0x100 or not size or offset + size > len(original):
                raise ValueError(f"Invalid DOL section {index}")
            sections[index] = offset, address, size

    if set(sections).intersection(range(7)) != set(STOCK_TEXT):
        raise ValueError("Expected the two original GHTJA4 code sections and a free slot 2")
    for index, expected in STOCK_TEXT.items():
        offset, address, size = sections[index]
        stock_layout = (0x100, 0x80003100, 0x2520) if index == 0 else (0x2620, 0x80018ba0, 0x217840)
        if (offset, address, size) != stock_layout or hashlib.sha256(original[offset:offset + size]).hexdigest() != expected:
            raise ValueError(f"GHTJA4 code section {index} differs from the supported original")
    bss_address, bss_size = struct.unpack_from(">II", original, 0xd8)
    if bss_address + bss_size > 0x80429d98 or any(
        address < RESERVED_END and CODE_BASE < address + size
        for _, address, size in sections.values()
    ):
        raise ValueError("The name routines' reserved memory overlaps the input DOL")

    blob, labels = code()
    dol = bytearray(original)
    new_offset = (len(dol) + 31) & ~31
    dol.extend(bytes(new_offset - len(dol)))
    dol.extend(blob)
    for table, value in ((0, new_offset), (0x48, CODE_BASE), (0x90, len(blob))):
        struct.pack_into(">I", dol, table + 8, value)

    edits={
     0x80173e64:branch(0x80173e64,labels['expand'],True),
     0x80173e6c:0x389f00ed, # display the expanded editor buffer
     0x80173e74:0x387f00ed, # original strlen/2 now sees the expanded editor buffer
     0x80173f98:branch(0x80173f98,labels['narrow'],True),
     0x80149554:branch(0x80149554,labels['narrow'],True), # fresh Story profile
     0x80171ff8:branch(0x80171ff8,labels['narrow'],True), # registered player creation
     0x8017209c:branch(0x8017209c,labels['narrow'],True), # player-list creation
     0x8014df54:branch(0x8014df54,labels['narrow'],True), # registered player rename
     0x8014e574:branch(0x8014e574,labels['expand'],True), # registered player editor
     0x8014e57c:0x389d00ed,
     0x8014e584:0x387d00ed,
     0x801ee138:branch(0x801ee138,labels['arena_floor']),
    }

    code_offset, code_address, _ = sections[1]
    for address, instruction in edits.items():
        struct.pack_into(">I", dol, code_offset + address - code_address, instruction)
    return dol

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Extracted, original-code GHTJA4 main.dol")
    parser.add_argument("output", type=Path, help="Path for a new patched DOL")
    args = parser.parse_args()
    try:
        patched = patch_dol(args.input.read_bytes())
        with args.output.open("xb") as output:
            output.write(patched)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    print(f"Wrote {args.output}")

if __name__ == "__main__":
    main()
