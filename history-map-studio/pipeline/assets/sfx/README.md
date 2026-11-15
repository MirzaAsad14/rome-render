# Sound library

Cue sounds in the episode file:  SFX = [(time_s, name, gain_db, max_len_s), ...]  e.g. (W(56), 'px_gallop', -8, 3)
`name` is a file in this folder without extension, or `lib/<name>`. sfx.py peak-normalises each cue to gain_db,
trims leading silence, fades the tail; make_video.sh then ducks the whole SFX bus under the narration.

Gain guide: combat (swords, horns, gallops, arrows, war cries, impacts) -6 to -8 dB; transitions/whooshes -11 to -14 dB;
ambience beds -24 to -28 dB. No gunfire/modern sounds before gunpowder warfare. Never meme sounds.

## Top folder (battle-ready)
atmos, battle, boom, bow, braam, drum_march, fire, fire_woosh, gallop, lowhit, marker, neigh, paper_flip, paper_rip, px_ancient_drums, px_arrows, px_arrows_many, px_battle_drums, px_braam, px_drum_loop, px_gallop, px_gallop_near, px_horn, px_horn_drums, px_march, px_march_amb, px_medieval_war, px_sword_fight, px_swords1, px_swords2, px_swords3, px_war_cry, riser, swoosh, sword_court, sword_shing, sword_strike, thud, timpani, whoosh6, whoosh_cine

## lib/ (cinematic pack, by category)
- horn: 5 files (lib/horn_01 ... lib/horn_05)
- impact: 5 files (lib/impact_01 ... lib/impact_05)
- subdrop: 5 files (lib/subdrop_01 ... lib/subdrop_05)
- subdrop_low: 10 files (lib/subdrop_low_01 ... lib/subdrop_low_10)
- whoosh_a: 10 files (lib/whoosh_a_01 ... lib/whoosh_a_10)
- whoosh_b: 10 files (lib/whoosh_b_01 ... lib/whoosh_b_10)
- whoosh_c: 10 files (lib/whoosh_c_01 ... lib/whoosh_c_10)
- hit: 28 files (lib/hit_01 ... lib/hit_28)
- fire: 9 files (lib/fire_01 ... lib/fire_09)
- water: 6 files (lib/water_01 ... lib/water_06)
- bell: 5 files (lib/bell_01 ... lib/bell_05)
- tension: 15 files (lib/tension_01 ... lib/tension_15)
- wind_riser: 3 files (lib/wind_riser_01 ... lib/wind_riser_03)
- riser: 20 files (lib/riser_01 ... lib/riser_20)
- swish: 16 files (lib/swish_01 ... lib/swish_16)

See lib/index.json for durations and original file names.
