# Workflow: title -> finished video

0. Setup once: `bash setup.sh` (Python deps + ffmpeg). Voice: `python produce.py voice` (free Edge, or ElevenLabs / HeyGen key).

1. TOPIC. `python produce.py new "<title>" --minutes N` (or `auto`). Creates episodes/<slug>.json, <slug>.py, <slug>.BRIEF.md.

2. RESEARCH + SCRIPT (episodes/<slug>.json "text"). ~130 words per minute. Structure in STYLE.md. Write "Chapter one." etc.
   as spoken words at each chapter start (they are the chapter cues). Add "say" respellings and "sources".

3. VOICE. `python pipeline/voice.py pipeline/episodes/<slug>.json` -> build/<slug>/words.json (word timings).
   Re-run after ANY script change.

4. STORYBOARD (episodes/<slug>.py). Go through the script sentence by sentence and add:
   - a CAMERA key (where the eye should be; width 6-12 deg for a city, 20-35 for a region, 45-70 for an empire);
   - CITIES labels for every place named; PEOPLE medallion for every person named (cue = the name);
   - BATTLES pill for every battle/siege/treaty; ARROWS for every march/invasion/campaign; RIPPLES for events at a place;
   - REALMS for every state on the map in that period (shape = coordinates, 'ISO:XXX', or {'hull': [cities]}), grow=
     from the capital when it expands; label it;
   - SIEGES close-up for every siege / battle / camp scene (5-12 s each);
   - PLATES (real images, 4-8 s) every 30-60 s; YEARS badge on every date; QUOTE card for a primary-source quote;
   - CHAPTERS with an era style; TITLE at the start; END_CARD.
   Test names: `python produce.py places Ctesiphon Merv`. Find images: `python produce.py images "Battle of X miniature"`,
   then `python pipeline/tools/commons.py get "File:..." <folder>/<name>`.

5. CHECK. `python produce.py check <slug>` -> 0 errors. Fix warnings about empty gaps, density, overlaps, whip pans.

6. PREVIEW. `python produce.py preview <slug> 12` and look at build/<slug>/sheet.jpg (+ still_*.jpg). Fix: labels off-screen,
   arrows pointing wrong, realm shapes wrong, medallion covering the action, faces of religious figures (must be light).

7. BUILD. `python produce.py build <slug>` -> out/<slug>_1080p.mp4, out/<slug>_master.mp4, out/<slug>_description.txt.
   It ends with an audio QA; fix any ERROR. Long video: see CLOUD.md (split rendering).

8. DELIVER: video + description (chapters with timestamps, sources, image credits, "borders approximate").
