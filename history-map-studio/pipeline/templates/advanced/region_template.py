"""Region config: Mediterranean to the Indus, c. 661-750 (approximate borders; neighbours static, the caliphate drawn per frame)."""
BOUNDS = (-12.0, 74.0, 12.0, 48.0)
K = 110

T = [
    dict(name='Byzantium', tint=(196, 168, 212), poly=[(19.5, 40), (20, 42.5), (24, 43.5), (28.5, 44.5), (29.5, 41.3), (33, 42.2), (36, 41.8), (41.5, 41.4), (41, 39.6), (38.5, 38.5), (36.6, 37.1), (34, 36.0), (30, 36.0), (27, 36.4), (23, 36.2), (20.5, 38)],
         labels=[('Byzantine Empire', (32.0, 39.4), 150, 2600, -6)]),
    dict(name='ByzSicily', tint=(196, 168, 212), poly=[(12.2, 38.3), (15.7, 38.4), (15.4, 36.5), (12.2, 37.5)]),
    dict(name='ByzItaly', tint=(196, 168, 212), poly=[(15.4, 40.6), (18.7, 40.3), (16.7, 37.8), (15.5, 38.5)]),
    dict(name='Franks', tint=(170, 192, 226), poly=[(-5.5, 48), (10.8, 48), (10.8, 46.5), (7, 45.9), (7.5, 44.2), (4.9, 43.9), (3.3, 43.7), (2.0, 43.0), (0, 42.9), (-1.8, 43.4), (-1.6, 46), (-5.5, 47.8)],
         labels=[('Kingdom of the Franks', (3.0, 46.3), 140, 2600, -4)]),
    dict(name='Lombards', tint=(222, 204, 150), poly=[(7, 45.9), (13.8, 46.6), (13.7, 45.6), (12.4, 44.2), (13.8, 43.4), (15.6, 41.9), (16, 40.9), (15.4, 40.6), (14, 41), (12.4, 41.8), (10.5, 43.2), (8.5, 44.3), (7.5, 44.2)],
         labels=[('Lombards', (11.5, 43.9), 100, 1500, -30)]),
    dict(name='Asturias', tint=(220, 190, 170), poly=[(-9.6, 43.9), (-3.4, 43.7), (-3.4, 42.9), (-7, 42.6), (-9.6, 42.9)]),
    dict(name='Khazars', tint=(226, 206, 156), hatch=True, poly=[(36.5, 48), (56, 48), (53.5, 44.5), (49.5, 42.3), (47.8, 41.9), (46, 42.8), (42, 43.4), (38, 44.6), (36.6, 45.4)],
         labels=[('Khazar Khaganate', (46.5, 45.9), 130, 2400, -4)]),
    dict(name='Turgesh', tint=(208, 196, 176), hatch=True, poly=[(60, 48), (74, 48), (74, 42.3), (70.8, 41.6), (68, 42.8), (63, 44.6), (60, 46)],
         labels=[('Turgesh', (68.5, 45.3), 120, 2200, -4)]),
    dict(name='Tibet', tint=(196, 186, 212), poly=[(74, 37.2), (74, 31), (80, 31), (80, 37.2)]),
    dict(name='Hind', tint=(212, 182, 160), poly=[(71.2, 30.5), (74, 34), (74, 12), (72.8, 12), (72.7, 20.5), (70.4, 21.6), (70.8, 23.2), (71.6, 24.6), (71.2, 27.2), (70.3, 28.4)],
         labels=[('Kingdoms of Hind', (73.0, 23.5), 110, 1800, 80)]),
    dict(name='Makuria', tint=(214, 194, 166), poly=[(25, 21.9), (36.6, 21.9), (38.5, 18), (36, 14), (33, 12), (25, 12)],
         labels=[('Makuria', (31.0, 18.0), 110, 1800, -4)]),
    dict(name='Aksum', tint=(198, 210, 176), poly=[(36.5, 14.6), (39, 18), (43.2, 12.6), (42, 12), (36, 12)]),
]

# name, (lon, lat), 'cap'|'town', side
TOWNS = [
    ('Damascus', (36.29, 33.51), 'cap', 'r'), ('Jerusalem', (35.23, 31.78), 'town', 'l'), ('Mecca', (39.83, 21.42), 'town', 'r'), ('Medina', (39.61, 24.47), 'town', 'r'),
    ('Kufa', (44.4, 32.03), 'town', 'r'), ('Basra', (47.81, 30.5), 'town', 'r'), ('Wasit', (45.85, 32.2), 'town', 'u'), ('Mosul', (43.13, 36.34), 'town', 'r'),
    ('Harran', (39.03, 36.86), 'town', 'u'), ('Antioch', (36.16, 36.2), 'town', 'l'), ('Fustat', (31.23, 30.01), 'town', 'l'), ('Alexandria', (29.92, 31.2), 'town', 'l'),
    ('Kairouan', (10.1, 35.68), 'town', 'r'), ('Tangier', (-5.8, 35.77), 'town', 'l'), ('Toledo', (-4.02, 39.86), 'town', 'r'), ('Cordoba', (-4.78, 37.89), 'cap', 'l'),
    ('Narbonne', (3.0, 43.18), 'town', 'r'), ('Tours', (0.69, 47.39), 'town', 'r'), ('Constantinople', (28.98, 41.01), 'cap', 'r'), ('Rome', (12.5, 41.9), 'town', 'l'),
    ('Merv', (61.83, 37.66), 'town', 'r'), ('Bukhara', (64.42, 39.77), 'town', 'l'), ('Samarkand', (66.96, 39.65), 'town', 'r'), ('Nishapur', (58.8, 36.21), 'town', 'd'),
    ('Isfahan', (51.67, 32.65), 'town', 'r'), ('Shiraz', (52.53, 29.59), 'town', 'r'), ('Debal', (67.5, 24.75), 'town', 'l'), ('Multan', (71.47, 30.2), 'town', 'l'),
    ('Tbilisi', (44.8, 41.7), 'town', 'r'), ('Derbent', (48.29, 42.06), 'town', 'r'), ('Sana\u2019a', (44.2, 15.35), 'town', 'r'), ('Tripoli', (13.19, 32.89), 'town', 'd'),
]
RIVER_LABELS = [('Euphrates', (41.2, 34.6), 60, 1400, -30), ('Tigris', (45.2, 34.0), 60, 1200, -50), ('Nile', (31.3, 26.5), 60, 1600, 82),
                ('Indus', (69.0, 27.6), 60, 1400, 60), ('Oxus', (62.5, 39.7), 60, 1400, -40)]
SEA_LABELS = [('Mediterranean Sea', (18.0, 34.4), 110, 4000, -4), ('Atlantic Ocean', (-10.5, 33.5), 100, 3000, 80), ('Arabian Sea', (63.0, 18.0), 110, 3000, -6),
              ('Red Sea', (38.4, 20.6), 70, 2000, -58), ('Caspian', (50.6, 41.0), 70, 1600, -80), ('Black Sea', (34.0, 43.3), 90, 2000, -4), ('Persian Gulf', (51.5, 27.0), 70, 1600, -30)]
FOREST_BOOST = [(-4.5, 41.0, 2.2), (-7.8, 40.6, 1.6), (-2.5, 38.6, 1.4), (2.0, 46.5, 4.0), (8.0, 47.0, 2.5), (33.0, 40.5, 3.0), (40.5, 41.0, 2.0), (50.5, 36.8, 1.5), (13.0, 43.0, 2.0), (-6.0, 42.5, 2.0), (24.0, 42.5, 2.5), (40, 45.5, 3.0)]
CFG = dict(territories=T, towns=TOWNS, hand_rivers=[], lakes=[], river_labels=RIVER_LABELS + SEA_LABELS, forest_boost=FOREST_BOOST,
           land=True, lsc=0.52, tsc=0.30, rsc=0.55, river_rank=4, lake_rank=3, forest_thr=0.86, boost_amp=2.6, forest_floor=-1, sea=(0.58, 0.69, 0.76))

# --- v5: finer relief/forest grain on the overview atlas, plus sharp detail atlases for every zoomed view ---
import math as _m
CFG.update(nsc=0.32, tsc=0.42, boost_amp=2.2, forest_thr=0.80, flat_sea=True, relief=0.20)
C0 = _m.cos(_m.radians((BOUNDS[2] + BOUNDS[3]) / 2))   # all atlases share the main projection's c
KM = K
def dcfg(Kd, tsc=1.15):
    r = Kd / KM; d = dict(CFG)
    d.update(lsc=CFG['lsc'] * r, rsc=CFG['rsc'] * r, tsc=tsc, nsc=Kd / 1300 * 2.6, forest_thr=0.70, boost_amp=2.4, river_rank=3, relief=0.17)
    return d
# name, (lon0, lon1, lat0, lat1), K
DETAILS = [('mid', (22.0, 72.0, 22.0, 44.0), 230), ('levant', (30.0, 49.0, 27.0, 40.5), 420),
           ('anatolia', (20.0, 39.0, 35.0, 46.0), 420), ('west', (-13.0, 11.0, 31.0, 50.5), 330), ('sindh', (56.0, 78.0, 20.0, 35.0), 330)]
