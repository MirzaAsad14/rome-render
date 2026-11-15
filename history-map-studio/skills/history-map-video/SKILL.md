---
name: history-map-video
description: Produce an animated-map history documentary (illustrated atlas, era-changing map styles, portrait/noor medallions, battle pills, tactical close-ups, continuous narration, SFX, music) from a title, or pick a topic automatically ("auto produce"). The episode is written as a data storyboard; the engine renders it.
---

# History map video

Follow ../../CLAUDE.md exactly. Short version:
1. `python produce.py new "<title>" --minutes N` (or `auto`).
2. Research; write the narration (~130 wpm, "Chapter one." at chapter starts, "say" respellings, "sources") into episodes/<slug>.json.
3. `python pipeline/voice.py pipeline/episodes/<slug>.json`.
4. Write the storyboard episodes/<slug>.py as DATA (cues = phrases from the script, places = names). Example: episodes/demo_chaldiran.py.
   Hit the QUALITY.md targets: 12-25 events/min, close-up for every siege/battle, medallion for every person, arrow for every march.
5. `python produce.py check <slug>` until 0 errors; `python produce.py preview <slug> 12` and look at the sheet; fix.
6. `python produce.py build <slug>`; deliver out/<slug>_1080p.mp4 + out/<slug>_description.txt.
Rules: workflow/RULES.md (respect rule: only the Prophet and the Sahaba as noor light).
