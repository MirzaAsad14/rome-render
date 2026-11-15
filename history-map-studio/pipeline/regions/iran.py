"""Region config: Greater Iran and its neighbours, from the Aegean to Delhi (physical base only).
Realms, towns and their labels change with every era, so they are drawn per frame by the episode, not baked here."""
import math as _m
BOUNDS = (18.0, 82.0, 12.0, 47.0)
K = 104

RIVER_LABELS = [('Euphrates', (40.6, 35.0), 60, 1400, -28), ('Tigris', (44.6, 34.6), 60, 1200, -52), ('Nile', (31.2, 26.0), 60, 1600, 82),
                ('Indus', (69.6, 27.4), 60, 1400, 62), ('Oxus', (62.4, 39.6), 60, 1400, -40), ('Karun', (48.9, 31.9), 46, 900, -60)]
SEA_LABELS = [('Mediterranean Sea', (25.5, 34.0), 100, 4000, -4), ('Arabian Sea', (63.0, 18.5), 110, 3000, -6), ('Red Sea', (38.6, 20.4), 66, 2000, -58),
              ('Caspian Sea', (50.9, 41.6), 66, 1600, -78), ('Black Sea', (34.0, 43.4), 90, 2000, -4), ('Persian Gulf', (51.2, 27.3), 62, 1600, -32),
              ('Aral Sea', (59.6, 45.2), 46, 800, -4), ('Gulf of Oman', (58.6, 24.4), 46, 1000, -30)]
# Caspian Hyrcanian forest, Zagros oak belt, Pontic & Caucasus forests, Punjab, Balkans
FOREST_BOOST = [(51.5, 36.7, 1.4), (49.2, 37.6, 0.9), (54.5, 36.9, 0.9), (47.5, 34.2, 1.6), (50.5, 31.5, 1.3), (45.6, 36.3, 1.2), (36.0, 41.0, 2.4),
                (42.0, 42.2, 1.6), (44.5, 42.3, 1.3), (23.5, 41.5, 2.4), (75.5, 31.5, 2.0), (72.5, 34.5, 1.4), (30.0, 40.0, 1.6)]
CFG = dict(territories=[], towns=[], hand_rivers=[], lakes=[], river_labels=RIVER_LABELS + SEA_LABELS, forest_boost=FOREST_BOOST,
           land=True, lsc=0.52, tsc=0.42, rsc=0.55, river_rank=4, lake_rank=3, forest_thr=0.82, boost_amp=3.4, forest_floor=-1,
           sea=(0.58, 0.69, 0.76), nsc=0.32, flat_sea=True, relief=0.19)
C0 = _m.cos(_m.radians((BOUNDS[2] + BOUNDS[3]) / 2))
KM = K
def dcfg(Kd, tsc=1.05):
    r = Kd / KM; d = dict(CFG)
    d.update(lsc=CFG['lsc'] * r, rsc=CFG['rsc'] * r, tsc=tsc, nsc=Kd / 1300 * 2.6, forest_thr=0.72, boost_amp=3.2, river_rank=3, relief=0.20)
    return d
# name, (lon0, lon1, lat0, lat1), K
DETAILS = [('persia', (40.0, 66.0, 23.0, 42.0), 230), ('west', (21.0, 50.0, 28.5, 43.0), 270), ('east', (55.0, 80.0, 24.0, 43.0), 270),
           ('gulf', (47.0, 61.0, 23.0, 33.5), 440), ('core', (44.0, 56.0, 28.0, 39.0), 440)]

# physical deserts (for era styles that colour arid land): (poly lon/lat)
DESERTS = [
    [(51.0, 36.0), (56.5, 36.3), (58.5, 34.0), (57.0, 32.6), (53.0, 33.2), (51.0, 34.4)],                       # Dasht-e Kavir
    [(57.0, 32.4), (60.0, 32.2), (60.2, 29.0), (58.5, 28.0), (57.3, 29.6)],                                     # Dasht-e Lut
    [(36.5, 30.0), (40.0, 33.6), (44.5, 32.4), (47.5, 30.0), (50.0, 27.0), (55.5, 24.0), (56.0, 21.0), (52.0, 16.5), (44.0, 16.0), (39.5, 22.0), (36.5, 27.0)],  # Arabia & Syrian desert
    [(53.0, 41.5), (60.5, 44.5), (65.0, 41.5), (63.0, 38.6), (57.5, 38.0), (54.0, 38.8)],                       # Karakum
    [(62.0, 43.5), (66.5, 43.0), (66.0, 41.0), (63.0, 41.2)],                                                   # Kyzylkum
    [(60.5, 31.5), (65.0, 31.3), (66.5, 29.0), (63.0, 28.5), (61.0, 29.5)],                                     # Registan / Sistan
    [(69.8, 29.0), (73.5, 28.5), (73.5, 25.0), (70.5, 24.5), (69.5, 26.5)],                                     # Thar
    [(24.5, 31.0), (31.0, 30.6), (32.0, 26.0), (33.5, 22.0), (24.5, 20.0)],                                     # Libyan / Western desert
]
