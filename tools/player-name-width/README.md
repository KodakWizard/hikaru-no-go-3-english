# Player name width fix for Hikaru no Go 3

This patch makes Latin player names display at normal width. It converts
full-width A–Z, a–z and 0–9 to ASCII when the player confirms a name, then
expands those characters in the temporary buffer when the name editor reopens.
Japanese characters and punctuation keep their original encoding.

## Build

1. Extract `main.dol` from the Japanese GameCube game (GHTJA4) or from your
   translation build with the original executable code.
2. Put both Python files in the same folder and run the command below.
   Python 3 and its standard library are sufficient.
3. Import `main-name-width.dol` as the boot executable using your existing
   disc build tools. The patched DOL is larger, so the disc builder must place
   it in available space and update the boot DOL pointer.

```sh
python build_name_width_patch.py main.dol main-name-width.dol
```

The builder checks the stock code sections and reserved memory before writing
a new file. If your translation already modifies executable instructions, use
the source as a porting reference and integrate the hooks into your build.

## Port to a modified executable

`name_width_routines.py` generates the PowerPC routines. The `narrow` and
`expand` entry points take the destination in r3 and the null-terminated
source in r4. The editor expects an 11-byte destination, including the
terminator. The `edits` table in the builder shows the five confirmation hooks,
two editor hooks, four buffer references and the arena hook. Map addresses
through your DOL section table and verify the original call sites before
recalculating branches. Place the routines in a declared executable section
and reserve their memory against heap allocation.

Test a fresh name and an existing name in the patched editor, including
deleting, cancelling and confirming. Save and reload, then check the name
in dialogue, the match HUD and results. Existing full-width names become
compact after reconfirmation in the editor. The target font needs ASCII glyphs.

The code is MIT licensed. Keep the included copyright and licence notice
when redistributing it.
