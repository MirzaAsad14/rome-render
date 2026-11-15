"""Episode: Iran, from Cyrus to 2026 (~18 min).
The map's own style ages with the story (styles.py): ancient -> medieval -> safavid -> qajar -> pahlavi -> modern,
dissolving at chapter cards. Respect rule: Muslim religious personalities appear only as NoorMedallion (light, no face).
2026 events are ongoing and contested: flagged on screen."""
import json, os, sys, math, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from kit import *
from kit import path_at
import numpy as np
import atlas, tactical as T_, styles as ST
from regions import iran as R
from episodes import tac_iran as TS

WD = json.load(open(os.path.join(ROOT, 'build/iran/words.json')))
END = WD['total']; VEND = WD['voice_end']; FPS = 24
W_ = 1920
def _n(s): return re.sub(r"[^\w]", '', s).lower()
WS = [_n(w['w']) for w in WD['words']]
def I(ph, after=0):
    toks = [_n(x) for x in ph.split()]
    for i in range(after, len(WS) - len(toks) + 1):
        if WS[i:i + len(toks)] == toks: return i
    raise KeyError(ph)
def T(ph, after=0): return WD['words'][I(ph, after)]['t0']
def Te(ph, after=0):
    i = I(ph, after) + len(ph.split()) - 1; return WD['words'][i]['t1']
def W(i): return WD['words'][i]['t0']

CHI = [i for i, w in enumerate(WS) if w == 'chapter']
CHT = [W(i) for i in CHI]
EPI = T('Epilogue')
NUM = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII', 'XIII', 'XIV']
TITLES = ['The Land of the Aryans', 'Cyrus the Great', 'Alexander', 'The Parthians', 'The Sasanians', 'The Arab Conquest',
          'Iranian Dynasties & Turkish Swords', 'The Mongols and Timur', 'The Safavids', 'Afghans and Nader Shah',
          'The Qajars and the Great Game', 'The Pahlavis', 'Revolution and War', 'The American Wars']

# ------------------------------------------------------------------ atlas & camera
P = atlas.Proj(*R.BOUNDS[:2], *R.BOUNDS[2:], K=R.K, c=R.C0)
PYR = atlas.build(P, R.CFG, os.path.join(ROOT, 'build/atlas_iran'))
DET = [(atlas.Proj(*b, K=Kd, c=R.C0), atlas.build(atlas.Proj(*b, K=Kd, c=R.C0), R.dcfg(Kd), os.path.join(ROOT, f'build/atlas_iran{n}'))) for n, b, Kd in R.DETAILS]
NAMES = [''] + [n for n, *_ in R.DETAILS]
LANDS = [Image.open(os.path.join(ROOT, f'build/atlas_iran{n}_land.png')).convert('L') for n in NAMES]
DESS = [Image.open(os.path.join(ROOT, f'build/atlas_iran{n}_desert.png')).convert('L') for n in NAMES]

C = dict(Persepolis=(52.89, 29.93), Pasargadae=(53.17, 30.2), Susa=(48.25, 32.19), Ecbatana=(48.51, 34.8), Babylon=(44.42, 32.54),
         Nineveh=(43.15, 36.36), Sardis=(28.04, 38.49), Memphis=(31.25, 29.85), Pella=(22.52, 40.76), Granicus=(27.3, 40.2),
         Issus=(36.2, 36.85), Gaugamela=(43.47, 36.56), Ctesiphon=(44.58, 33.09), Carrhae=(39.03, 36.87), Edessa=(38.79, 37.16),
         Jerusalem=(35.23, 31.78), Alexandria=(29.92, 31.2), Constantinople=(28.98, 41.01), Qadisiyyah=(44.4, 31.7), Nahavand=(48.37, 34.19),
         Merv=(61.83, 37.6), Baghdad=(44.37, 33.31), Bukhara=(64.42, 39.77), Samarkand=(66.96, 39.65), Nishapur=(58.8, 36.21),
         Ghazni=(68.42, 33.55), Zaranj=(61.88, 30.96), Herat=(62.2, 34.35), Dandanaqan=(61.6, 37.3), Manzikert=(42.54, 39.15),
         Isfahan=(51.67, 32.65), Otrar=(68.3, 42.85), Alamut=(50.58, 36.44), Tabriz=(46.29, 38.08), Shiraz=(52.53, 29.59),
         Chaldiran=(44.0, 39.08), Hormuz=(56.46, 27.07), Kandahar=(65.7, 31.6), Mashhad=(59.6, 36.3), Karnal=(76.99, 29.69),
         Delhi=(77.2, 28.6), Tehran=(51.39, 35.69), Tiflis=(44.8, 41.7), Bushehr=(50.84, 28.97), Basra=(47.8, 30.5),
         Khorramshahr=(48.18, 30.44), Abadan=(48.3, 30.34), Ahvaz=(48.67, 31.32), Fordow=(50.98, 34.88), Natanz=(51.73, 33.72),
         Qeshm=(55.9, 26.8), Islamabad=(73.05, 33.7), Medina=(39.6, 24.5), Athens=(23.73, 37.98), Marathon=(23.97, 38.15),
         Salamis=(23.5, 37.95), Bactra=(66.9, 36.76), Hamadan=(48.51, 34.8), Mosul=(43.13, 36.34), Tel_Aviv=(34.78, 32.08),
         Al_Udeid=(51.31, 25.12), Bahrain=(50.6, 26.2), Al_Dhafra=(54.55, 24.24), Kuwait=(47.9, 29.35), Dezful=(48.4, 32.38),
         Qasr_e_Shirin=(45.57, 34.51), Kerman=(57.08, 30.28), Rome=(12.5, 41.9))

def cam_keys():
    k = [(0.0, 51.4, 35.7, 9.0), (T('Nearly two') - .4, 51.4, 35.7, 9.0), (T('Between these') - .1, 51.4, 35.7, 7.4),
         (T('Between these') + 1.3, 53, 32.5, 44, 'cut'), (T('So when'), 53, 32.5, 46), (CHT[0] - .2, 53, 32.5, 42),
         (CHT[0] + 1.5, 53, 32.5, 36), (T('Iran is a high'), 53, 32.8, 30), (T('From around 3200'), 49, 32, 14),
         (T('Then, late'), 56, 35, 34), (T('The first of these'), 48.5, 34.8, 16), (T('In 612'), 45.5, 36, 17), (T('The Medes now'), 45, 37, 42),
         (CHT[1] + .5, 50, 32, 24), (T('In 550'), 51, 32, 16), (T('In 547'), 38, 36, 32), (T('In 539') - .4, 44.4, 33, 18),
         (T('His son Cambyses'), 39, 30.5, 36), (T('Then came Darius'), 47, 33, 40), (T('built the Royal Road'), 38.5, 35, 34),
         (T('introduced a gold'), 52, 30.5, 16), (T('At its height'), 46, 31, 62), (T('Only the Greeks'), 26.5, 38.5, 20),
         (T('Persia remained'), 40, 35, 44), (CHT[2] + .5, 30, 38, 40), (T('In 334'), 26, 40, 18), (T('He won at'), 31, 38.5, 20),
         (T('In 331'), 43, 36.2, 16), (T('Alexander took'), 48, 32, 18), (T('Darius was murdered'), 56, 34, 26), (T('When Alexander died'), 48, 33, 50),
         (CHT[3] + .5, 54, 36, 34), (T('Around 247'), 57.5, 37.5, 20), (T('Under Mithridates'), 50, 34, 30), (T('In 53 BC'), 40, 36.5, 16),
         (T('For nearly five'), 46, 34, 36), (T('But their kingdom'), 52, 33, 38), (CHT[4] + .5, 50, 31, 22), (T('In 224'), 50, 31, 18),
         (T('His son Shapur'), 46, 34, 40), (T('In 260'), 39, 37, 16), (T('Under Khosrow the First'), 46, 33, 30), (T('But his grandson'), 38, 35, 46),
         (T('By 628'), 42, 32, 50), (CHT[5] + .5, 44, 30, 30), (T('In 636'), 44.5, 32, 14), (T('Ctesiphon fell'), 45, 33, 14),
         (T('In 642'), 48, 34, 16), (T('The last Sasanian king'), 55, 35, 34), (T('he was killed near Merv'), 61, 37, 18),
         (T('Iran became part'), 45, 30, 62), (T('Persian administrators'), 52, 34, 40),
         (CHT[6] + .5, 56, 35, 44), (T('The Tahirids'), 60, 35, 30), (T('The Samanids'), 63, 38, 30), (T('And the Buyids'), 49, 33, 28),
         (T('Then came the Turks'), 66, 32, 36), (T('In 1040'), 60, 37, 20), (T('The Seljuks ruled'), 47, 37, 48), (T('After them came'), 58, 39, 44),
         (T('In 1218'), 68, 42, 18), (CHT[7] + .5, 66, 41, 24), (T('The answer came'), 64, 40, 24), (T('1221 Merv'), 60, 37, 20),
         (T('Irrigation canals'), 59, 36, 20), (T('In 1256 Hulagu'), 50.5, 36.4, 14), (T('and in 1258') - .4, 45, 34, 14),
         (T('Hulagu founded'), 48, 36, 44), (T('A century later'), 60, 35, 40), (T('When Isfahan'), 51.7, 32.6, 14), (T('After Timur'), 47, 37, 30),
         (CHT[8] + .5, 47, 37.5, 24), (T('a fourteen year'), 46.3, 38, 14), (T('He made Twelver'), 52, 33, 40), (T('In 1514'), 44.5, 39, 14),
         (T('fought for its life'), 53, 35, 52), (T('Then came Shah Abbas'), 52, 33, 38), (T('in 1622'), 56.4, 27.3, 14), (T('He made Isfahan'), 51.7, 32.6, 12),
         (T('like the English'), 40, 36, 50), (CHT[9] + .5, 57, 32, 30), (T('An Afghan army'), 60, 31, 30), (T('Hotak defeated') - .4, 52, 32.7, 12),
         (T('Iran was rescued'), 59, 36, 22), (T('Then he turned east'), 66, 33, 40), (T('In 1739'), 75.5, 29.5, 14), (T('He returned home'), 64, 32, 44),
         (T('But Nader grew'), 54, 33, 36), (T('Karim'), 52.5, 29.6, 16), (CHT[10] + .5, 53, 33, 30), (T('He made Tehran'), 51.4, 35.7, 14),
         (T('But a new kind'), 52, 37, 40), (T('By the treaties'), 46, 40, 16), (T('When Iran tried'), 56, 31, 30), (T('Iran was never colonised'), 56, 32, 44),
         (T('In 1906'), 51.4, 35.7, 14), (T('year later Britain'), 54, 32, 26), (CHT[11] + .5, 51.4, 35.7, 16), (T('In 1925'), 53, 32.5, 26),
         (T('And in 1935'), 53, 32.5, 30), (T('But in 1941'), 52, 33, 36), (T('In 1951'), 50, 31, 20), (T('Two years later'), 51.4, 35.7, 14),
         (T('The Shah returned'), 53, 32.5, 28), (CHT[12] + .5, 51.4, 35.7, 12), (T('In November, students'), 51.4, 35.7, 9),
         (T('Then, on the twenty second'), 48, 32, 18), (T('Cities like Khorramshahr'), 48.4, 31.0, 14), (T('the Cities, Iraqi'), 48.5, 33.5, 18),
         (T('before a ceasefire'), 50, 32, 30), (CHT[13] + .5, 46, 32, 40), (T('2025, after Israel'), 46, 33, 30), (T('American bombers hit'), 51.4, 34, 10),
         (T('Then, on the twenty eighth'), 46, 32, 34), (T('The opening strikes'), 51.4, 35.7, 9), (T('Iran answered'), 46, 30, 34),
         (T('and closed the Strait'), 56.3, 26.6, 10), (T('On the eighth of March'), 51.4, 35.7, 12), (T('In April, Pakistan'), 63, 31, 40),
         (T('deal, and the United'), 54, 27, 22), (T('In November 2026'), 55.9, 26.8, 8), (T('the war that began'), 53, 30, 30),
         (EPI + .5, 53, 32.5, 46), (T('Many conquered it'), 53, 33, 50), (T('Plutarch records') - .2, 50.9, 30.4, 9), (END, 51.0, 30.4, 8)]
    out = []
    for key in k:
        t_, lon, lat, wl = key[:4]; hl = wl / 2; hv = hl * H / W_ / R.C0
        lon = clamp(lon, R.BOUNDS[0] + hl + .2, R.BOUNDS[1] - hl - .2) if 2 * hl < R.BOUNDS[1] - R.BOUNDS[0] else lon
        lat = clamp(lat, R.BOUNDS[2] + hv + .2, R.BOUNDS[3] - hv - .2) if 2 * hv < R.BOUNDS[3] - R.BOUNDS[2] else lat
        out.append((t_, lon, lat, wl) + tuple(key[4:]))
    return out
cam = Camera(P, PYR, cam_keys(), details=DET)


def crop_masks(t):
    lon, lat, wl = cam.at(t); outs = []
    for MS in (LANDS, DESS):
        out = None; acc = 0.0
        for ai, w in reversed(cam.layers(lon, lat, wl)):
            Pa = cam.atl[ai][0]
            cx, cy = Pa.xy(lon, lat); vw = wl * Pa.c * Pa.K; vh = vw * H / W_
            box = ((cx - vw / 2) / 2, (cy - vh / 2) / 2, (cx + vw / 2) / 2, (cy + vh / 2) / 2)
            m = np.asarray(MS[ai].transform((W_, H), Image.EXTENT, box, Image.BILINEAR), np.float32) / 255
            if out is None: out, acc = m, w
            else: acc += w; out = out + (m - out) * (w / acc)
        outs.append(out)
    return outs


def wash(fr, sc, land, poly, col, a, circle=None, line=True, strength=.36):
    if a <= 0: return
    m = Image.new('L', (W_, H), 0); ImageDraw.Draw(m).polygon([sc(*p) for p in atlas.rough(poly, .35, .10)], fill=255)
    mm = np.asarray(m, np.float32) / 255
    if circle is not None:
        (clon, clat), rad = circle; cx, cy = sc(clon, clat); px_per_deg = sc(clon + 1, clat)[0] - cx
        yy, xx = np.ogrid[0:H, 0:W_]; d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / max(1e-3, px_per_deg)
        mm = mm * np.clip((rad - d) / 1.2, 0, 1)
    mm = mm * land
    if mm.max() <= 0.01: return
    arr = np.asarray(fr, np.float32)
    k = (mm * a * strength)[..., None]
    arr[..., :3] = arr[..., :3] * (1 - k) + np.array(col, np.float32) * k
    if line:
        e = np.asarray(Image.fromarray((mm * 255).astype(np.uint8)).filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(3)), np.float32) / 255
        ke = (np.clip(e * 1.5, 0, 1) * a * .85)[..., None]
        arr[..., :3] = arr[..., :3] * (1 - ke) + np.array(tuple(int(c * .55) for c in col), np.float32) * ke
    fr.paste(Image.fromarray(arr.astype(np.uint8), 'RGBA'))


# ------------------------------------------------------------------ realms (lon, lat)
ELAM = [(47.0, 33.5), (49.5, 33.0), (51.5, 31.0), (52.5, 29.5), (50.5, 29.0), (48.5, 30.0), (47.3, 31.0)]
MEDES = [(32, 41.8), (36, 41.2), (41, 41.5), (46, 41.8), (49, 40.5), (50, 37.5), (54, 37.2), (58, 37.8), (62, 37.5), (63, 35), (60, 32), (56, 31.5),
         (52, 32.5), (49, 33), (46.5, 33.5), (44, 35.5), (41, 36.8), (37, 37.2), (33.5, 38.5)]
PERSIS = [(50.5, 31.8), (53.5, 31.5), (55, 29), (53.5, 27), (51, 28.5), (50, 30.5)]
ACH = [(22.5, 42), (26, 42.8), (29, 41.2), (33, 42), (41, 41.5), (45, 42.5), (48.5, 42), (51, 40), (53.5, 41.5), (58, 43), (62, 44.5), (67, 43.5), (71, 41),
       (73.5, 39), (73.5, 36.5), (71.5, 35), (73, 33.5), (74, 31), (71.5, 28), (69, 24), (66, 25), (61.5, 25), (57, 26.5), (54, 26.5), (51, 27.5),
       (48.5, 29.5), (47, 30), (44.5, 31), (40, 33.5), (36, 31), (35, 29.5), (34.5, 28), (33, 26), (32.8, 22), (30, 21.8), (28, 22), (25, 29.5),
       (24, 31.5), (26, 33), (32, 32), (34, 35), (36, 36.3), (30, 36.2), (27, 36.6), (26, 38.5), (26, 40.2), (23, 40.3)]
SELEUCID = [(28, 36.5), (31, 40), (36, 38.5), (41, 39.5), (45, 40), (49.5, 39), (53.5, 41), (58, 42), (62, 43.5), (67, 43), (71, 41), (73, 38),
            (71, 35), (72, 32), (69, 27), (66, 25), (61.5, 25), (57, 26.5), (54, 26.5), (51, 27.5), (48.5, 29.5), (47, 30), (44.5, 31), (40, 33),
            (36, 33), (35.5, 36)]
PARTHIA = [(38.5, 37.5), (41.5, 38.5), (44.5, 39.5), (48.5, 39.5), (50.5, 37.5), (53.5, 38), (58, 38.5), (61.5, 37.5), (64, 37.2), (66.5, 34.5),
           (66, 30), (62, 26), (57.5, 25.5), (56, 26.5), (54, 26.5), (51, 27.8), (48.5, 29.8), (47, 30), (44.5, 31), (41, 33), (40.5, 35.5)]
SASAN = [(38.5, 37.5), (41.5, 40.5), (42, 42.3), (45, 42.5), (48, 42), (51, 39.5), (53.5, 40), (58, 39.5), (62, 39.5), (66, 39.5), (68.5, 37.5),
         (70.5, 35), (69.5, 31), (67.5, 26), (66, 25), (61.5, 25), (57, 26.5), (58.5, 23.5), (57, 22), (54, 23.7), (51.5, 24.5), (50, 26),
         (48.5, 29), (47, 30), (44.5, 31), (41, 32.5), (39.5, 34.5)]
ROME = [(25.5, 31.5), (25.5, 36), (26, 42), (36, 41.8), (41, 41), (41, 38.5), (38.5, 37.5), (37.5, 36), (36.8, 33), (35.5, 30), (34.5, 28),
        (33, 24), (31, 22), (25, 22)]
CALIPH = [(25, 31.5), (31, 31.5), (34, 31.3), (35.8, 34.5), (36.2, 36.3), (37.5, 37.0), (40.5, 37.5), (43.5, 37.5), (45, 39), (48, 39.5), (50, 37.3),
          (54, 37.3), (58, 37.8), (62, 36.5), (63, 33), (61.5, 30), (61.5, 25.5), (57.5, 25.5), (59.8, 22.5), (55, 17), (52, 16), (45, 12.6),
          (43, 12.7), (39, 21), (36.6, 22), (33, 24), (31.5, 22), (25, 22)]
TAHIR = [(55.5, 36), (58, 38.2), (62, 37.8), (63.5, 35), (60, 33.8), (56.5, 34.5)]
SAFFAR = [(58.5, 32.5), (63, 33), (65.5, 30), (62.5, 27.8), (59, 28.5)]
SAMANID = [(58, 37.5), (56, 40), (60, 42.5), (64, 43.5), (69, 43), (71.5, 41), (71, 39), (70, 37.3), (67, 35), (64, 34.5), (61, 35), (59, 36)]
BUYID = [(44, 37), (46.5, 38.5), (49.5, 37.8), (52, 36.5), (55.5, 36), (56.5, 33.5), (57.5, 29.5), (57, 26.5), (54, 26.5), (51, 27.8), (48.5, 29.8),
         (47, 30), (44.5, 31), (42.5, 33), (43, 35.5)]
GHAZNA = [(55, 37), (59, 38.5), (63, 38), (67, 37.5), (71, 37), (74, 35), (77, 31.5), (75, 29.5), (71, 28), (69, 24.5), (66, 25), (61.5, 25.5),
          (58.5, 27), (56.5, 30), (53, 33), (52, 35.5)]
SELJUK = [(27, 40.5), (29, 41.2), (34, 41.5), (40, 41), (44, 41.8), (47, 42), (50, 40), (53.5, 41.5), (58, 43), (64, 44), (70, 43), (73, 40.5), (72, 37.5),
          (70, 36), (67, 35), (64, 34), (62, 32), (61.5, 27), (58, 25.8), (57, 26.5), (54, 26.5), (51, 27.8), (48.5, 29.8), (47, 30), (44.5, 31),
          (40, 33), (36, 31), (34.8, 32.5), (36, 36.3), (31, 36.5), (28, 37)]
KHWAR = [(44.5, 37.5), (47, 39.5), (49.5, 38), (53.5, 41), (57, 43.5), (61, 45.5), (66, 45), (70, 43), (72.5, 41), (71.5, 37.5), (70, 35), (68, 34.5),
         (66, 31), (62.5, 27), (58, 25.8), (57, 26.5), (54, 26.5), (51, 27.8), (48.5, 29.8), (47, 32), (45.5, 34)]
ILKHAN = [(27, 38.5), (29, 41.2), (34, 41.5), (40, 41), (43, 42.5), (47.5, 42), (49.5, 41), (50, 39), (53.5, 38), (58, 38), (62, 37.5), (64, 36), (64, 31),
          (62, 27), (58, 25.8), (57, 26.5), (54, 26.5), (51, 27.8), (48.5, 29.8), (47, 30), (44.5, 31), (41, 33.5), (40, 36), (36.5, 37), (32, 36.5), (28, 37)]
TIMURID = [(40, 40), (44, 42), (47.5, 42), (49.5, 41), (51, 39), (53.5, 41.5), (58, 43.5), (64, 44.5), (70, 43.5), (73.5, 40), (73.5, 36.5), (71, 34.5),
           (72, 32), (70, 29), (66.5, 26), (62, 25.5), (58, 25.8), (57, 26.5), (54, 26.5), (51, 27.8), (48.5, 29.8), (47, 30), (44.5, 31), (42.5, 33.5),
           (41, 36.5), (38.5, 37.5)]
SAFAVID = [(41.5, 41.5), (43.5, 42.3), (46.5, 42.2), (48.5, 41.5), (49.5, 40.5), (51, 39), (53.5, 38), (56, 38.2), (60, 37), (62, 36), (64, 34.5),
           (64.5, 31.5), (62, 29.5), (61.5, 25.5), (58, 25.8), (57, 26.5), (54, 26.5), (51, 27.8), (48.5, 29.8), (47, 30.5), (45.5, 33), (44.5, 36.5), (43, 38.5)]
OTTOMAN = [(26, 42), (30, 41.5), (36, 41.8), (41.5, 41.5), (43, 38.5), (44.5, 36.5), (45.5, 33), (47, 30.5), (48.5, 29.8), (47.5, 29), (44, 29.5), (40, 33),
           (36, 30), (35, 28), (33, 26), (25, 26), (25, 31.5), (26, 36), (26, 40)]
UZBEK = [(55.5, 40), (58, 43), (62, 45), (68, 44), (71, 42), (70, 38.5), (68, 37.2), (65, 37.3), (62, 36.5), (60, 37)]
HOTAK = [(61, 34), (64, 34.8), (68, 34), (68.5, 31), (66.5, 29.5), (63, 29.5), (61, 31)]
AFSHAR = [(41.5, 41.5), (43.5, 42.3), (46.5, 42.2), (48.5, 41.5), (49.5, 40.5), (53.5, 41.5), (58, 42.5), (62, 41.5), (66, 39.5), (70, 37.5), (71.5, 35),
          (74, 33.5), (72.5, 30), (71, 28), (69.5, 24.5), (66, 25), (61.5, 25.5), (58, 25.8), (57, 26.5), (54, 26.5), (51, 27.8), (48.5, 29.8), (47, 30.5),
          (45.5, 33), (44.5, 36.5), (43, 38.5)]
IRANM = [(44.0, 39.4), (44.8, 39.7), (46.5, 38.9), (48, 38.4), (48.9, 38.4), (49.0, 37.6), (51, 36.8), (53.9, 36.9), (56, 37.9), (57.5, 38.1), (60.4, 36.6),
         (61.2, 35.6), (60.9, 34.3), (60.5, 33.1), (60.9, 31.5), (61.8, 31.0), (61.6, 29.8), (60.9, 29.4), (62.8, 28.2), (63.3, 26.7), (61.6, 25.2),
         (57.3, 25.7), (54.5, 26.6), (51.5, 27.9), (50.0, 29.8), (48.5, 30), (48.0, 30.5), (47.7, 31.0), (47.4, 32.4), (46.1, 33.0), (45.4, 34.0),
         (45.6, 35.0), (46.1, 35.7), (45.3, 36.0), (44.8, 37.2), (44.2, 38.0)]
CAUC = [(40.5, 41.5), (41.5, 43.3), (44, 42.8), (46.5, 42), (48.6, 41.8), (49.6, 40.5), (49, 39.2), (48, 38.4), (46.5, 38.9), (45, 39.5), (44, 39.7), (43.5, 41)]
RUS_SPH = [(44.0, 39.4), (44.8, 39.7), (46.5, 38.9), (48, 38.4), (48.9, 38.4), (49.0, 37.6), (51, 36.8), (53.9, 36.9), (56, 37.9), (57.5, 38.1), (60.4, 36.6),
           (61.2, 35.6), (60.9, 34.3), (54.4, 31.9), (51.7, 32.6), (45.6, 34.4), (45.4, 34.0), (45.6, 35.0), (46.1, 35.7), (45.3, 36.0), (44.8, 37.2), (44.2, 38.0)]
BRI_SPH = [(60.9, 33.4), (57.0, 30.3), (56.3, 27.2), (57.3, 25.7), (61.6, 25.2), (63.3, 26.7), (62.8, 28.2), (60.9, 29.4), (61.6, 29.8), (61.8, 31.0), (60.9, 31.5), (60.5, 33.1)]
IRAQ = [(38.8, 33.4), (41.0, 34.4), (42.2, 37.3), (44.8, 37.2), (45.3, 36.0), (46.1, 35.7), (45.6, 35.0), (45.4, 34.0), (46.1, 33.0), (47.4, 32.4), (47.7, 31.0),
        (48.0, 30.5), (48.5, 30), (47.9, 29.9), (47.0, 29.1), (44.7, 29.2), (42.0, 31.1), (39.2, 32.2)]
ISRAEL = [(34.3, 31.3), (34.9, 33.1), (35.6, 33.2), (35.5, 31.5), (35.0, 29.5), (34.3, 31.0)]

COL = {k: KC[k] for k in KC}
def _r(t0, t1, poly, kind, name=None, at=None, grow=None, size=56, strength=.36):
    return dict(t0=t0, t1=t1, poly=poly, col=COL[kind], name=name, at=at, grow=grow, size=size, s=strength)

REALMS = [
    _r(T('From around 3200'), T('The first of these') + 1, ELAM, 'elam', 'ELAM', (49.4, 31.6), size=40),
    _r(T('The first of these') + .5, T('took Ecbatana') + 1.5, MEDES, 'mede', 'MEDIA', (54.0, 36.4), grow=(C['Ecbatana'], 3, 30, T('The first of these') + .5, T('The Medes now') + 3)),
    _r(T('Cyrus of'), T('took Ecbatana') + 1.5, PERSIS, 'persian', 'PERSIS', (52.5, 29.6), size=36),
    _r(T('took Ecbatana'), T('Persepolis burned') + 1.2, ACH, 'persian', 'ACHAEMENID EMPIRE', (52.5, 33.5),
       grow=(C['Pasargadae'], 14, 48, T('took Ecbatana'), T('At its height') + 1.5), size=64),
    _r(T('Persepolis burned'), T('drove the Seleucids') + 2, SELEUCID, 'greek', 'SELEUCID EMPIRE', (50.5, 34.0), size=58),
    _r(T('Around 247'), CHT[4] + 4, PARTHIA, 'parthian', 'PARTHIAN EMPIRE', (54.0, 33.5), grow=(C['Merv'], 3, 30, T('Around 247'), T('built their capital') + 1), size=56),
    _r(CHT[3] + 1, T('By 628') + 2, ROME, 'roman', 'ROME', (31.5, 38.6), size=50),
    _r(T('In 224'), T('he was killed near Merv') + 1, SASAN, 'sasanian', 'SASANIAN EMPIRE', (54.0, 33.0), grow=(C['Persepolis'], 3, 30, T('In 224'), T('His son Shapur') + 1), size=58),
    _r(T('In 636') - 1, CHT[6] + 2, CALIPH, 'caliph', 'CALIPHATE', (43, 28), grow=(C['Medina'], 14, 42, T('In 636') - 1, T('he was killed near Merv') + 1), size=58),
    _r(T('The Tahirids'), T('Then came the Turks') + 1, TAHIR, 'turk', 'Tahirids', (59.5, 36.2), size=30),
    _r(T('The Saffarids'), T('Then came the Turks') + 1, SAFFAR, 'elam', 'Saffarids', (61.8, 30.3), size=30),
    _r(T('The Samanids'), T('Then came the Turks') + 1, SAMANID, 'caliph', 'Samanids', (64.5, 40.4), size=34),
    _r(T('And the Buyids'), T('Then came the Turks') + 1, BUYID, 'sasanian', 'Buyids', (50.5, 32.5), size=36),
    _r(T('Mahmud of Ghazni'), T('In 1055') + 1, GHAZNA, 'mughal', 'GHAZNAVIDS', (66, 32), size=44),
    _r(T('In 1040'), T('After them came') + 1, SELJUK, 'turk', 'SELJUK EMPIRE', (52, 35), grow=(C['Merv'], 3, 40, T('In 1040'), T('beat Byzantium') + 1), size=58),
    _r(T('After them came'), T('Hulagu founded') + 1, KHWAR, 'uzbek', 'KHWARAZMIAN EMPIRE', (58, 37), size=52),
    _r(T('Hulagu founded'), T('A century later') + 1.5, ILKHAN, 'mongol', 'ILKHANATE', (50, 35), size=60),
    _r(T('In the 1380s') - .5, T('After Timur') + 2, TIMURID, 'timurid', 'TIMURID EMPIRE', (58, 37), grow=(C['Samarkand'], 3, 36, T('A century later') + 1, T('When Isfahan')), size=56),
    _r(T('crowned Shah', I('Chapter nine')), T('By 1722') + 1, SAFAVID, 'safavid', 'SAFAVID IRAN', (53, 33), grow=(C['Tabriz'], 2, 26, T('crowned Shah', I('Chapter nine')), T('that still separate') + 1), size=58),
    _r(T('In 1514') - 1, CHT[9] + 1, OTTOMAN, 'ottoman', 'OTTOMAN EMPIRE', (35, 38.5), size=48),
    _r(T('Ottomans and the Uzbeks') - .5, CHT[9] + 1, UZBEK, 'uzbek', 'UZBEKS', (63.5, 41), size=36),
    _r(T('An Afghan army'), T('Iran was rescued') + 1, HOTAK, 'afghan', 'HOTAKS', (64.8, 32.2), size=36),
    _r(T('Iran was rescued'), T('in 1747') + 1.5, AFSHAR, 'afshar', 'AFSHARID IRAN', (55, 33), grow=(C['Mashhad'], 4, 30, T('Iran was rescued'), T('He returned home')), size=58),
    _r(T('After him, Karim'), CHT[10] + 2, IRANM, 'safavid', 'ZAND IRAN', (54, 31.5), size=48),
    _r(T('began to reunite'), CHT[11] + 2, IRANM, 'qajar', 'QAJAR IRAN', (55, 32.5), grow=(C['Tehran'], 2, 22, T('began to reunite'), T('crowned Shah', I('Chapter eleven')) + 1), size=56),
    _r(T('began to reunite') + 2, T('Iran lost') + 1.5, CAUC, 'qajar', None, None),
    _r(T('Iran lost'), CHT[11] + 2, CAUC, 'russia', 'RUSSIAN EMPIRE', (45.5, 41.3), size=36, strength=.5),
    _r(T('divided Iran into'), CHT[11] + 1, RUS_SPH, 'roman', 'RUSSIAN ZONE', (52, 35.5), size=40, strength=.55),
    _r(T('divided Iran into') + .6, CHT[11] + 1, BRI_SPH, 'britain', 'BRITISH ZONE', (60.0, 28.2), size=34, strength=.55),
    _r(CHT[11] + .5, EPI + 1, IRANM, 'iran', 'IRAN', (55, 32), size=60, strength=.30),
    _r(T('Then, on the twenty second') - .5, T('before a ceasefire') + 4, IRAQ, 'iraq', 'IRAQ', (43.5, 32.6), size=40),
    _r(CHT[13] + 1, T('Epilogue') - .5, ISRAEL, 'israel', 'ISRAEL', (34.0, 32.4), size=26, strength=.5),
]

# ------------------------------------------------------------------ arrows: (t0, t1, fade, pts(lon,lat), kind, w0, w1, dashed)
def _a(t0, t1, fade, names, kind, w0=12, w1=28, dashed=False):
    return (t0, t1, fade, [C[n] if isinstance(n, str) else n for n in names], kind, w0, w1, dashed)
INV0 = I('a land invaded'); INV1 = T('So when')
ARROWS = [
    _a(T('Greeks', INV0) - .2, T('Greeks', INV0) + 1.2, INV1, [(36, 38.5), (44, 36.5), (49, 34.5)], 'greek'),
    _a(T('Arabs', INV0) - .2, T('Arabs', INV0) + 1.2, INV1, [(42, 27), (46, 31), (50, 33.5)], 'caliph'),
    _a(T('Turks', INV0) - .2, T('Turks', INV0) + 1.2, INV1, [(66, 41.5), (60, 37.5), (55, 35)], 'turk'),
    _a(T('Mongols', INV0) - .2, T('Mongols', INV0) + 1.2, INV1, [(70, 44), (63, 39.5), (56.5, 36.5)], 'mongol'),
    _a(T('Afghans', INV0) - .2, T('Afghans', INV0) + 1.2, INV1, [(69, 32), (62, 32.3), (55.5, 32.5)], 'afghan'),
    _a(T('Russians', INV0) - .2, T('Russians', INV0) + 1.2, INV1, [(46, 45), (47.5, 41), (49, 38)], 'russia'),
    _a(T('British', INV0) - .2, T('British', INV0) + 1.2, INV1, [(57, 22.5), (53, 26), (51, 29.5)], 'britain'),
    _a(T('Americans', INV0) - .2, T('Americans', INV0) + 1.2, INV1, [(38, 30), (45, 31.5), (51, 34.5)], 'usa'),
    _a(T('new peoples arrived') - .2, T('the noble ones'), T('That word is') + 1, [(66, 42), (61, 38.5), (56, 35.5), (52, 34)], 'persian', 14, 32),
    _a(T('allied with Babylon'), T('destroyed Nineveh') + 1, T('The Medes now') + 1, ['Ecbatana', (46, 35.7), 'Nineveh'], 'mede'),
    _a(T('Persis defeated') - .3, T('took Ecbatana') + .8, T('Most historians') + 2, ['Pasargadae', (51, 32.5), 'Ecbatana'], 'persian', 14, 32),
    _a(T('marched west and'), T('taking Sardis') + .5, T('In 539') - .5, ['Ecbatana', (44, 37), (37, 38.2), (32, 38.7), 'Sardis'], 'persian', 14, 32),
    _a(T('His son Cambyses') - .2, T('added Egypt') + 1, T('Then came Darius') + 1, [(43, 33), (36, 31.5), (33, 30.8), 'Memphis'], 'persian', 14, 32),
    _a(T('built the Royal Road'), T('Susa, introduced') + .3, T('introduced a gold') + 1.5, ['Sardis', (33, 38.9), (38.5, 37.5), (43.5, 36.5), (45.5, 34), 'Susa'], 'persian', 8, 18, True),
    _a(T('At Marathon') - .3, T('490 BC'), T('480 BC') + 2.5, [(27, 38.6), (25, 38.3), 'Marathon'], 'persian'),
    _a(T('at Salamis') - .3, T('480 BC') + .3, T('were turned back') + 1.5, [(27.5, 39.6), (25.2, 39.0), (24.0, 38.2), 'Salamis'], 'persian'),
    _a(T('In 334'), T('crossed into Asia') + .5, T('Two hundred and twenty') , ['Pella', (25, 40.8), 'Granicus'], 'greek', 14, 32),
    _a(T('He won at'), T('333 BC'), T('Two hundred and twenty'), ['Granicus', (31, 39), (34.5, 37.3), 'Issus'], 'greek', 14, 32),
    _a(T('In 331'), T('Gaugamela, near') + .5, T('Two hundred and twenty'), ['Issus', (38.5, 36.4), (41.2, 36.8), 'Gaugamela'], 'greek', 14, 32),
    _a(T('Alexander took'), T('Persepolis burned'), T('Two hundred and twenty'), ['Gaugamela', (44.7, 34.2), 'Babylon', (47, 32.3), 'Susa', (51, 30.8), 'Persepolis'], 'greek', 14, 32),
    _a(T('Darius was murdered'), T('while fleeing east'), T('Two hundred and twenty') + 1, ['Ecbatana', (53, 35.6), (57.5, 36.4), (60.3, 36.6)], 'persian', 10, 22, True),
    _a(T('drove the Seleucids') - .5, T('and Mesopotamia') + .5, T('Their weapon') + 1, ['Merv', (55, 36.5), 'Ecbatana', 'Ctesiphon'], 'parthian', 14, 32),
    _a(T('destroyed a Roman') - .6, T('army of seven'), T('For nearly five') + 1, [(36.5, 36.3), (38, 36.6), 'Carrhae'], 'roman'),
    _a(T('humiliated Rome three'), T('In 260') + .3, T('Under Khosrow the First'), ['Ctesiphon', (41.5, 35.5), 'Edessa'], 'sasanian', 14, 32),
    _a(T('His armies took'), T('reached the walls'), T('By 628') + 1, ['Ctesiphon', (39.5, 34.8), (36.5, 33.2), 'Jerusalem', (33, 31.0), 'Alexandria'], 'sasanian', 14, 32),
    _a(T('reached the walls') - .4, T('of Constantinople') + .3, T('By 628') + 1, ['Ctesiphon', (40.5, 37), (35, 39), (31, 40.4), (29.4, 40.8)], 'sasanian', 14, 32),
    _a(T('emperor Heraclius'), T('them. By 628'), T('By 628') + 2, [(40, 41.3), (44, 40.2), (46, 37.5), (45.4, 34.6), (44.9, 33.5)], 'roman', 14, 32),
    _a(T('In 636') - .5, T('Muslim army under'), T('Ctesiphon fell') + 2, [(41.5, 28), (43, 30.5), 'Qadisiyyah'], 'caliph', 14, 32),
    _a(T('In 642'), T('Nahavand, the last'), T('The last Sasanian king') + 1, ['Ctesiphon', (46.5, 33.8), 'Nahavand'], 'caliph', 14, 32),
    _a(T('fled from city'), T('he was killed near Merv'), T('Iran became part') + 1, ['Ctesiphon', 'Nahavand', 'Isfahan', (54.5, 32), (57, 34), (59.5, 36), 'Merv'], 'sasanian', 10, 22, True),
    _a(T('Abbasid revolution'), T('launched from Khorasan') + .5, T('The Persian language') + 1, ['Merv', 'Nishapur', (53, 35.5), 'Hamadan', 'Baghdad'], 'abbasid', 14, 30),
    _a(T('marched into Baghdad'), T('ruled the caliph'), T('Then came the Turks') + .5, ['Isfahan', (48.5, 33.6), 'Baghdad'], 'sasanian', 12, 28),
    _a(T('raiding deep into'), T('seventeen times'), T('In 1040') + .5, ['Ghazni', (71, 33.5), (74, 31.5), (76.5, 29.5)], 'mughal', 12, 28),
    _a(T('In 1055') - .5, T('Baghdad as sultan'), T('The Seljuks ruled') + 2, ['Merv', 'Nishapur', (53, 35.6), 'Hamadan', 'Baghdad'], 'turk', 14, 32),
    _a(T('beat Byzantium at'), T('in 1071'), T('their great Persian') + 1, ['Tabriz', (43.5, 39), 'Manzikert'], 'turk'),
    _a(T('Mongol armies stormed'), T('and Samarkand') + .4, T('Hulagu founded'), [(72, 45.5), 'Otrar', 'Bukhara', 'Samarkand'], 'mongol', 16, 34),
    _a(T('1221 Merv'), T('Nishapur were annihilated'), T('Hulagu founded'), ['Bukhara', (63, 38.6), 'Merv', 'Nishapur'], 'mongol', 16, 34),
    _a(T('destroyed the fortress'), T('of Alamut') + .3, T('Hulagu founded'), ['Nishapur', (54.5, 36.6), 'Alamut'], 'mongol', 14, 32),
    _a(T('In the 1380s'), T('and Shiraz') + .4, T('After Timur') + 1, ['Samarkand', (64, 37.5), 'Herat', (56, 35.5), (50, 37.5), 'Tabriz'], 'timurid', 14, 32),
    _a(T('took Herat') + .6, T('and Shiraz') + .6, T('After Timur') + 1, ['Herat', (57.5, 32), (54.5, 30.2), 'Shiraz'], 'timurid', 12, 28),
    _a(T('entered Tabriz with') - .4, T('his Qizilbash warriors'), T('He made Twelver') + 2, [(44.5, 39.6), (45.5, 38.8), 'Tabriz'], 'safavid'),
    _a(T('In 1514') - .3, T('Chaldiran, Ottoman'), T('and for a century') + 1, [(40, 39.5), (42.5, 39.3), 'Chaldiran'], 'ottoman', 14, 32),
    _a(T('and took Tabriz', I('Chaldiran')), T('and for a century') - .2, T('fought for its life') + 1, ['Chaldiran', (45.2, 38.6), 'Tabriz'], 'ottoman'),
    _a(T('retook Tabriz and'), T('and Baghdad,') + .4, T('in 1622') + .5, ['Isfahan', (48.5, 34.5), 'Baghdad'], 'safavid'),
    _a(T('expelled the Portuguese') - .3, T('from Hormuz') + .3, T('He made Isfahan') + .5, ['Shiraz', (55, 28.2), 'Hormuz'], 'safavid'),
    _a(T('An Afghan army'), T('Hotak defeated'), T('Iran was rescued') + .5, ['Kandahar', (61, 31.5), 'Kerman', (54.5, 32), 'Isfahan'], 'afghan', 14, 32),
    _a(T('He drove out') - .2, T('the Afghans,') + .5, T('Then he turned east'), ['Mashhad', (55.5, 34), 'Isfahan'], 'afshar', 14, 32),
    _a(T('Then he turned east'), T('entered Delhi') + .3, T('He returned home') + 2, ['Isfahan', 'Kandahar', (68.8, 33.6), (71.6, 33.9), (74.5, 31.6), 'Karnal', 'Delhi'], 'afshar', 16, 34),
    _a(T('In two wars Russia'), T('defeated Iran') + .3, T('By the treaties') + 3, [(45, 44.5), 'Tiflis', (46.5, 40.2), (47.5, 39)], 'russia', 14, 32),
    _a(T('Britain landed troops'), T('in the Persian Gulf') + .5, T('Iran was never colonised'), [(54, 23.5), (52, 27), 'Bushehr'], 'britain', 14, 32),
    _a(T('marched on Tehran'), T('Cossack brigade') + .5, T('In 1925'), [(49.5, 37.5), (50.3, 36.5), 'Tehran'], 'iran'),
    _a(T('British and Soviet'), T('armies invaded'), T('Reza Shah was forced') + 1, [(46, 41.8), (47, 39.5), 'Tabriz', (49.5, 36.5)], 'russia', 14, 32),
    _a(T('British and Soviet') + .3, T('armies invaded') + .3, T('Reza Shah was forced') + 1, ['Basra', 'Abadan', 'Ahvaz'], 'britain', 14, 32),
    _a(T('British and Soviet') + .6, T('armies invaded') + .6, T('Reza Shah was forced') + 1, [(45, 33.4), 'Qasr_e_Shirin', (47.5, 34.3)], 'britain', 12, 28),
    _a(T('invaded. The war'), T('The war lasted'), T('before a ceasefire') + 2, ['Basra', (48.2, 30.75), (48.8, 31.1)], 'iraq', 14, 32),
    _a(T('invaded. The war') + .2, T('The war lasted') + .2, T('before a ceasefire') + 2, [(46.6, 32.5), 'Dezful'], 'iraq', 14, 32),
    _a(T('invaded. The war') + .4, T('The war lasted') + .4, T('before a ceasefire') + 2, [(45, 34.2), 'Qasr_e_Shirin', (46.4, 34.4)], 'iraq', 14, 32),
    _a(T('Iraqi missiles fell'), T('on Tehran') + .3, T('It brought trench') + 1.5, ['Baghdad', (47.5, 35.2), 'Tehran'], 'iraq', 6, 16),
    _a(T('after Israel struck'), T('Iran, American bombers'), T('Then, on the twenty eighth'), ['Tel_Aviv', (42, 35), (48, 35.3), 'Natanz'], 'israel', 6, 16),
    _a(T('American bombers hit'), T('of Fordow'), T('Then, on the twenty eighth'), [(44, 31.5), (48, 33.8), 'Fordow'], 'usa', 7, 18),
    _a(T('American bombers hit') + .3, T('Natanz and'), T('Then, on the twenty eighth'), [(44.5, 31.2), (48.5, 33), 'Natanz'], 'usa', 7, 18),
    _a(T('American bombers hit') + .6, T('and Isfahan', I('Fordow')), T('Then, on the twenty eighth'), [(45, 30.9), (48.8, 32.2), 'Isfahan'], 'usa', 7, 18),
    _a(T('launched a joint war'), T('Operation Epic Fury'), T('Iran answered') + 1, ['Tel_Aviv', (42, 35.5), (48, 35.8), 'Tehran'], 'israel', 7, 18),
    _a(T('launched a joint war') + .4, T('Operation Epic Fury') + .4, T('Iran answered') + 1, [(54, 22.5), (55, 28.5), 'Tehran'], 'usa', 7, 18),
    _a(T('Iran answered'), T('drones against Israel'), T('and closed the Strait'), ['Tehran', (45, 35.5), (38, 33.4), 'Tel_Aviv'], 'iran', 6, 16),
    _a(T('and American bases') - .2, T('across the Gulf'), T('and closed the Strait') + .5, ['Isfahan', (51, 28), 'Al_Udeid'], 'iran', 6, 16),
    _a(T('and American bases'), T('across the Gulf') + .3, T('and closed the Strait') + .5, ['Shiraz', (51.5, 27.5), 'Bahrain'], 'iran', 6, 16),
    _a(T('and American bases') + .2, T('across the Gulf') + .6, T('and closed the Strait') + .5, ['Ahvaz', 'Kuwait'], 'iran', 6, 16),
    _a(T('struck air defences'), T('the island of Qeshm'), T('the war that began') + 1, [(58.5, 24.0), (57, 25.8), 'Qeshm'], 'usa', 6, 16),
]

# ------------------------------------------------------------------ marks
RIPPLES = [(T('destroyed Nineveh'), T('The Medes now'), 'Nineveh'), (T('took Ecbatana') - .2, T('Most historians') + 1, 'Ecbatana'),
           (T('taking Sardis'), T('In 539') - .4, 'Sardis'), (T('Persepolis burned') - .2, T('Darius was murdered'), 'Persepolis'),
           (T('killed the triumvir'), T('For nearly five'), 'Carrhae'), (T('near Edessa'), T('carved the scene'), 'Edessa'),
           (T('Ctesiphon fell'), T('In 642'), 'Ctesiphon'), (T('he was killed near Merv'), T('Iran became part'), 'Merv'),
           (T('in 1218'), T('Chapter eight'), 'Otrar'), (T('Nishapur were annihilated'), T('In 1256 Hulagu'), 'Nishapur'),
           (T('of Alamut'), T('and in 1258'), 'Alamut'), (T('rebelled in 1387'), T('After Timur'), 'Isfahan'),
           (T('entered Delhi'), T('He returned home'), 'Delhi'), (T('murdered him in his tent'), T('After him, Karim'), 'Mashhad'),
           (T('He made Tehran'), T('But a new kind'), 'Tehran'), (T('In 1906'), T('year later Britain'), 'Tehran'),
           (T('nationalised the oil'), T('Two years later'), 'Abadan'), (T('a coup backed'), T('The Shah returned'), 'Tehran'),
           (T('the Shah left'), T('In November, students'), 'Tehran'), (T('Cities like Khorramshahr'), T('the Cities, Iraqi'), 'Khorramshahr')]
MODERN_HITS = [(T('strike Tehran'), T('Between these') + .5, 'Tehran'), (T('Iraqi missiles fell') + 1.3, T('It brought trench') + 1, 'Tehran'),
               (T('of Fordow') + .2, T('Then, on the twenty eighth'), 'Fordow'), (T('Natanz and') + .2, T('Then, on the twenty eighth'), 'Natanz'),
               (T('and Isfahan', I('Fordow')) + .3, T('Then, on the twenty eighth'), 'Isfahan'), (T('The opening strikes'), T('Iran answered'), 'Tehran'),
               (T('drones against Israel') + .3, T('and closed the Strait'), 'Tel_Aviv'), (T('across the Gulf') + .2, T('and closed the Strait') + .5, 'Al_Udeid'),
               (T('across the Gulf') + .4, T('and closed the Strait') + .5, 'Bahrain'), (T('the island of Qeshm'), T('the war that began') + 1, 'Qeshm')]

PILLS = [
    (T('In 612'), T('The Medes now'), 'Fall of Nineveh', '612 BC', 'mede', 'elam'),
    (T('In 550'), T('Most historians') + 2, 'Cyrus takes Ecbatana', '550 BC', 'persian', 'mede'),
    (T('In 547'), T('In 539') - .4, 'Fall of Sardis', '547 BC', 'persian', 'elam'),
    (T('At Marathon'), T('480 BC') - .2, 'Battle of Marathon', '490 BC', 'greek', 'persian'),
    (T('at Salamis'), T('Persia remained'), 'Battle of Salamis', '480 BC', 'greek', 'persian'),
    (T('He won at') + .3, T('then at Issus'), 'Battle of the Granicus', '334 BC', 'greek', 'persian'),
    (T('In 331'), T('Alexander took'), 'Battle of Gaugamela', '1 October 331 BC', 'greek', 'persian'),
    (T('In 53 BC'), T('For nearly five'), 'Battle of Carrhae', '53 BC', 'parthian', 'roman'),
    (T('In 224'), T('He took the title'), 'Battle of Hormozgan', '224 AD', 'sasanian', 'parthian'),
    (T('In 260'), T('carved the scene'), 'Battle of Edessa', '260 AD', 'sasanian', 'roman'),
    (T('fought a twenty six'), T('By 628'), 'Byzantine-Sasanian War', '602-628', 'sasanian', 'roman'),
    (T('In 636'), T('Ctesiphon fell'), 'Battle of al-Qadisiyyah', '636 AD', 'caliph', 'sasanian'),
    (T('In 642'), T('The last Sasanian king'), 'Battle of Nahavand', '642 AD', 'caliph', 'sasanian'),
    (T('In 1040'), T('and in 1055'), 'Battle of Dandanaqan', '1040', 'turk', 'mughal'),
    (T('beat Byzantium at'), T('their great Persian'), 'Battle of Manzikert', '1071', 'turk', 'roman'),
    (T('In 1218'), T('Chapter eight'), 'Otrar Massacre', '1218', 'uzbek', 'mongol'),
    (T('rebelled in 1387'), T('After Timur'), 'Isfahan Massacre', '1387', 'timurid', 'timurid'),
    (T('In 1514'), T('and for a century'), 'Battle of Chaldiran', '23 August 1514', 'ottoman', 'safavid'),
    (T('in 1622'), T('He made Isfahan'), 'Capture of Hormuz', '1622', 'safavid', 'portugal'),
    (T('In 1739'), T('He returned home'), 'Battle of Karnal', '24 February 1739', 'afshar', 'mughal'),
    (T('By the treaties'), T('When Iran tried'), 'Gulistan 1813 · Turkmenchay 1828', 'Treaties with Russia', 'russia', 'qajar'),
    (T('When Iran tried'), T('Iran was never colonised'), 'Anglo-Persian War', '1856-1857', 'britain', 'qajar'),
    (T('In 1906'), T('year later Britain'), 'Constitutional Revolution', '1906', 'iran', 'qajar'),
    (T('year later Britain'), CHT[11], 'Anglo-Russian Convention', '1907', 'britain', 'russia'),
    (T('But in 1941'), T('Reza Shah was forced'), 'Anglo-Soviet Invasion', 'August 1941', 'britain', 'iran'),
    (T('Two years later'), T('The Shah returned'), '1953 Coup', 'August 1953', 'usa', 'iran'),
    (T('In January 1979'), T('In November, students'), 'Iranian Revolution', '1979', 'iran', 'iran'),
    (T('In November, students'), T('Then, on the twenty second'), 'Hostage Crisis', '444 days, 1979-1981', 'iran', 'usa'),
    (T('Then, on the twenty second'), T('before a ceasefire'), 'Iran-Iraq War', '1980-1988', 'iraq', 'iran'),
    (T('2025, after Israel'), T('Then, on the twenty eighth'), 'Twelve-Day War', 'June 2025', 'usa', 'iran'),
    (T('Then, on the twenty eighth'), T('The opening strikes') + 2, 'Operation Epic Fury', '28 February 2026', 'usa', 'iran'),
    (T('and closed the Strait'), T('On the eighth of March'), 'Strait of Hormuz closed', '2026', 'iran', 'usa'),
    (T('In April, Pakistan'), T('The talks ended'), 'Islamabad Talks', 'April 2026', 'pakistan', 'pakistan'),
    (T('In November 2026'), T('the war that began') + 2, 'Strikes on Qeshm', 'November 2026', 'usa', 'iran'),
]

class Med2:
    def __init__(self, make): self.v = {False: make(False), True: make(True)}
    def draw(self, fr, pos, t, t0, t1, target=None, flip=True): self.v[flip].draw(fr, pos, t, t0, t1, target=target)
def M(f, name, title, kind, crop, fallen=False): return Med2(lambda fl: Medallion('iran/' + f, name, title, kind, D=230, flip=fl, fallen=fallen, crop=crop))
def NM(name, title, kind): return Med2(lambda fl: NoorMedallion(name, title, kind, D=230, flip=fl))
MED = [  # (medallion, t0, t1, pos, target town)
    (M('cyrus.jpg', 'Cyrus the Great', 'Imagined portrait, 1553', 'persian', (0.18, 0.06, 0.78, 0.66)), T('Cyrus the Great') + .3, T('Most historians') + 2, 'Pasargadae'),
    (M('darius.jpg', 'Darius I', 'King of Kings, 522-486 BC', 'persian', (0.02, 0.12, 0.72, 0.58)), T('Then came Darius'), T('built the Royal Road'), 'Persepolis'),
    (M('darius3.jpg', 'Darius III', 'Last Achaemenid king', 'persian', (0.48, 0.06, 0.9, 0.46)), T('where Darius the'), T('In 331') + 3, 'Issus'),
    (M('crassus.jpg', 'Marcus Crassus', 'Killed at Carrhae, 53 BC', 'roman', (0.33, 0.02, 0.67, 0.53), fallen=True), T('killed the triumvir') - .4, T('For nearly five') + 1, 'Carrhae'),
    (M('genghis.jpg', 'Genghis Khan', 'Great Khan, 1206-1227', 'mongol', (0.2, 0.18, 0.8, 0.65)), T('sent by Genghis'), T('1221 Merv'), 'Otrar'),
    (M('hulagu.jpg', 'Hulagu Khan', 'Founder of the Ilkhanate', 'mongol', (0.25, 0.03, 0.85, 0.40)), T('In 1256 Hulagu'), T('and in 1258') - .4, 'Alamut'),
    (M('hulagu.jpg', 'Hulagu Khan', 'Founder of the Ilkhanate', 'mongol', (0.25, 0.03, 0.85, 0.40)), T('Hulagu founded'), T('his descendant Ghazan'), 'Tabriz'),
    (M('timur.jpg', 'Timur', 'Tamerlane, r. 1370-1405', 'timurid', (0.12, 0.18, 0.88, 0.76)), T('new conqueror, Timur'), T('When Isfahan'), 'Samarkand'),
    (M('abbas.jpg', 'Shah Abbas I', 'Shah of Iran, 1588-1629', 'safavid', (0.08, 0.14, 0.78, 0.66)), T('Then came Shah Abbas'), T('in 1622'), 'Isfahan'),
    (M('nader.jpg', 'Nader Shah', 'Shah of Iran, 1736-1747', 'afshar', (0.15, 0.2, 0.85, 0.78)), T('Nader of the Afshar'), T('In 1739'), 'Mashhad'),
    (M('nader.jpg', 'Nader Shah', 'Shah of Iran, 1736-1747', 'afshar', (0.15, 0.2, 0.85, 0.78)), T('Historians have called'), T('After him, Karim'), 'Mashhad'),
    (M('reza_shah.jpg', 'Reza Shah', 'Shah of Iran, 1925-1941', 'iran', (0.30, 0.08, 0.75, 0.41)), T('Reza Khan marched'), T('But in 1941'), 'Tehran'),
    (M('mreza_shah.jpg', 'Mohammad Reza Shah', 'Shah of Iran, 1941-1979', 'iran', (0.22, 0.04, 0.78, 0.41)), T('Mohammad Reza. In'), T('In 1951'), 'Tehran'),
    (M('mosaddegh.jpg', 'Mohammad Mosaddegh', 'Prime Minister, 1951-1953', 'iran', (0.25, 0.1, 0.8, 0.51)), T('Prime Minister Mohammad'), T('The Shah returned'), 'Tehran'),
    (NM("Sa'd ibn Abi Waqqas", 'Commander at Qadisiyyah, 636', 'caliph'), T('Muslim army under'), T('Ctesiphon fell'), 'Qadisiyyah'),
    (NM('Shah Ismail I', 'Founder of Safavid Iran, 1501', 'safavid'), T('a fourteen year'), T('Many historians see'), 'Tabriz'),
    (NM('Ruhollah Khomeini', 'Supreme Leader, 1979-1989', 'iran'), T('Ayatollah Ruhollah Khomeini'), T('In November, students'), 'Tehran'),
    (NM('Ali Khamenei', 'Supreme Leader, 1989-2026', 'iran'), T("Iran's Supreme Leader"), T('Iran answered'), 'Tehran'),
    (NM('Mojtaba Khamenei', 'Supreme Leader from March 2026', 'iran'), T('his son, Mojtaba'), T('In April, Pakistan'), 'Tehran'),
]

# town labels: (t0, t1, name, size)
def _L(t0, t1, *names, size=34): return [(t0, t1, n, size) for n in names]
LABELS = (_L(0, T('Between these') + .5, 'Tehran', size=40)
          + _L(T('From around 3200'), T('The first of these'), 'Susa') + _L(T('with Sumer and'), CHT[1], 'Babylon')
          + _L(T('The first of these'), CHT[1] + 1, 'Ecbatana') + _L(T('In 612'), T('But their own'), 'Nineveh')
          + _L(CHT[1], T('In 547'), 'Pasargadae') + _L(T('In 547'), T('Then came Darius') + 1, 'Sardis')
          + _L(T('His son Cambyses'), T('Then came Darius'), 'Memphis') + _L(T('built the Royal Road'), T('introduced a gold') + 1, 'Sardis', 'Susa')
          + _L(T('introduced a gold'), T('At its height'), 'Persepolis') + _L(T('Only the Greeks'), T('Persia remained'), 'Athens')
          + _L(CHT[2], T('He won at'), 'Pella') + _L(T('He won at'), T('In 331'), 'Granicus', 'Issus') + _L(T('In 331'), T('Darius was murdered'), 'Gaugamela', 'Babylon', 'Susa', 'Persepolis')
          + _L(T('built their capital'), CHT[6], 'Ctesiphon') + _L(T('In 53 BC'), T('For nearly five'), 'Carrhae') + _L(T('In 260'), T('Under Khosrow the First'), 'Edessa')
          + _L(T('His armies took'), T('By 628') + 1, 'Jerusalem', 'Alexandria', 'Constantinople') + _L(T('In 636'), T('Ctesiphon fell'), 'Qadisiyyah')
          + _L(T('In 642'), T('The last Sasanian king'), 'Nahavand') + _L(T('The last Sasanian king'), T('Iran became part'), 'Merv', 'Isfahan')
          + _L(T('The Samanids'), T('And the Buyids'), 'Bukhara') + _L(T('And the Buyids'), T('Then came the Turks'), 'Baghdad') + _L(T('Then came the Turks'), T('In 1040'), 'Ghazni')
          + _L(T('In 1040'), T('The Seljuks ruled'), 'Merv') + _L(T('The Seljuks ruled'), T('their great Persian'), 'Isfahan', 'Baghdad', 'Manzikert')
          + _L(T('In 1218'), T('1221 Merv'), 'Otrar', 'Bukhara', 'Samarkand') + _L(T('1221 Merv'), T('In 1256 Hulagu'), 'Merv', 'Nishapur')
          + _L(T('In 1256 Hulagu'), T('and in 1258'), 'Alamut') + _L(T('Hulagu founded'), T('A century later'), 'Tabriz', 'Baghdad')
          + _L(T('A century later'), T('After Timur'), 'Samarkand', 'Herat', 'Tabriz', 'Shiraz', 'Isfahan')
          + _L(CHT[8], T('He made Twelver'), 'Tabriz') + _L(T('In 1514'), T('and for a century'), 'Chaldiran', 'Tabriz')
          + _L(T('Then came Shah Abbas'), CHT[9], 'Isfahan') + _L(T('in 1622'), T('He made Isfahan'), 'Hormuz')
          + _L(T('An Afghan army'), T('Iran was rescued'), 'Kandahar', 'Isfahan') + _L(T('Iran was rescued'), T('In 1739'), 'Mashhad', 'Isfahan')
          + _L(T('In 1739'), T('He returned home'), 'Delhi', 'Karnal') + _L(T('Karim'), CHT[10], 'Shiraz')
          + _L(T('He made Tehran'), CHT[11] + 1, 'Tehran', size=38) + _L(T('By the treaties'), T('When Iran tried'), 'Tiflis')
          + _L(T('When Iran tried'), T('Iran was never colonised'), 'Herat', 'Bushehr') + _L(CHT[11], EPI, 'Tehran', size=38)
          + _L(T('In 1951'), T('Two years later'), 'Abadan') + _L(T('Then, on the twenty second'), T('before a ceasefire') + 2, 'Baghdad', 'Khorramshahr')
          + _L(T('2025, after Israel'), T('Then, on the twenty eighth'), 'Fordow', 'Natanz', 'Isfahan')
          + _L(T('Iran answered'), T('and closed the Strait'), 'Tel_Aviv') + _L(T('and closed the Strait'), T('the war that began'), 'Hormuz', 'Qeshm')
          + _L(T('In April, Pakistan'), T('The talks ended'), 'Islamabad') + _L(T('Plutarch records') - .5, END, 'Pasargadae', size=40))

YEARS = [(0, '330 BC'), (T('Nearly two'), '2026'), (T('From around 3200'), '3200 BC'), (T('Then, late'), '1500 BC'), (T('In 612'), '612 BC'),
         (CHT[1], '550 BC'), (T('In 547'), '547 BC'), (T('In 539'), '539 BC'), (T('His son Cambyses'), '525 BC'), (T('Then came Darius'), '522 BC'),
         (T('At Marathon'), '490 BC'), (T('at Salamis'), '480 BC'), (CHT[2], '334 BC'), (T('then at Issus'), '333 BC'), (T('In 331'), '331 BC'),
         (T('Persepolis burned'), '330 BC'), (T('When Alexander died'), '323 BC'), (CHT[3], '247 BC'), (T('In 53 BC'), '53 BC'), (CHT[4], '224 AD'),
         (T('In 260'), '260 AD'), (T('Under Khosrow the First'), '531 AD'), (T('But his grandson'), '602 AD'), (T('By 628'), '628 AD'),
         (CHT[5], '636 AD'), (T('In 642'), '642 AD'), (T('until in 651'), '651 AD'), (T('Abbasid revolution'), '750'), (T('around 1010'), '1010'),
         (CHT[6], '821'), (T('And the Buyids'), '945'), (T('Then came the Turks'), '1000'), (T('In 1040'), '1040'), (T('In 1055'), '1055'),
         (T('beat Byzantium'), '1071'), (T('After them came'), '1200'), (T('In 1218'), '1218'), (CHT[7], '1219'), (T('1221 Merv'), '1221'),
         (T('In 1256 Hulagu'), '1256'), (T('and in 1258'), '1258'), (T('in 1295'), '1295'), (T('In the 1380s'), '1380s'), (T('rebelled in 1387'), '1387'),
         (T('After Timur'), '1410'), (CHT[8], '1501'), (T('In 1514'), '1514'), (T('Then came Shah Abbas'), '1588'), (T('in 1622'), '1622'),
         (CHT[9], '1722'), (T('in 1736'), '1736'), (T('In 1739'), '1739'), (T('in 1747'), '1747'), (CHT[10], '1789'), (T('in 1796'), '1796'),
         (T('By the treaties'), '1813'), (T('Turkmenchay in 1828'), '1828'), (T('When Iran tried'), '1857'), (T('In 1906'), '1906'), (T('year later Britain'), '1907'),
         (CHT[11], '1921'), (T('In 1925'), '1925'), (T('And in 1935'), '1935'), (T('But in 1941'), '1941'), (T('In 1951'), '1951'), (T('Two years later'), '1953'),
         (CHT[12], '1979'), (T('Then, on the twenty second'), '1980'), (T('before a ceasefire'), '1988'), (CHT[13], '1990s'), (T('2025, after Israel'), '2025'),
         (T('Then, on the twenty eighth'), '2026'), (EPI, 'Today'), (T('Plutarch records'), '530 BC')]

def year_at(t):
    y = YEARS[0][1]
    for t0, s in YEARS:
        if t >= t0: y = s
    return y

# ------------------------------------------------------------------ era styles
STY = [(0, 'modern'), (T('Between these'), 'medieval'), (CHT[0], 'ancient'), (CHT[6], 'medieval'), (CHT[8], 'safavid'), (CHT[10], 'qajar'),
       (CHT[11], 'pahlavi'), (CHT[12], 'modern'), (EPI, 'medieval'), (T('Plutarch records') - .5, 'ancient')]
XS = 1.6  # style dissolve length
def style_at(t):
    a = STY[0][1]
    for i, (t0, s) in enumerate(STY):
        if t >= t0 + XS: a = s
        elif t >= t0: return STY[i - 1][1] if i else s, s, smooth(prog(t, t0, t0 + XS))
    return a, a, 1.0

def _sty(t): A, B, f = style_at(t); return B if f >= .5 else A

def town(fr, sc, name, a, style, size=34):
    lon, lat = C[name]; x, y = sc(lon, lat)
    if not (-100 < x < W_ + 100 and -60 < y < H + 60): return
    lay = Image.new('RGBA', (W_, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    dc = {'modern': (110, 230, 250), 'pahlavi': (200, 30, 40), 'qajar': (20, 20, 20), 'safavid': (150, 30, 24), 'ancient': (90, 40, 16)}.get(style, (30, 22, 20))
    r = 7
    d.ellipse([x - r - 3, y - r - 3, x + r + 3, y + r + 3], fill=(250, 246, 236, int(230 * a)))
    d.ellipse([x - r, y - r, x + r, y + r], fill=dc + (int(255 * a),))
    ST.label(d, (x, y - 16), name.replace('_', ' ').replace('Qasr e', 'Qasr-e'), style, size, anchor='md', alpha=a)
    fr.alpha_composite(lay)

def realm_label(fr, sc, text, pos, size, a, style):
    x, y = sc(*pos)
    if not (-300 < x < W_ + 300): return
    font, col = ST.REALM[style]
    lay = Image.new('RGBA', (W_, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    s = ' '.join(text) if text.isupper() and len(text) < 14 else text
    d.text((x, y), s, font=ST.F(font, size), fill=col[:3] + (int(col[3] * a),), anchor='mm',
           stroke_width=2, stroke_fill=(250, 246, 236, int(120 * a)) if style not in ('modern', 'medieval') else (10, 10, 14, int(140 * a)))
    fr.alpha_composite(lay)

def missile_hit(fr, pos, t, t0, t1):
    a = life(t, t0, t1, .15, .5)
    if a <= 0: return
    k = prog(t, t0, t0 + .7)
    def fn(d, S):
        for i in range(3):
            ph = ((t - t0) * .8 + i / 3) % 1; r = 20 + 70 * ph
            d.ellipse([S((pos[0] - r, pos[1] - r)), S((pos[0] + r, pos[1] + r))], outline=(255, 120, 60, int(220 * a * (1 - ph))), width=int(4 * Z))
        L = 34; g = 14
        for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):  # HUD target brackets
            cx, cy = pos[0] + sx * L, pos[1] + sy * L
            d.line([S((cx, cy)), S((cx - sx * g, cy)), ], fill=(110, 230, 250, int(255 * a)), width=int(3 * Z))
            d.line([S((cx, cy)), S((cx, cy - sy * g))], fill=(110, 230, 250, int(255 * a)), width=int(3 * Z))
        rr = 18 * (1 - k) + 6
        d.ellipse([S((pos[0] - rr, pos[1] - rr)), S((pos[0] + rr, pos[1] + rr))], fill=(255, 230, 160, int(255 * a * (1 - k * .6))))
    local_draw(fr, (pos[0] - 110, pos[1] - 110, pos[0] + 110, pos[1] + 110), fn)
    flame(fr, (pos[0], pos[1] + 4), t, a * smooth(prog(t, t0 + .2, t0 + .6)), .8)

def hatch(fr, sc, poly, t, t0, t1, col=(200, 30, 30)):
    """diagonal danger hatching (blockade / closed strait)"""
    a = life(t, t0, t1, .5, .5)
    if a <= 0: return
    m = Image.new('L', (W_, H), 0); ImageDraw.Draw(m).polygon([sc(*p) for p in poly], fill=int(150 * a))
    lines = Image.new('L', (W_, H), 0); dl = ImageDraw.Draw(lines)
    for x in range(-H, W_, 26): dl.line([(x, H), (x + H, 0)], fill=255, width=7)
    al = Image.fromarray((np.asarray(m, np.float32) * np.asarray(lines, np.float32) / 255).astype(np.uint8))
    lay = Image.new('RGBA', (W_, H), col + (0,)); lay.putalpha(al); fr.alpha_composite(lay)
HORMUZ = [(55.6, 26.0), (56.8, 27.4), (57.3, 26.9), (56.9, 25.6), (56.2, 25.2)]
GULF_COAST = [(48.5, 30.2), (50.5, 28.3), (52.5, 27.0), (55, 26.4), (57.5, 25.5), (59, 25.0), (59, 24.2), (57, 24.6), (54.8, 25.6), (52.3, 26.2), (50.0, 27.6), (48.2, 29.6)]

HATCH = [(T('and closed the Strait'), T('On the eighth of March'), HORMUZ, (200, 30, 30)),
         (T('blockaded Irans') - .2, T('A memorandum signed') + 1, GULF_COAST, (40, 80, 200)),
         (T('collapsed in the Strait') - .3, T('In November 2026') + .5, HORMUZ, (200, 30, 30))]
TQ0, TQ1, TPL = T('O man') - .6, T('Twenty five centuries') - .2, T('Plutarch records')
TC = dict(sw=T('So when'), wr=T('Which rulers'), lb=T('Let us begin'), e28=T('Then, on the twenty eighth'), wf=T('When was Iran founded'))


def title_card(fr, t):
    a = life(t, TC['sw'], CHT[0] - .2, .6, .5)
    if a <= 0: return
    g = Image.new('RGBA', (W_, H), (8, 6, 4, int(120 * a))); fr.alpha_composite(g)
    lay = Image.new('RGBA', (W_, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    k = ease_out(prog(t, TC['sw'], TC['sw'] + 1.2))
    d.text((W_ / 2, 440 + 20 * (1 - k)), 'I  R  A  N', font=ST.F('Cinzel.ttf', 168), fill=(246, 230, 196, int(255 * a)), anchor='mm', stroke_width=4, stroke_fill=(40, 24, 10, int(220 * a)))
    a2 = a * smooth(prog(t, TC['wr'], TC['wr'] + .6))
    d.text((W_ / 2, 570), 'Founders · Conquerors · Governments', font=ST.F('EBGaramond-Italic.ttf', 54), fill=(236, 220, 190, int(255 * a2)), anchor='mm', stroke_width=2, stroke_fill=(20, 12, 6, int(200 * a2)))
    a3 = a * smooth(prog(t, TC['lb'], TC['lb'] + .6))
    d.text((W_ / 2, 650), '550 BC  -  2026', font=ST.F('Cinzel.ttf', 44), fill=(214, 190, 140, int(255 * a3)), anchor='mm')
    fr.alpha_composite(lay)

def ongoing_tag(fr, t):
    a = life(t, TC['e28'], EPI, .5, .5)
    if a <= 0: return
    lay = Image.new('RGBA', (W_, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    blink = .65 + .35 * math.sin(t * 4)
    d.rounded_rectangle([48, 950, 700, 1010], radius=8, fill=(10, 18, 26, int(200 * a)), outline=(240, 70, 60, int(255 * a)), width=2)
    d.ellipse([66, 968, 90, 992], fill=(240, 60, 50, int(255 * a * blink)))
    d.text((104, 980), 'ONGOING CONFLICT · REPORTS STILL DEVELOPING', font=ST.F('RobotoCondensed.ttf', 26), fill=(230, 240, 246, int(255 * a)), anchor='lm')
    fr.alpha_composite(lay)

DYN = ['Medes', 'Achaemenids', 'Seleucids', 'Parthians', 'Sasanians', 'Caliphs', 'Tahirids', 'Saffarids', 'Samanids', 'Buyids', 'Ghaznavids', 'Seljuks',
       'Khwarazmshahs', 'Ilkhans', 'Timurids', 'Turkmen', 'Safavids', 'Hotaks', 'Afsharids', 'Zands', 'Qajars', 'Pahlavis', 'Islamic Republic']
DKIND = ['mede', 'persian', 'greek', 'parthian', 'sasanian', 'caliph', 'turk', 'elam', 'caliph', 'sasanian', 'mughal', 'turk', 'uzbek', 'mongol', 'timurid',
         'turk', 'safavid', 'afghan', 'afshar', 'safavid', 'qajar', 'iran', 'iran']
_d0 = I('twenty Medes Achaemenids') + 1
DT = []
_j = _d0
for nm in DYN:
    i = I(nm.split()[0], _j); DT.append(W(i)); _j = i + 1
def dynasty_roll(fr, t):
    a = life(t, DT[0] - .6, TC['wf'] + .2, .5, .5)
    if a <= 0: return
    lay = Image.new('RGBA', (W_, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([960, 120, 1860, 960], radius=24, fill=(18, 14, 12, int(200 * a)), outline=(214, 172, 70, int(220 * a)), width=3)
    d.text((1410, 180), 'Ruling houses of Iran', font=ST.F('Cinzel.ttf', 44), fill=(240, 222, 180, int(255 * a)), anchor='mm')
    for n, (nm, kd, t0) in enumerate(zip(DYN, DKIND, DT)):
        k = smooth(prog(t, t0 - .05, t0 + .25)) * a
        if k <= 0: continue
        col, row = n // 12, n % 12
        x, y = 1000 + col * 440, 240 + row * 58
        d.ellipse([x, y + 8, x + 26, y + 34], fill=KC[kd] + (int(255 * k),), outline=(240, 230, 210, int(255 * k)), width=2)
        d.text((x + 40, y + 21), f'{n + 1:>2}  {nm}', font=ST.F('EBGaramond-Italic.ttf', 40), fill=(244, 236, 220, int(255 * k)), anchor='lm')
    fr.alpha_composite(lay)

QI0 = I('O man'); QI1 = I('covers my body') + 2
CYQ = SourceCard('iran/cyrus.jpg', 'Tomb of Cyrus', 'as recorded by Plutarch', [WD['words'][i]['w'] for i in range(QI0, QI1 + 1)],
                 [W(i) for i in range(QI0, QI1 + 1)], box=(70, 430, 900, 520))


def overlays(fr, sc, wl, t, style, land):
    zf = clamp(18 / wl, 0.7, 1.3)
    for r in REALMS:
        if not (r['t0'] - .1 < t < r['t1'] + .1): continue
        a = life(t, r['t0'], r['t1'], 1.0, 1.0)
        circ = None
        if r['grow']:
            c, r0, r1, g0, g1 = r['grow']; rad = lerp(r0, r1, ease_io(prog(t, g0, g1)))
            if rad < r1 - .01: circ = (c, rad)
        wash(fr, sc, land, r['poly'], r['col'], a, circle=circ, strength=r['s'] * (.8 if style == 'modern' else 1))
    for r in REALMS:
        if r['name'] and r['t0'] < t < r['t1']:
            realm_label(fr, sc, r['name'], r['at'], r['size'] * clamp(zf, .75, 1.2), life(t, r['t0'] + .8, r['t1'], .8, .6), style)
    for t0, t1, n, s in LABELS:
        if t0 - .1 < t < t1 + .1: town(fr, sc, n, life(t, t0, t1, .4, .4), style, s)
    for t0, t1, tf, pts, kind, w0, w1, dashed in ARROWS:
        if t < t0 or t > tf + 1: continue
        arrow(fr, [sc(*p) for p in pts], ease_io(prog(t, t0, t1)), kind, w0, w1, 1 - smooth(prog(t, tf, tf + 1)), dashed=dashed)
    for t0, t1, n in RIPPLES:
        if t0 < t < t1: ripples(fr, sc(*C[n]), t, t0, t1, R=70)
    for t0, t1, n in MODERN_HITS:
        if t0 < t < t1: missile_hit(fr, sc(*C[n]), t, t0, t1)
    for a0, a1, poly, col in HATCH: hatch(fr, sc, poly, t, a0, a1, col)
    for med, t0, t1, tgt in MED:
        if t0 - .1 < t < t1 + .5:
            tx, ty = sc(*C[tgt]); right = tx < W_ * .55
            pos = (W_ - 330, 380) if right else (330, 380)
            med.draw(fr, pos, t, t0, t1, target=(tx, ty - 6), flip=right)
    for t0, t1, ti, sb, lk, rk in PILLS:
        draw_pill3(fr, (W_ / 2, 110), t, t0, t1, ti, sb, lk, rk)


def map_layer(t):
    fr, sc, wl = cam.frame(t)
    land, des = crop_masks(t)
    A, B, f = style_at(t)
    lon, lat, _ = cam.at(t); view = (lon, lat, wl, sc)
    base = ST.stylize(fr, land, des, A, view, t)
    if f < 1 and A != B: base = Image.blend(base, ST.stylize(fr, land, des, B, view, t), f)
    style = B if f >= .5 else A
    overlays(base, sc, wl, t, style, land)
    if f < 1 and A != B:
        base = Image.blend(ST.finish(base.copy(), A), ST.finish(base, B), f)
    else: base = ST.finish(base, style)
    title_card(base, t); ongoing_tag(base, t); dynasty_roll(base, t)
    if TPL - .3 < t: CYQ.draw(base, t, TQ0, TQ1)
    if EPI + .3 < t < EPI + 3.2: chapter(base, t, EPI + .3, EPI + 3.2, '·', 'Epilogue')
    for i, t0 in enumerate(CHT):
        if t0 - .1 < t < t0 + 3.6: chapter(base, t, t0, t0 + 3.6, NUM[i], TITLES[i])
    paste(base, year_badge(year_at(t)), (W_ - 160, 86), 1, 1)
    return base


def map_dissolve(t):
    d = cam.dissolve(t)
    if not d: return map_layer(t)
    a, b, f = d
    try:
        cam.force = a; A = map_layer(t).convert('RGBA')
        cam.force = b; B = map_layer(t).convert('RGBA')
    finally:
        cam.force = None
    return Image.blend(A, B, f)


# ------------------------------------------------------------------ tactical close-ups (base 3000x1800)
def _tac(name, spec, keys): return T_.Tactical(name, spec, keys)
tP0 = T('Nearly two') - .3
TPERS = _tac('persepolis', TS.PERSEPOLIS, [(0.0, 1500, 900, 2700), (tP0, 1500, 820, 1900)])
TPERS.camps[0][0].update(t0=0.2, spread=1.2)
tP1 = T('Persepolis burned') - .5; tP2 = T('Darius was murdered') + .2
TPERS2 = _tac('persepolis', TS.PERSEPOLIS, [(tP1, 1500, 860, 2300), (tP2, 1500, 800, 1800)])
TPERS2.camps[0][0].update(t0=tP1, spread=.6)
tB0 = T('In 539') - .4; tB1 = T('His proclamation')
TBAB = _tac('babylon', TS.BABYLON, [(tB0, 1700, 900, 2800), (tB1, 1600, 900, 2000)])
TBAB.camps[0][0].update(t0=tB0, spread=.8)
tG0 = T('and in 1258') - .4; tG1 = T('Hulagu founded')
TBAG = _tac('baghdad', TS.BAGHDAD, [(tG0, 1400, 900, 2900), (tG1, 1150, 880, 2000)])
for cp in TBAG.camps: cp[0].update(t0=tG0, spread=.8)
tI0 = T('Hotak defeated') - .4; tI1 = T('Iran was rescued')
TISF = _tac('isfahan', TS.ISFAHAN, [(tI0, 1500, 1000, 2900), (tI1, 1500, 900, 2100)])
for cp in TISF.camps: cp[0].update(t0=tI0, spread=1.0)

def tac_pers(t):
    fr, sc = TPERS.frame(t); TPERS.draw_camps(fr, sc, t)
    TPERS.burn_city(fr, sc, t, 0.5, idx=0, n=12, seed=3)
    for i, (x, y, a) in enumerate([(900, 1300, 20), (2100, 1300, -20), (1500, 1250, 0)]):
        paste(fr, T_.rot_tile('greek', 44, a), sc(x, y), back_out(prog(t, .5 + i * .15, .9 + i * .15)), 1)
    draw_pill3(fr, (W_ / 2, 110), t, .3, tP0 - .2, 'Persepolis', '330 BC', 'greek', 'persian')
    paste(fr, year_badge('330 BC'), (W_ - 160, 86), 1, 1)
    return ST.finish(fr, 'ancient')

def tac_pers2(t):
    fr, sc = TPERS2.frame(t); TPERS2.draw_camps(fr, sc, t)
    TPERS2.burn_city(fr, sc, t, tP1 + .3, idx=0, n=12, seed=5)
    paste(fr, year_badge('330 BC'), (W_ - 160, 86), 1, 1)
    draw_pill3(fr, (W_ / 2, 110), t, tP1 + .2, tP2 - .2, 'Burning of Persepolis', '330 BC', 'greek', 'persian')
    return ST.finish(fr, 'ancient')

def tac_bab(t):
    fr, sc = TBAB.frame(t); TBAB.draw_camps(fr, sc, t)
    arrow(fr, [sc(*p) for p in ((2450, 920), (2200, 900), (1950, 890))], ease_io(prog(t, tB0 + 1, tB0 + 3)), 'persian', 18, 36)
    if t > tB0 + 3: ripples(fr, sc(1800, 890), t, tB0 + 3, tB1, col=(255, 240, 200), R=90)
    draw_pill3(fr, (W_ / 2, 110), t, tB0 + .3, tB1 - .2, 'Cyrus enters Babylon', '539 BC', 'persian', 'elam')
    paste(fr, year_badge('539 BC'), (W_ - 160, 86), 1, 1)
    return ST.finish(fr, 'ancient')

def tac_bag(t):
    fr, sc = TBAG.frame(t); TBAG.draw_camps(fr, sc, t)
    TBAG.burn_city(fr, sc, t, tG0 + 1.2, idx=0, n=12, seed=7)
    draw_pill3(fr, (W_ / 2, 110), t, tG0 + .3, tG1 - .2, 'Sack of Baghdad', 'February 1258', 'mongol', 'caliph')
    MED[6][0].draw(fr, (W_ - 330, 400), t, tG0 + .6, tG1 - .3, target=sc(400, 900), flip=True)
    paste(fr, year_badge('1258'), (W_ - 160, 86), 1, 1)
    return ST.finish(fr, 'medieval')

def tac_isf(t):
    fr, sc = TISF.frame(t); TISF.draw_camps(fr, sc, t)
    for i, (x, y) in enumerate([(1200, 700), (1800, 800), (1500, 600)]):
        T_.smoke(fr, sc(x, y), t + i, smooth(prog(t, tI0 + 2 + i, tI0 + 3 + i)) * .8, 1.1 * TISF.s, i)
    draw_pill3(fr, (W_ / 2, 110), t, tI0 + .3, tI1 - .2, 'Siege of Isfahan', 'March-October 1722', 'afghan', 'safavid')
    paste(fr, year_badge('1722'), (W_ - 160, 86), 1, 1)
    return ST.finish(fr, 'safavid')

SEGS = [(0.0, tP0, tac_pers), (tB0, tB1, tac_bab), (tP1, tP2, tac_pers2), (tG0, tG1, tac_bag), (tI0, tI1, tac_isf)]
XF = 0.5

def _cap(k):
    c = json.load(open(os.path.join(ROOT, 'assets/img/iran/CREDITS.json')))[k]
    a = c.get('artist', '').replace('Unknown authorUnknown author', '').replace('Unknown creatorUnk', '').strip()
    a = re.sub(r'\s+', ' ', a)[:40]
    return f"{c['license']}" + (f', {a}' if a else '') + ', via Wikimedia Commons'
PLATES = [
    (T('His proclamation'), T('His son Cambyses'), Plate('iran/cyrus_cylinder.jpg', crop=(0.22, 0.1, 0.86, 0.62), caption='The Cyrus Cylinder, British Museum. ' + _cap('cyrus_cylinder'))),
    (T('the ceremonial capital'), T('On the cliff of Behistun'), Plate('iran/persepolis_chipiez.jpg', caption='Persepolis, reconstruction by Charles Chipiez, 1884. ' + _cap('persepolis_chipiez'))),
    (T('On the cliff of Behistun'), T('Clay tablets found'), Plate('iran/behistun.jpg', crop=(0, 0.05, 1, 0.75), caption='The Behistun relief of Darius I. ' + _cap('behistun'))),
    (T('then at Issus'), T('In 331'), Plate('iran/issus_mosaic.jpg', caption='Alexander Mosaic, Pompeii, c. 100 BC. ' + _cap('issus_mosaic'))),
    (T('and carved the scene'), T('Under Khosrow the First'), Plate('iran/shapur_relief.jpg', caption='Triumph of Shapur I, Naqsh-e Rostam. ' + _cap('shapur_relief'))),
    (T('the great palace'), T('But his grandson'), Plate('iran/taq_kasra.jpg', caption='Taq Kasra, the palace arch of Ctesiphon, 1934. ' + _cap('taq_kasra'))),
    (T('the poet Ferdowsi'), CHT[6] - .2, Plate('iran/shahnameh.jpg', crop=(0, 0.45, 1, 1), caption='Ferdowsi with court poets, Shahnameh manuscript. ' + _cap('shahnameh'))),
    (T('with its great square'), T('Persian painting'), Plate('iran/naqsh_jahan.jpg', caption='Naqsh-e Jahan Square, Isfahan. ' + _cap('naqsh_jahan'))),
]


def end_card(fr, t):
    a = smooth(prog(t, VEND + .4, VEND + 1.5))
    if a <= 0: return fr
    fr.alpha_composite(Image.new('RGBA', fr.size, (14, 12, 16, int(195 * a))))
    lay = Image.new('RGBA', fr.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.text((W_ / 2, 450), 'I  R  A  N', font=ST.F('Cinzel.ttf', 120), fill=(244, 232, 206, int(255 * a)), anchor='mm')
    d.text((W_ / 2, 560), 'From Cyrus to 2026', font=ST.F('EBGaramond-Italic.ttf', 54), fill=(214, 200, 176, int(255 * a)), anchor='mm')
    a2 = smooth(prog(t, VEND + 1.5, VEND + 2.3))
    d.text((W_ / 2, 690), 'Events of 2026 are ongoing; some figures remain disputed.', font=ST.F('IMFeENit28P.ttf', 32), fill=(200, 190, 176, int(255 * a2)), anchor='mm')
    d.text((W_ / 2, 740), 'Portraits of religious figures are shown as light out of respect.', font=ST.F('IMFeENit28P.ttf', 32), fill=(200, 190, 176, int(255 * a2)), anchor='mm')
    fr.alpha_composite(lay); return fr


def render(t):
    segs = [(t0, t1, (lambda tt, pl=pl, a=t0, b=t1: pl.render(tt, a, b))) for t0, t1, pl in PLATES] + [(a, b, fn) for a, b, fn in SEGS]
    segs.sort(key=lambda s_: s_[0])
    act = []
    for t0, t1, fn in segs:
        a = min(smooth(prog(t, t0, t0 + XF)) if t0 > 0 else 1.0, 1 - smooth(prog(t, t1 - XF, t1)))
        if a > 0: act.append((a, fn))
    full = [i for i, (a, _) in enumerate(act) if a >= .999]
    if full: fr = act[full[-1]][1](t); act = act[full[-1] + 1:]
    else: fr = map_dissolve(t)
    for a, fn in act:
        fr = Image.blend(fr.convert('RGBA'), fn(t).convert('RGBA'), a)
    fr = end_card(fr.convert('RGBA'), t)
    out = sharpen(grade(fr))
    out = drop_in(out, t, 0.8)
    fb = 1 - smooth(prog(t, END - 0.8, END))
    if fb < 1: out = Image.blend(Image.new('RGB', out.size), out, fb)
    return out


# ------------------------------------------------------------------ sound
HITS = sorted(set([round(x, 2) for x in CHT + [EPI, T('strike Tehran'), T('Persepolis burned'), T('and in 1258'), T('The opening strikes')]]))
def _era(t): return _sty(t)
def _build_sfx():
    ev = []
    ev += [(0.0, 'px_horn_drums', -8, 5), (0.4, 'fire_big', -14, 8), (T('Nearly two') - .3, 'whoosh_cine', -12, 2), (T('Nearly two'), 'hud1', -12, 2),
           (T('strike Tehran') - .6, 'jet_pass', -10, 3), (T('strike Tehran'), 'boom_impact', -8, 4), (T('Between these'), 'whoosh6', -12, 2),
           (T('So when') - .2, 'trailer1', -8, 5)]
    for i, t0 in enumerate(CHT):
        e = _era(t0 + 2)
        if e == 'modern': ev += [(t0 - .2, 'subdrop', -9, 3), (t0, 'hud2', -11, 2)]
        else: ev += [(t0 - .2, 'px_braam', -9, 4), (t0 + .1, 'paper_flip', -13, 1.5)]
    ev += [(EPI - .2, 'bells', -12, 2.5), (EPI, 'paper_flip', -13, 1.5)]
    for t0, t1, tf, pts, kind, *_ in ARROWS:
        e = _era(t0)
        if e == 'modern':
            nm = 'jet_pass' if kind in ('usa', 'israel') else ('rocket' if kind == 'iran' else ('mg' if kind == 'iraq' else 'whoosh6'))
            ev.append((t0, nm, -11, 3))
        elif e in ('pahlavi', 'qajar'): ev.append((t0, 'px_march', -13, 3))
        else: ev.append((t0, 'px_gallop' if len(ev) % 2 else 'px_march', -12, 3))
    for t0, t1, n in RIPPLES:
        ev.append((t0, 'cine_boom' if _era(t0) in ('pahlavi', 'modern') else 'thud', -10, 2.5))
    for t0, t1, n in MODERN_HITS: ev.append((t0, 'boom_impact', -9, 3))
    for t0, t1, *_ in PILLS:
        e = _era(t0); ev.append((t0, 'hud_sel' if e in ('modern', 'pahlavi') else ('low_horn' if e == 'qajar' else 'px_horn'), -12, 3))
    for med, t0, t1, tgt in MED: ev.append((t0, 'swoosh', -16, 1.2))
    for t0, t1, pl in PLATES: ev.append((t0, 'whoosh6', -15, 2))
    ev += [(tB0, 'px_ancient_drums', -12, 5), (tB0 + 1, 'px_war_cry', -12, 2.5), (tP1, 'fire_big', -12, 6), (tP1, 'px_braam', -9, 4),
           (tG0, 'px_battle_drums', -12, tG1 - tG0), (tG0 + 1.2, 'fire_big', -12, 7), (tG0 + .8, 'px_arrows_many', -10, 3),
           (tI0, 'px_battle_drums', -14, tI1 - tI0), (tI0 + 1, 'px_medieval_war', -11, 4),
           (T('In 1514') + .5, 'boom', -10, 3), (T('Chaldiran, Ottoman') + .3, 'px_swords1', -9, 2), (T('In 331') + .8, 'px_sword_fight', -10, 4),
           (T('In 53 BC') + .4, 'px_arrows_many', -9, 3), (T('In 636') + .6, 'px_swords2', -9, 2.5), (T('Mongol armies stormed'), 'px_gallop_near', -9, 4),
           (T('In 1739') + .3, 'px_swords3', -9, 2.5), (T('American bombers hit') - .4, 'jet_pass', -9, 3), (T('Operation Epic Fury'), 'trailer3', -9, 5),
           (T('the war that began'), 'hud_type', -16, 4), (T('Plutarch records') - .4, 'bells', -14, 2.5), (VEND + .3, 'trailer1', -10, 5),
           (END - 2.5, 'paper_flip', -15, 1.5)]
    ev.sort()
    out = []; last = {}
    for t0, nm, db, ml in ev:
        if out and abs(t0 - out[-1][0]) < .35 and out[-1][1] == nm: continue
        out.append((round(max(0, t0), 2), nm, db, round(ml, 2)))
    return out
SFX = _build_sfx()
