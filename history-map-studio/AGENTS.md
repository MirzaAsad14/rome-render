# History Map Studio 2 - instructions for the AI assistant

You produce animated-map history documentaries in the "History Vanguard" style. This folder renders every frame locally
(Python + ffmpeg), so the same inputs give the same video. YOU write two files per episode; the engine does all drawing:

    pipeline/episodes/<slug>.json   the narration script (+ "say" respellings, sources)
    pipeline/episodes/<slug>.py     the STORYBOARD: plain lists/dicts (camera, realms, arrows, people, battles, close-ups...)

Never write drawing code, coordinates from memory, or times in seconds. Use CUES (phrases from the narration) and PLACE NAMES.
A complete working example: pipeline/episodes/demo_chaldiran.{json,py}. Blank template: pipeline/templates/story_template.py.

## Read first (in order)
1. workflow/RULES.md     non-negotiable rules (respect rule, accuracy, audio, images)
2. workflow/WORKFLOW.md  the exact steps and commands
3. workflow/QUALITY.md   the quality bar; what makes a video look like the reference channel
4. workflow/STYLE.md     script structure + era map styles

## The loop (do not skip steps)
    python produce.py new "<title>" --minutes N          # or: python produce.py auto --minutes N
    (research; write the script into episodes/<slug>.json)
    python pipeline/voice.py pipeline/episodes/<slug>.json
    (write the storyboard episodes/<slug>.py using phrases from the script as cues)
    python produce.py check <slug>                       # must say 0 errors; fix every WARN you can
    python produce.py preview <slug> 12                  # open pipeline/build/<slug>/sheet.jpg and LOOK; fix and repeat
    python produce.py build <slug>                       # -> pipeline/out/<slug>_1080p.mp4 + _description.txt

## Hard rules for you
- Run the commands. Never claim a video exists that you did not render. Never skip `check` or `preview`.
- If a cue is "not in narration", copy the exact words from the script (check suggests the closest match).
- If a place is unknown, add it to PLACES as (lon, lat) from a reliable source (Wikipedia coordinates), never a guess.
- Respect rule: ONLY the Prophet and the Sahaba (7th century) become noor light (automatic). Everyone later - caliphs after
  the Companions, sultans, shahs, ayatollahs - gets a real period portrait like any other ruler.
- API keys: the user runs `python produce.py voice` themselves; never ask them to paste a key into chat.
- Long videos (> 3 min) render for hours on a laptop: offer `python produce.py part <slug> i/n` on several machines
  (or Kaggle / Colab notebooks: see workflow/CLOUD.md), then `python produce.py join <slug> n`.

## If you cannot run code (plain ChatGPT / Grok chat)
Write the two files exactly as above (copy the template's structure), tell the user to run, in this folder:
`bash setup.sh`, `python pipeline/voice.py pipeline/episodes/<slug>.json`, `python produce.py check <slug>` and paste the
output back to you; fix what it reports; then `python produce.py preview <slug>` (send you the sheet image) and `build`.


## Opening and transitions (v2.1)
- Cold open: the first map falls in from the top as a tilted sheet with a soft gear tick (`INTRO = 'sheet'`).
- Hook, then the channel logo sting: put `"sting_after": "<last words of the hook>"` and `"sting_gap": 3.2` in the episode .json. The voice keeps one TTS pass and opens one gap there. The logo card (dark slate, gold gear turning, emblem in the centre, channel name in bevelled gold) falls in from the top with light glowing from its bottom edge, then dissolves back into the map. Set `BRAND` once per channel; never copy another channel's logo.
- Big camera jumps: `'wipe'` on the camera key (new view falls in from the top over the old one, shadow on the old page). Close-ups roll in the same way and the map rolls back over them.
- Sounds are automatic: gear_tick on every sheet, logo_shimmer + gears + whoosh_metal on the sting.
