"""The Rise of Rome (753 BC - AD 117). Storyboard in the approved 'Chaldiran v2.10' structure (pure data for story.py),
plus small helpers that build the camera path and Rome's growing territory chapter by chapter.
Borders are approximate (see episodes/rome_geo.py)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rome_geo as RG
from rome_geo import G, polys

SLUG = 'rise_of_rome'
STYLE = 'atlas'
FPS = 24
REALM_MODE = 'occlude'      # one tint per pixel, later realms cover earlier ones, soft borders
MARK_LIFE = 'chapter'       # crossed swords stay until the next chapter slide ...
MARK_HOLD = 90              # ... but never longer than 90 s
MARK_MAX = 3                # at most 3 swords within MARK_RADIUS (4.5 deg); the oldest fades as a new one lands
RING_GAP = 40
RING_SKIP = ['Rome', 'Carthage']   # named constantly; rung explicitly in RINGS instead
MAX_DETAILS = 24
ATLAS_FADE = 0.35
CREST_MONOGRAM = True   # people with no surviving likeness: initials in Roman capitals, never an invented face
DETAIL_CRISP = 1.05    # ~1 atlas px per screen px in close views (keeps the detail atlases buildable on 2 cores)
DETAIL_MERGE = (9000, 7000)
DETAIL_LABEL_K = 0.4   # sea/river names in close views at about the same screen size as on the overview
BOUNDS = (-16.0, 58.0, 17.0, 62.0)   # whole Roman world, Britain to the Persian Gulf (keeps the overview atlas crisp)

BRAND = dict(name='YOUR CHANNEL')
STING = True
INTRO = 'sheet'

PLACES = {
    'Palatine': (12.486, 41.889), 'Veii': (12.40, 42.02), 'Allia': (12.56, 42.04), 'Caudine Forks': (14.60, 41.05), 'Sentinum': (12.93, 43.38),
    'Heraclea': (16.68, 40.21), 'Asculum': (15.57, 41.20), 'Beneventum': (14.78, 41.13), 'Tarentum': (17.24, 40.47), 'Messana': (15.55, 38.19),
    'Mylae': (15.24, 38.22), 'Aegates': (12.25, 37.97), 'Agrigentum': (13.58, 37.31), 'Lilybaeum': (12.44, 37.80), 'Panormus': (13.36, 38.12),
    'Saguntum': (-0.27, 39.68), 'New Carthage': (-0.98, 37.60), 'Trebia': (9.60, 45.03), 'Trasimene': (12.07, 43.19), 'Metaurus': (12.85, 43.70),
    'Massilia': (5.37, 43.30), 'Pergamon': (27.18, 39.13), 'Pydna': (22.55, 40.37), 'Cynoscephalae': (22.55, 39.43), 'Magnesia': (27.43, 38.61),
    'Philippi': (24.29, 41.01), 'Brundisium': (17.94, 40.64), 'Byzantium': (28.98, 41.01), 'Sarmizegetusa': (23.31, 45.62), 'Teutoburg': (8.13, 52.41),
    'Charax': (47.95, 30.5), 'Ostia': (12.29, 41.75), 'Neapolis': (14.25, 40.85), 'Gades': (-6.29, 36.53), 'Utica': (10.06, 37.06), 'Cyrene': (21.86, 32.82),
    'Ephesus': (27.34, 37.94), 'Sinope': (35.15, 42.03), 'Seleucia': (44.52, 33.10), 'Carrhae': (39.03, 36.87), 'Rubicon': (12.42, 44.10),
    'Pelusium': (32.55, 31.04), 'Artaxata': (44.55, 39.95), 'Nisibis': (41.22, 37.07), 'Londinium': (-0.09, 51.51), 'Lugdunum': (4.83, 45.76),
    'Mediolanum': (9.19, 45.46), 'Aquileia': (13.37, 45.77), 'Tarraco': (1.25, 41.12), 'Narbo': (3.0, 43.18), 'Ambracia': (20.98, 39.16),
    'Clusium': (11.95, 43.02), 'Capua': (14.25, 41.08), 'Croton': (17.12, 39.08), 'Hadrumetum': (10.64, 35.83), 'Apollonia': (19.47, 40.72),
    'Hellespont': (26.4, 40.2), 'Aquae Sextiae': (5.45, 43.53), 'Vercellae': (8.42, 45.32), 'Chaeronea': (22.84, 38.49), 'Athens': (23.73, 37.98),
    'Coracesium': (32.0, 36.53), 'Jerusalem': (35.23, 31.78), 'Antioch': (36.16, 36.2), 'Geneva': (6.14, 46.2), 'Bibracte': (4.04, 46.92),
    'Gergovia': (3.12, 45.71), 'Alesia': (4.50, 47.54), 'Zeugma': (37.87, 37.06), 'Ravenna': (12.2, 44.42), 'Ariminum': (12.57, 44.06),
    'Dyrrhachium': (19.45, 41.32), 'Pharsalus': (22.38, 39.30), 'Thessalonica': (22.94, 40.64), 'Sardis': (28.04, 38.49), 'Actium': (20.77, 38.95),
    'Corcyra': (19.92, 39.62), 'Vetera': (6.45, 51.66), 'Gesoriacum': (1.61, 50.73), 'Rutupiae': (1.33, 51.29), 'Camulodunum': (0.90, 51.89),
    'Pompeii': (14.49, 40.75), 'Viminacium': (21.21, 44.74), 'Drobeta': (22.66, 44.63), 'Tapae': (22.53, 45.53), 'Edessa': (38.79, 37.15),
    'Ctesiphon': (44.58, 33.09), 'Selinus': (32.27, 36.27), 'Tunis': (10.17, 36.80), 'Clupea': (11.10, 36.85), 'Zama': (9.45, 36.30),
    'Cannae': (16.13, 41.31), 'Carthage': (10.32, 36.85), 'Rome': (12.50, 41.90), 'Corinth': (22.88, 37.91), 'Pella': (22.52, 40.76),
    'Alexandria': (29.92, 31.20), 'Syracuse': (15.29, 37.07), 'Rhodes': (28.22, 36.44), 'Damascus': (36.29, 33.51), 'Babylon': (44.42, 32.54),
    'Corfinium': (13.84, 42.12), 'Mons Graupius': (-3.5, 56.9), 'Vesontio': (6.02, 47.24), 'Belgae': (3.5, 50.0),
}

# ------------------------------------------------------------------ chapters, years
CHAPTERS = [('Chapter one', "The Wolf's City", 'atlas'), ('Chapter two', 'Masters of Italy', 'atlas'), ('Chapter three', 'War at Sea', 'atlas'),
            ('Chapter four', 'Hannibal', 'atlas'), ('Chapter five', 'Mistress of the Mediterranean', 'atlas'),
            ('Chapter six', 'The Republic Turns on Itself', 'atlas'), ('Chapter seven', 'Pompey and Caesar', 'atlas'),
            ('Chapter eight', 'The Last Civil War', 'atlas'), ('Chapter nine', 'The Roman Peace', 'atlas')]
CH = {i + 1: c[0] for i, c in enumerate(CHAPTERS)}
YEARS = [(0, '8th c. BC'), ('Nine hundred years later', 'AD 117'), ('This is the story of how', '753 BC'),
         ('seven hundred and fifty three BC', '753 BC'), ('five hundred and nine BC', '509 BC'),
         ('Chapter two', '509 BC'), ('three hundred and ninety six BC', '396 BC'), ('three hundred and ninety BC', '390 BC'),
         ('three hundred and twelve BC', '312 BC'), ('humiliation at the Caudine Forks', '321 BC'), ('two hundred and ninety five BC', '295 BC'),
         ('two hundred and eighty BC', '280 BC'), ('again at Asculum', '279 BC'), ('two hundred and seventy five BC', '275 BC'), ('two hundred and sixty four BC, Rome', '264 BC'),
         ('Chapter three', '264 BC'), ('two hundred and sixty BC', '260 BC'), ('two hundred and fifty six BC', '256 BC'), ('two hundred and forty one BC', '241 BC'),
         ('soon Sardinia and Corsica', '238 BC'),
         ('Chapter four', '237 BC'), ('two hundred and eighteen BC', '218 BC'), ('In June of the following year', '217 BC'), ('two hundred and sixteen BC', '216 BC'),
         ('two hundred and seven BC', '207 BC'), ('captured New Carthage', '209 BC'), ('drove the Carthaginians from Spain', '206 BC'), ('two hundred and four BC', '204 BC'),
         ('two hundred and two BC', '202 BC'),
         ('Chapter five', '200 BC'), ('one hundred and ninety seven BC', '197 BC'), ('In one hundred and ninety, at Magnesia', '190 BC'), ('one hundred and sixty eight', '168 BC'),
         ('one hundred and forty nine BC', '149 BC'), ('one hundred and forty six BC', '146 BC'),
         ('Chapter six', '133 BC'), ('Twelve years later', '121 BC'), ('Then came the generals', '107 BC'), ('one hundred and two and one hundred', '102 BC'),
         ('rose in the Social War', '91 BC'), ('eighty eight BC', '88 BC'), ('made himself dictator', '82 BC'), ('a gladiator named Spartacus', '73 BC'),
         ('Chapter seven', '67 BC'), ('in sixty three BC took Jerusalem', '63 BC'), ('In sixty BC', '60 BC'), ('from fifty eight BC', '58 BC'), ('crossed twice into Britain', '55 BC'),
         ('In fifty two BC', '52 BC'), ('invaded Parthia', '53 BC'), ('January forty nine BC', '49 BC'), ('forty eight BC', '48 BC'), ('first for ten years', '46 BC'),
         ('On the Ides of March', '15 March 44 BC'),
         ('Chapter eight', '44 BC'), ('in forty two BC', '42 BC'), ('settled their scores at home', '43 BC'), ('The victors divided', '40 BC'),
         ('thirty one BC', '31 BC'), ('Within a year', '30 BC'), ('In January twenty seven BC', '27 BC'),
         ('Chapter nine', '27 BC'), ('The conquests went on', '15 BC'), ('in AD nine', 'AD 9'), ('AD forty three', 'AD 43'), ('AD eighty', 'AD 80'),
         ('AD ninety eight', 'AD 98'), ('In two hard wars', 'AD 101-106'), ('AD one hundred and fourteen', 'AD 114'), ('AD one hundred and sixteen', 'AD 116'),
         ('In that moment', 'AD 117')]


def off(cue, d):
    """shift a cue by d seconds (keeps an existing offset)"""
    m = re.search(r'\s([+-]\d+(?:\.\d+)?)$', cue)
    if m: return f"{cue[:m.start()]} {float(m.group(1)) + d:+.2f}"
    return f'{cue} {d:+.2f}'


# ------------------------------------------------------------------ camera (smooth glides; 'cut' dissolves for long jumps; 'wipe' only at chapters)
CAMERA = []
_last = [None]
def cam(cue, place, w):
    CAMERA.append((cue, place, w)); _last[0] = (place, w)
def cut(cue, place, w, hold=1.8):
    p, pw = _last[0]; CAMERA.append((off(cue, -hold), p, pw)); CAMERA.append((cue, place, w, 'cut')); _last[0] = (place, w)
def wipe(n, place, w):
    p, pw = _last[0]; CAMERA.append((off(CH[n], -1.0), p, pw)); CAMERA.append((off(CH[n], 1.2), place, w, 'wipe')); _last[0] = (place, w)

# hook
cam(0, 'Rome', 10); cam('On a hill above', 'Palatine', 7.5); cam('Their neighbours are older', (12.9, 42.0), 13)
cam('Nine hundred years later', (14.5, 41.6), 19); cam('the descendants of those +1.2', (17, 41.5), 34); cam('one in five of all', (18, 41.0), 56)
cam('The Greek historian Polybius', (16, 41.0), 44); cam('in less than fifty three years', (17, 41.2), 40); cam('Fifty three years was only', (13, 42.0), 22); cam('This is the story of how', 'Rome', 10)
# chapter one
wipe(1, 'Rome', 9); cam('Twin boys', 'Palatine', 7.5); cam('Grown to manhood', 'Palatine', 7); cam('Livy, writing under Augustus', (12.6, 41.9), 9); cam('more fit for poets', (12.55, 41.92), 8.2); cam('The traditional date', 'Rome', 8.8)
cam('Archaeology tells a quieter story', 'Palatine', 7); cam('Rome grew where a river crossing', 'Rome', 11); cam('Etruscan cities to the north', (11.9, 42.8), 11)
cam('Latins and Greeks to the south', (14.3, 41.0), 15); cam('In the Forum, beneath', 'Rome', 8); cam('Tradition gives Rome seven kings', (12.4, 42.1), 10); cam('The last three were Etruscans', (12.2, 42.4), 11); cam('From the Etruscans, too', (12.0, 42.7), 12); cam('carried before every Roman', 'Rome', 9)
cam('The last of all, Tarquin', 'Rome', 9); cam('they drove the king out', (12.2, 42.4), 10); cam('Power passed to two consuls', 'Rome', 9); cam('a council of elders', (12.5, 41.92), 8.2)
cam('the Senate and the People of Rome', 'Rome', 7.5)
# chapter two
wipe(2, (12.5, 42.15), 10); cam('Its greatest rival was Veii', (12.45, 42.0), 8); cam('Rome doubled its land', (12.5, 42.0), 9)
cam('Then catastrophe came from the north', (11.2, 44.0), 18); cam('destroyed a Roman army at', (12.5, 42.1), 9.5); cam('Livy tells how the sacred', 'Rome', 8); cam('When the Romans paid a ransom', 'Rome', 9); cam('Rome never forgot it', 'Rome', 10)
cam('turned south', (13.6, 41.5), 13); cam('In three long wars against the Samnites', (14.4, 41.6), 11); cam('won victory at Sentinum', (13.2, 42.6), 11)
cam('Its secret weapon was not', (13.4, 42.0), 15); cam('the Greek city of Tarentum', (17.5, 40.3), 14); cam('Pyrrhus beat the Romans', (16.2, 40.8), 10)
cam('Beaten at Beneventum', (15.6, 40.9), 11); cam('he sailed home', (18.2, 40.0), 13); cam('By two hundred and sixty four BC, Rome', (13.8, 41.3), 19)
# chapter three
wipe(3, (14.0, 38.4), 13); cam('Across a strait just', 'Messana', 8); cam('beyond it Carthage', (11.6, 37.4), 13)
cam('the richest power in the western', (5.0, 38.5), 30); cam('both powers were drawn', 'Messana', 9); cam('Rome had almost no warships', (13.0, 40.5), 14)
cam('built a fleet of one hundred', (13.5, 40.0), 16); cam('They added a weapon', (14.5, 39.3), 14); cam('off Mylae on the north coast', 'Mylae', 8); cam('An inscription from his victory', (14.2, 38.3), 11); cam('a Roman army even landed', (11.4, 37.0), 11)
cam('The war ground on through storms', (12.8, 37.6), 13); cam('off the Aegates Islands', 'Aegates', 8.5); cam('Carthage gave up Sicily', (12.5, 39.0), 15)
cam('In time the Romans would call', (12.0, 39.0), 30)
# chapter four
wipe(4, (-2.0, 38.6), 16); cam('That son was Hannibal', 'New Carthage', 11); cam('after he took the Roman ally', 'Saguntum', 9)
cam('He marched from New Carthage', (-0.5, 39.6), 15); cam('through the Pyrenees', (2.6, 42.3), 15); cam('across the Rhone', (4.9, 43.9), 14)
cam('over the Alps in late autumn', (7.0, 45.0), 11); cam('Polybius says the army left', (6.0, 44.2), 16); cam('but only about twenty thousand', (7.3, 45.0), 10); cam('What followed was a nightmare', (10.5, 44.0), 16)
cam('at the river Trebia', 'Trebia', 8.5); cam('In June of the following year', (11.2, 43.8), 11); cam('at Lake Trasimene', 'Trasimene', 8.5)
cam('Then, on the second of August', (14.3, 42.2), 13); cam('at Cannae in Apulia', 'Cannae', 8.5); cam("Livy says Hannibal's brother", (13.0, 39.2), 22); cam('Yet Hannibal did not march', (14.5, 41.5), 13); cam('Yet Rome would not make peace', (13.5, 42.0), 12)
cut('Hannibal\'s brother Hasdrubal crossed', (8.0, 44.0), 20); cam('destroyed at the river Metaurus', 'Metaurus', 9)
cut('A young general, Publius', (0.0, 39.5), 14); cam('in two hundred and four BC landed', (11.5, 37.6), 13); cam('Hannibal was recalled', (13.5, 37.8), 18)
cam('At Zama, in two hundred', 'Zama', 8.5); cam('Carthage surrendered its fleet', (10.0, 36.6), 12); cam('Scipio came home', (11.5, 39.0), 22)
# chapter five
wipe(5, (21.5, 39.5), 26); cam('Rome turned east', (25.0, 38.0), 30); cam('to the kingdoms carved', (30.0, 36.8), 36); cam('at Cynoscephalae', 'Cynoscephalae', 9); cam('at Magnesia in Asia Minor', (26.5, 39.0), 11)
cam('And at Pydna', 'Pydna', 9); cam('Polybius, the Greek hostage', (22.0, 40.0), 12); cut('Then Rome finished its old enemy', 'Rome', 10)
cam('In one hundred and forty nine BC Rome', (11.0, 38.5), 13); cam('After a three year siege', 'Carthage', 8.5); cam('saw him weep', (10.35, 36.88), 8); cam('The famous story that the Romans', (10.4, 36.9), 9)
cut('Roman troops sacked Corinth', 'Corinth', 9); cam('Africa and Macedonia became', (16.0, 39.0), 16); cut('Polybius had his answer', (16.0, 39.0), 40); cam('Rome had become the master', (15.0, 39.5), 46); cam('From Spain to Asia Minor', (14.0, 39.0), 50)
# chapter six
wipe(6, (12.8, 42.0), 12); cam('Conquest brought slaves', (13.0, 41.6), 11); cam('the rich bought up the land', (13.4, 41.3), 10); cam('the tribune Tiberius Gracchus', 'Rome', 8); cam('It was the first time since', 'Rome', 7.5); cam('Twelve years later', 'Rome', 9)
cam('Then came the generals', (10.0, 43.5), 18); cam('opened the legions to the landless', (11.0, 43.3), 15); cam('who now looked to their commander', (10.0, 44.0), 17); cam('Marius was consul seven', (8.5, 44.5), 17); cam('he destroyed the migrating Cimbri', (6.5, 45.0), 16); cam("Then Rome's Italian allies", (13.8, 42.0), 12)
cam('Lucius Cornelius Sulla did', (13.2, 41.6), 10); cut('a war in the east against Mithridates', (28.0, 39.5), 22); cut('posted lists of his enemies', 'Rome', 9)
cam('a gladiator named Spartacus', (14.5, 41.0), 14); cam('Appian says six thousand captives', (13.4, 41.4), 10); cam('The Republic survived Sulla', (13.0, 41.8), 16)
# chapter seven
wipe(7, (24.0, 37.0), 30); cam('Then he conquered the east', (33.0, 37.5), 22); cam('took Jerusalem', 'Jerusalem', 8.5)
cut('he joined the richest man in Rome', 'Rome', 10); cut('As governor of Gaul from', (3.0, 46.8), 17); cam('crossed twice into Britain', (1.0, 50.6), 11)
cam('Plutarch claims that in less', (2.5, 46.8), 17); cam('killing one million', (2.6, 47.1), 15.5); cam('Ancient numbers like these', (2.0, 47.2), 15); cam('but the toll was terrible', (3.0, 46.6), 13); cam('all Gaul rose under', (3.5, 46.4), 12); cam('Caesar trapped him in the hill fort', 'Alesia', 8.5)
cam('Vercingetorix laid down his arms', 'Alesia', 9); cut('Crassus, hungry for glory', (38.0, 36.8), 13); cam('where Plutarch says twenty', 'Carrhae', 9); cut('Ordered to give up his army', 'Rubicon', 8.5)
cam('Suetonius gives his words', (12.6, 43.3), 10); cut('At Pharsalus in Greece', 'Pharsalus', 9); cam('who fled to Egypt', (27.0, 34.5), 18)
cut('Caesar made himself dictator', 'Rome', 9); cam('On the Ides of March', 'Rome', 7.5)
# chapter eight
wipe(8, 'Rome', 10); cam("Octavian joined Caesar's", (19.0, 40.8), 18); cam('at Philippi in Macedonia', 'Philippi', 9)
cut('Before that, the new allies', 'Rome', 9); cut('The victors divided the Roman world', (18.0, 38.5), 42); cam('Octavian took Italy and the west', (14.0, 41.0), 39); cam('the war of words', (16.5, 40.2), 26); cam('off the headland of Actium', 'Actium', 8.5)
cam('The queen broke out -1.4', (20.9, 38.45), 9); cam('her squadron and fled +0.8', (24.0, 35.0), 18); cam('Octavian entered Alexandria', 'Alexandria', 9); cam('Egypt, the richest land', (29.0, 30.5), 16)
cut('In January twenty seven BC', (14.0, 41.5), 24); cam('After that time, he wrote', (13.0, 42.0), 20); cam('In truth, the Republic was over', (16.0, 40.0), 50)
# chapter nine
wipe(9, (13.0, 43.5), 26); cam('He cut the armies of the civil', (12.5, 44.0), 28); cam('stationed them on the frontiers', (14.0, 45.0), 32); cam('Suetonius says he found Rome', 'Rome', 9); cam('The doors of the temple of Janus', 'Rome', 8); cam('Augustus boasted that', 'Rome', 9.5); cam('The conquests went on', (12.0, 45.5), 26)
cam('in the Teutoburg Forest', (8.4, 52.0), 10); cam('The Rhine became the frontier', (8.0, 49.0), 18); cut('Claudius invaded Britain', (-1.0, 52.0), 13)
cut('Under the Flavian emperors', 'Rome', 10); cam('Then, in AD ninety eight', (16.0, 44.0), 24); cam('In two hard wars he crossed', (23.0, 45.3), 11)
cam('The war is carved in a spiral', (23.0, 45.6), 13); cam('In AD one hundred and fourteen -1.2', (24.0, 45.6), 14); cut('he turned on Parthia', (40.5, 37.0), 18); cam('captured the Parthian capital', 'Ctesiphon', 9)
cam('sailed down the Tigris', (47.0, 31.2), 10); cam('he watched a ship leaving', (49.0, 29.6), 9); cam('In that moment the Roman Empire', (18.0, 41.0), 56); cam('But revolts were already', (38.0, 36.0), 24)
cam('among the Jewish communities', (34.0, 32.0), 20); cam('His successor, Hadrian', (30.0, 38.0), 36); cut('The historian Tacitus', (-2.5, 55.0), 13); cam('put into the mouth of a British', (-3.4, 56.3), 11); cam('The village on the Tiber', (18.0, 41.0), 56)
cam('It would never be larger', (14.0, 41.5), 40); cam('How it held on', (17.0, 41.5), 54)

# ------------------------------------------------------------------ map: towns small per frame, realm names big
MAP = dict(realms=[], towns=[
    ('Rome', 'cap', 'r'), ('Veii', 'minor', 'u'), ('Ostia', 'minor', 'l'), ('Capua', 'town', 'u'), ('Neapolis', 'minor', 'd'), ('Tarentum', 'town', 'r'),
    ('Brundisium', 'town', 'r'), ('Messana', 'town', 'r'), ('Syracuse', 'town', 'r'), ('Agrigentum', 'minor', 'd'), ('Lilybaeum', 'minor', 'l'),
    ('Carthage', 'cap', 'r'), ('Utica', 'minor', 'l'), ('Massilia', 'town', 'd'), ('Saguntum', 'minor', 'r'), ('New Carthage', 'town', 'd'), ('Gades', 'town', 'r'),
    ('Tarraco', 'minor', 'r'), ('Narbo', 'minor', 'l'), ('Lugdunum', 'minor', 'r'), ('Mediolanum', 'minor', 'r'), ('Aquileia', 'minor', 'r'),
    ('Alesia', 'minor', 'r'), ('Londinium', 'minor', 'r'), ('Athens', 'town', 'r'), ('Corinth', 'town', 'l'), ('Pella', 'cap', 'r'), ('Byzantium', 'town', 'r'),
    ('Pergamon', 'cap', 'r'), ('Ephesus', 'town', 'l'), ('Rhodes', 'minor', 'r'), ('Sinope', 'town', 'r'), ('Antioch', 'cap', 'r'), ('Damascus', 'minor', 'r'),
    ('Jerusalem', 'town', 'l'), ('Alexandria', 'cap', 'r'), ('Cyrene', 'town', 'r'), ('Seleucia', 'minor', 'l'), ('Ctesiphon', 'cap', 'r'), ('Babylon', 'minor', 'l'),
    ('Charax', 'minor', 'r'), ('Artaxata', 'minor', 'r'), ('Nisibis', 'minor', 'r'), ('Sarmizegetusa', 'cap', 'r'), ('Clusium', 'minor', 'r')])
KINDS = {'roman': (168, 28, 34), 'carthage': (112, 52, 150), 'etruscan': (196, 112, 40), 'latin': (204, 176, 64), 'samnite': (64, 128, 64),
         'greek': (40, 100, 176), 'gaul': (96, 134, 40), 'macedon': (206, 152, 30), 'seleucid': (36, 112, 148), 'ptolemaic': (214, 178, 70),
         'parthia': (40, 132, 118), 'pontus': (150, 40, 112), 'numidia': (176, 136, 86), 'germanic': (46, 104, 62), 'dacian': (128, 80, 46),
         'pergamon': (124, 100, 176), 'epirus': (36, 152, 172), 'syracuse': (70, 144, 204), 'antony': (214, 112, 36), 'armenia': (190, 90, 124),
         'briton': (64, 120, 70), 'nabataean': (190, 150, 108), 'iberian': (150, 128, 88), 'judea': (88, 120, 168), 'pompeian': (60, 82, 150)}

# ------------------------------------------------------------------ realms
def R(name, kind, shp, at, until, label=None, size=0, tilt=-10, grow=None, group=None, label_until=None, fade=1.0, label_gap=None):
    d = dict(name=name, kind=kind, shapes=shp if isinstance(shp[0][0], tuple) else [shp], at=at, until=until, size=size, tilt=tilt, fade=fade)
    if label: d['label_at'] = label
    if grow: d['grow'] = dict(grow)
    if group: d['group'] = group
    if label_until: d['label_until'] = label_until
    if label_gap: d['label_gap'] = label_gap
    return d
P_ = lambda *parts: polys(G(*parts))

E1 = 'Chapter one'; E2 = 'Chapter two'; E3 = 'Chapter three'; E4 = 'Chapter four'; E5 = 'Chapter five'; E6 = 'Chapter six'; E7 = 'Chapter seven'; E8 = 'Chapter eight'; E9 = 'Chapter nine'
END = 'end'
REALMS = [
    # ---- Italy's neighbours (hook -> ch2)
    R('Etruscans', 'etruscan', RG.ETRUSCANS, 'Their neighbours are older', 'Then catastrophe came from', (11.4, 43.2), 30, -20, label_gap=('the descendants of those', 'Fifty three years was only +0.6')),
    R('Latins', 'latin', RG.LATINS, 'Their neighbours are older', 'Its secret weapon was not', (13.15, 41.48), 18, -15, label_gap=('the descendants of those', 'Fifty three years was only +0.6')),
    R('Samnites', 'samnite', RG.SAMNITES, 'Their neighbours are older +0.4', 'Its secret weapon was not', (14.55, 41.45), 22, -30, label_gap=('the descendants of those', 'Fifty three years was only +0.6')),
    R('Greek cities', 'greek', RG.MAGNA_GRAECIA, 'Their neighbours are older +0.8', 'By two hundred and sixty four BC, Rome', (16.6, 39.4), 24, -40, label_gap=('the descendants of those', 'Fifty three years was only +0.6')),
    R('Carthage', 'carthage', [*RG.CARTH_AFRICA, *RG.CARTH_SICILY, *RG.CARTH_SPAIN_COAST, *P_(RG.SARDINIA())], 'Their neighbours are older +1.2', 'Carthage surrendered its fleet', (8.5, 35.4), 46, -6, label_gap=('the descendants of those', 'Fifty three years was only +0.6')),
    R('Gauls', 'gaul', RG.GAULS_CIS, 'Gallic warriors crossed', 'Chapter four', (9.6, 45.3), 34, -6),
    R('Epirus', 'epirus', RG.EPIRUS, 'Pyrrhus, King of Epirus', 'Chapter five', (20.3, 39.8), 20, -40),
    R('Syracuse', 'syracuse', RG.SYRACUSE, 'Chapter three', 'Chapter four', (14.9, 37.15), 14, -10),
    R('Carthage', 'carthage', RG.CARTH_BARCID, 'Carthage rebuilt its power', 'drove the Carthaginians from Spain', (-3.6, 38.0), 30, -12, grow=dict({'from': 'New Carthage', 'until': 'Carthage rebuilt its power +4'})),
    R('Numidia', 'numidia', [*RG.NUMIDIA, *RG.MAURETANIA], 'Carthage surrendered its fleet', 'Chapter seven', (3.0, 35.2), 34, -4),
    R('Carthage', 'carthage', RG.CARTH_201, 'Carthage surrendered its fleet', 'Africa and Macedonia became', (9.9, 35.9), 16, -10),
    R('Iberian tribes', 'iberian', P_('ISO:ESP#0', 'ISO:PRT#0'), 'Chapter four', 'The conquests went on +4', (-5.5, 41.3), 26, -8),
    R('Gaul', 'gaul', polys(RG.gaul()), 'Chapter four', 'conquered everything between the Rhine +4', (2.2, 47.2), 40, -10),
    R('Germanic tribes', 'germanic', RG.GERMANIA_FREE, 'Chapter six', END, (11.5, 52.2), 34, -8),
    R('Britons', 'briton', polys(RG._iso('GBR', 0)), 'crossed twice into Britain', END, (-4.0, 57.2), 26, -60),
    # ---- the Hellenistic east
    R('Macedon', 'macedon', RG.MACEDON, 'Chapter four', 'Then Rome finished its old enemy', (22.6, 41.2), 30, -6),
    R('Greek leagues', 'greek', RG.GREEK_LEAGUES, 'Chapter four', 'Africa and Macedonia became', (22.1, 37.6), 18, -30),
    R('Seleucid Empire', 'seleucid', RG.SELEUCID_200, 'Chapter four', 'And at Pydna', (44.0, 34.0), 46, -8),
    R('Seleucid Empire', 'seleucid', RG.SELEUCID_188, 'And at Pydna', 'Then he conquered the east +3', (42.0, 34.0), 40, -8),
    R('Ptolemaic Egypt', 'ptolemaic', RG.PTOLEMAIC, 'Chapter four', 'Egypt, the richest land +3', (30.8, 27.0), 34, -70),
    R('Pergamon', 'pergamon', RG.PERGAMON_200, 'Chapter four', 'And at Pydna'),
    R('Pergamon', 'pergamon', RG.PERGAMON_188, 'And at Pydna', 'Chapter six', (29.2, 38.7), 22, -10),
    R('Rhodes', 'greek', RG.RHODES, 'Chapter four', 'Chapter six'),
    R('Parthia', 'parthia', RG.PARTHIA_200, 'Chapter four', 'Chapter six', (57.0, 36.5), 26, -6),
    R('Parthia', 'parthia', RG.PARTHIA, 'Chapter six', END, (50.5, 33.5), 44, -8),
    R('Pontus', 'pontus', RG.PONTUS_100, 'Chapter six', 'a war in the east against Mithridates'),
    R('Pontus', 'pontus', RG.PONTUS_88, 'a war in the east against Mithridates', 'Then he conquered the east +3', (34.0, 40.6), 30, -6,
      grow=dict({'from': 'Sinope', 'r0': 3, 'until': 'a war in the east against Mithridates +4'})),
    R('Armenia', 'armenia', RG.ARMENIA, 'Chapter six', 'He annexed Armenia +3', (43.2, 40.0), 22, -10),
    R('Judea', 'judea', RG.JUDEA, 'took Jerusalem', 'Chapter nine', (35.4, 31.9), 12, -60),
    R('Dacia', 'dacian', P_(RG.DACIA_KINGDOM), 'Chapter eight', 'In AD one hundred and fourteen +2', (25.0, 45.7), 30, -10),
    R('Nabataeans', 'nabataean', RG.ARABIA_PETRAEA, 'Chapter seven', 'Chapter nine +60', (36.3, 30.3), 16, -60),
]

# ---- Rome: pieces grow when conquered; at every chapter slide they are merged into one base shape (cheaper to draw)
ROME_PIECES = {   # chapter: [(cue, grow-from, parts, grow-seconds)]
    0: [(0, 'Rome', RG.ROME_753, 0.1)],
    1: [('Power passed to two consuls', 'Rome', RG.ROME_509, 2.5)],
    2: [('Rome doubled its land', 'Veii', RG.ROME_396, 2.5), ('Its secret weapon was not', 'Rome', RG.ROME_290, 4.0),
        ('Rome controlled the whole peninsula', 'Rome', [RG.italy_264()], 4.5)],
    3: [('Carthage gave up Sicily', 'Messana', [RG.SICILY()], 3.0), ('soon Sardinia and Corsica', (9.0, 41.0), [RG.SARDINIA(), RG.CORSICA()], 3.0)],
    4: [('In two hundred and eighteen BC', (10.5, 45.0), [RG.italy_north()], 2.0), ('drove the Carthaginians from Spain', 'New Carthage', RG.HISP_206, 3.5)],
    5: [('Africa and Macedonia became', 'Carthage', RG.AFRICA_146, 2.5), ('Africa and Macedonia became +0.6', 'Pella', [*RG.MACEDON, *RG.GREEK_LEAGUES, *RG.ILLYRIA], 3.5),
        ('From Spain to Asia Minor', (-2.0, 40.0), RG.HISP_133, 3.0)],
    6: [('Chapter six +2', 'Pergamon', RG.ASIA_133, 3.0), ('Then came the generals', 'Narbo', RG.NARBONENSIS, 3.0), ('posted lists of his enemies +1', 'Cyrene', RG.CYRENAICA, 2.0)],
    7: [('Then he conquered the east', 'Antioch', [*RG.SYRIA, *RG.CILICIA, *RG.BITHYNIA_PONTUS, *RG.CRETE], 4.0),
        ('conquered everything between the Rhine', 'Alesia', [RG.gaul()], 4.0), ('Caesar made himself dictator', 'Utica', [*RG.AFRICA_NOVA, *RG.HISP_44], 3.0)],
    8: [('Egypt, the richest land', 'Alexandria', RG.EGYPT, 2.5), ('In January twenty seven BC', (32.0, 39.0), ['ISO:TUR', *RG.CYPRUS], 3.0)],
    9: [('The conquests went on', (12.0, 46.5), RG.DANUBE_PROVINCES, 4.0), ('The conquests went on +0.8', (-6.0, 42.8), ['ISO:ESP#0', 'ISO:PRT#0'], 3.0),
        ('Claudius invaded Britain', 'Camulodunum', [RG.britain(RG.BRITAIN_CLIP_43)], 3.0), ('Under the Flavian emperors', (-2.0, 53.5), [RG.britain(RG.BRITAIN_CLIP_117)], 2.0),
        ('Under the Flavian emperors +1', (2.0, 35.5), [*RG.MAURETANIA_PROV, *RG.THRACE, *RG.CAPPADOCIA_ETC, *RG.JUDEA], 3.0),
        ('In AD one hundred and fourteen -1', 'Sarmizegetusa', RG.DACIA_PROV, 2.5), ('In AD one hundred and fourteen -0.5', (36.0, 30.5), RG.ARABIA_PETRAEA, 2.0)],
}
LOST = {   # pieces that Rome later gives up: (chapter, cue, place, parts, grow, until)
    'germania': (9, 'The conquests went on +1.5', (8.5, 50.5), RG.GERMANIA_ROMAN, 3.0, 'lost three entire legions +1'),
    'armenia': (9, 'He annexed Armenia', 'Artaxata', RG.ARMENIA, 2.5, 'gave up the new eastern provinces +1'),
    'mesopotamia': (9, 'took Mesopotamia', 'Nisibis', RG.MESOPOTAMIA, 3.5, 'gave up the new eastern provinces +1.5'),
}
NEXT = {k: (CH[k + 1] if k + 1 in CH else END) for k in range(0, 10)}
acc = []
for k in range(0, 10):
    if k >= 2:   # merged base for this chapter: everything won before it
        REALMS.append(R(None, 'roman', polys(G(*acc)), off(CH[k], -1.0), off(NEXT[k], 1.5), group='Rome', fade=0.05))
    for cue, frm, parts, gs in ROME_PIECES.get(k, []):
        start = cue
        until = off(NEXT[k], 1.5) if k else off(CH[2], 1.5)
        REALMS.append(R(None, 'roman', polys(G(*parts)), start, until, group='Rome', fade=0.3,
                        grow={'from': frm, 'r0': 0.3, 'until': off(start, gs) if isinstance(start, str) else gs}))
        acc += parts
for key, (k, cue, frm, parts, gs, until) in LOST.items():
    REALMS.append(R(None, 'roman', polys(G(*parts)), cue, until, group='Rome', fade=0.3, grow={'from': frm, 'r0': 0.3, 'until': off(cue, gs)}))
# the AD 117 empire, flashed in the cold open and shown again at its height
REALMS.append(R('Roman Empire', 'roman', polys(RG.empire_117()), 'the descendants of those', 'Fifty three years was only +0.5', (17.0, 43.5), 70, -6,
                grow={'from': 'Rome', 'r0': 0.5, 'until': 'Persian Gulf> +0.4'}, group='Rome', fade=0.4))
# names of Rome (label holders: an invisible speck at sea carries the big curved name)
SPECK = lambda lon, lat: [[(lon, lat), (lon + .01, lat), (lon, lat + .01)]]
REALMS += [
    R('Rome', 'roman', SPECK(11.4, 41.2), 'Chapter one +3', 'Power passed to two consuls', (12.62, 42.12), 16, -10),
    R('Roman Republic', 'roman', SPECK(11.4, 41.2), 'Power passed to two consuls +1', 'Chapter two', (12.62, 42.1), 16, -10),
    R('Roman Republic', 'roman', SPECK(11.4, 41.2), 'Chapter two +3', 'Its secret weapon was not', (12.6, 42.05), 18, -10),
    R('Roman Republic', 'roman', SPECK(11.4, 41.2), 'Its secret weapon was not +4', 'Chapter four', (13.6, 42.2), 28, -32),
    R('Roman Republic', 'roman', SPECK(11.4, 41.2), 'Chapter four +3', 'Chapter six', (13.2, 42.4), 40, -32),
    R('Roman Republic', 'roman', SPECK(11.4, 41.2), 'Chapter six +3', 'The victors divided the Roman world', (14.0, 42.6), 44, -32),
    R('Roman Empire', 'roman', SPECK(11.4, 41.2), 'In January twenty seven BC +3', 'In that moment the Roman', (15.5, 43.5), 56, -14),
    R('Roman Empire', 'roman', SPECK(11.4, 41.2), 'In that moment the Roman +1', END, (17.0, 44.0), 72, -6),
    # the split of the Roman world (40-31 BC): Antony's east covers the Roman tint, Octavian's west keeps it
    R('Antony', 'antony', P_(*RG.MACEDON, *RG.GREEK_LEAGUES, *RG.ASIA_133, *RG.BITHYNIA_PONTUS, *RG.CILICIA, *RG.SYRIA, *RG.CYRENAICA, *RG.CRETE),
      'The victors divided the Roman world', 'Within a year', (28.0, 38.6), 34, -8),
    R('Octavian', 'roman', SPECK(11.4, 41.2), 'The victors divided the Roman world +0.5', 'In January twenty seven BC', (9.0, 43.0), 40, -10),
]

# ------------------------------------------------------------------ armies (every march carries its commander)
A = lambda at, to, fade, path, kind, leader, cav=False, **k: dict(at=at, to=to, fade=fade, path=path, kind=kind, leader=leader, cavalry=cav, **k)
ARROWS = [
    A('they drove the king out', 'they drove the king out> +2.5', 'Power passed to two', ['Rome', (12.15, 42.45), 'Clusium'], 'roman', 'Tarquin the Proud', style='raid'),
    A('besieged it for ten years', 'took it in three', 'Rome doubled its land', ['Rome', (12.42, 41.98), 'Veii'], 'roman', 'Camillus'),
    A('Gallic warriors crossed', 'sacked Rome itself>', 'Rome never forgot it', [(10.6, 45.1), (11.3, 44.2), 'Clusium', (12.3, 42.6), 'Allia', 'Rome'], 'gaul', 'Brennus', True),
    A('the censor Appius Claudius', 'to carry the legions south>', 'In three long wars', ['Rome', (13.0, 41.55), 'Capua'], 'roman', None, dashed=True, width=(6, 12)),
    A('won victory at Sentinum -2', 'won victory at Sentinum>', 'Its secret weapon was not +2', ['Rome', (12.8, 42.6), 'Sentinum'], 'roman', 'Fabius Rullianus'),
    A('with elephants and a professional', 'Pyrrhus beat the Romans', 'Plutarch has him say', ['Ambracia', (19.0, 39.9), 'Tarentum', 'Heraclea'], 'epirus', 'Pyrrhus', True),
    A('again at Asculum', 'but at a dreadful cost', 'Plutarch has him say +2', ['Heraclea', (16.2, 40.8), 'Asculum'], 'epirus', 'Pyrrhus', True),
    A('he sailed home', 'he sailed home> +2.5', 'By two hundred and sixty four BC, Rome +2', ['Beneventum', 'Tarentum', (19.0, 39.8), 'Ambracia'], 'epirus', 'Pyrrhus', True),
    A('both powers were drawn', 'It became a war that', 'Rome had almost no warships', ['Rome', 'Capua', (16.0, 39.6), (16.05, 39.0)], 'roman', 'Appius Claudius Caudex'),
    A('both powers were drawn +0.8', 'It became a war that', 'Rome had almost no warships', ['Carthage', (11.5, 37.6), 'Lilybaeum', 'Panormus', (14.0, 38.05), (14.5, 37.98)], 'carthage', 'Hanno'),
    A('met the Carthaginian fleet', 'The ravens dropped', 'An inscription from his victory +2', ['Messana', (15.5, 38.4), 'Mylae'], 'roman', 'Gaius Duilius'),
    A('met the Carthaginian fleet', 'The ravens dropped', 'An inscription from his victory +2', ['Panormus', (14.2, 38.4), (15.0, 38.45)], 'carthage', 'Hannibal Gisco'),
    A('a Roman army even landed', 'only to be destroyed', 'The war ground on +2', ['Agrigentum', (12.5, 37.0), 'Clupea', 'Tunis'], 'roman', 'Regulus'),
    A('a new fleet destroyed', 'off the Aegates Islands>', 'Carthage gave up Sicily', ['Lilybaeum', (12.0, 37.9), 'Aegates'], 'roman', 'Lutatius Catulus'),
    A('He marched from New Carthage', 'with war elephants>', 'What followed was a nightmare', ['New Carthage', 'Saguntum', (0.6, 41.0), (2.7, 42.4), (3.4, 43.4),
      (4.6, 43.8), (5.2, 44.6), (6.2, 45.0), (6.95, 44.75), (7.6, 45.0)], 'carthage', 'Hannibal'),
    A('In December, at the river', 'ambushed a consular army', 'In June of the following year +1', [(7.6, 45.0), (8.6, 45.1), 'Trebia'], 'carthage', 'Hannibal'),
    A('In June of the following year', 'he hid his army', 'Then, on the second +1', ['Trebia', (10.3, 44.3), (11.2, 43.6), 'Trasimene'], 'carthage', 'Hannibal'),
    A('Then, on the second of August', 'at Cannae in Apulia>', 'Hannibal let his centre', ['Trasimene', (13.2, 42.6), (14.8, 41.8), 'Cannae'], 'carthage', 'Hannibal'),
    A("Livy says Hannibal's brother", 'onto the floor of the Carthaginian>', 'Yet Hannibal did not march +1', ['Cannae', (16.0, 39.5), (13.0, 37.6), 'Carthage'], 'carthage', 'Mago'),
    A("Hannibal's brother Hasdrubal crossed", 'with a second army>', 'Livy says his head +2', [(2.7, 42.4), (4.6, 43.8), (6.9, 44.9), (8.5, 45.0), (10.8, 44.6), (12.3, 44.2), 'Metaurus'], 'carthage', 'Hasdrubal'),
    A('captured New Carthage -1', 'captured New Carthage>', 'drove the Carthaginians from Spain +2', ['Tarraco', 'Saguntum', 'New Carthage'], 'roman', 'Scipio'),
    A('in two hundred and four BC landed', 'landed in Africa>', 'Hannibal was recalled +1', ['Lilybaeum', (11.2, 37.4), 'Utica'], 'roman', 'Scipio'),
    A('Hannibal was recalled', 'to defend his city>', 'At Zama +1', ['Croton', (14.5, 37.0), 'Hadrumetum'], 'carthage', 'Hannibal'),
    A('At Zama, in two hundred', 'charged down lanes', 'Carthage surrendered its fleet', ['Utica', (9.8, 36.7), 'Zama'], 'roman', 'Scipio'),
    A('the legions broke the Macedonian', 'phalanx of King Philip>', 'In one hundred and ninety, at Magnesia', ['Apollonia', (21.0, 40.0), 'Cynoscephalae'], 'roman', 'Flamininus'),
    A('they routed the Seleucid king', 'Antiochus the Great>', 'And at Pydna', ['Hellespont', (27.0, 39.4), 'Magnesia'], 'roman', 'Lucius Scipio'),
    A('the consul Aemilius Paullus', 'the army of the last', 'Polybius, the Greek hostage +2', ['Apollonia', (21.5, 40.4), 'Pydna'], 'roman', 'Aemilius Paullus'),
    A('Rome found a pretext', 'After a three year siege', 'stormed Carthage', ['Lilybaeum', (11.0, 37.3), 'Utica', 'Carthage'], 'roman', 'Scipio Aemilianus'),
    A('Roman troops sacked Corinth', 'sacked Corinth> +1.5', 'Africa and Macedonia became', ['Pella', (22.6, 39.2), 'Corinth'], 'roman', 'Mummius'),
    A('he destroyed the migrating Cimbri', 'and Teutones>', 'who had wiped out Roman', [(10.0, 51.0), (7.5, 49.0), (4.5, 46.0), 'Aquae Sextiae'], 'germanic', 'Teutobod', style='raid'),
    A('he destroyed the migrating Cimbri +0.6', 'who had wiped out', "Then Rome's Italian allies", ['Rome', (10.0, 44.0), (7.5, 43.8), 'Aquae Sextiae'], 'roman', 'Gaius Marius'),
    A('who had wiped out Roman', 'armies in Gaul>', "Then Rome's Italian allies +1", [(11.5, 47.5), (10.8, 46.5), 'Vercellae'], 'germanic', 'Boiorix', style='raid'),
    A('he marched his legions on Rome', 'on Rome itself>', 'After a war in the east', ['Capua', (13.5, 41.4), 'Rome'], 'roman', 'Sulla'),
    A('a war in the east against Mithridates +1', 'he returned', 'posted lists of his enemies', ['Brundisium', 'Dyrrhachium', 'Athens', 'Chaeronea'], 'roman', 'Sulla'),
    A('a gladiator named Spartacus', 'across Italy>', 'Appian says six thousand', ['Capua', (14.4, 40.9), (14.6, 42.2), (11.0, 44.5), (16.0, 39.5), (15.7, 38.2)], 'iberian', 'Spartacus', style='raid'),
    A('he swept the pirates', 'in a single summer>', 'Then he conquered the east +1', ['Ostia', (12.5, 38.5), (20.0, 36.0), (26.0, 35.3), 'Coracesium'], 'roman', 'Pompey'),
    A('Then he conquered the east', 'ended the Seleucid kingdom>', 'took Jerusalem +2', ['Ephesus', (33.0, 39.5), (38.0, 40.0), 'Antioch', 'Damascus', 'Jerusalem'], 'roman', 'Pompey'),
    A('Caesar conquered everything', 'and the Atlantic>', 'crossed twice into Britain +2', ['Geneva', 'Bibracte', 'Vesontio', (4.5, 48.8), 'Belgae'], 'roman', 'Julius Caesar'),
    A('crossed twice into Britain', 'wrote his own account', 'Plutarch claims that +1', ['Gesoriacum', (1.4, 51.0), 'Rutupiae', (0.0, 51.45)], 'roman', 'Julius Caesar'),
    A('all Gaul rose under', 'Vercingetorix>', 'Caesar trapped him', ['Gergovia', (3.9, 46.6), 'Alesia'], 'gaul', 'Vercingetorix', True),
    A('Caesar trapped him -1.5', 'Caesar trapped him', 'Vercingetorix laid down +2', [(5.0, 46.0), (4.8, 47.0), 'Alesia'], 'roman', 'Julius Caesar'),
    A('invaded Parthia', 'died at Carrhae>', 'With Crassus gone', ['Antioch', 'Zeugma', 'Carrhae'], 'roman', 'Crassus'),
    A('crossed the little river Rubicon', 'into Italy in January>', 'Suetonius gives his words +2', ['Ravenna', 'Rubicon', 'Ariminum', (13.0, 43.2)], 'roman', 'Julius Caesar'),
    A('At Pharsalus in Greece -1.5', 'At Pharsalus in Greece +0.5', 'Caesar defeated Pompey', ['Brundisium', 'Dyrrhachium', (21.0, 40.0), 'Pharsalus'], 'roman', 'Julius Caesar'),
    A('who fled to Egypt', 'stepped ashore>', 'Caesar made himself dictator', ['Pharsalus', (23.5, 38.6), (27.0, 36.0), (31.0, 32.0), 'Pelusium'], 'pompeian', 'Pompey'),
    A("Octavian joined Caesar's", 'at Philippi in Macedonia>', 'they crushed the assassins +1', ['Brundisium', 'Dyrrhachium', 'Thessalonica', 'Philippi'], 'roman', 'Mark Antony'),
    A('and in forty two BC', 'at Philippi in Macedonia>', 'they crushed the assassins +1', ['Sardis', (27.0, 40.0), (26.0, 40.9), 'Philippi'], 'pompeian', 'Brutus'),
    A("Octavian's admiral Agrippa", 'trapped the fleet', 'The queen broke out -0.7', [(21.25, 37.3), (20.45, 37.7), (20.05, 38.1), (20.15, 38.45)], 'roman', 'Agrippa'),
    A('The queen broke out', 'her squadron and fled>', 'Within a year', ['Actium', (21.5, 37.0), (25.0, 34.6), (29.0, 31.8), 'Alexandria'], 'ptolemaic', 'Cleopatra VII'),
    A('and Antony followed her', 'and Antony followed her> +2', 'Within a year +1', ['Actium', (21.8, 36.8), (25.5, 34.3), (29.3, 31.7), 'Alexandria'], 'antony', 'Mark Antony'),
    A('Octavian entered Alexandria -1', 'Octavian entered Alexandria>', 'Egypt, the richest land', [(34.0, 32.5), 'Pelusium', 'Alexandria'], 'roman', 'Octavian'),
    A('the general Varus', 'lost three entire legions', 'Suetonius says the old emperor', ['Vetera', (8.0, 52.0), (8.6, 52.5), 'Teutoburg'], 'roman', 'Varus'),
    A('lost three entire legions', 'to the Germanic chief Arminius>', 'Suetonius says the old emperor +1', [(9.4, 52.0), (8.7, 52.2), 'Teutoburg'], 'germanic', 'Arminius'),
    A('Claudius invaded Britain', 'AD forty three>', 'Under the Flavian emperors', ['Gesoriacum', 'Rutupiae', (0.3, 51.5), 'Camulodunum'], 'roman', 'Claudius'),
    A('In two hard wars he crossed', 'conquered Dacia>', 'The war is carved +1', ['Viminacium', 'Drobeta', 'Tapae', 'Sarmizegetusa'], 'roman', 'Trajan'),
    A('He annexed Armenia', 'took Mesopotamia>', 'captured the Parthian capital +1', ['Antioch', 'Zeugma', 'Edessa', 'Nisibis', 'Artaxata'], 'roman', 'Trajan'),
    A('captured the Parthian capital -1', 'captured the Parthian capital>', 'sailed down the Tigris', ['Nisibis', (43.0, 35.5), 'Ctesiphon'], 'roman', 'Trajan'),
    A('sailed down the Tigris', 'to the Persian Gulf>', 'In that moment the Roman', ['Ctesiphon', (46.5, 31.6), 'Charax', (49.0, 29.4)], 'roman', 'Trajan'),
]

# ------------------------------------------------------------------ battles
BATTLES = [  # (from, to, title, year, left kind, right kind)
    ('besieged it for ten years', 'by a tunnel dug', 'Siege of Veii', '406-396 BC', 'roman', 'etruscan'),
    ('destroyed a Roman army at', 'and sacked Rome itself', 'Battle of the Allia', '390 BC', 'gaul', 'roman'),
    ('humiliation at the Caudine Forks', 'where a whole army', 'Caudine Forks', '321 BC', 'samnite', 'roman'),
    ('won victory at Sentinum', 'Its secret weapon was not', 'Battle of Sentinum', '295 BC', 'roman', 'samnite'),
    ('Pyrrhus beat the Romans at Heraclea', 'and again at Asculum', 'Battle of Heraclea', '280 BC', 'epirus', 'roman'),
    ('Beaten at Beneventum', 'he sailed home', 'Battle of Beneventum', '275 BC', 'roman', 'epirus'),
    ('off Mylae on the north coast', 'The ravens dropped +1.5', 'Battle of Mylae', '260 BC', 'roman', 'carthage'),
    ('only to be destroyed outside', 'The war ground on', 'Battle of the Bagradas', '255 BC', 'carthage', 'roman'),
    ('off the Aegates Islands', 'Carthage gave up Sicily', 'Battle of the Aegates', '241 BC', 'roman', 'carthage'),
    ('In December, at the river', 'ambushed a consular army', 'Battle of the Trebia', '218 BC', 'carthage', 'roman'),
    ('at Lake Trasimene', 'he hid his army', 'Lake Trasimene', '217 BC', 'carthage', 'roman'),
    ('at Cannae in Apulia', 'Hannibal let his centre', 'Battle of Cannae', '2 August 216 BC', 'carthage', 'roman'),
    ('destroyed at the river Metaurus', 'Livy says his head', 'Battle of the Metaurus', '207 BC', 'roman', 'carthage'),
    ('At Zama, in two hundred', "Hannibal's elephants charged", 'Battle of Zama', '202 BC', 'roman', 'carthage'),
    ('at Cynoscephalae', 'In one hundred and ninety, at Magnesia', 'Battle of Cynoscephalae', '197 BC', 'roman', 'macedon'),
    ('at Magnesia in Asia Minor', 'And at Pydna', 'Battle of Magnesia', '190 BC', 'roman', 'seleucid'),
    ('And at Pydna', 'Polybius, the Greek hostage', 'Battle of Pydna', '168 BC', 'roman', 'macedon'),
    ('Roman troops sacked Corinth', 'Africa and Macedonia became', 'Sack of Corinth', '146 BC', 'roman', 'greek'),
    ('he destroyed the migrating Cimbri', 'who had wiped out', 'Aquae Sextiae', '102 BC', 'roman', 'germanic'),
    ('who had wiped out Roman', "Then Rome's Italian allies", 'Battle of Vercellae', '101 BC', 'roman', 'germanic'),
    ('rose in the Social War', 'Rome won, and gave', 'The Social War', '91-88 BC', 'roman', 'samnite'),
    ('he returned, made himself', 'posted lists', 'Battle of Chaeronea', '86 BC', 'roman', 'pontus'),
    ('took Jerusalem -1', 'In sixty BC', 'Siege of Jerusalem', '63 BC', 'roman', 'judea'),
    ('all Gaul rose under', 'Caesar trapped him', 'Siege of Alesia', '52 BC', 'roman', 'gaul'),
    ('died at Carrhae', 'With Crassus gone', 'Battle of Carrhae', '53 BC', 'parthia', 'roman'),
    ('At Pharsalus in Greece', 'Caesar defeated Pompey', 'Battle of Pharsalus', '9 August 48 BC', 'roman', 'pompeian'),
    ('at Philippi in Macedonia', 'they crushed the assassins', 'Battle of Philippi', '42 BC', 'roman', 'pompeian'),
    ('off the headland of Actium', 'The queen broke out', 'Battle of Actium', '2 September 31 BC', 'roman', 'antony'),
    ('in the Teutoburg Forest', 'lost three entire legions', 'Teutoburg Forest', 'AD 9', 'germanic', 'roman'),
    ('In two hard wars he crossed', 'conquered Dacia', 'Conquest of Dacia', 'AD 101-106', 'roman', 'dacian'),
    ('captured the Parthian capital', 'and sailed down', 'Fall of Ctesiphon', 'AD 116', 'roman', 'parthia'),
]
MARKS = [('destroyed a Roman army at', 'Allia', '390 BC'), ('humiliation at the Caudine Forks', 'Caudine Forks', '321 BC'), ('won victory at Sentinum', 'Sentinum', '295 BC'),
         ('Pyrrhus beat the Romans at Heraclea', 'Heraclea', '280 BC'), ('and again at Asculum', 'Asculum', '279 BC'), ('Beaten at Beneventum', 'Beneventum', '275 BC'),
         ('The ravens dropped', 'Mylae', '260 BC'), ('only to be destroyed outside', 'Tunis', '255 BC'), ('off the Aegates Islands', 'Aegates', '241 BC'),
         ('ambushed a consular army', 'Trebia', '218 BC'), ('he hid his army', 'Trasimene', '217 BC'), ('The Romans were surrounded', 'Cannae', '216 BC'),
         ('destroyed at the river Metaurus', 'Metaurus', '207 BC'), ("Hannibal had lost his first", 'Zama', '202 BC'), ('at Cynoscephalae', 'Cynoscephalae', '197 BC'),
         ('at Magnesia in Asia Minor', 'Magnesia', '190 BC'), ('And at Pydna', 'Pydna', '168 BC'), ('Roman troops sacked Corinth', 'Corinth', '146 BC'),
         ('he destroyed the migrating Cimbri', 'Aquae Sextiae', '102 BC'), ('who had wiped out Roman', 'Vercellae', '101 BC'), ('he returned, made himself', 'Chaeronea', '86 BC'),
         ('Vercingetorix laid down his arms', 'Alesia', '52 BC'), ('died at Carrhae', 'Carrhae', '53 BC'), ('Caesar defeated Pompey', 'Pharsalus', '48 BC'),
         ('they crushed the assassins', 'Philippi', '42 BC'), ('trapped the fleet of Antony', 'Actium', '31 BC'), ('lost three entire legions', 'Teutoburg', 'AD 9'),
         ('The war is carved in a spiral', 'Sarmizegetusa', 'AD 106'), ('sailed down the Tigris', 'Ctesiphon', 'AD 116')]
RIPPLES = [('they drove the king out', 'Power passed', 'Rome'), ('humiliation at the Caudine Forks', 'Its secret weapon', 'Caudine Forks'),
           ('quarrel over Messana', 'It became a war', 'Messana'), ('The ravens dropped', 'An inscription', 'Mylae'), ('only to be destroyed outside', 'The war ground on', 'Tunis'),
           ('beat him to death', 'Plutarch says more', 'Rome'), ('on Rome itself', 'After a war in the east', 'Rome'), ('murdered as he stepped ashore', 'Caesar made himself', 'Pelusium'),
           ('stabbed him to death', 'Suetonius counts', 'Rome'), ('his head and hands were nailed', 'The victors divided', 'Rome'), ('buried Pompeii', 'Then, in AD ninety eight', 'Pompeii'),
           ('Trajan died on his way home', 'His successor, Hadrian', 'Selinus'), ('they make a desert', 'The village on the Tiber', 'Mons Graupius'), ('the sacred geese of Juno', 'When the Romans paid', 'Rome')]
RINGS = [('On a hill above', 'Rome'), ('founded a city on the Palatine', 'Rome'), ('In the Forum, beneath', 'Rome'), ('Its greatest rival was Veii', 'Veii'),
         ('beyond it Carthage', 'Carthage'), ('Hamilcar, it was said', 'Carthage'), ('to defend his city', 'Carthage'), ('stormed Carthage', 'Carthage'),
         ('Yet Hannibal did not march', 'Rome'), ('at Cannae in Apulia', 'Cannae'), ('At Zama, in two', 'Zama'), ('crossed the little river Rubicon', 'Rubicon'),
         ('the doors of the temple of Janus', 'Rome'), ('Under the Flavian emperors', 'Rome'), ('the Parthian capital Ctesiphon', 'Ctesiphon'), ('Vesuvius buried Pompeii', 'Pompeii'),
         ('Then catastrophe came', 'Rome'), ('Rome had almost no warships', 'Ostia'), ('Trajan died on his way', 'Selinus')]
HATCH = [('rose in the Social War', 'Rome won, and gave', [[(13.0, 42.9), (14.2, 42.6), (15.4, 41.6), (15.2, 40.9), (14.4, 41.0), (13.6, 41.6), (13.1, 42.2)]], (200, 30, 30)),
         ('all Gaul rose under', 'Caesar trapped him', polys(RG.gaul()), (200, 30, 30)),
         ('But revolts were already burning', 'In August AD one', RG.MESOPOTAMIA, (200, 30, 30))]

# ------------------------------------------------------------------ people (real period images; crests where no likeness survives)
I = lambda f: 'rome/' + f
PEOPLE = [
    dict(at='historian Polybius', until='Who is so worthless -0.7', name='Polybius', title='Greek historian, c. 200-118 BC', kind='greek', image=I('polybius.jpg'), crop=(0.32, 0.0, 0.82, 0.25)),
    dict(at='Twin boys', until='suckled by a she wolf -0.2', name='Romulus and Remus', title='Legendary founders (Capitoline Wolf)', kind='roman', place='Palatine', image=I('wolf.jpg'), crop=(0.40, 0.45, 0.72, 0.95)),
    dict(at='Livy, writing under Augustus', until='The traditional date -0.2', name='Livy', title='Roman historian, 59 BC - AD 17', kind='roman'),
    dict(at='by the scholar Varro', until='Archaeology tells +1.5', name='Varro', title='Roman scholar, 116-27 BC', kind='roman'),
    dict(at='Tarquin the Proud', until='According to Livy, when', name='Tarquin the Proud', title='Last king of Rome (tradition)', kind='etruscan', place='Rome'),
    dict(at='the noblewoman Lucretia', until='they drove the king out -0.3', name='Lucretia', title='Roman noblewoman (Livy)', kind='roman', place='Rome'),
    dict(at='besieged it for ten years +0.3', until='by a tunnel dug -0.2', name='Camillus', title='Roman general', kind='roman', place='Veii'),
    dict(at='the Gallic chief Brennus', until='vae victis -0.2', name='Brennus', title='Gallic chieftain', kind='gaul', place='Rome'),
    dict(at='the censor Appius Claudius', until='In three long wars -0.3', name='Appius Claudius', title='Censor, builder of the Appian Way', kind='roman', place='Rome'),
    dict(at='Pyrrhus, King of Epirus', until='Pyrrhus beat the Romans -0.3', name='Pyrrhus', title='King of Epirus', kind='epirus', place='Tarentum', image=I('pyrrhus.jpg'), crop=(0.12, 0.05, 0.90, 0.62)),
    dict(at='Plutarch has him say', until='Beaten at Beneventum -0.2', name='Plutarch', title='Greek biographer, c. AD 46-120', kind='greek'),
    dict(at='Polybius says the Romans used', until='They added a weapon -0.2', name='Polybius', title='Greek historian, c. 200-118 BC', kind='greek', image=I('polybius.jpg'), crop=(0.32, 0.0, 0.82, 0.25)),
    dict(at='the consul Gaius Duilius', until='The ravens dropped +1', name='Gaius Duilius', title='Consul, victor of Mylae', kind='roman', place='Mylae'),
    dict(at='The general Hamilcar', until='That son was Hannibal -0.2', name='Hamilcar Barca', title='Carthaginian general', kind='carthage', place='New Carthage'),
    dict(at='That son was Hannibal', until='after he took the Roman ally -0.3', name='Hannibal', title='Carthaginian general, 247-183 BC', kind='carthage', place='New Carthage', image=I('hannibal.jpg'), crop=(0.28, 0.06, 0.78, 0.42)),
    dict(at='Polybius says the army left', until='Exactly which pass -0.2', name='Polybius', title='Greek historian, c. 200-118 BC', kind='greek', image=I('polybius.jpg'), crop=(0.32, 0.0, 0.82, 0.25)),
    dict(at='Polybius puts the dead', until='Livy, at about -0.1', name='Polybius', title='Greek historian, c. 200-118 BC', kind='greek', image=I('polybius.jpg'), crop=(0.32, 0.0, 0.82, 0.25)),
    dict(at='Livy, at about', until='Either way, it was -0.1', name='Livy', title='Roman historian, 59 BC - AD 17', kind='roman'),
    dict(at='His cavalry commander Maharbal', until='Yet Rome would not make peace -0.2', name='Maharbal', title='Carthaginian cavalry commander', kind='carthage', place='Cannae'),
    dict(at='led by Quintus Fabius', until="Hannibal's brother Hasdrubal -2.0", name='Fabius Maximus', title='"Cunctator", the Delayer', kind='roman', place='Rome'),
    dict(at="Hannibal's brother Hasdrubal", until='Livy says his head -0.3', name='Hasdrubal', title="Hannibal's brother", kind='carthage'),
    dict(at='Publius Cornelius Scipio', until='Hannibal was recalled -0.3', name='Scipio', title='Scipio Africanus, 236-183 BC', kind='roman', image=I('scipio.jpg'), crop=(0.22, 0.20, 0.78, 0.47)),
    dict(at='a new name: Africanus', until='Chapter five -0.3', name='Scipio Africanus', title='Victor of Zama', kind='roman', image=I('scipio.jpg'), crop=(0.22, 0.20, 0.78, 0.47)),
    dict(at='King Philip the Fifth', until='In one hundred and ninety, at Magnesia -0.2', name='Philip V', title='King of Macedon, 221-179 BC', kind='macedon', place='Pella', image=I('philip5.jpg'), crop=(0.20, 0.08, 0.86, 0.92)),
    dict(at='the Seleucid king', until='And at Pydna -0.2', name='Antiochus III', title='Seleucid king, "the Great"', kind='seleucid', place='Magnesia', image=I('antiochus.jpg'), crop=(0.14, 0.06, 0.82, 0.52)),
    dict(at='the consul Aemilius Paullus', until='Perseus -0.2', name='Aemilius Paullus', title='Consul, victor of Pydna', kind='roman', place='Pydna'),
    dict(at='Perseus', until='and explained it to his -0.2', name='Perseus', title='Last king of Macedon', kind='macedon', place='Pella', image=I('perseus.jpg'), crop=(0.0, 0.0, 0.48, 1.0)),
    dict(at='The elder Cato', until='In one hundred and forty nine -0.2', name='Cato the Elder', title='Censor (portrait identification uncertain)', kind='roman', place='Rome', image=I('cato.jpg'), crop=(0.12, 0.04, 0.88, 0.80)),
    dict(at='After a three year siege', until='stormed Carthage -0.1', name='Scipio Aemilianus', title='Destroyer of Carthage', kind='roman', place='Carthage'),
    dict(at='Polybius stood beside Scipio', until='The famous story -0.2', name='Polybius', title='Eyewitness at Carthage', kind='greek', image=I('polybius.jpg'), crop=(0.32, 0.0, 0.82, 0.25)),
    dict(at='the tribune Tiberius Gracchus', until='Senators and their followers -0.2', name='Tiberius Gracchus', title='Tribune of the plebs, 133 BC', kind='roman', place='Rome'),
    dict(at='Plutarch says more than', until='It was the first time -0.2', name='Plutarch', title='Greek biographer, c. AD 46-120', kind='greek'),
    dict(at='Twelve years later his brother', until='and some three thousand -0.2', name='Gaius Gracchus', title='Tribune, 123-122 BC', kind='roman', place='Rome'),
    dict(at='Gaius Marius, a new man', until='he destroyed the migrating -0.2', name='Gaius Marius', title='Consul seven times (identification uncertain)', kind='roman', image=I('marius.jpg'), crop=(0.18, 0.06, 0.80, 0.56)),
    dict(at='Lucius Cornelius Sulla', until='he marched his legions -0.2', name='Sulla', title='Dictator, 82-79 BC', kind='roman', place='Rome', image=I('sulla.jpg'), crop=(0.12, 0.04, 0.88, 0.55)),
    dict(at='against Mithridates of Pontus', until='he returned -0.2', name='Mithridates VI', title='King of Pontus', kind='pontus', place='Sinope', image=I('mithridates.jpg'), crop=(0.20, 0.10, 0.84, 0.66)),
    dict(at='a gladiator named Spartacus', until='Appian says six -0.2', name='Spartacus', title='Leader of the slave revolt', kind='iberian', place='Capua'),
    dict(at='Appian says six', until='The Republic survived Sulla -0.2', name='Appian', title='Greek historian, 2nd c. AD', kind='greek'),
    dict(at='Gnaeus Pompeius, Pompey', until='Then he conquered the east -0.2', name='Pompey', title='Pompey the Great, 106-48 BC', kind='roman', image=I('pompey.jpg'), crop=(0.16, 0.06, 0.84, 0.62)),
    dict(at='the richest man in Rome, Crassus', until='an ambitious aristocrat -0.2', name='Crassus', title='Richest man in Rome', kind='roman', place='Rome', image=I('crassus.jpg'), crop=(0.25, 0.0, 0.75, 0.75)),
    dict(at='Gaius Julius Caesar', until='As governor of Gaul -2.0', name='Julius Caesar', title='100-44 BC', kind='roman', place='Rome', image=I('caesar.jpg'), crop=(0.18, 0.06, 0.82, 0.42)),
    dict(at='Plutarch claims that', until='Ancient numbers like these -0.2', name='Plutarch', title='Greek biographer, c. AD 46-120', kind='greek'),
    dict(at='the Arvernian chief Vercingetorix', until='Caesar trapped him -0.3', name='Vercingetorix', title='Arvernian chief (gold stater)', kind='gaul', place='Alesia', image=I('vercingetorix.jpg'), crop=(0.02, 0.02, 0.98, 0.98)),
    dict(at='Crassus, hungry for glory', until='where Plutarch says -0.2', name='Crassus', title='Triumvir, died 53 BC', kind='roman', place='Carrhae', image=I('crassus.jpg'), crop=(0.25, 0.0, 0.75, 0.75)),
    dict(at='Suetonius gives his words', until='At Pharsalus -0.3', name='Suetonius', title='Roman biographer, c. AD 69-122', kind='roman'),
    dict(at='Caesar made himself dictator', until='On the Ides of March -0.2', name='Julius Caesar', title='Dictator for life', kind='roman', place='Rome', image=I('caesar.jpg'), crop=(0.18, 0.06, 0.82, 0.42)),
    dict(at='On the Ides of March', until='stabbed him to death -0.3', name='Brutus', title='Assassin (denarius, 42 BC)', kind='pompeian', place='Rome', image=I('brutus.jpg'), crop=(0.03, 0.06, 0.49, 0.94)),
    dict(at='Gaius Octavius', until='Octavian joined -0.2', name='Octavian', title='Caesar\'s heir, later Augustus', kind='roman', place='Rome', image=I('augustus.jpg'), crop=(0.49, 0.03, 0.71, 0.18)),
    dict(at="Caesar's lieutenant Mark Antony", until='and in forty two BC -0.2', name='Mark Antony', title='Caesar\'s lieutenant', kind='roman', image=I('antony.jpg'), crop=(0.22, 0.06, 0.76, 0.56)),
    dict(at='Brutus and Cassius both', until='Before that, the new -0.2', name='Cassius', title='Assassin of Caesar', kind='pompeian', place='Philippi'),
    dict(at='Appian says some three', until='the orator Cicero -0.2', name='Appian', title='Greek historian, 2nd c. AD', kind='greek'),
    dict(at='the orator Cicero', until='The victors divided -0.3', name='Cicero', title='Orator and consul, 106-43 BC', kind='roman', place='Rome', image=I('cicero.jpg'), crop=(0.08, 0.16, 0.92, 0.72)),
    dict(at='the Queen of Egypt, Cleopatra', until='Octavian took Italy -0.2', name='Cleopatra VII', title='Queen of Egypt, last of the Ptolemies', kind='ptolemaic', place='Alexandria', image=I('cleopatra.jpg'), crop=(0.12, 0.10, 0.88, 0.68)),
    dict(at="Octavian's admiral Agrippa", until='The queen broke out -0.3', name='Agrippa', title='Admiral at Actium', kind='roman', image=I('agrippa.jpg'), crop=(0.15, 0.05, 0.85, 0.70)),
    dict(at='a new name: Augustus', until='In his own record -0.2', name='Augustus', title='First emperor, 27 BC - AD 14', kind='roman', place='Rome', image=I('augustus.jpg'), crop=(0.49, 0.03, 0.71, 0.18)),
    dict(at='After that time, he wrote', until='In truth, the Republic -0.2', name='Augustus', title='Res Gestae 34', kind='roman', place='Rome', image=I('augustus.jpg'), crop=(0.49, 0.03, 0.71, 0.18)),
    dict(at='Augustus ruled for forty', until='Suetonius says he found -0.2', name='Augustus', title='First emperor, 27 BC - AD 14', kind='roman', place='Rome', image=I('augustus.jpg'), crop=(0.49, 0.03, 0.71, 0.18)),
    dict(at='Suetonius says he found', until='The doors of the temple -0.2', name='Suetonius', title='Roman biographer, c. AD 69-122', kind='roman'),
    dict(at='the general Varus', until='to the Germanic chief -0.2', name='Varus', title='Governor of Germania', kind='roman', place='Teutoburg'),
    dict(at='Claudius invaded Britain', until='Under the Flavian -0.3', name='Claudius', title='Emperor, AD 41-54', kind='roman', image=I('claudius.jpg'), crop=(0.20, 0.08, 0.80, 0.52)),
    dict(at='the first emperor born outside Italy', until='In two hard wars -0.2', name='Trajan', title='Emperor, AD 98-117', kind='roman', image=I('trajan.jpg'), crop=(0.18, 0.06, 0.82, 0.62)),
    dict(at='the gold rich kingdom', until='in what is now Romania -0.1', name='Decebalus', title='King of Dacia', kind='dacian', place='Sarmizegetusa'),
    dict(at='says Cassius Dio', until='In that moment the Roman -0.3', name='Cassius Dio', title='Roman historian, c. AD 155-235', kind='roman'),
    dict(at='His successor, Hadrian', until='The historian Tacitus -0.3', name='Hadrian', title='Emperor, AD 117-138', kind='roman', image=I('hadrian.jpg'), crop=(0.18, 0.04, 0.78, 0.52)),
    dict(at='The historian Tacitus', until='The village on the Tiber -0.3', name='Tacitus', title='Roman historian, c. AD 56-120', kind='roman'),
    # army leaders only (no pop-up medallion; their token rides at the head of the march)
    dict(name='Fabius Rullianus', title='Consul at Sentinum', kind='roman', show=False),
    dict(name='Appius Claudius Caudex', title='Consul, 264 BC', kind='roman', show=False),
    dict(name='Hanno', title='Carthaginian commander', kind='carthage', show=False),
    dict(name='Hannibal Gisco', title='Carthaginian admiral', kind='carthage', show=False),
    dict(name='Regulus', title='Consul, 256 BC', kind='roman', show=False),
    dict(name='Lutatius Catulus', title='Consul, 242 BC', kind='roman', show=False),
    dict(name='Flamininus', title='Consul, 198 BC', kind='roman', show=False),
    dict(name='Lucius Scipio', title='Consul, 190 BC', kind='roman', show=False),
    dict(name='Mummius', title='Consul, 146 BC', kind='roman', show=False),
    dict(name='Teutobod', title='King of the Teutones', kind='germanic', show=False),
    dict(name='Boiorix', title='King of the Cimbri', kind='germanic', show=False),
    dict(name='Mago', title="Hannibal's brother", kind='carthage', show=False),
    dict(name='Arminius', title='Germanic chief', kind='germanic', show=False),
]

PLATES = [
    dict(at='suckled by a she wolf', until='Grown to manhood +1.6', image=I('wolf.jpg'), caption='The Capitoline Wolf, Musei Capitolini, Rome (twins added in the Renaissance). CC0, via Wikimedia Commons'),
    dict(at='On the Palatine, excavators', until='Rome grew where a river -0.2', image=I('p_palatine.jpg'), caption='The Palatine Hill, Rome, where Iron Age hut foundations were found. CC BY 2.0 BIG ALBERT, via Wikimedia Commons'),
    dict(at='In the Forum, beneath', until='Tradition gives Rome seven kings +0.8', image=I('p_lapis.jpg'), caption='Lapis Niger cippus, Roman Forum, 6th century BC: one of the oldest Latin inscriptions. Public domain, via Wikimedia Commons'),
    dict(at='vae victis', until='Rome never forgot it +1.2', image=I('p_brennus.jpg'), caption='Paul Jamin, "Le Brenn et sa part de butin", 1893. Public domain, via Wikimedia Commons'),
    dict(at='Exactly which pass he crossed', until='What followed was a nightmare +1.5', image=I('p_turner_alps.jpg'), caption='J. M. W. Turner, "Snow Storm: Hannibal and his Army Crossing the Alps", 1812, Tate. Public domain, via Wikimedia Commons'),
    dict(at='Either way, it was one', until="Livy says Hannibal's brother +0.5", image=I('p_cannae.jpg'), caption='John Trumbull, "The Death of Paulus Aemilius at the Battle of Cannae", 1773, Yale University Art Gallery. Public domain'),
    dict(at='Carthage surrendered its fleet', until='Scipio came home -0.2', image=I('p_zama.jpg'), caption='Cornelis Cort after Giulio Romano, "The Battle between Scipio and Hannibal at Zama", 1567, Metropolitan Museum. CC0'),
    dict(at='Polybius had his answer', until='From Spain to Asia Minor -0.2', image=I('p_vernet.jpg'), caption='Carle Vernet, "The Triumph of Aemilius Paulus" (detail), 1789, Metropolitan Museum. Public domain'),
    dict(at='The famous story that the Romans', until='In the same year, Roman troops +0.6', image=I('p_carthage.jpg'), caption='Ruins of Carthage on the Byrsa hill, Tunisia. CC BY-SA 2.0 Tracey Hind, via Wikimedia Commons'),
    dict(at='and some three thousand', until='Then came the generals +0.4', image=I('p_gracchus.jpg'), caption='Francois Topino-Lebrun, "The Death of Gaius Gracchus", 1792. Public domain, via Wikimedia Commons'),
    dict(at='Vercingetorix laid down his arms', until='Crassus, hungry for glory -1.9', image=I('p_vercingetorix.jpg'), caption='Lionel Royer, "Vercingetorix throws down his arms at the feet of Julius Caesar", 1899. Public domain'),
    dict(at='stabbed him to death', until='Suetonius counts twenty three -0.1', image=I('p_death_caesar.jpg'), caption='Jean-Leon Gerome, "The Death of Caesar", 1867, Walters Art Museum. Public domain'),
    dict(at='The queen broke out', until='Within a year +0.3', image=I('p_actium.jpg'), caption='Lorenzo A. Castro, "The Battle of Actium, 2 September 31 BC", 1672, National Maritime Museum. Public domain'),
    dict(at='In his own record, the Res Gestae', until='After that time, he wrote -0.2', image=I('p_resgestae.jpg'), caption='Res Gestae Divi Augusti, Monumentum Ancyranum, Ankara (Perrot & Guillaume, 1862). CC0, via Wikimedia Commons'),
    dict(at='Quintilius Varus, give me', until='The Rhine became the frontier +1.4', image=I('p_varus.jpg'), caption='Otto Albert Koch, "Varusschlacht", 1909. Public domain, via Wikimedia Commons'),
    dict(at='the Colosseum rose', until='Then, in AD ninety eight -0.2', image=I('p_colosseum.jpg'), caption='The Colosseum (Flavian Amphitheatre), opened AD 80. CC BY-SA 4.0, via Wikimedia Commons'),
    dict(at="around Trajan's Column", until='In AD one hundred and fourteen -1.2', image=I('p_column.jpg'), caption="Trajan's Column, Rome, AD 113: a scene from the Dacian Wars. Public domain, via Wikimedia Commons"),
]
QUOTE = dict(**{'from': 'Who is so worthless', 'to': 'under their rule'}, title='Polybius, Histories 1.1', sub='written c. 150 BC', image=I('polybius.jpg'))

SIEGES = [   # tactical close-ups
    dict(at='by a tunnel dug', until='Then catastrophe came', city='Veii', attacker='roman', defender='etruscan', climate='temperate', title='Siege of Veii', sub='Camillus digs under the walls', year='396 BC', leaders=dict(attacker='Camillus')),
    dict(at='sacked Rome itself', until='Livy tells how the sacred geese', city='Rome', attacker='gaul', defender='roman', climate='temperate', river='Tiber', burn=True, title='Sack of Rome', sub='only the Capitol holds out', year='390 BC', leaders=dict(attacker='Brennus')),
    dict(at='Pyrrhus beat the Romans +1.2', until='Plutarch has him say', field=True, ancient=True, attacker='epirus', defender='roman', climate='steppe', title='Heraclea and Asculum', sub='elephants and phalanx', year='280-279 BC', leaders=dict(attacker='Pyrrhus')),
    dict(at='after he took the Roman ally Saguntum', until='and Hannibal did what -0.1', city='Saguntum', attacker='carthage', defender='iberian', climate='arid', burn=True, title='Siege of Saguntum', sub='the spark of the Second Punic War', year='219 BC', leaders=dict(attacker='Hannibal')),
    dict(at='ambushed a consular army', until='In June of the following year', field=True, ancient=True, attacker='carthage', defender='roman', climate='winter', river=True, title='Battle of the Trebia', sub='ambush in the snow', year='218 BC', leaders=dict(attacker='Hannibal')),
    dict(at='he hid his army', until='Then, on the second of August', field=True, ancient=True, attacker='carthage', defender='roman', climate='temperate', river='Lake Trasimene', title='Lake Trasimene', sub='ambush in the morning mist', year='217 BC', leaders=dict(attacker='Hannibal')),
    dict(at='Hannibal let his centre', until='Polybius puts the dead', field=True, ancient=True, attacker='carthage', defender='roman', climate='steppe', river='Aufidus', title='Battle of Cannae', sub='the double envelopment', year='216 BC', leaders=dict(attacker='Hannibal')),
    dict(at="Hannibal's elephants charged", until='Carthage surrendered its fleet', field=True, ancient=True, attacker='roman', defender='carthage', climate='arid', title='Battle of Zama', sub='lanes open for the elephants', year='202 BC', leaders=dict(attacker='Scipio', defender='Hannibal')),
    dict(at='and explained it to his', until='Then Rome finished its old enemy', field=True, ancient=True, attacker='roman', defender='macedon', climate='steppe', title='Legion against phalanx', sub='Pydna', year='168 BC', leaders=dict(attacker='Aemilius Paullus')),
    dict(at='stormed Carthage', until='Polybius stood beside Scipio', city='Carthage', attacker='roman', defender='carthage', climate='arid', burn=True, title='Siege of Carthage', sub='the city burns for days', year='146 BC', leaders=dict(attacker='Scipio Aemilianus')),
    dict(at='took Jerusalem', until='In sixty BC he joined -1.9', city='Jerusalem', attacker='roman', defender='judea', climate='arid', title='Siege of Jerusalem', sub='Pompey takes the Temple Mount', year='63 BC', leaders=dict(attacker='Pompey')),
    dict(at='Caesar trapped him in the hill fort', until='Excavations around Alesia +1.5', city='Alesia', attacker='roman', defender='gaul', climate='temperate', title='Siege of Alesia', sub='two rings of siege works', year='52 BC', leaders=dict(attacker='Julius Caesar', defender='Vercingetorix')),
    dict(at='Caesar defeated Pompey', until='who fled to Egypt', field=True, ancient=True, attacker='roman', defender='pompeian', climate='steppe', river='Enipeus', title='Battle of Pharsalus', sub='Caesar against Pompey', year='48 BC', leaders=dict(attacker='Julius Caesar', defender='Pompey')),
    dict(at='at Philippi in Macedonia +0.8', until='Brutus and Cassius both -0.1', field=True, ancient=True, attacker='roman', defender='pompeian', climate='temperate', title='Battle of Philippi', sub='the end of the assassins', year='42 BC', leaders=dict(attacker='Mark Antony', defender='Brutus')),
    dict(at='Antony fell on his sword', until='Egypt, the richest land', city='Alexandria', attacker='roman', defender='ptolemaic', climate='arid', title='Alexandria', sub='the last of the Ptolemies', year='30 BC', leaders=dict(attacker='Octavian', defender='Cleopatra VII')),
    dict(at='to the Germanic chief Arminius', until='Quintilius Varus, give me -0.2', field=True, ancient=True, attacker='germanic', defender='roman', climate='temperate', river=True, title='Teutoburg Forest', sub='three legions lost', year='AD 9', leaders=dict(attacker='Arminius', defender='Varus')),
    dict(at='in what is now Romania', until="around Trajan's Column -0.1", city='Sarmizegetusa', attacker='roman', defender='dacian', climate='temperate', burn=True, title='Sarmizegetusa', sub='the Dacian capital falls', year='AD 106', leaders=dict(attacker='Trajan', defender='Decebalus')),
    dict(at='captured the Parthian capital', until='and sailed down the Tigris', city='Ctesiphon', attacker='roman', defender='parthia', climate='arid', river='Tigris', title='Ctesiphon', sub='the Parthian capital taken', year='AD 116', leaders=dict(attacker='Trajan')),
]
END_CARD = dict(title='THE RISE OF ROME', sub='Next: how the empire held on, and how it fell', notes=['Borders, routes and numbers approximate.', 'Ancient casualty figures are uncertain.'])
SFX_EXTRA = [('sacked Rome itself +0.5', 'fire_big', -12, 5), ('The ravens dropped', 'px_battle_drums', -12, 3), ('Hannibal let his centre +2', 'px_gallop_near', -10, 3),
             ('stabbed him to death', 'lowhit', -10, 2.5), ('The queen broke out', 'whoosh6', -16, 2)]

import story; story.compile(globals())
