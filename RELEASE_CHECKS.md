# Public-tool verification

- Portable Python patcher reconstructed the complete Version 1 image from the original
  Japanese ISO and cumulative BPS; SHA-256 matches the published target exactly.
- Eight deterministic tool tests passed, covering command decoding, corrupt/truncated
  patches, wrong source size/hash, oversize edits, missing tokens and embedded nulls.
- The staged text editor verified all 5,917 baseline entries against the actual
  finished image, changed one test sentence, and wrote a separate output. A complete
  comparison confirmed only that allowed text slot changed. The shipped catalogue
  retains the original Version 1 wording; the test output is not distributed.
- The static game audit is in QA_REPORT.json. Native image decoding is a structural
  check; it does not certify visual appearance. Manual gameplay remains pending.
- Distribution uses an explicit source/text/document allowlist. No ISO, extracted
  game archive, memory card, emulator/account settings or commercial font is included.

- The compiled Windows patcher streaming engine independently applied the full BPS
  and reproduced the exact target SHA-256. Its interactive file-dialogue flow still
  needs a user acceptance check; this engine test does not certify gameplay.

Version 1.0.1: fresh full-disc static audit passed; eight portable-tool tests passed.
The updated compiled Windows engine and Python patcher each reconstructed the
exact v57 target SHA-256 from the original Japanese image. All 5,917 catalogue
baselines were checked against the new image. The earlier single-slot editor
write test applies to the unchanged editor/text layout from Version 1.0.0.
No new editor-write or interactive GUI/gameplay certification is claimed.
