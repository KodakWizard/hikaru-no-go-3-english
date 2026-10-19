# v55 scope and evidence

This is a game-side name-entry experiment based on exact v53, separate from the
v54 save conversion. No GCI files or user configuration are part of the ISO/BPS.

Confirmed-name copies patched to narrow fullwidth Latin/digits to ASCII:

| Native call | Purpose / source evidence |
|---|---|
| 0x80149554 | Fresh Story profile: destination stack 0x50a0 = profile 0x3260 + name 0x1e40; native profile copied through 0x80023874 |
| 0x80173f98 | Current Story name confirmation, global profile + 0x1e40 |
| 0x80171ff8 | Registered-player record constructor, name at record + 1 |
| 0x8017209c | Registered-player list creation, name at record + 1 |
| 0x8014df54 | Registered-player rename, selected record + 1 |

Original memcpy/strcpy-based name display sites from v08/v11/v13 are unchanged.
Font renderer and glyph classification code are unchanged. Source name-editor
buffers remain in their original two-byte form. Only destination names narrow.

Editor loading at 0x80173e64 and 0x8014e574 expands stored ASCII alphanumerics back
to their original fullwidth CP932 values in the temporary editor. Each accompanying
font/strlen source reference is switched to that buffer. Thus original strlen/2,
two-byte backspace, five-character count, replacement and Japanese keyboard tables
are retained. Existing saved fullwidth names need one in-game reconfirmation; there
is no automatic conversion at load time, and cancelling does not commit a name.

Code placement is an explicitly declared DOL text section 2, 436 bytes at
0x8042c000. It does not overlap any original loaded section, the declared BSS
(end 0x80419d92), startup stack top 0x80429d98, or default-thread stack. OSInit's
fallback arena low is 0x8042bda0. OSSetArenaLo at 0x801ee138 branches to a leaf
clamp which executes the original store after enforcing floor 0x8042c400. Higher
requested arena values are retained. This reserves code storage against heap
allocation. No code is placed in string tails, former helper ranges, or BSS.

Both converters are leaf functions: no stack writes, calls, LR/CTR operations,
floating-point state, or nonvolatile-register changes. Offline execution decodes
the actual assembled PPC words. 2068 deterministic cases exercise every ASCII
letter/digit, fullwidth Latin, Japanese, mixed names, round trips, byte-counting,
deletion and source preservation. Six arena boundary cases exercise both branches.
These are static/instruction tests; they do not replace emulator testing.

The complete patched DOL is relocated to a disc extent disjoint from all original
and active resources. Before overwrite that extent is exact original disc padding,
preserving all prior modified inactive extents. Only boot-header DOL pointer and
this new DOL extent differ in the whole disc versus v53. Within the old DOL content,
only the twelve recorded instructions and three new text-section header fields
may differ. All other old DOL bytes, all 719 active resources, FST, artwork, font,
scripts and GBA content are exact v53. Finished-disc readback and BPS reconstruction
against the original ISO pass. Original and v53 hashes were rechecked unchanged.

An unpublished initial candidate that only covered the current Story rename was
preserved in translation_work/name_test_v55/pre_new_profile_review. Use the final
English_NameEntry_Test_v55 output, SHA256
762a9330cc52d2c57915f423286720d80582f25effbf8549cd5847abb15a438d.

Required runtime evidence remains: fresh Story creation, registered-player creation
and editing, current Story rename, re-opening an ASCII name, deletion/replacement,
cancel/confirm, Japanese/mixed input, normal saving and cold reload, match-result
exit and room return. Real-hardware boot and broader optional-path regression are
not certified. Emulator automation remains blocked by product policy.
