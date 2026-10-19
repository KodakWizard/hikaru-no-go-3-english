# Source guide

`project.py`: portable application of this project's BPS SourceRead/TargetRead
variant, hash verification and conservative GameCube text editing. Stdlib only.

`editable_text.json`: current DOL and directly referenced GCS strings with immutable
baseline, offset and current byte capacity. Use `english` for community changes.
GCS records can share an offset; identical edits must be applied consistently.

`name_entry_v55.py`: scoped PowerPC name-entry assembly generation and offline
instruction tests. Its historical import searches translation_work/python_libs;
install capstone into your Python environment if using it on a clean machine.
`TECHNICAL_AUDIT.md` records the declared text section and bounded arena reservation.

`development_sources.zip`: original Python development sources at archive root,
with retained authored working JSON/manifests under translation_work/. Extract into
an empty development directory. Install Pillow and capstone for relevant tools;
Windows artwork renderers refer to locally installed Arial/Georgia fonts. Font
binaries are not distributed. Extract the legally obtained original disc locally.
Historical builders reference earlier outputs and extracted/decoded resources;
they document the development process and are not all standalone entrypoints.
Earlier experimental sources are historical, not endorsed runtime fixes.

`release_qa.py` in that archive is the fresh read-only local release audit. It
compares the original, v53 native-graphics baseline and current v56 image, resolves
live FST/DOL addresses, validates the v55 code whitelist and audits known text,
GBA pointers and native texture decoding. Input fixtures must be supplied locally.

`QA_REPORT.json`: fresh static results and remaining coverage gaps.
`build_report.json`: original v56 build provenance and BPS reconstruction results.
`dialogue_layout_changes.json`: exact v56 before/after line breaks.

The release is exactly reproducible with the BPS and required source ISO. A single
fully portable build from all historical artistic/translation source edits remains
future work. Please keep this distinction in derivative release documentation.

WindowsPatcher.cs is the standalone graphical patcher source. Build instructions
are in BUILD_WINDOWS_PATCHER.md. Its stream engine is verified against the full ISO.

Version 1.0.1 adds title_layers_v57.py, build_title_layers_v57.py and their
restored background/logo working PNGs to development_sources.zip. See TITLE_UPDATE.md.
