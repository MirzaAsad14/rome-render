"""Episode: The Hunt for the Grand Prince (Sit River, 1238). v2: illustrated atlas + motion kit.
Every beat is pinned to a narration word index via W(i), so re-voicing re-times the edit."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from kit import *
from kit import path_at
import atlas
from regions import rus_1238 as R
import tactical as T
from episodes import tac_rus1238 as TS

WD = json.load(open(os.path.join(ROOT, 'build/sit_river_v4/words.json')))
def W(i): return WD['words'][i]['t0']
def WE(i): return WD['words'][i]['t1']
END = WD['total']; VEND = WD['voice_end']; FPS = 30

P = atlas.Proj(*R.BOUNDS[:2], *R.BOUNDS[2:], K=1300)
PYR = atlas.build(P, R.CFG, os.path.join(ROOT, 'build/atlas_rus1238'))

C = {n: ll for n, ll, *_ in R.TOWNS}
for a, b in (('Vladimir', 'Volodimer-on-Klyazma'), ('Tver', 'Tfer'), ('Uglich', 'Ugleche Pole'), ('Pereyaslavl', 'Pereyaslavl-Zalessky'), ('Novgorod', 'Novgorod the Great')): C[a] = C[b]
CAMP = (38.42, 57.95)
cam = Camera(P, PYR, [
    (0.0, 38.9, 56.85, 8.8), (0.9, 39.0, 56.8, 8.4), (W(2), 39.7, 56.55, 6.5),
    (W(17) - 0.3, 40.0, 56.55, 4.68), (W(28), 40.0, 56.62, 4.94), (W(45), 38.85, 57.68, 4.42),
    (W(46) + 0.5, 38.85, 57.68, 4.42), (W(48) + 0.5, 39.75, 56.4, 5.72), (W(55), 39.65, 56.45, 5.98),
    (W(56) + 0.3, 39.65, 56.45, 5.98), (W(60), 38.7, 56.85, 7.0), (W(66), 38.6, 56.9, 7.2),
    (W(73), 38.35, 57.72, 3.9), (W(78), 38.4, 57.85, 3.38),
    (W(86) - 0.2, 38.2, 57.95, 2.99), (W(88), 38.0, 57.95, 2.99), (W(116), 37.98, 57.96, 2.79),
    (W(141) - 0.25, 35.2, 57.05, 4.3), (W(151), 34.95, 57.15, 4.3), (END, 33.7, 57.65, 5.6),
])

PLATES = [  # (start, end, plate)
    (W(12) - 0.3, W(17) - 0.25, Plate('sack_vladimir.gif', crop=(0, 0, 1, 0.64), caption='The sack of Vladimir. Illustrated Chronicle of Ivan the Terrible, 16th century', zoom=(1.0, 1.07))),
    (W(78) - 0.15, W(86) + 0.2, Plate('scene_hunt.png', full=True, zoom=(1.02, 1.12), pan=(-40, 0))),
    (W(116) + 0.1, W(141) + 0.7, Plate('kirill_finds_yuri.png', crop=(0, 0, 1, 0.62), caption='Bishop Kirill finds the body of Grand Prince Yuri. Illustrated Chronicle, 16th century', zoom=(1.0, 1.09))),
]
XF = 0.45  # crossfade seconds

M_YURI = PopMedallion('yuri_cut.png', 'Yuri II', 'Grand Prince of Vladimir', 'rus', D=250)
M_YURI_R = PopMedallion('yuri_cut.png', 'Yuri II', 'Grand Prince of Vladimir', 'rus', D=250, flip=True)
M_BATU = PopMedallion('batu_cut.png', 'Batu', 'Mongol Khan', 'mongol', D=250, flip=True)
M_BUR = PopMedallion('burundai_cut.png', 'Burundai', 'Mongol general', 'mongol', D=250, flip=True)
M_FALLEN = PopMedallion('yuri_cut.png', 'Yuri II', 'Slain on the Sit, 4 March 1238', 'rus', D=250, fallen=True, flip=True)
QUOTE = WD['words'][98:116]
CARD = SourceCard('rashid_portrait.png', 'Rashid al-Din', 'Ilkhanid historian, c. 1300',
                  [w['w'] for w in QUOTE], [w['t0'] for w in QUOTE], box=(70, 560, 860, 270))
# Edge returns words without punctuation; restore the quote's punctuation for display
CARD.lines = layout_words(['\u201cThe', 'emir', 'of', 'this', 'province,', 'Yurku,', 'fled', 'and', 'went', 'into', 'the', 'forest;', 'he', 'too', 'was', 'captured', 'and', 'killed.\u201d'], CARD.font, CARD.box[2] - 90)

ROUTE = [C['Vladimir'], (40.25, 56.6), (39.9, 57.1), (39.45, 57.55), (38.9, 57.85), CAMP]
FLAMES = {'Vladimir': -9, 'Suzdal': -9, 'Moscow': -9, 'Ryazan': -9, 'Kolomna': -9, 'Rostov': W(62), 'Yaroslavl': W(63) + 0.5, 'Tver': W(65) + 0.3,
          'Pereyaslavl': W(60), 'Uglich': W(69), 'Torzhok': W(149)}
ARROWS = [
    ([C['Vladimir'], (40.2, 56.6), (39.8, 56.95), C['Rostov']], W(56), W(62)),
    ([C['Rostov'], (39.6, 57.42), C['Yaroslavl']], W(62), W(63) + 0.6),
    ([C['Vladimir'], (39.6, 56.52), C['Pereyaslavl'], (37.9, 56.62), (36.8, 56.78), C['Tver']], W(57), W(65) + 0.3),
    ([C['Pereyaslavl'], (38.55, 57.15), C['Uglich']], W(59), W(69)),
]
HITS = [W(2), W(47), W(78), W(86), W(116), W(149)]


def map_layer(t):
    fr, sc, wl = cam.frame(t)
    zf = clamp(4.7 / wl, 0.75, 1.35)  # marks grow slightly when zoomed in
    # scorched trail of the horde (persists)
    for (pts, a0, a1), sd in zip(ARROWS, range(9)):
        scorch(fr, [sc(*p) for p in pts], ease_io(prog(t, a0, a1)), t, 46 * zf, .55, sd)
    scorch(fr, [sc(*p) for p in [C['Vladimir'], (40.9, 55.6), (40.4, 55.1), C['Ryazan']]], 1, t, 46 * zf, .55, 7)
    scorch(fr, [sc(*p) for p in [C['Vladimir'], (39.4, 55.9), (38.5, 55.85), C['Moscow']]], 1, t, 46 * zf, .55, 8)
    # sacked cities
    for n, t0 in FLAMES.items():
        if t >= t0: flame(fr, sc(*C[n]), t, smooth(prog(t, t0, t0 + .5)) * (1 if t - t0 < 4 else .8), zf)
    # Sit river highlight when named
    ga = life(t, W(44) - .3, W(56), .6, .8)
    if ga > 0: river_glow(fr, [sc(*p) for p in atlas.meander(R.SIT)], ga * .9)
    # Yuri's march north
    rk = ease_io(prog(t, W(30), W(45)))
    if t < W(86): arrow(fr, [sc(*p) for p in ROUTE], rk, 'rus', 10, 24, 1 - smooth(prog(t, W(56), W(57))), dashed=True)
    if W(30) <= t < W(45): tile(fr, path_at([sc(*p) for p in ROUTE], rk)[0], 'rus', t, W(30), s=46)
    # the camp and its scattered regiments
    camp_tiles = [CAMP, (38.66, 57.87), (38.24, 58.06)]
    for i, p in enumerate(camp_tiles):
        t0 = W(45) + i * .25
        cr = ease_out(prog(t, W(87) + i * .3, W(87) + .6 + i * .3))
        block(fr, sc(*p), 'rus', t, t0, scale=zf * .55, cols=3, rows=2, crossed=cr)
    if W(45) < t < W(47) + .5: ripples(fr, sc(*CAMP), t, W(45), W(47) + .5, R=80)
    # Mongol host at Vladimir
    vx0, vy0 = sc(*C['Vladimir'])
    block(fr, (vx0 - 40, vy0 + 110), 'mongol', t, W(47) + .2, W(57) + .5, scale=zf * .9)
    # columns tear through the land
    for pts, a0, a1 in ARROWS:
        arrow(fr, [sc(*p) for p in pts], ease_io(prog(t, a0, a1)), 'mongol', 14, 28, 1 - smooth(prog(t, W(73), W(75))))
    # Burundai's detachment
    bur_path = [C['Uglich'], (38.18, 57.7), (38.3, 57.86), (CAMP[0] - .03, CAMP[1] - .015)]
    tile(fr, (lambda p: (p[0] - 34, p[1] + 26))(sc(*C['Uglich'])), 'mongol', t, W(69), W(86), s=int(50 * zf))
    arrow(fr, [sc(*p) for p in bur_path], ease_io(prog(t, W(70), W(77))), 'mongol', 16, 32, 1 - smooth(prog(t, W(88), W(89))))
    if W(74) < t < W(86): ripples(fr, sc(*CAMP), t, W(74), W(86), (255, 236, 236), R=90)
    # battle: Mongol tiles close in
    for i, (a, b) in enumerate([((38.1, 57.78), (38.33, 57.92)), ((38.8, 57.78), (38.58, 57.9)), ((38.0, 58.15), (38.2, 58.02))]):
        k = ease_out(prog(t, W(86) - .1 + i * .2, W(87) + .3 + i * .2))
        block(fr, sc(lerp(a[0], b[0], k), lerp(a[1], b[1], k)), 'mongol', t, W(86) - .1 + i * .2, W(116), scale=zf * .55, cols=3, rows=2)
    cx, cy = sc(*CAMP)
    if t > W(86): paste(fr, swords_icon(), (cx, cy), back_out(prog(t, W(86), W(86) + .4)), 1)
    draw_pill3(fr, (cx + 60, cy - 170), t, W(86), W(116), 'Battle of the Sit River', '4 March 1238')
    # Torzhok and the road to Novgorod
    tx, ty = sc(*C['Torzhok'])
    draw_pill3(fr, (tx + 60, ty - 140), t, W(149), END, 'Siege of Torzhok', '1238', 'mongol', 'rus')
    arrow(fr, [sc(*p) for p in (C['Torzhok'], (34.0, 57.45), (32.9, 57.95), (31.8, 58.35), C['Novgorod'])], 0.86 * ease_io(prog(t, W(151), VEND + 1.2)), 'mongol', 16, 32)
    if t > W(153): ripples(fr, sc(*C['Novgorod']), t, W(153), END, R=90)
    # characters
    vx, vy = sc(*C['Vladimir'])
    M_YURI.draw(fr, (vx - 330, vy - 170), t, W(18) - .1, W(28), target=(vx - 20, vy - 10))
    M_BATU.draw(fr, (vx - 230, vy - 230), t, W(47), W(58) + .3, target=(vx - 30, vy - 10))
    ux, uy = sc(*C['Uglich'])
    M_BUR.draw(fr, (ux + 520, uy + 40), t, W(69) - .1, W(78) - .1, target=(ux + 25, uy + 15))
    M_FALLEN.draw(fr, (cx + 460, cy + 230), t, W(115) - .2, W(116) + .6, target=(cx, cy + 25))
    # source card (Rashid al-Din, words in sync)
    CARD.draw(fr, t, W(88) - .2, W(116) - .25)
    # year badge + chapter
    paste(fr, year_badge('1238'), (W_ - 160, 86), back_out(prog(t, W(1) - .2, W(1) + .3)), smooth(prog(t, W(1) - .2, W(1))))
    chapter(fr, t, 0.95, W(2) - 0.1, 'I', 'The Hunt for the Grand Prince')
    return fr


W_ = 1920

# ------------------------------------------------------------ tactical close-ups
TV = T.Tactical('vladimir', TS.VLADIMIR, [(W(2) - .6, 1500, 820, 2400), (W(12) + .7, 1480, 780, 1950)])
for cp in TV.camps: cp[0]['t0'] = W(2) - .5; cp[0]['spread'] = 1.2
TSIT = T.Tactical('sit', TS.SIT, [(W(36) - .6, 1700, 880, 2150), (W(47), 1760, 860, 1650),
                                   (W(86) - .3, 1760, 880, 2400), (W(100), 1780, 870, 1850), (W(116) + 1, 1790, 860, 1600)])
TSIT.camps[0][0].update(t0=W(36) - .3, spread=1.6, scale=1.3)
TTZ = T.Tactical('torzhok', TS.TORZHOK, [(W(141) - .3, 1500, 700, 2300), (W(151) + .4, 1500, 640, 1850)])
for cp in TTZ.camps: cp[0]['t0'] = W(141) - .2; cp[0]['spread'] = 1.4
M_VAS = None
SIT_RAIDS = [  # Mongol attack lanes into the Rus camp (base px): start, end, delay
    ([(3060, 520), (2500, 640), (2000, 760)], .0), ([(1900, 1860), (1900, 1400), (1820, 1070)], .3),
    ([(1150, -60), (1450, 300), (1640, 620)], .6), ([(3060, 1300), (2500, 1150), (2050, 980)], .9)]
SIT_TILES = [(1580, 760, -12), (1700, 960, 8), (1880, 820, -4), (1990, 950, 15), (1650, 650, 20), (1900, 680, -18), (1560, 940, 4)]


def tac_vladimir(t):
    fr, sc = TV.frame(t); TV.draw_camps(fr, sc, t)
    TV.burn_city(fr, sc, t, W(4), n=12, seed=3)
    TV.burn_city(fr, sc, t, W(13) - .2, n=6, seed=9)
    # siege ring of tiles around the walls
    for i, (x, y, a) in enumerate([(960, 760, 6), (2040, 740, -8), (1500, 1120, 0), (1150, 480, 12), (1860, 470, -14), (1200, 1050, -6), (1820, 1050, 9)]):
        T.paste(fr, T.rot_tile('mongol', 44, a), sc(x, y), back_out(prog(t, W(2) - .2 + i * .12, W(2) + .25 + i * .12)), 1)
    paste(fr, year_badge('1238'), (W_ - 160, 86), 1, 1)
    chapter(fr, t, 0.95, W(2) - 0.1, 'I', 'The Hunt for the Grand Prince')
    draw_pill3(fr, (W_ / 2, 120), t, W(2) - .2, W(12), 'Sack of Vladimir', 'February 1238')
    return fr


def tac_sit(t):
    fr, sc = TSIT.frame(t); TSIT.draw_camps(fr, sc, t)
    # Rus regiments in camp
    for i, (x, y, a) in enumerate(SIT_TILES):
        t0 = W(38) + i * .15
        cr = ease_out(prog(t, W(104) + i * .25, W(104) + .5 + i * .25))
        if t >= t0:
            paste(fr, T.rot_tile('rus', 44, a), sc(x, y), back_out(prog(t, t0, t0 + .4)), 1)
            if cr > 0:
                def fn(d, S, p=sc(x, y), cr=cr):
                    r = 20 * cr
                    for s_ in (1, -1): d.line([S((p[0] - r, p[1] - r * s_)), S((p[0] + r, p[1] + r * s_))], fill=(20, 16, 16, 255), width=Z * 6)
                    for s_ in (1, -1): d.line([S((p[0] - r, p[1] - r * s_)), S((p[0] + r, p[1] + r * s_))], fill=(240, 236, 230, 255), width=Z * 3)
                local_draw(fr, (sc(x, y)[0] - 30, sc(x, y)[1] - 30, sc(x, y)[0] + 30, sc(x, y)[1] + 30), fn)
    if t > W(86):
        # Mongol raids converge
        for pts, dl in SIT_RAIDS:
            k = ease_io(prog(t, W(86) + dl, W(88) + dl))
            arrow(fr, [sc(*p) for p in pts], k, 'mongol', 16, 34, 1 - smooth(prog(t, W(100), W(101))))
            tip = path_at([sc(*p) for p in pts], max(k, .01))[0]
            if k > 0: paste(fr, T.rot_tile('mongol', 44, int(dl * 30) - 10), (tip[0] + 30, tip[1] - 30), back_out(prog(t, W(86) + dl, W(86) + dl + .4)), 1)
        cx, cy = sc(1780, 850)
        paste(fr, swords_icon(60), (cx, cy - 10), back_out(prog(t, W(87), W(87) + .4)), 1)
        draw_pill3(fr, (W_ / 2, 110), t, W(86), W(116) + .4, 'Battle of the Sit River', '4 March 1238')
        M_BUR.draw(fr, (W_ - 330, 560), t, W(86) - .1, W(88) - .1, target=sc(2050, 980))
        CARD.draw(fr, t, W(88) - .2, W(116) - .25)
        M_FALLEN.draw(fr, (W_ - 330, 640), t, W(115) - .2, W(116) + .6, target=(cx, cy + 20))
    else:
        M_YURI_R.draw(fr, (W_ - 330, 330), t, W(39), W(46) + .6, target=sc(1780, 860))
        draw_pill3(fr, (W_ / 2, 110), t, W(43), W(47), 'Camp on the Sit', 'Winter 1237–38', 'rus', 'rus')
    paste(fr, year_badge('1238'), (W_ - 160, 86), 1, 1)
    return fr


def tac_torzhok(t):
    fr, sc = TTZ.frame(t); TTZ.draw_camps(fr, sc, t)
    for i, (x, y, a) in enumerate([(1100, 560, 8), (1900, 520, -10), (1500, 300, 4), (1250, 330, 14), (1760, 330, -12), (1500, 1020, 0)]):
        paste(fr, T.rot_tile('mongol', 44, a), sc(x, y), back_out(prog(t, W(141) + i * .12, W(141) + .4 + i * .12)), 1)
    TTZ.burn_city(fr, sc, t, W(150) - .1, n=10, seed=5)
    draw_pill3(fr, (W_ / 2, 110), t, W(142), W(151) + .6, 'Siege of Torzhok', '5 March 1238')
    paste(fr, year_badge('1238'), (W_ - 160, 86), 1, 1)
    return fr


SEGS = [(W(2) - .6, W(12) + .7, tac_vladimir, True), (W(36) - .5, W(47) - .1, tac_sit, True), (W(86) - .3, W(116) + .9, tac_sit, True),
        (W(141) - .3, W(151) + .3, tac_torzhok, True)]



def end_card(fr, t):
    a = smooth(prog(t, VEND + .5, VEND + 1.6))
    if a <= 0: return fr
    dark = Image.new('RGBA', fr.size, (14, 12, 16, int(185 * a))); fr.alpha_composite(dark)
    lay = Image.new('RGBA', fr.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.text((W_ / 2, 470), 'The Battle of the Sit River', font=F('IMFeENrm28P.ttf', 104), fill=(244, 236, 222, int(255 * a)), anchor='mm')
    d.text((W_ / 2, 575), '4 March 1238', font=F('IMFeENit28P.ttf', 46), fill=(214, 200, 180, int(255 * a)), anchor='mm')
    a2 = smooth(prog(t, VEND + 1.6, VEND + 2.4))
    d.text((W_ / 2, 700), 'Next: Kozelsk, the Evil City', font=F('IMFeENsc28P.ttf', 40), fill=(200, 70, 60, int(255 * a2)), anchor='mm')
    fr.alpha_composite(lay); return fr


def render(t):
    segs = [(t0, t1, (lambda tt, pl=pl, a=t0, b=t1: pl.render(tt, a, b))) for t0, t1, pl in PLATES] + [(a, b, fn) for a, b, fn, _ in SEGS]
    segs.sort(key=lambda s_: s_[0])
    act = []
    for t0, t1, fn in segs:
        a = min(smooth(prog(t, t0, t0 + XF)), 1 - smooth(prog(t, t1 - XF, t1)))
        if a > 0: act.append((a, fn))
    full = [i for i, (a, _) in enumerate(act) if a >= .999]
    if full: fr = act[full[-1]][1](t); act = act[full[-1] + 1:]
    else: fr = map_layer(t)
    for a, fn in act:
        top = fn(t)
        fr = Image.blend(fr.convert('RGBA'), top.convert('RGBA'), a)
    fr = end_card(fr, t)
    out = sharpen(grade(fr))
    out = drop_in(out, t, 0.8)
    fb = 1 - smooth(prog(t, END - 0.8, END))
    if fb < 1: out = Image.blend(Image.new('RGB', out.size), out, fb)
    return out
