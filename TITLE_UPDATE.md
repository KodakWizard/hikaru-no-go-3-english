# Version 1.0.1 title update

Two existing native RGBA8 backgrounds now share one clean Sai illustration and
the existing transparent English logo. White upper borders are straight and
uniform; released English copyright pixels are preserved. The menu board grid
is composited behind the logo. Native menu sprites, prompts and animation data
are unchanged. The background is an AI-assisted restoration approved by the
maintainer; it is not a pixel-exact reproduction of the original illustration.

Only title/title.bpe and its FST location/size entry differ from Version 1.0.0.
All 719 active disc files were compared, native dimensions/formats/descriptors
and decoded size are preserved, and cumulative BPS reconstruction passed.
This remains a beta: cold-boot transitions and menu selection require testing.

Apply the new patch to the original Japanese ISO, not Version 1.0.0.
The full source changes and required generated background/transparent logo are
in development_sources.zip, at the paths used by title_layers_v57.py.
The historical builder also requires a locally reconstructed v56 ISO plus the
original inventory/metadata working inputs described in SOURCE_GUIDE.md.
Existing game artwork and character/logo rights are excluded from the MIT licence.
