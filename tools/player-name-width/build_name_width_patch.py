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

    # All keys are GHTJA4 runtime addresses. The DOL section table maps
    # them to file offsets before the replacement instructions are written.
    edits = {
        # Story mode: confirm a new profile or confirm a renamed profile.
        0x80149554: branch(0x80149554, labels["narrow"], True),  # New Story profile
        0x80173F98: branch(0x80173F98, labels["narrow"], True),  # Story rename

        # Registered players: confirm the name in each creation or rename path.
        0x80171FF8: branch(0x80171FF8, labels["narrow"], True),  # Register a player
        0x8017209C: branch(0x8017209C, labels["narrow"], True),  # Create from player list
        0x8014DF54: branch(0x8014DF54, labels["narrow"], True),  # Rename a registered player

        # Story name editor: expand the saved name into the temporary buffer.
        0x80173E64: branch(0x80173E64, labels["expand"], True),
        0x80173E6C: 0x389F00ED,  # Display the expanded name (r4 = r31 + 0xED)
        0x80173E74: 0x387F00ED,  # Count its two-byte slots (r3 = r31 + 0xED)

        # Registered player editor: use its own temporary buffer for the same steps.
        0x8014E574: branch(0x8014E574, labels["expand"], True),
        0x8014E57C: 0x389D00ED,  # Display the expanded name (r4 = r29 + 0xED)
        0x8014E584: 0x387D00ED,  # Count its two-byte slots (r3 = r29 + 0xED)

        # System memory setup: reserve the new code below the heap.
        0x801EE138: branch(0x801EE138, labels["arena_floor"]),
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
