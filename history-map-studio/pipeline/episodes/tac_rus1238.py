"""Tactical close-up scene specs for the 1238 campaign (base canvas 3000x1800 px)."""
VLADIMIR = dict(size=(3000, 1800), seed=21, forest=.50, tree=44,
    rivers=[dict(pts=[(-60, 1330), (600, 1240), (1200, 1310), (1800, 1250), (2400, 1350), (3060, 1280)], w=110, label='Klyazma', lab_at=.25),
            dict(pts=[(640, -60), (820, 420), (1000, 760), (1080, 1000), (1180, 1290)], w=38, label='Lybed', lab_at=.3)],
    roads=[[(1060, 760), (700, 760), (300, 700), (-60, 660)], [(1960, 700), (2400, 640), (3060, 560)], [(1500, 1100), (1500, 1250), (1500, 1500), (1450, 1860)]],
    bridges=[((1500, 1215), (1500, 1395))],
    cities=[dict(center=(1500, 760), rx=500, ry=320, label='Volodimer', fs=78, churches=4, gates=[0.0, 0.25, 0.5], lab_off=(0, -20), amp=.09)],
    clear=[(600, 700, 260), (2450, 700, 260), (1500, 1560, 300)],
    camps=[dict(kind='mongol', center=(560, 720), r=(250, 200), tents=14, horses=9, fires=8, tiles=5),
           dict(kind='mongol', center=(2460, 700), r=(250, 210), tents=14, horses=9, fires=8, tiles=5),
           dict(kind='mongol', center=(1500, 1580), r=(420, 140), tents=12, horses=8, fires=7, tiles=6)])

SIT = dict(size=(3000, 1800), seed=33, forest=.42, tree=44,
    rivers=[dict(pts=[(1250, -60), (1120, 380), (1380, 760), (1180, 1180), (1320, 1860)], w=72, label='Sit', lab_at=.45),
            dict(pts=[(-60, 1500), (500, 1380), (900, 1300), (1240, 1260)], w=34)],
    roads=[[(1700, 860), (2300, 700), (3060, 640)], [(1700, 860), (1500, 1300), (1400, 1860)]],
    clear=[(1760, 860, 360), (1960, 760, 200)],
    camps=[dict(kind='rus', center=(1780, 850), r=(330, 230), tents=16, horses=10, fires=9, tiles=0)])

TORZHOK = dict(size=(3000, 1800), seed=47, forest=.47, tree=44,
    rivers=[dict(pts=[(-60, 640), (700, 900), (1400, 860), (2100, 1120), (3060, 1060)], w=96, label='Tvertsa', lab_at=.7)],
    roads=[[(1220, 600), (700, 500), (-60, 420)], [(1800, 560), (2400, 440), (3060, 380)]],
    cities=[dict(center=(1500, 560), rx=330, ry=230, label='Torzhok', fs=60, churches=2, gates=[0.05, 0.3, 0.55], amp=.12)],
    clear=[(600, 300, 250), (2350, 420, 250), (1650, 1300, 300)],
    camps=[dict(kind='mongol', center=(620, 300), r=(260, 170), tents=12, horses=8, fires=7, tiles=4),
           dict(kind='mongol', center=(2380, 400), r=(260, 180), tents=12, horses=8, fires=7, tiles=4),
           dict(kind='mongol', center=(1650, 1330), r=(380, 170), tents=12, horses=8, fires=7, tiles=6)])
