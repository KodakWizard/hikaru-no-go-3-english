# Known limitations and release gates

- This is a beta. The manual routes in RUNTIME_CHECKLIST.md have not been certified.
- The game-side v55 name fix has positive user feedback, but fresh/registered
  profile paths, deletion, persistence and long sessions still need acceptance tests.
- Fullwidth names in existing saves need one in-game name reconfirmation. Editing
  itself intentionally retains the original wide-character buffer and display.
- Font outlines may still clip at some native glyph edges. The previous conversation
  font was restored after a later experiment produced inconsistent letter weights.
  No blanket claim of halo-free or clipping-free rendering is made.
- Two GCS dispatchers lack a complete parser: script/mission/mission.gcs and
  script/tutorial/tutorial.gcs. Known operand surveys are not full execution coverage.
- GBA compound kanji numeral construction and packed character/name graphics remain
  partly unclassified. Actual transfer and all GBA modes are untested.
- Optional Story branches, visual bubble variants, credits/end screens and hardware
  behaviour require further coverage. Zero Japanese candidates in known text records
  does not prove all game content is translated.
- Japanese scenery signage and collectible packaging are intentionally retained.
- Modified images may not match achievement-service game hashes. Achievement support
  has not been validated; it must not be advertised as supported.
