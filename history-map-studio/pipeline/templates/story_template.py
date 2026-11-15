"""STORYBOARD TEMPLATE - copy to episodes/<slug>.py, fill the lists, delete what you do not use.
Every time is a CUE (a phrase from the narration), see story.py header:
  'Then came Darius'  'Then came Darius>' (end)  'Then came Darius +0.5'  'crowned Shah @ Chapter nine'  'ch:3'  'end'  'vend'  12.5
Every place is a NAME (python3 places.py <name> to test) or (lon, lat). Kinds (colours + emblems) are listed in KINDS_AVAILABLE below.

QUALITY BAR (qa.py checks most of this):
  * something new on screen every 3-6 s: camera key on every sentence, a label for every place spoken, a medallion for every person,
    a battle pill for every battle, an arrow for every march, a plate (real image) every 30-60 s;
  * a SIEGES close-up whenever the narration is at a city, siege, camp or battlefield;
  * chapters every 1-3 minutes with an era STYLE that fits the period;
  * camera jumps longer than the view use 'wipe' (the new map rolls in as a sheet, with a gear tick) or 'cut' (dissolve), never a whip pan.
"""
SLUG = 'my_episode'
STYLE = 'medieval'   # ancient | medieval | safavid | qajar | pahlavi | modern  (look before the first chapter)
PLACES = {}          # {'Some Fort': (lon, lat)} only for names the gazetteer lacks
KINDS = {}           # new factions: {'venice': (150, 30, 40)} (plain shield, no emblem)
# KINDS_AVAILABLE: rus mongol umayyad abbasid byz frank persian mede greek roman parthian sasanian caliph turk timurid safavid ottoman
#                  uzbek afghan mughal afshar russia britain iran usa israel iraq portugal elam qajar pakistan
# BOUNDS = (lon0, lon1, lat0, lat1)   # optional: normally computed from the CAMERA keys

TITLE = dict(at='<first words>', until='Chapter one -0.2', sub_at='<later phrase>', title='SHORT TITLE', sub='Subtitle line', dates='1514')
CHAPTERS = [('Chapter one', 'Title of chapter one', 'medieval'),     # (cue, title, era style or None)
            ('Chapter two', 'Title of chapter two', None)]
STYLES = []          # extra style switches: [('In 1906', 'pahlavi')]
YEARS = [(0, '1514')]  # (cue, text) year badge, top right

BRAND = dict(name='YOUR CHANNEL')   # channel name in bevelled gold; emblem='brand/emblem.png' (centre of the turning gear) or logo='brand/logo.png'
STING = True       # logo sting: plays in the gap after the hook (set "sting_after": "<last words of hook>", "sting_gap": 3.2 in the .json)
INTRO = 'sheet'    # the first map rolls in from the bottom as a tilted sheet
TRANSITION = 'sheet'   # close-ups fall in from the top; 'dissolve' for the old cross-fade

CAMERA = [           # (cue, place or (lon, lat), view width in degrees, optional 'wipe' | 'cut')
    (0, 'Tabriz', 8),
    ('Chapter one +1', 'Isfahan', 30, 'wipe')]

REALMS = [           # shape: [(lon, lat)...] | ['ISO:IRN', 'ISO:IRQ'] | {'hull': ['Tabriz', 'Herat', 'Shiraz'], 'pad': 1.5} | {'circle': 'Rome', 'r': 3}
    dict(at='<cue>', until='<cue>', kind='safavid', name='SAFAVID IRAN', shape={'hull': ['Tabriz', 'Herat', 'Shiraz', 'Baghdad']},
         label_at=None, grow=dict(**{'from': 'Tabriz'}, until='<cue>'), size=54, strength=.36)]
ARROWS = [dict(at='<cue>', to='<cue>', fade='<cue>', path=['Tabriz', 'Chaldiran'], kind='safavid', width=(12, 28), dashed=False)]
CITIES = [('<cue>', '<cue>', ['Tabriz', 'Isfahan'], 34)]           # labels: (from, until, names, size)
RIPPLES = [('<cue>', '<cue>', 'Tabriz')]                           # event pulse on a place
STRIKES = []                                                       # modern missile / air strike markers (modern style)
HATCH = []                                                         # (from, until, shape, (r, g, b)) danger hatching: blockades, closed straits
BATTLES = [('<cue>', '<cue>', 'Battle of X', '23 August 1514', 'ottoman', 'safavid')]   # pill at top: title, subtitle, left kind, right kind
PEOPLE = [           # image from tools/commons.py (licence-safe); no image -> heraldic crest; Muslim religious figures -> noor light automatically
    dict(at='<name spoken>', until='<cue>', name='Name', title='Role, years', kind='ottoman', place='Istanbul', image=None, crop=None, fallen=False)]
PLATES = [dict(at='<cue>', until='<cue>', image='folder/file.jpg', caption='What it is. Licence, via Wikimedia Commons', crop=None)]
SIEGES = [           # tactical close-up; climate arid|steppe|temperate|winter; field=True for an open battle; burn=cue or True
    dict(at='<cue>', until='<cue>', city='Isfahan', attacker='afghan', defender='safavid', climate='arid', river='Zayandeh Rud',
         burn='<cue>', title='Siege of Isfahan', sub='1722', year='1722', style='safavid')]
QUOTE = None         # dict(from='<first quoted words>', to='<last quoted words>', image='folder/x.jpg', title='Chronicle name', sub='as recorded by ...')
ROLL = None          # list card: dict(at, until, title='Ruling houses', items=[('<cue>', 'Medes', 'mede'), ...])
ONGOING = None       # dict(at, until, text='ONGOING CONFLICT · REPORTS STILL DEVELOPING') for current events
END_CARD = dict(title='TITLE', sub='One line', notes=['Borders and routes approximate.'])
SFX_EXTRA = []       # (cue, sound name in assets/sfx, gain dB, max seconds) - automatic SFX already cover arrows, pills, chapters, sieges
AUTO_SFX = True

import story; story.compile(globals())
