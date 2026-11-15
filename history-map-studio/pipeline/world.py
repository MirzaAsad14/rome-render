"""Automatic region: build the illustrated atlas for ANY part of the world from bounds alone.

The AI no longer hand-writes a region file. story.py calls auto_region(bounds, camera_views):
  * picks K (px per degree) so the overview atlas is crisp but fits in memory,
  * adds DETAIL atlases around every close camera view (quality rule: no blurry zoom-ins),
  * bakes sea / river labels and arid zones (for the era styles) from the world lists below.
"""
import math, os
from PIL import Image, ImageDraw, ImageFilter

# (name, (lon, lat), size_at_K104, arc_radius, tilt_deg)
SEAS = [('Mediterranean Sea', (18.0, 34.4), 100, 4000, -4), ('Black Sea', (34.0, 43.4), 90, 2000, -4), ('Caspian Sea', (50.9, 41.6), 66, 1600, -78),
        ('Persian Gulf', (51.2, 27.3), 62, 1600, -32), ('Red Sea', (38.6, 20.4), 66, 2000, -58), ('Arabian Sea', (63.0, 18.5), 110, 3000, -6),
        ('Gulf of Oman', (58.6, 24.4), 46, 1000, -30), ('Aral Sea', (59.6, 45.2), 46, 800, -4), ('Atlantic Ocean', (-28.0, 38.0), 120, 4000, 80),
        ('North Sea', (3.5, 56.0), 80, 2000, -10), ('Baltic Sea', (19.5, 57.5), 70, 1600, -60), ('Adriatic Sea', (15.2, 43.0), 46, 1200, -40),
        ('Aegean Sea', (25.0, 38.8), 50, 1000, -70), ('Bay of Bengal', (88.0, 15.0), 100, 3000, -6), ('Indian Ocean', (75.0, 3.0), 130, 5000, -4),
        ('South China Sea', (114.0, 14.0), 90, 2400, -30), ('East China Sea', (125.5, 29.0), 70, 1800, -40), ('Sea of Japan', (135.0, 40.5), 70, 1800, -40),
        ('Yellow Sea', (123.0, 35.5), 60, 1200, -70), ('Pacific Ocean', (155.0, 25.0), 140, 6000, -4), ('Gulf of Mexico', (-90.0, 25.0), 80, 2400, -6),
        ('Caribbean Sea', (-75.0, 15.0), 90, 2600, -6), ('English Channel', (-1.5, 50.0), 40, 900, -12), ('Bay of Biscay', (-5.0, 45.5), 50, 1000, -30),
        ('Sea of Azov', (36.6, 46.1), 34, 600, -30), ('White Sea', (38.0, 65.5), 50, 900, -30), ('Ionian Sea', (19.0, 37.5), 50, 1100, -60),
        ('Tyrrhenian Sea', (12.0, 40.0), 50, 1100, -60), ('Gulf of Aden', (48.0, 12.2), 46, 1000, -10), ('Barents Sea', (40.0, 72.0), 80, 2000, -4)]
RIVERS = [('Euphrates', (40.6, 35.0), 60, 1400, -28), ('Tigris', (44.6, 34.6), 60, 1200, -52), ('Nile', (31.2, 26.0), 60, 1600, 82),
          ('Indus', (69.6, 27.4), 60, 1400, 62), ('Oxus', (62.4, 39.6), 60, 1400, -40), ('Jaxartes', (66.5, 42.4), 54, 1400, -30),
          ('Danube', (24.0, 43.9), 60, 1600, -4), ('Volga', (46.5, 49.0), 60, 1600, 60), ('Dnieper', (33.4, 48.4), 54, 1200, 50),
          ('Don', (40.5, 48.4), 54, 1200, 50), ('Rhine', (6.9, 50.6), 50, 1200, 70), ('Ganges', (84.0, 25.6), 60, 1600, -8),
          ('Yellow River', (110.5, 35.6), 60, 1600, -50), ('Yangtze', (113.0, 30.4), 60, 1600, -8), ('Mississippi', (-90.8, 35.0), 54, 1600, 80),
          ('Loire', (0.5, 47.3), 46, 1000, -4), ('Seine', (2.0, 49.0), 40, 800, -20), ('Po', (10.5, 45.1), 40, 800, -4), ('Vistula', (19.5, 52.6), 46, 1000, 70)]
# arid zones (rough polygons, lon/lat) - era styles tint these sand / ochre
DESERTS = [
    [(-17, 21), (-5, 30), (10, 32), (25, 31), (32, 29), (33, 22), (36, 18), (30, 14), (15, 15), (0, 16), (-16, 16)],             # Sahara
    [(36.5, 30.0), (40.0, 33.6), (44.5, 32.4), (47.5, 30.0), (50.0, 27.0), (55.5, 24.0), (56.0, 21.0), (52.0, 16.5), (44.0, 16.0), (39.5, 22.0), (36.5, 27.0)],
    [(51.0, 36.0), (56.5, 36.3), (58.5, 34.0), (57.0, 32.6), (53.0, 33.2), (51.0, 34.4)], [(57.0, 32.4), (60.0, 32.2), (60.2, 29.0), (58.5, 28.0), (57.3, 29.6)],
    [(53.0, 41.5), (60.5, 44.5), (65.0, 41.5), (63.0, 38.6), (57.5, 38.0), (54.0, 38.8)], [(62.0, 43.5), (66.5, 43.0), (66.0, 41.0), (63.0, 41.2)],
    [(60.5, 31.5), (65.0, 31.3), (66.5, 29.0), (63.0, 28.5), (61.0, 29.5)], [(69.8, 29.0), (73.5, 28.5), (73.5, 25.0), (70.5, 24.5), (69.5, 26.5)],
    [(77, 41), (88, 41), (90, 38.5), (84, 37), (77, 38)], [(95, 45), (105, 45.5), (112, 44), (110, 41.5), (100, 40), (94, 42)],          # Taklamakan, Gobi
    [(-71, -18), (-69, -18), (-69.5, -27), (-71, -27)], [(15, -18), (25, -18), (26, -26), (19, -27)], [(122, -20), (135, -21), (134, -29), (123, -29)],
    [(-117, 36), (-112, 35), (-110, 31), (-114, 30.5), (-117, 33)]]


def auto_region(bounds, views=(), max_details=8, crisp=1.5, merge=(9000, 7000), label_k=None):
    """bounds (lon0, lon1, lat0, lat1); views [(lon, lat, view_width_deg)] -> region namespace"""
    lon0, lon1, lat0, lat1 = bounds
    C0 = math.cos(math.radians((lat0 + lat1) / 2))
    K = int(max(40, min(130, 6800 / ((lon1 - lon0) * C0), 5200 / (lat1 - lat0))))
    r = K / 104
    inb = lambda p: lon0 <= p[0] <= lon1 and lat0 <= p[1] <= lat1
    labels = [(n, p, int(s * r), int(R * r), a) for n, p, s, R, a in SEAS + RIVERS if inb(p)]
    CFG = dict(territories=[], towns=[], hand_rivers=[], lakes=[], river_labels=labels, forest_boost=[], clear_polys=DESERTS, land=True,
               lsc=0.52 * r, tsc=0.32, rsc=0.55 * r, river_rank=4 if K < 90 else 5, lake_rank=3, forest_thr=0.46, boost_amp=3.4, forest_floor=-1,
               sea=(0.58, 0.69, 0.76), nsc=0.32 * r, flat_sea=True, relief=0.19)
    def dcfg(Kd):
        rr = Kd / K; d = dict(CFG)
        d.update(lsc=CFG['lsc'] * rr, rsc=CFG['rsc'] * rr, tsc=0.80, nsc=Kd / 1300 * 2.6, river_rank=3, relief=0.20,
                 river_labels=[(n, p, int(s * (label_k if label_k else rr)), int(R * (label_k if label_k else rr)), a) for n, p, s, R, a in labels])
        # label_k: sea/river names are already scaled by lsc (= rr); label_k < rr keeps them screen-sized in close views
        return d
    # detail atlases: one per cluster of close views, K high enough for >= 1 atlas px per screen px
    det = []
    for lon, lat, wl in sorted(views, key=lambda v: v[2]):
        need = 1920 / (wl * C0)
        if need <= K * 1.25: continue
        Kd = int(min(540, need * crisp))   # 1.5 atlas px per screen px: crisper close views
        hw, hh = wl * 1.15, wl * 1.15 * 1080 / 1920 / C0 + .6
        box = [max(lon0, lon - hw), min(lon1, lon + hw), max(lat0, lat - hh), min(lat1, lat + hh)]
        merged = False
        for d in det:
            b = d[1]
            if b[0] - .5 <= lon <= b[1] + .5 and b[2] - .5 <= lat <= b[3] + .5 and abs(d[2] - Kd) / Kd < .45:
                nb = [min(b[0], box[0]), max(b[1], box[1]), min(b[2], box[2]), max(b[3], box[3])]
                if (nb[1] - nb[0]) * C0 * d[2] < merge[0] and (nb[3] - nb[2]) * d[2] < merge[1]: d[1] = nb; merged = True; break
        if not merged: det.append([f'd{len(det)}', box, Kd])
    DETAILS = [(n, tuple(b), k) for n, b, k in det][:max_details]
    return dict(BOUNDS=tuple(bounds), K=K, C0=C0, CFG=CFG, dcfg=dcfg, DETAILS=DETAILS, DESERTS=DESERTS)


def desert_mask(P, path, deserts, rough):
    w, h = P.w // 2, P.h // 2; m = Image.new('L', (w, h), 0); d = ImageDraw.Draw(m)
    for poly in deserts: d.polygon([(x / 2, y / 2) for x, y in (P.xy(*p) for p in rough(poly, .3, .12))], fill=255)
    m.filter(ImageFilter.GaussianBlur(max(4, P.K * .25))).save(path)
