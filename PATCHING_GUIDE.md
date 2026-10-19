# Apply the Version 1 patch — no coding needed

## Windows (recommended)

1. Download **Hikaru_no_Go_3_English_v1.0.2.zip** from Releases and extract it.
2. Keep `Hikaru_English_Patcher.exe` and `Hikaru_no_Go_3_English_v1.0.2.bps`
   together in the extracted folder. Double-click `Hikaru_English_Patcher.exe`.
3. Next to **Original ISO**, click **Browse...** and select your original Japanese
   **GHTJA4** ISO. Compressed RVZ and already-patched images are not accepted.
4. The English BPS is selected automatically. If it is blank, select the included
   `.bps` file with its **Browse...** button.
5. Click **Apply patch...**, choose a new filename/location, and wait. Do not close
   the patcher while it is working.
6. When it says **Patch complete**, the entire output SHA-256 has been verified.
   Cold boot the new English ISO in Dolphin. Normal memory-card saves can be used.

Windows patcher: 64-bit Windows with .NET Framework 4.5 or newer (included in normal
Windows 10/11 installations). Source is `WindowsPatcher.cs`; original project code,
not a bundled third-party patching program. It never overwrites existing files or
edits saves. Leave at least 1.5 GB free for the separate output image.

## Other platforms or existing patching software

The `.bps` is a standard BPS1 patch with embedded checksums. Use a BPS-compatible
patching application that supports 1.46 GB disc images. Smaller-ROM-oriented tools
may run out of memory. The supplied Python streaming alternative in README.md is
verified with this exact image and needs no additional Python packages.

## Troubleshooting

- **Wrong image/checksum:** use the unmodified Japanese GHTJA4 ISO. Do not patch an
  older English build. Source must be 1,459,978,240 bytes, SHA-256:
  `c6882110afa9ef27bf49f2e0530e37c51164d5ad0c10466cb164fc1b938406fc`.
- **Existing filename:** choose a new output filename; originals are never overwritten.
- **Not enough space:** allow at least 1.5 GB for output in addition to input/downloads.
- **Failed output verification:** do not use a partial output; download/extract the
  patch again and retry with a new output filename.
- **Old text/graphics after patching:** cold boot the new ISO; don't resume an old
  emulator save state. Existing wide Latin names need one in-game reconfirmation.

Version 1 is published as a beta while the gameplay checklist remains pending.
