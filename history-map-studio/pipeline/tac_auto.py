"""Tactical close-up specs generated from a few words, so every siege / battle gets a close-up without hand-drawing.

make(city='Isfahan', attacker='afghan', defender='safavid', climate='arid', river=True, field=False, seed=7)
  climate: arid | temperate | winter | steppe      field=True -> open battlefield (two armies, no city)
Base canvas 3000x1800 (tactical.py)."""
import random

WATER = ((52, 74, 96), (96, 132, 160), (122, 162, 190), (140, 180, 206), (196, 220, 234))
CLIM = {
    'arid': dict(ground=(206, 188, 152), tree_tint=(0.66, 0.78, 0.50), water=WATER, forest=.62, tree=40),
    'steppe': dict(ground=(186, 178, 140), tree_tint=(0.70, 0.80, 0.52), water=WATER, forest=.60, tree=36),
    'temperate': dict(ground=(150, 158, 120), tree_tint=(0.55, 0.85, 0.45), water=WATER, forest=.42, tree=44),
    'winter': dict(forest=.47, tree=44),     # tactical.py defaults: snow grey + frozen rivers
}
PAL = {
    'arid': dict(ground=(150, 126, 96), street=(200, 180, 146), roof=(184, 158, 120), edge=(228, 210, 176), ridge=(132, 108, 82), wall=(198, 172, 130), wall_hi=(234, 216, 178)),
    'stone': dict(ground=(140, 128, 112), street=(206, 196, 176), roof=(168, 150, 128), edge=(236, 226, 206), ridge=(120, 104, 88), wall=(212, 200, 178), wall_hi=(244, 236, 218)),
}

def make(city='', attacker='mongol', defender=None, climate='arid', river=False, field=False, seed=7, churches=0, label=None):
    rng = random.Random(seed); c = dict(size=(3000, 1800), seed=seed, **CLIM.get(climate, CLIM['arid']))
    if river:
        y = rng.choice([1300, 1350, 520])
        c['rivers'] = [dict(pts=[(-60, y), (700, y - 70 + rng.randint(-40, 40)), (1500, y + rng.randint(-60, 60)), (2300, y - 50), (3060, y + 30)], w=90,
                            label=river if isinstance(river, str) else '', lab_at=.22)]
    if field:
        c['clear'] = [(900, 700, 520), (2100, 1100, 520)]
        c['camps'] = [dict(kind=defender or 'rus', center=(900, 680), r=(460, 240), tents=12, horses=10, fires=4, tiles=6),
                      dict(kind=attacker, center=(2150, 1120), r=(460, 240), tents=12, horses=12, fires=4, tiles=6)]
        c['field'] = True
        c.setdefault('rivers', [dict(pts=[(-60, 1500), (600, 1420), (1300, 1560), (2000, 1640), (3060, 1580)], w=70, label='', lab_at=.2)])
        c['roads'] = [[(-60, 640), (500, 660), (900, 700), (1500, 900), (2150, 1100), (3060, 1180)]]
        c['clear'] = c['clear'] + [(1640, 1050, 330)]
        c['wagons'] = [[(1660, 780), (1590, 960), (1600, 1150), (1680, 1330)]]   # wagon fort chained in front of the attacker's guns
        return c
    pal = PAL['arid'] if climate in ('arid', 'steppe') else ({} if climate == 'winter' else PAL['stone'])
    city_d = dict(center=(1500, 760), rx=560, ry=320, label=label if label is not None else city, fs=80, churches=churches,
                  gates=[0.05, 0.3, 0.55, 0.8], amp=.05)
    if pal: city_d['pal'] = pal
    c['cities'] = [city_d]
    c['roads'] = [[(1500, 1080), (1480, 1500), (1450, 1860)], [(2050, 700), (2600, 560), (3060, 500)], [(950, 760), (400, 700), (-60, 640)]]
    c['clear'] = [(1500, 760, 640), (1500, 1520, 420), (2620, 760, 360), (380, 760, 360)]
    c['camps'] = [dict(kind=attacker, center=(1500, 1540), r=(520, 150), tents=14, horses=10, fires=6, tiles=4),
                  dict(kind=attacker, center=(2620, 780), r=(260, 320), tents=8, horses=6, fires=3, tiles=2),
                  dict(kind=attacker, center=(380, 760), r=(260, 320), tents=8, horses=6, fires=3, tiles=2)]
    return c
