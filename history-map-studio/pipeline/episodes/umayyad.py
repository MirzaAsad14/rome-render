"""Episode: The Umayyad Caliphate, 661-750 (one-minute overview).
Respect rule: every religious personality (caliphs included) is shown only as a NoorMedallion - no face, only light."""
import json, os, sys, math
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from kit import *
from kit import path_at
import numpy as np
import atlas, tactical as T
from regions import caliphate_750 as R
from episodes import tac_caliphate as TS

WD = json.load(open(os.path.join(ROOT, 'build/umayyad/words.json')))
def W(i): return WD['words'][i]['t0']
END = WD['total']; VEND = WD['voice_end']; FPS = 30
W_ = 1920

P = atlas.Proj(*R.BOUNDS[:2], *R.BOUNDS[2:], K=R.K, c=R.C0)
PYR = atlas.build(P, R.CFG, os.path.join(ROOT, 'build/atlas_cal750'))
DET = [(atlas.Proj(*b, K=Kd, c=R.C0), atlas.build(atlas.Proj(*b, K=Kd, c=R.C0), R.dcfg(Kd), os.path.join(ROOT, f'build/atlas_cal750{n}'))) for n, b, Kd in R.DETAILS]
LANDS = [Image.open(os.path.join(ROOT, 'build/atlas_cal750_land.png')).convert('L')] + \
        [Image.open(os.path.join(ROOT, f'build/atlas_cal750{n}_land.png')).convert('L') for n, *_ in R.DETAILS]
C = {n: ll for n, ll, *_ in R.TOWNS}
ZAB = (43.4, 36.1); BUSIR = (30.9, 29.2); GIB = (-5.4, 36.0)

cam = Camera(P, PYR, [
    (0.0, 37.5, 32.0, 20), (W(7) - .3, 37.5, 31.0, 20), (W(20), 39.0, 30.0, 24), (W(29), 39.0, 30.5, 26),
    (W(30), 37.0, 32.5, 14), (W(41), 36.5, 32.3, 12),
    (W(49) - .1, 31.0, 30.0, 60), (W(52) + .2, 31.0, 30.0, 62),
    (W(55) + .1, -3.5, 37.0, 15), (W(60) + .2, -4.0, 37.9, 14),
    (W(62) + .6, 66.5, 27.0, 17, 'cut'), (W(68), 67.5, 27.5, 16), (W(69) + .1, 52.0, 29.0, 44),
    (W(70) + .4, 31.0, 30.0, 70), (W(90), 31.0, 30.5, 72),
    (W(93), 29.5, 40.3, 13), (W(98) - .5, 29.0, 40.6, 12.5), (W(99) + .3, 2.5, 45.0, 14, 'cut'), (W(103) + .3, 2.0, 45.3, 13),
    (W(105) + .1, 52.0, 34.0, 36, 'cut'), (W(117), 50.0, 34.5, 34), (W(120), 43.5, 35.5, 12), (W(126), 43.4, 35.9, 9),
    (W(142) - .3, 37.5, 33.0, 22), (W(148), 34.5, 31.5, 22),
    (W(150), 12.0, 35.0, 48), (W(157), 2.0, 35.5, 38), (W(162), -4.2, 37.6, 14), (END, -4.6, 37.8, 12.5),
], details=DET)

# caliphate extent (lon, lat); clipped to land per frame, so the sea side can be loose
CORE = [(25, 32.5), (31, 32.5), (34.6, 36.6), (36.6, 37.1), (38.5, 38.4), (41, 39.6), (44, 39.4), (48.5, 38.6), (50, 37.3), (54, 37.3), (57, 36.6),
        (61, 36.5), (61.5, 30), (61, 26), (57.5, 25.5), (59.8, 22.5), (55, 17), (52, 16), (45, 12.6), (43, 12.7), (39, 21), (36.6, 22), (25, 22)]
MAX = [(-9.6, 42.5), (-3.4, 42.7), (-1.8, 43.4), (0, 42.9), (2.0, 43.0), (3.3, 43.7), (4.9, 43.9), (6, 43), (6, 38.5), (12, 38), (12, 33), (20, 32),
       (25, 32.5), (31, 32.5), (34.6, 36.6), (36.6, 37.1), (38.5, 38.4), (41, 39.6), (41.5, 41.4), (43, 42.4), (46, 42.8), (47.8, 41.9), (49.5, 40.5),
       (53, 39), (54, 40.5), (56.5, 42), (60, 43.5), (63, 44.6), (68, 42.8), (70.8, 41.6), (71.5, 40.2), (73.5, 39), (73.6, 37.5), (71.5, 36.6),
       (70.5, 34.5), (69.5, 32.5), (70.3, 28.4), (71.2, 27.2), (71.6, 24.6), (70.8, 23.2), (68.5, 22.5), (62, 24), (59.8, 22.5), (55, 17), (52, 16),
       (45, 12.6), (43, 12.7), (39, 21), (36.6, 22), (25, 22), (25, 27), (10, 27.5), (-2, 28), (-10, 28), (-12, 30), (-12, 36), (-10.5, 37), (-10.5, 42)]
ABB = [(4, 38.5), (12, 38), (12, 33), (20, 32)] + MAX[12:-6] + [(25, 27), (10, 27.5), (4, 28)]
UMA = (54, 140, 92); ABC = (24, 24, 28)


def land_crop(t):
    lon, lat, wl = cam.at(t); out = None; acc = 0.0
    for ai, w in reversed(cam.layers(lon, lat, wl)):
        Pa = cam.atl[ai][0]; LAND = LANDS[ai]
        cx, cy = Pa.xy(lon, lat); vw = wl * Pa.c * Pa.K; vh = vw * H / W_
        box = ((cx - vw / 2) / 2, (cy - vh / 2) / 2, (cx + vw / 2) / 2, (cy + vh / 2) / 2)
        m = np.asarray(LAND.transform((W_, H), Image.EXTENT, box, Image.BILINEAR), np.float32) / 255
        if out is None: out, acc = m, w
        else: acc += w; out = out + (m - out) * (w / acc)
    return out


def wash(fr, sc, land, poly, col, a, circle=None, base=None, line=True, paint=True):
    if a <= 0: return None
    m = Image.new('L', (W_, H), 0); ImageDraw.Draw(m).polygon([sc(*p) for p in atlas.rough(poly, .35, .10)], fill=255)
    mm = np.asarray(m, np.float32) / 255
    if circle is not None:
        (clon, clat), rad = circle; cx, cy = sc(clon, clat); px_per_deg = sc(clon + 1, clat)[0] - cx
        yy, xx = np.ogrid[0:H, 0:W_]; d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / max(1e-3, px_per_deg)
        mm = mm * np.clip((rad - d) / 1.2, 0, 1)
    if base is not None: mm = np.maximum(mm, base)
    mm = mm * land
    if not paint: return mm
    arr = np.asarray(fr, np.float32)
    k = (mm * a * .36)[..., None]
    arr[..., :3] = arr[..., :3] * (1 - k) + np.array(col, np.float32) * k
    if line:
        e = np.asarray(Image.fromarray((mm * 255).astype(np.uint8)).filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(3)), np.float32) / 255
        ke = (np.clip(e * 1.5, 0, 1) * a * .85)[..., None]
        lc = tuple(int(c * .55) for c in col)
        arr[..., :3] = arr[..., :3] * (1 - ke) + np.array(lc, np.float32) * ke
    fr.paste(Image.fromarray(arr.astype(np.uint8), 'RGBA'))
    return mm


M_MUAW = NoorMedallion('Muawiya I', 'First Umayyad caliph, 661-680', 'umayyad', D=240, flip=True)
M_ABDM = NoorMedallion('Abd al-Malik', 'Caliph, 685-705', 'umayyad', D=240, flip=True)
M_MARW = NoorMedallion('Marwan II', 'Last Umayyad caliph, 744-750', 'umayyad', D=240, flip=True)
M_ABDR = NoorMedallion('Abd al-Rahman I', 'Emir of Cordoba, 756-788', 'umayyad', D=240)

PLATES = [
    (W(41) - .2, W(49) - .2, Plate('dome_rock.jpg', crop=(0.22, 0.14, 0.86, 0.66), caption='The Dome of the Rock, Jerusalem, completed 691-692. Photo: Godot13, CC BY-SA 4.0', zoom=(1.0, 1.08))),
]
YEARS = [(0, '661'), (W(30), '685'), (W(54), '711'), (W(69), '720'), (W(95), '718'), (W(99), '732'), (W(104), '740s'), (W(118), '750')]


def year_at(t):
    y = YEARS[0][1]
    for t0, s in YEARS:
        if t >= t0: y = s
    return y


def map_layer(t):
    fr, sc, wl = cam.frame(t)
    land = land_crop(t)
    zf = clamp(18 / wl, 0.8, 1.25)
    # caliphate: core from Muawiya, growth wave from Damascus during the conquests
    ca = smooth(prog(t, W(5), W(7) + .5))
    grow = lerp(0, 52, ease_io(prog(t, W(52), W(80))))
    if grow <= 0: wash(fr, sc, land, CORE, UMA, ca)
    else: wash(fr, sc, land, MAX, UMA, ca, circle=(C['Damascus'], grow), base=wash(fr, sc, land, CORE, UMA, 1, paint=False))
    # Abbasid black tide from Merv
    ab = lerp(0, 60, ease_io(prog(t, W(108), W(150))))
    if ab > 0: wash(fr, sc, land, ABB, ABC, 1.0, circle=(C['Merv'], ab))
    # capital moves to Damascus
    arrow(fr, [sc(*p) for p in (C['Kufa'], (41.0, 33.6), C['Damascus'])], ease_io(prog(t, W(15), W(20))), 'umayyad', 10, 24, 1 - smooth(prog(t, W(29), W(30))), dashed=True)
    # conquest arrows
    arrow(fr, [sc(*p) for p in (C['Tangier'], GIB, (-5.0, 37.0), C['Cordoba'], (-4.4, 38.9), C['Toledo'])], ease_io(prog(t, W(56), W(61) + .6)), 'umayyad', 14, 30, 1 - smooth(prog(t, W(90), W(91))))
    arrow(fr, [sc(*p) for p in (C['Shiraz'], (58.0, 26.6), (63.5, 25.4), C['Debal'], (69.3, 27.5), C['Multan'])], ease_io(prog(t, W(63), W(68) + .4)), 'umayyad', 14, 30, 1 - smooth(prog(t, W(90), W(91))))
    arrow(fr, [sc(*p) for p in (C['Merv'], C['Bukhara'], C['Samarkand'])], ease_io(prog(t, W(70), W(74))), 'umayyad', 12, 26, 1 - smooth(prog(t, W(90), W(91))))
    arrow(fr, [sc(*p) for p in (C['Kairouan'], (2, 35.4), (-3.5, 35.4), C['Tangier'])], ease_io(prog(t, W(52), W(56))), 'umayyad', 12, 26, 1 - smooth(prog(t, W(90), W(91))))
    # stalled at Constantinople and Tours
    cx_, cy_ = sc(*C['Constantinople'])
    arrow(fr, [sc(*p) for p in (C['Antioch'], (33.5, 38.0), (30.0, 40.3), (29.2, 40.85))], ease_io(prog(t, W(93), W(96))), 'umayyad', 14, 30, 1 - smooth(prog(t, W(100), W(101))))
    block(fr, (cx_ + 10, cy_ - 70), 'byz', t, W(95), W(101), scale=zf * .5, cols=3, rows=2)
    if W(96) < t < W(101): paste(fr, swords_icon(54), (cx_ - 40, cy_ + 20), back_out(prog(t, W(96), W(96) + .4)), 1)
    draw_pill3(fr, (W_ / 2, 110), t, W(94), W(98) - .5, 'Siege of Constantinople', '717-718', 'umayyad', 'byz')
    tx, ty = sc(*C['Tours'])
    arrow(fr, [sc(*p) for p in (C['Narbonne'], (1.5, 44.4), (0.8, 46.2), (0.7, 46.9))], ease_io(prog(t, W(99), W(102))), 'umayyad', 14, 30, 1 - smooth(prog(t, W(104), W(105))))
    block(fr, (tx + 20, ty - 60), 'frank', t, W(100), W(105), scale=zf * .5, cols=3, rows=2)
    if W(102) < t < W(105): paste(fr, swords_icon(54), (tx - 10, ty + 40), back_out(prog(t, W(102), W(102) + .4)), 1)
    draw_pill3(fr, (W_ / 2, 960), t, W(100), W(103) + .2, 'Battle of Tours', '732', 'umayyad', 'frank')
    # Abbasid revolt
    arrow(fr, [sc(*p) for p in (C['Merv'], C['Nishapur'], (53, 35.5), C['Isfahan'], (47.5, 33.4), C['Kufa'])], ease_io(prog(t, W(110), W(118))), 'abbasid', 16, 34, 1 - smooth(prog(t, W(142), W(143))))
    arrow(fr, [sc(*p) for p in (C['Kufa'], (44.2, 34.4), (43.6, 35.6))], ease_io(prog(t, W(119), W(124))), 'abbasid', 16, 34, 1 - smooth(prog(t, W(142), W(143))))
    draw_pill3(fr, (W_ / 2, 110), t, W(112), W(118), 'The Abbasid Revolution', '747-750', 'abbasid', 'umayyad')
    # Marwan's flight and death
    arrow(fr, [sc(*p) for p in (ZAB, C['Harran'], C['Damascus'], C['Jerusalem'], (32.5, 30.8), BUSIR)], ease_io(prog(t, W(142), W(146))), 'umayyad', 10, 24, 1 - smooth(prog(t, W(150), W(151))), dashed=True)
    if t > W(147): ripples(fr, sc(*BUSIR), t, W(147), W(152), R=80)
    draw_pill3(fr, (W_ / 2, 110), t, W(146), W(150), 'Death of Marwan II', 'Busir, Egypt, 750', 'abbasid', 'umayyad')
    # Abd al-Rahman's escape to al-Andalus
    arrow(fr, [sc(*p) for p in (C['Damascus'], (33, 31.2), (25, 31.5), (15, 32.2), C['Kairouan'], (2, 35.6), (-4, 35.5), GIB, C['Cordoba'])],
          ease_io(prog(t, W(152), W(162))), 'umayyad', 12, 28, 1, dashed=True)
    if t > W(162): ripples(fr, sc(*C['Cordoba']), t, W(162), END, R=90)
    draw_pill3(fr, (W_ / 2, 110), t, W(56), W(62), 'Conquest of Hispania', '711', 'umayyad', 'umayyad')
    draw_pill3(fr, (W_ / 2, 110), t, W(63), W(69), 'Conquest of Sindh', '711-712', 'umayyad', 'umayyad')
    # medallions (noor only)
    dx, dy = sc(*C['Damascus'])
    M_MUAW.draw(fr, (W_ - 330, 360), t, W(7), W(21), target=(dx - 6, dy - 6))
    M_ABDM.draw(fr, (W_ - 330, 360), t, W(30), W(41) - .3, target=(dx - 6, dy - 6))
    kx, ky = sc(*C['Cordoba'])
    M_ABDR.draw(fr, (330, 380), t, W(153), END, target=(kx + 8, ky - 6))
    paste(fr, year_badge(year_at(t)), (W_ - 160, 86), 1, 1)
    return fr


# ------------------------------------------------------------ tactical close-ups
TD = T.Tactical('damascus', TS.DAMASCUS, [(0.0, 1500, 920, 2350), (W(7) + .5, 1500, 900, 1900)])
TD.camps[0][0].update(t0=0.4, spread=1.4, scale=1.2)
TZ = T.Tactical('zab', TS.ZAB, [(W(126) - .4, 1600, 900, 2600), (W(134), 1600, 880, 2150), (W(141) + .5, 1650, 880, 1900)])
TZ.camps[0][0].update(t0=W(126) - .3, spread=.8, scale=1.2); TZ.camps[1][0].update(t0=W(126) - .3, spread=.8, scale=1.2)
UM_LINE = [(1350, 700, 20), (1480, 640, 20), (1250, 800, 20), (1150, 560, 15), (1050, 700, 20)]
AB_LINE = [(1950, 1000, 20), (2080, 940, 20), (1850, 1100, 20), (2200, 1060, 15), (1980, 1180, 20), (2300, 920, 25)]


def tac_damascus(t):
    fr, sc = TD.frame(t); TD.draw_camps(fr, sc, t)
    for i, (x, y, a) in enumerate([(880, 900, 6), (2120, 900, -8), (1500, 450, 0), (1500, 1220, 0)]):
        paste(fr, T.rot_tile('umayyad', 44, a), sc(x, y), back_out(prog(t, .6 + i * .15, 1.0 + i * .15)), 1)
    paste(fr, year_badge('661'), (W_ - 160, 86), 1, 1)
    chapter(fr, t, 0.95, W(2) + .2, 'I', 'The Umayyad Caliphate')
    draw_pill3(fr, (W_ / 2, 110), t, W(2) + .3, W(7), 'Damascus', 'Capital of the Caliphate, 661', 'umayyad', 'umayyad')
    return fr


def tac_zab(t):
    fr, sc = TZ.frame(t); TZ.draw_camps(fr, sc, t)
    adv = ease_io(prog(t, W(131), W(137)))  # Umayyads cross the bridge and attack
    for i, (x, y, a) in enumerate(UM_LINE):
        t0 = W(126) + i * .12
        if t < t0: continue
        px, py = lerp(x, x + 260, adv), lerp(y, y + 200, adv)
        rout = ease_out(prog(t, W(140) + i * .1, W(141) + i * .1))
        px, py = lerp(px, x - 120, rout), lerp(py, y - 120, rout)
        paste(fr, T.rot_tile('umayyad', 44, a), sc(px, py), back_out(prog(t, t0, t0 + .4)), 1)
        cr = ease_out(prog(t, W(140) + i * .15, W(140) + .5 + i * .15))
        if cr > 0:
            def fn(d, S, p=sc(px, py), cr=cr):
                r = 20 * cr
                for s_ in (1, -1): d.line([S((p[0] - r, p[1] - r * s_)), S((p[0] + r, p[1] + r * s_))], fill=(20, 16, 16, 255), width=Z * 6)
                for s_ in (1, -1): d.line([S((p[0] - r, p[1] - r * s_)), S((p[0] + r, p[1] + r * s_))], fill=(240, 236, 230, 255), width=Z * 3)
            q = sc(px, py); local_draw(fr, (q[0] - 30, q[1] - 30, q[0] + 30, q[1] + 30), fn)
    for i, (x, y, a) in enumerate(AB_LINE):
        t0 = W(126) + .3 + i * .12
        if t < t0: continue
        k = ease_io(prog(t, W(138), W(141)))
        paste(fr, T.rot_tile('abbasid', 44, a), sc(lerp(x, x - 300, k), lerp(y, y - 230, k)), back_out(prog(t, t0, t0 + .4)), 1)
    arrow(fr, [sc(*p) for p in ((1200, 640), (1500, 760), (1760, 900))], ease_io(prog(t, W(131), W(134))), 'umayyad', 16, 34, 1 - smooth(prog(t, W(139), W(140))))
    arrow(fr, [sc(*p) for p in ((2250, 1120), (1950, 950), (1550, 720), (1250, 560))], ease_io(prog(t, W(139), W(141) + .3)), 'abbasid', 18, 38)
    if t > W(136): paste(fr, swords_icon(60), sc(1720, 900), back_out(prog(t, W(136), W(136) + .4)), 1)
    M_MARW.draw(fr, (W_ - 330, 420), t, W(130) - .2, W(138), target=sc(1200, 640))
    draw_pill3(fr, (W_ / 2, 110), t, W(126), W(142), 'Battle of the Great Zab', 'January 750', 'abbasid', 'umayyad')
    paste(fr, year_badge('750'), (W_ - 160, 86), 1, 1)
    return fr


SEGS = [(0.0, W(7) + .2, tac_damascus), (W(126) - .4, W(142) - .1, tac_zab)]
XF = 0.45


def end_card(fr, t):
    a = smooth(prog(t, VEND + .5, VEND + 1.6))
    if a <= 0: return fr
    dark = Image.new('RGBA', fr.size, (14, 12, 16, int(185 * a))); fr.alpha_composite(dark)
    lay = Image.new('RGBA', fr.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.text((W_ / 2, 470), 'The Umayyad Caliphate', font=F('IMFeENrm28P.ttf', 104), fill=(244, 236, 222, int(255 * a)), anchor='mm')
    d.text((W_ / 2, 575), '661 - 750', font=F('IMFeENit28P.ttf', 46), fill=(214, 200, 180, int(255 * a)), anchor='mm')
    a2 = smooth(prog(t, VEND + 1.6, VEND + 2.4))
    d.text((W_ / 2, 700), 'Next: The Emirate of Cordoba', font=F('IMFeENsc28P.ttf', 40), fill=(80, 170, 110, int(255 * a2)), anchor='mm')
    fr.alpha_composite(lay); return fr


HITS = [W(0), W(49), W(56), W(96), W(118), W(136), W(153)]


def map_dissolve(t):
    """long camera jumps flagged 'cut' dissolve between two fully composited views (map + overlays), no whip pan"""
    d = cam.dissolve(t)
    if not d: return map_layer(t)
    a, b, f = d
    try:
        cam.force = a; A = map_layer(t).convert('RGBA')
        cam.force = b; B = map_layer(t).convert('RGBA')
    finally:
        cam.force = None
    return Image.blend(A, B, f)

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
    fr = end_card(fr, t)
    out = sharpen(grade(fr))
    out = drop_in(out, t, 0.8)
    fb = 1 - smooth(prog(t, END - 0.8, END))
    if fb < 1: out = Image.blend(Image.new('RGB', out.size), out, fb)
    return out

# sound effects from the user's library (assets/sfx); (time, name, gain dB, max length s)
SFX = [(0.0, 'px_march_amb', -27, W(49)), (0.05, 'px_horn_drums', -7, 5), (0.9, 'paper_flip', -14, 1.5),
       (W(2) + .3, 'swoosh', -14, 1.2), (W(7) - .1, 'px_braam', -6, 4), (W(15), 'px_drum_loop', -17, 3),
       (W(30) - .1, 'whoosh_cine', -12, 2), (W(41) - .25, 'px_ancient_drums', -9, 4),
       (W(49) - .2, 'whoosh6', -12, 2), (W(49), 'px_battle_drums', -24, W(126) - W(49) - .4), (W(52), 'px_horn', -8, 3.5),
       (W(56) - .1, 'swoosh', -14, 1.2), (W(56), 'px_gallop', -8, 3),
       (W(63) - .1, 'swoosh', -14, 1.2), (W(63), 'px_gallop_near', -7, 3), (W(70), 'px_war_cry', -8, 2.5),
       (W(93), 'px_medieval_war', -7, 4), (W(96), 'px_swords1', -6, 2),
       (W(100), 'px_arrows_many', -8, 2.5), (W(102), 'px_swords2', -6, 2), (W(105), 'px_ancient_drums', -9, 5), (W(110), 'px_horn', -8, 3),
       (W(118), 'px_braam', -6, 4), (W(124), 'px_war_cry', -8, 2), (W(126) - .4, 'whoosh6', -11, 2),
       (W(126) - .2, 'px_sword_fight', -8, 12), (W(128), 'px_arrows', -8, 2.5), (W(131), 'px_gallop_near', -7, 3.5), (W(131), 'neigh', -10, 2),
       (W(136), 'px_swords3', -6, 2), (W(140), 'thud', -7, 2), (W(142), 'whoosh_cine', -12, 2),
       (W(147), 'thud', -7, 2), (W(150), 'whoosh6', -13, 2), (W(153), 'px_horn', -8, 3.5),
       (W(162), 'lowhit', -7, 4), (END - 2.5, 'paper_flip', -15, 1.5)]
