"""DEMO storyboard: Battle of Chaldiran (1514). Pure data - story.py does all drawing, styles, close-ups and sound.
Copy this file (or templates/story_template.py) for a new episode."""
SLUG = 'demo_chaldiran'
STYLE = 'atlas'                         # look before the first chapter; chapters below switch it
PLACES = {'Khoy': (44.95, 38.55), 'Urmia': (45.07, 37.55), 'Nakhchivan': (45.41, 39.21), 'Marash': (36.93, 37.58), 'Kefe': (35.38, 45.03)}                           # extra (lon, lat) for anything the gazetteer lacks

# no title card over the map (competitor presents the place with a pill + ring instead)
_OLD_TITLE = dict(at='Chaldiran, August', until='Sultan Selim -0.3', sub_at='two empires', title='CHALDIRAN', sub='Ottomans against Safavids', dates='23 August 1514')
CHAPTERS = [('Chapter one', 'The Challenge', 'atlas'),       # (cue, title, era style)
            ('Chapter two', 'The Battle', 'atlas')]
YEARS = [(0, '1514'), ('In 1501', '1501'), ('Within ten years', '1510'), ('Selim answered', '1514'), ('Chapter two', '1514')]

BRAND = dict(name='YOUR CHANNEL')   # your channel name; optional emblem='brand/emblem.png' (centre symbol) or logo='brand/logo.png'
STING = True                        # logo sting in the narration gap set by "sting_after" in the .json
INTRO = 'sheet'                     # first map rolls in as a sheet (with a soft gear tick)

CAMERA = [  # (cue, place, view width in degrees[, 'cut' = dissolve | 'wipe' = sheet roll-in])
    (0, 'Chaldiran', 12), ('Chaldiran, August +0.9', 'Chaldiran', 8.5), ('two empires', 'Chaldiran', 13),
    ('Sultan Selim', 'Ankara', 24), ('Shah Ismail brings', 'Tabriz', 16),
    ('Chapter one +1', 'Tabriz', 12), ('Within ten years', 'Isfahan', 30), ('Ottoman Anatolia', 'Ankara', 24),
    ('marching east', (40.0, 39.3), 22),
    ('Chapter two +1', 'Chaldiran', 12, 'wipe'), ('Two weeks later', 'Tabriz', 11), ('The Ottomans soon', (44.0, 37.5), 30)]

SAF = [(40.2, 41.0), (42.8, 41.1), (45.0, 41.1), (46.6, 41.6), (48.5, 41.5), (49.5, 40.5), (51, 39), (53.5, 38), (56, 38.2), (60, 37), (62, 36), (64, 34.5),
                (64.5, 31.5), (62, 29.5), (61.5, 25.5), (58, 25.8), (57, 26.5), (54, 26.5), (51, 27.8), (48.5, 29.8), (47, 30.5), (45.5, 33), (44.5, 36.5), (42.5, 37.2), (40.6, 38.6)]
MAP = dict(   # baked into the map like the competitor: realm colours (trees take the tint), huge curved names, town icons + labels
    realms=[
        dict(name='Ottoman Empire', kind='ottoman', tilt=-10, labels=[('Ottoman Empire', (32.6, 39.3), 210, 4200, -8)],
             shapes=[[(26, 42), (30, 41.5), (36, 41.8), (40.2, 41.0), (40.6, 38.6), (40, 37.6), (38.6, 37.6), (36.0, 36.6), (34, 36.2), (30, 36.2), (26, 37), (25, 40)],
                     [(19.4, 42), (19.0, 44.5), (21, 44.8), (22.5, 44.3), (25, 43.7), (28, 43.9), (28.6, 44.9), (29.7, 45.2), (28, 41.6), (26.0, 40.6), (24, 40.5), (22.5, 40), (21, 39.5), (20.0, 39.8), (19.4, 41)]]),
        dict(name='Mamluk Sultanate', kind='mamluk', tint=(222, 200, 140), tilt=-30, labels=[('Mamluk Sultanate', (36.2, 31.0), 260)],
             shape=[(25, 31.5), (29, 31), (32, 31.3), (34.2, 31.3), (34.9, 32.8), (35.6, 35.5), (35.9, 36.6), (38, 36.6), (38.8, 36.5), (38.5, 35), (37.5, 33.5), (38, 32), (37, 30),
                    (35.5, 28.5), (37.5, 25), (39.5, 22), (40, 20), (39, 19.3), (37, 21.5), (35, 25), (33.5, 27.5), (32.5, 29.8), (31, 28), (31, 24), (32.5, 22), (25, 22)]),
        dict(name='Dulkadir', kind='dulkadir', tint=(170, 208, 160), shape=[(36.0, 36.7), (36.3, 38.3), (37.5, 38.9), (38.6, 38.6), (38.7, 37.6), (38.0, 36.9), (37.0, 36.8)],
             labels=[('Dulkadir', (37.4, 37.85), 110)]),
        dict(name='Georgia', kind='georgia', tint=(196, 166, 210), shape=[(40.0, 41.6), (41.5, 41.5), (43.3, 41.2), (45, 41.2), (46.5, 41.7), (46.5, 42.2), (45.5, 42.6), (43.5, 42.9), (42, 43.3), (40.3, 43.3), (39.9, 42.5)],
             labels=[('Georgia', (43.6, 42.0), 130, 2600, -6)]),
        dict(name='Shaybanid Khanate', kind='uzbek', tint=(178, 184, 216), hatch=True, tilt=-12, labels=[('Shaybanids', (62.5, 41.6), 240)],
             shape=[(55.5, 45), (60, 45), (66, 45), (68, 44), (68, 37.3), (66, 37.2), (64, 37.8), (62.5, 38.5), (60, 40), (58, 40.8), (56, 42), (55.5, 43.5)]),
        dict(name='Safavid Iran', kind='safavid', shape=SAF, tilt=-12, labels=[('Safavid Iran', (53.5, 33.2), 230, 3800, -12)]),
    ],
    towns=[('Istanbul', 'cap', 'r', '(Constantinople)'), ('Edirne', 'town', 'l'), 'Bursa', 'Ankara', 'Konya', 'Sivas', 'Amasya', 'Trabzon', 'Erzincan', 'Erzurum',
           'Kayseri', 'Diyarbakir', 'Van', ('Chaldiran', 'town', 'l'), 'Khoy', ('Tabriz', 'cap', 'r'), 'Ardabil', 'Qazvin', 'Hamadan', 'Isfahan', 'Kashan', 'Shiraz',
           'Yazd', 'Kerman', 'Mashhad', 'Herat', 'Baghdad', 'Mosul', 'Basra', 'Aleppo', 'Damascus', ('Cairo', 'cap', 'r'), 'Jerusalem', 'Mecca', 'Medina',
           ('Tbilisi', 'cap', 'r'), ('Samarkand', 'cap', 'r'), 'Bukhara', 'Thessaloniki', 'Sofia', 'Malatya', ('Marash', 'town', 'l'), 'Urmia', 'Nakhchivan', 'Shamakhi', 'Merv', 'Balkh', 'Kandahar'])
KINDS = {'mamluk': (200, 150, 40), 'dulkadir': (60, 140, 60), 'georgia': (120, 70, 150), 'uzbek': (70, 80, 160)}

REALMS = []   # every realm is baked into MAP; the Safavid rise is shown with arrows from Tabriz
ARROWS = [  # path is a list of places / (lon, lat); 'to' = fully drawn, 'fade' = gone
    dict(at='Within ten years', to='taken all of Iran>', fade='Ottoman Anatolia', path=['Tabriz', 'Qazvin', 'Isfahan', 'Shiraz'], kind='safavid', leader='Shah Ismail I', cavalry=True),
    dict(at='Within ten years +0.4', to='taken all of Iran> +0.3', fade='Ottoman Anatolia', path=['Tabriz', 'Hamadan', 'Baghdad'], kind='safavid', width=(10, 24)),
    dict(at='Within ten years +0.8', to='taken all of Iran> +0.6', fade='Ottoman Anatolia', path=['Qazvin', 'Mashhad', 'Herat'], kind='safavid', width=(10, 24)),
    dict(at='his preachers', to='Ottoman Anatolia>', fade='Selim answered +1', path=['Erzincan', 'Sivas', 'Amasya'], kind='safavid', style='raid'),
    dict(at='his preachers +0.5', to='Ottoman Anatolia> +0.4', fade='Selim answered +1', path=['Erzurum', 'Malatya', 'Kayseri', 'Konya'], kind='safavid', style='raid'),
    dict(at='marching east', to='sixty thousand men>', fade='Chapter two', path=['Bursa', 'Ankara', 'Sivas', 'Erzincan', 'Erzurum', 'Chaldiran'], kind='ottoman', width=(14, 32), leader='Selim I'),
    dict(at='the Qizilbash charged', to='charged> +0.8', fade='The cannon broke +1.5', path=['Tabriz', (44.8, 38.7), (44.15, 39.05)], kind='safavid', width=(16, 34), leader='Shah Ismail I', cavalry=True),
    dict(at='Two weeks later', to='entered Tabriz>', fade='The Ottomans soon +2', path=['Chaldiran', 'Khoy', 'Tabriz'], kind='ottoman', leader='Selim I'),
]
CITIES = []   # town names are baked into the map (MAP['towns'])
RIPPLES = [('The cannon broke', 'Two weeks later', 'Chaldiran')]   # named cities get a turning white ring automatically
MARKS = [('The cannon broke', 'Chaldiran', '1514')]   # crossed swords + year stay on the map
BATTLES = [('Chaldiran, August +0.3', 'Sultan Selim -0.4', 'Battle of Chaldiran', '1514', 'ottoman', 'safavid'), ('Chapter two +1', 'Two weeks later', 'Battle of Chaldiran', '23 August 1514', 'ottoman', 'safavid')]
PEOPLE = [  # respect rule is automatic: only the Prophet and the Sahaba become noor light; everyone else gets a real period portrait
    dict(at='Sultan Selim', until='and Janissary +0.3', name='Selim I', title='Ottoman Sultan, later Caliph', kind='ottoman', place='Ankara', image='chaldiran/selim.jpg', crop=(0.20, 0.20, 0.80, 0.62)),
    dict(at='who believe', until='Chapter one -0.3', name='Shah Ismail I', title='Founder of Safavid Iran', kind='safavid', place='Tabriz', image='chaldiran/ismail.jpg', crop=(0.14, 0.22, 0.86, 0.80)),
]
PLATES = [dict(at='and Janissary', until='who believe', image='chaldiran/janissaries.jpg', caption='Janissary recruitment, Suleymanname, c. 1558. Public domain, via Wikimedia Commons'),
          dict(at='the Shah himself', until='Two weeks later +0.6', image='chaldiran/battle_mini.jpg', caption='Battle of Chaldiran, Selim-nama by Shukri-i Bitlisi, 1524. Public domain, via Wikimedia Commons'),
          dict(at='The Ottomans soon +1.5', until='vend +0.5', image='chaldiran/battlefield.jpg', caption='The plain of Chaldiran today. Public domain, via Wikimedia Commons')]
SIEGES = [  # tactical close-ups: field=True is an open battle; city='X' gives walls, streets and a besieging camp
    dict(at='Selim had chained', until='Two weeks later', field=True, attacker='ottoman', defender='safavid', climate='steppe',
         title='Chaldiran', sub='Ottoman guns behind wagons', year='1514', style='atlas', leaders=dict(attacker='Selim I', defender='Shah Ismail I'))]
END_CARD = dict(title='CHALDIRAN', sub='The border that still divides Turkey and Iran', notes=['Borders and routes approximate.'])
SFX_EXTRA = [('The cannon broke', 'boom', -9, 3), ('the Qizilbash charged', 'px_gallop_near', -9, 3)]

import story; story.compile(globals())
