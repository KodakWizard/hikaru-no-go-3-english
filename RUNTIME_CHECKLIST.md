# Manual runtime acceptance checklist — Version 1 beta

Status: **all items below pending**. Static checks are recorded separately.
Use a copy of a normal memory-card save. Cold boot; do not resume an older save
state. Record emulator version/settings relevant to reproduction and patch SHA.
For each item record PASS/FAIL, route, screenshot and notes. Do not upload saves
or complete emulator configs to public issues.

- [ ] Title before/after Start/X: same logo size/position, board grid retained,
      no pasted seams, discolouration or unintended bottom strip; Story centred;
      larger Free Match on one line.
- [ ] New Story: enter 1- and 5-character Latin/digit names; delete/retype,
      confirm/cancel, reopen editor; test mixed/Japanese input if available.
- [ ] Existing profile: reconfirm the name in-game; compare spacing in dialogue,
      HUD, file list and results. No letters missing and no overrun.
- [ ] Registered-player create/rename/reopen/delete/cancel; verify the correct
      player changes and no neighbouring profile changes.
- [ ] Save, exit, cold boot, reload: name, skill, rank, Story and time retained.
- [ ] Room Data → Management → each submenu → room: all open and return safely.
- [ ] Map → Internet Cafe → accept → match → results → exit → continue playing.
- [ ] Akari, Kaga and Sai match results: resign/win/loss/draw where reachable;
      half-komi 6.5, zero komi, integer and half-point margins, single/double digits;
      no overlapping units, missing values or remaining half glyph.
- [ ] All midgame commentary bubble variants: whole words, <=3 lines, punctuation
      stays with its word. Revisit Sai's "Poor shape, isn't / it...?".
- [ ] Large Sai room introduction: "Then let me stay with you." and subsequent
      greeting; map pro-teaches-Go line; long Story lines and player-name tokens:
      useful width, no clipping or overlap with A prompt.
- [ ] Every character's introductions, reactions, rematches and outcome branches
      encountered: speaker voice, natural wording, numerical conditions correct.
- [ ] Saving/loading animation and empty card/list: English, no isolated dot or
      punctuation wrapping to its own line; Slot A/B and absent/full-card prompts.
- [ ] Kifu Replay empty list/Classics/all rows/replay: names, colour and numbers,
      move controls, start/end/exit and results; no accidental Japanese UI text.
- [ ] Odd/Even selection, Captures (idle and animated), territory/points, thinking
      and counting labels: no halo or clipped outlines in either colour polarity.
- [ ] Player results: headings centred above numbers; match captions separate
      from values; Change Player controls work in both directions; footer legible.
- [ ] Training and all five problem books: headings, problem goals, correct/wrong
      feedback, retries, assessment results and unlock/save prompts fit.
- [ ] Effects/equipment/options/controller ports: every selection and help ticker.
- [ ] Credits and ending/promotional cards: names/copy readable, layout stable.
- [ ] GBA transfer/cancel/port errors, match program and all five exercise books:
      actual transfer, controls, goals, feedback, save/load, numeric formatting.
- [ ] Longer session across Story branches, promotions/demotions and optional
      routes: no new hangs; record unvisited branches rather than assuming PASS.
- [ ] If targeting hardware: repeat startup/save/Management/cafe/results and GBA
      routes on actual supported hardware. Emulator success is a separate result.

Approved exceptions: Japanese background building/shop signage and collectible
packaging. Other Japanese gameplay text should be reported with context.
