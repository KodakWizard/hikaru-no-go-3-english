# Version 1.0.2 result-screen update

v58 translates existing glyph pixels inside six native win43 atlas cells, retaining
their palettes and dimensions. Resign/time and Win/Loss ink now has a minimum
12-native-pixel gap in the static survey. Digits and top score/name panels are unchanged.

Final v59 replaces an existing 31-word window at RAM 8012f054..8012f0cc in the
half-point results display routine. Some words are unchanged. No hook, branch,
call, helper allocation, global constant or format string is added. Half-point
X coordinates are adjusted and half/outcome Y is explicitly copied from the
established pt widget Y. Whole-point paths remain exact. No score, komi, winner,
save or other point-display computation is changed; all other DOL bytes match v58.
All 719 active files are exact v58; relative to v57 only the win atlas archive,
its FST entry and documented display instructions differ.

8,000 offline instruction cases include deliberately stale incoming sprite Y,
whole/half margins 0..999, both colours and outcomes. Write/register guards and
extra coordinate extremes pass. A discarded initial draft fails the stronger
stale-Y regression guard and is not used in this release. Offline tests cannot
replace full runtime testing. User feedback is positive for the final build.

Sources: result_spacing_v58.py, build_result_spacing_v58.py, point_layout_v59.py,
build_point_layout_v59.py, and release_qa_v102.py. Supporting reports are in
development_sources.zip. Historical builders need local extracted inputs and
earlier reconstructed images; see SOURCE_GUIDE.md. No commercial font is included.
