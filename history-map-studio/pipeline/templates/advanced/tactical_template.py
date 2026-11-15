"""Tactical close-ups for the Umayyad episode (summer, Near East palette). Base canvas 3000x1800."""
SAND = dict(ground=(204, 190, 160), tree_tint=(0.62, 0.80, 0.50),
            water=((52, 74, 96), (96, 132, 160), (122, 162, 190), (140, 180, 206), (196, 220, 234)))
CITYPAL = dict(ground=(150, 128, 100), street=(196, 178, 146), roof=(178, 154, 120), edge=(226, 210, 178), ridge=(130, 108, 84),
               wall=(196, 170, 128), wall_hi=(232, 214, 176))

DAMASCUS = dict(size=(3000, 1800), seed=61, forest=.40, tree=40, **SAND,
    rivers=[dict(pts=[(-60, 520), (500, 640), (1000, 700), (1500, 600), (2100, 700), (2600, 820), (3060, 900)], w=60, label='Barada', lab_at=.2)],
    roads=[[(1500, 1180), (1450, 1500), (1400, 1860)], [(2000, 900), (2600, 1100), (3060, 1200)], [(1000, 900), (500, 1100), (-60, 1250)]],
    cities=[dict(center=(1500, 900), rx=520, ry=290, label='Damascus', fs=78, churches=0, gates=[0.0, 0.2, 0.45, 0.7], pal=CITYPAL, amp=.05)],
    clear=[(1500, 900, 600), (1500, 1450, 500), (2600, 1300, 400), (400, 1400, 450)],
    camps=[dict(kind='umayyad', center=(1500, 1430), r=(420, 150), tents=12, horses=10, fires=0, tiles=4)])

ZAB = dict(size=(3000, 1800), seed=75, forest=.62, tree=40, **SAND,
    rivers=[dict(pts=[(3060, 260), (2400, 520), (1800, 760), (1300, 980), (800, 1220), (300, 1500), (-60, 1700)], w=110, label='Great Zab', lab_at=.62)],
    bridges=[((1590, 760), (1700, 960))],
    clear=[(900, 600, 520), (2300, 1250, 520)],
    camps=[dict(kind='umayyad', center=(900, 560), r=(460, 260), tents=16, horses=12, fires=0, tiles=0),
           dict(kind='abbasid', center=(2300, 1280), r=(460, 260), tents=16, horses=12, fires=0, tiles=0)])
