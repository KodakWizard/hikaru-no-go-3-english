# Public-tool verification

- Portable Python patcher reconstructed the complete v0.56 image from the original
  Japanese ISO and cumulative BPS; SHA-256 matches the published target exactly.
- Eight deterministic tool tests passed, covering command decoding, corrupt/truncated
  patches, wrong source size/hash, oversize edits, missing tokens and embedded nulls.
- The staged text editor verified all 5,917 baseline entries against the actual
  finished image, changed one test sentence, and wrote a separate output. A complete
  comparison confirmed only that allowed text slot changed. The shipped catalogue
  retains the original v0.56 wording; the test output is not distributed.
- The static game audit is in QA_REPORT.json. Native image decoding is a structural
  check; it does not certify visual appearance. Manual gameplay remains pending.
- Distribution uses an explicit source/text/document allowlist. No ISO, extracted
  game archive, memory card, emulator/account settings or commercial font is included.
