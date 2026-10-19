# Contributing

Start from Version 1 beta and reproduce the issue with a cold boot and a normal save.
Open an issue with the screen/route, version, expected result, actual result and a
screenshot if relevant. Do not attach a game ISO, personal save, account token or
entire emulator configuration. State whether you used an old save state.

For wording changes, give Japanese context, before/after English, speaker and
scene. Preserve character voice, Go rules and conditions, and all runtime tokens.
Keep punctuation with its word and wrap at word boundaries. Labels and continuing
clauses do not automatically need full stops. Avoid guessing name readings.

Edit only `english` in editable_text.json. Keep `baseline`, offsets and capacity
unchanged. The current tool safely edits DOL and referenced GCS slots without
expanding a native resource. It writes a separate ISO and never edits a save.
Large room/Story bubbles use 26 halfwidth cells by three lines; reserve 12 cells
for each `$digit` name token. Small battle bubbles use 18 by three. The line-break
character for these DOL bubbles is `↓`; script speech uses LF. A byte fit alone is
not proof of a visual fit. Script headers and body variants need scene testing.

Longer text, GBA changes, sprite edits and runtime code changes require a dedicated
native-format/pointer/code audit. Do not change dimensions, palette counts or decoded
archive sizes casually: earlier builds had menu hangs following resource changes.
Keep native cells and alpha edges; check both outline polarities for clipping and
halos. Never solve spacing by changing a user's external save.

Submit a pull request with problem, before/after text or art, tests and known gaps.
Contributions are accepted under the licence scope in LICENSE_SCOPE.md.
