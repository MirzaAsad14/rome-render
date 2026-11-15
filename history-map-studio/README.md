# History Map Studio 2 (plugin)

Make animated-map history documentaries (History Vanguard style) with any AI assistant + your computer.

## What changed in v2 (why results are better)
- Episodes are a DATA STORYBOARD (pipeline/episodes/<slug>.py): the AI lists beats, the engine (story.py) draws everything.
  No more hand-written drawing code, so other AIs can't produce broken or empty scenes.
- Cues are spoken PHRASES, not word numbers or seconds: edits to the script don't silently shift every visual.
- Places by NAME: built-in gazetteer (300 historical sites + 34,000 cities + country borders). No guessed coordinates.
- Any region of the world works: the illustrated atlas and sharp zoom-in detail maps are generated automatically.
- Era map styles (ancient -> medieval -> Persian miniature -> engraved -> printed atlas -> modern display) per chapter.
- Automatic tactical close-ups (walled city or open battlefield, climate, camps, burning) from one line.
- Respect rule enforced in code: only the Prophet and the Sahaba become noor light; later rulers get real portraits.
- Automatic era-appropriate SFX + music hits; the mix keeps the voice clear; audio loudness QA.
- `produce.py check` quality gate (cues, places, pacing/density, overlaps, whip pans, pronunciation) and contact-sheet preview.
- Licence-safe Wikimedia Commons image fetcher with automatic credits; YouTube description with chapter timestamps.
- Split rendering for long videos across machines / Kaggle / Colab.

## Quick start
    bash setup.sh                                   # Python deps + ffmpeg check
    python3 produce.py voice                        # free Edge voice, or ElevenLabs / HeyGen API key (premium)
    python3 produce.py build demo_chaldiran          # test: renders the 1-min demo (Battle of Chaldiran)
    python3 produce.py new "Battle of Molodi (1572)" --minutes 10
    python3 produce.py auto --minutes 1             # no title? auto-picks a topic
    python3 produce.py check <slug> && python3 produce.py preview <slug> && python3 produce.py build <slug>

## Use with your AI
- Claude Code: copy this folder, run `claude` inside it (reads CLAUDE.md), or install as a plugin
  (`.claude-plugin/plugin.json`, skill `history-map-video`, commands /make-video, /auto-video, /voice).
- Claude.ai: Settings > Capabilities > Skills > upload skills/history-map-video as a zip; attach the rest to a Project.
- Codex / Cursor: run in this folder (reads AGENTS.md).
- ChatGPT: see prompts/chatgpt_custom_gpt.md.   Grok: see prompts/grok.md.

Exactly identical results need the render to run here (Python + ffmpeg). Chat-only assistants can write the script and
scene files, then you run `python3 produce.py build <slug>`.

## Folder map
    CLAUDE.md / AGENTS.md     instructions for the AI
    workflow/                 RULES, WORKFLOW, STYLE, topics.json (auto-produce bank)
    produce.py                voice | new | auto | build | list
    pipeline/                 engine: atlas.py (map), kit.py (motion graphics), tactical.py (close-ups), voice.py (Edge/ElevenLabs/HeyGen),
                              music.py, sfx.py, render.py, make_video.sh, regions/, episodes/, templates/, assets/ (fonts, geo, img, sfx)

## Note on legacy episodes
`episodes/iran.py` and everything in `templates/advanced/` are the older hand-written style (Python scenes, word-index cues). They still work as references, but new episodes should use `story.py` storyboards (see `templates/story_template.py` and `episodes/demo_chaldiran.py`). `iran.py` needs its atlases rebuilt first with `pipeline/tools/build_atlas_iran.py`.
