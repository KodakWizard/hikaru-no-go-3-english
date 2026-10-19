# Hikaru no Go 3 — English translation

Community English translation of the Japanese GameCube game, with editable text,
original development tools and documented binary patching work.

**Current build: v0.56 beta. Gameplay acceptance tests are pending.**
This is an actively tested translation, not a claim that every optional route,
graphic or GBA download is fully verified. See QA_REPORT.json, KNOWN_ISSUES.md and
RUNTIME_CHECKLIST.md before reporting or closing a problem.

## Play

Download the v0.56 beta patch from this repository's Releases page. Extract the
release ZIP. Supply your own unmodified Japanese **GHTJA4** disc image.
Python 3.10 or newer is sufficient; applying the patch has no external dependencies.

```text
python project.py apply "Hikaru no Go 3 (Japan).iso" "Hikaru_no_Go_3_English_DialogueLayout_v56.bps" "Hikaru no Go 3 English v56.iso"
```

Source ISO: 1,459,978,240 bytes.
SHA-256: `c6882110afa9ef27bf49f2e0530e37c51164d5ad0c10466cb164fc1b938406fc`

Patched SHA-256:
`372cc172e7ed33fe0d5313f8ed6c5c94e6152700954e571b802a6abbb14cdf87`

The tool refuses a different source and existing output paths, and verifies the
finished image. Cold boot the resulting image; old emulator save states may retain
old code or graphics. Normal memory-card saves can be used. To narrow an existing
Latin player name, open the game's name editor and confirm it once. Name editing
itself retains the original wide-character display and deletion rules.

## Improve the translation

See CONTRIBUTING.md. `editable_text.json` contains 5,917 current verified GameCube
text-slot records, including Japanese references. Change `english`, retaining
`baseline` and metadata, then run:

```text
python project.py edit "Hikaru no Go 3 English v56.iso" editable_text.json "my-test-build.iso"
```

This conservative editor supports same-size-or-shorter CP932 text and checks
placeholders, bounds, shared slots and known bubble budgets. It deliberately
refuses unsafe expansion. GBA text and broader resource relocation use the
historical source tools described in SOURCE_GUIDE.md.

## Source and working files

The repository contains the portable patch/editor tool, editable current text,
the latest layout before/after record, QA results, source of the game-side name
conversion, and an archive of the original development Python sources and textual
working manifests. The archive preserves the development layout and is intended
for research and continued work. Historical builders depend on earlier local
builds and extracted input; they are not a one-command clean-room source build.
Exact reproduction of the released ISO is supported through the verified BPS
patch and original Japanese ISO.

No full disc image, emulator, memory-card save, account configuration, commercial
font file or extracted original game archive is included.

## Licence and attribution

Original project tools, documentation and translation contributions are available
under MIT; see LICENSE and LICENSE_SCOPE.md. Original game material and third-party
components retain their respective ownership and terms. The original game credits
remain in the game. This is an unofficial fan project, unaffiliated with the rights
holders. Contributions and corrections are welcome.
