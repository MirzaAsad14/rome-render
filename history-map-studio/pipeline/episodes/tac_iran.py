"""Tactical close-ups for the Iran episode (arid Iranian plateau palette). Base canvas 3000x1800."""
SAND = dict(ground=(206, 188, 152), tree_tint=(0.66, 0.78, 0.50),
            water=((52, 74, 96), (96, 132, 160), (122, 162, 190), (140, 180, 206), (196, 220, 234)))
MUD = dict(ground=(150, 126, 96), street=(200, 180, 146), roof=(184, 158, 120), edge=(228, 210, 176), ridge=(132, 108, 82),
           wall=(198, 172, 130), wall_hi=(234, 216, 178))
STONE = dict(ground=(140, 128, 112), street=(206, 196, 176), roof=(168, 150, 128), edge=(236, 226, 206), ridge=(120, 104, 88),
             wall=(212, 200, 178), wall_hi=(244, 236, 218))

# Persepolis: the royal terrace under Kuh-e Rahmat, Macedonian camp on the plain (330 BC)
PERSEPOLIS = dict(size=(3000, 1800), seed=33, forest=.70, tree=38, **SAND,
    roads=[[(1500, 1040), (1500, 1400), (1460, 1860)], [(-60, 1500), (800, 1450), (1500, 1400), (2300, 1460), (3060, 1520)]],
    cities=[dict(center=(1500, 760), rx=560, ry=300, label='Persepolis', fs=80, churches=0, gates=[0.25], pal=STONE, amp=.03)],
    clear=[(1500, 760, 640), (1500, 1420, 520), (700, 1400, 400), (2300, 1420, 400)],
    camps=[dict(kind='greek', center=(1500, 1430), r=(560, 180), tents=16, horses=10, fires=6, tiles=5)])

# Babylon on the Euphrates (539 BC)
BABYLON = dict(size=(3000, 1800), seed=39, forest=.66, tree=40, **SAND,
    rivers=[dict(pts=[(1300, -60), (1380, 400), (1460, 900), (1420, 1300), (1520, 1860)], w=110, label='Euphrates', lab_at=.18)],
    cities=[dict(center=(1480, 900), rx=640, ry=420, label='Babylon', fs=86, churches=0, gates=[0.0, 0.15, 0.35, 0.55, 0.75, 0.9], pal=MUD, amp=.03)],
    clear=[(1480, 900, 700), (2550, 900, 420)],
    camps=[dict(kind='persian', center=(2560, 920), r=(330, 420), tents=14, horses=10, fires=4, tiles=4)])

# Siege of Isfahan by the Afghans (March-October 1722)
ISFAHAN = dict(size=(3000, 1800), seed=72, forest=.56, tree=40, **SAND,
    rivers=[dict(pts=[(-60, 1300), (600, 1250), (1200, 1290), (1800, 1240), (2400, 1300), (3060, 1260)], w=70, label='Zayandeh Rud', lab_at=.25)],
    bridges=[((1480, 1190), (1500, 1360))],
    roads=[[(1500, 1360), (1520, 1860)], [(2100, 700), (2700, 500), (3060, 420)]],
    cities=[dict(center=(1500, 760), rx=600, ry=330, label='Isfahan', fs=84, churches=0, gates=[0.05, 0.3, 0.55, 0.8], pal=MUD, amp=.05)],
    clear=[(1500, 760, 660), (1500, 1560, 420), (2650, 760, 380), (350, 700, 380)],
    camps=[dict(kind='afghan', center=(1500, 1580), r=(520, 150), tents=14, horses=10, fires=6, tiles=4),
           dict(kind='afghan', center=(2650, 760), r=(260, 330), tents=8, horses=6, fires=3, tiles=2),
           dict(kind='afghan', center=(350, 700), r=(260, 330), tents=8, horses=6, fires=3, tiles=2)])

# Baghdad besieged by Hulagu (January-February 1258)
BAGHDAD = dict(size=(3000, 1800), seed=58, forest=.60, tree=40, **SAND,
    rivers=[dict(pts=[(1700, -60), (1580, 400), (1450, 800), (1560, 1200), (1420, 1860)], w=130, label='Tigris', lab_at=.15)],
    bridges=[((1380, 860), (1560, 820))],
    cities=[dict(center=(1050, 880), rx=420, ry=360, label='Baghdad', fs=84, churches=0, gates=[0.1, 0.35, 0.6, 0.85], pal=MUD, amp=.05),
            dict(center=(2050, 820), rx=330, ry=300, label='', fs=60, churches=0, gates=[0.5], pal=MUD, amp=.05)],
    clear=[(1050, 880, 520), (2050, 820, 420), (350, 900, 380), (2700, 1300, 360), (1000, 1550, 380)],
    camps=[dict(kind='mongol', center=(330, 900), r=(240, 420), tents=12, horses=12, fires=4, tiles=3),
           dict(kind='mongol', center=(2700, 1320), r=(260, 300), tents=10, horses=8, fires=3, tiles=2),
           dict(kind='mongol', center=(1000, 1560), r=(420, 160), tents=10, horses=8, fires=3, tiles=2)])
