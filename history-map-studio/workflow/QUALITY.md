# Quality bar (what separates a good result from a weak one)

Weak results from other assistants came from: few events (a static map with narration over it), coordinates guessed from
memory, missing close-ups, faces where light was required, SFX drowning the voice, and skipping the preview. The engine now
blocks most of these; you must still supply enough BEATS.

Targets for every minute of video
- 12-25 visual events per minute (`check` prints the number). Never more than 9 s without something new.
- 4-8 camera keys per minute; dissolve ('cut') for long jumps; slow push-ins on key moments.
- Every person named: medallion (2.5-6 s). Every place named: label. Every battle: pill + ripple + (close-up if > 1 sentence).
- Every movement of armies: arrow following real routes (via intermediate towns, not straight lines across mountains/seas).
- One real image plate every 30-60 s; one primary-source quote card per video.
- Chapters every 1-3 min, each with an era style that matches the period:
  ancient (before ~600 AD) | medieval (600-1500, the default parchment) | safavid (Persian/Islamic 1500-1750, miniature) |
  qajar (1750-1900, engraved survey) | pahlavi (1900-1970, printed atlas) | modern (1970-today, digital military display).

Look check on the contact sheet
- Realm shapes follow coasts and rivers; no state colour spilling into the sea far from its coast.
- Labels readable, not cut by the frame, not under a medallion; medallion arrow points to the right town.
- Close-ups: the right climate (arid / steppe / temperate / winter), the right attacker colours.
- No two pills or medallions on screen together.

Script check
- Cold open with a striking scene (place + date), then the question the video answers.
- Concrete numbers with honest uncertainty ("perhaps sixty thousand"); end with a consequence or a quote.


## Opening and transitions (v2.1)
- Cold open: the first map falls in from the top as a tilted sheet with a soft gear tick (`INTRO = 'sheet'`).
- Hook, then the channel logo sting: put `"sting_after": "<last words of the hook>"` and `"sting_gap": 3.2` in the episode .json. The voice keeps one TTS pass and opens one gap there. The logo card (dark slate, gold gear turning, emblem in the centre, channel name in bevelled gold) falls in from the top with light glowing from its bottom edge, then dissolves back into the map. Set `BRAND` once per channel; never copy another channel's logo.
- Big camera jumps: `'wipe'` on the camera key (new view falls in from the top over the old one, shadow on the old page). Close-ups roll in the same way and the map rolls back over them.
- Sounds are automatic: gear_tick on every sheet, logo_shimmer + gears + whoosh_metal on the sting.

- Sheet transitions take 1.4-1.6 s with ease in-out (slow start, slow landing); never snap.
- Medieval map is aged tan parchment, never white.
