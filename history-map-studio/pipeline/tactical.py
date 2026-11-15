"""Tactical close-up engine: winter battle maps at town scale (walled cities with streets and roofs,
camps with tents, fires and horses, scattered unit tiles), in the style of a zoomed-in siege map.
Static ground is rendered once per scene and cached; everything that moves is drawn per frame."""
import os, math, random, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import atlas
from kit import (Z, W, H, F, clamp, prog, smooth, ease_out, ease_io, back_out, lerp, life, down, paste,
                 local_draw, unit_tile, emblem, flame, flame_frames, arrow, catmull)

ROOT = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------- static ground
def _polyline(d, pts, width, fill):
    d.line(pts, fill=fill, width=int(width), joint='curve')
    r = width / 2
    for p in (pts[0], pts[-1]): d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=fill)


def _dist_field(size, draw_fn):
    """distance (px, approximate) from anything draw_fn paints, via repeated blur of a mask"""
    m = Image.new('L', size, 0); draw_fn(ImageDraw.Draw(m))
    a = np.asarray(m.filter(ImageFilter.GaussianBlur(60)), np.float32) / 255
    return a


def blob(cx, cy, rx, ry, seed, n=48, amp=0.10, rot=0.0):
    rng = random.Random(seed); ph = [rng.uniform(0, 6.28) for _ in range(3)]
    pts = []
    for i in range(n):
        a = i / n * 2 * math.pi
        k = 1 + amp * (math.sin(a * 2 + ph[0]) * .6 + math.sin(a * 3 + ph[1]) * .3 + math.sin(a * 5 + ph[2]) * .15)
        x, y = math.cos(a) * rx * k, math.sin(a) * ry * k
        pts.append((cx + x * math.cos(rot) - y * math.sin(rot), cy + x * math.sin(rot) + y * math.cos(rot)))
    return pts


def _city(base, d, c, seed):
    """walled city: dark interior, streets, embossed roofs, walls with towers and gates, letter-spaced label"""
    rng = random.Random(seed)
    cx, cy, rx, ry = c['center'][0], c['center'][1], c['rx'], c['ry']
    poly = blob(cx, cy, rx, ry, seed, amp=c.get('amp', .10), rot=c.get('rot', 0))
    # moat shadow + outer ring
    sh = Image.new('L', base.size, 0); ImageDraw.Draw(sh).polygon([(x + 10, y + 16) for x, y in poly], fill=150)
    sh = sh.filter(ImageFilter.GaussianBlur(18)); base.paste((40, 38, 40), (0, 0), sh)
    pal = c.get('pal', dict(ground=(78, 68, 64), street=(112, 100, 92), roof=(62, 52, 49), edge=(118, 104, 98), ridge=(44, 36, 34), wall=(132, 104, 84), wall_hi=(170, 140, 116)))
    d.polygon(poly, fill=pal['ground'])
    mask = Image.new('L', base.size, 0); ImageDraw.Draw(mask).polygon(poly, fill=255)
    lay = Image.new('RGBA', base.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    # streets: a few curved avenues through the gates + lanes
    gates = c.get('gates', [0.15, 0.55, 0.8])
    gpts = [poly[int(g * len(poly)) % len(poly)] for g in gates]
    hub = (cx + rng.uniform(-.15, .15) * rx, cy + rng.uniform(-.1, .1) * ry)
    streets = []
    for g in gpts:
        mid = ((g[0] + hub[0]) / 2 + rng.uniform(-.12, .12) * rx, (g[1] + hub[1]) / 2 + rng.uniform(-.12, .12) * ry)
        streets.append(catmull([g, mid, hub], 12))
    for _ in range(9):
        a = (cx + rng.uniform(-.85, .85) * rx, cy + rng.uniform(-.8, .8) * ry)
        b = (a[0] + rng.uniform(-.7, .7) * rx, a[1] + rng.uniform(-.6, .6) * ry)
        streets.append([a, b])
    smask = Image.new('L', base.size, 0); sd = ImageDraw.Draw(smask)
    for i, s in enumerate(streets): sd.line(s, fill=255, width=18 if i < len(gpts) else 10, joint='curve')
    sarr = np.asarray(smask) > 0; marr = np.asarray(mask) > 0
    ld.bitmap((0, 0), smask, fill=pal['street'] + (255,))
    # buildings
    ang0 = rng.uniform(0, 3.14)
    for _ in range(int(rx * ry / 160)):
        x = cx + rng.uniform(-1, 1) * rx; y = cy + rng.uniform(-1, 1) * ry
        if not (0 <= int(x) < base.width and 0 <= int(y) < base.height) or not marr[int(y), int(x)] or sarr[int(y), int(x)]: continue
        w, h = rng.uniform(14, 34), rng.uniform(10, 22)
        a = ang0 + rng.choice([0, math.pi / 2]) + rng.uniform(-.12, .12)
        ca, sa = math.cos(a), math.sin(a)
        corners = [(x + ca * dx - sa * dy, y + sa * dx + ca * dy) for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
        ld.polygon([(px + 3, py + 4) for px, py in corners], fill=(30, 24, 22, 170))
        sh_ = rng.uniform(.85, 1.1)
        ld.polygon(corners, fill=tuple(int(v * sh_) for v in pal['roof']) + (255,))
        ld.line([corners[3], corners[0], corners[1]], fill=pal['edge'] + (255,), width=2)
        ld.line([(corners[0][0] + corners[3][0]) / 2, (corners[0][1] + corners[3][1]) / 2, (corners[1][0] + corners[2][0]) / 2, (corners[1][1] + corners[2][1]) / 2], fill=pal['ridge'] + (255,), width=1)
    # churches (pale, cross-shaped)
    for k in range(c.get('churches', 2)):
        x = cx + rng.uniform(-.45, .45) * rx; y = cy + rng.uniform(-.4, .4) * ry; s = 18
        for bx in ((x - s, y - s / 2.6, x + s, y + s / 2.6), (x - s / 2.6, y - s, x + s / 2.6, y + s)):
            ld.rectangle([bx[0] + 3, bx[1] + 4, bx[2] + 3, bx[3] + 4], fill=(30, 24, 22, 170))
        for bx in ((x - s, y - s / 2.6, x + s, y + s / 2.6), (x - s / 2.6, y - s, x + s / 2.6, y + s)):
            ld.rectangle(bx, fill=(196, 190, 182, 255), outline=(90, 80, 76, 255))
        ld.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(214, 178, 96, 255), outline=(90, 70, 40, 255))
    clip = Image.new('L', base.size, 0); clip.paste(lay.getchannel('A'), (0, 0), mask)
    lay.putalpha(clip); base.alpha_composite(lay)
    d = ImageDraw.Draw(base)
    for s in streets: pass
    # walls
    ring = poly + [poly[0]]
    d.line(ring, fill=(42, 32, 28), width=24, joint='curve')
    d.line(ring, fill=pal['wall'], width=14, joint='curve')
    d.line(ring, fill=pal['wall_hi'], width=4, joint='curve')
    for i in range(0, len(poly), 4):
        x, y = poly[i]; d.ellipse([x - 11, y - 11, x + 11, y + 11], fill=(120, 94, 76), outline=(40, 30, 26), width=3)
    for g in gpts:
        d.rectangle([g[0] - 16, g[1] - 16, g[0] + 16, g[1] + 16], fill=(96, 74, 60), outline=(36, 28, 24), width=4)
    # label
    lab = c.get('label')
    if lab:
        txt = ' '.join(lab); fnt = F('Almendra-Regular.ttf', c.get('fs', 64))
        ll = Image.new('RGBA', base.size, (0, 0, 0, 0)); dd = ImageDraw.Draw(ll)
        lx, ly = cx + c.get('lab_off', (0, 0))[0], cy + c.get('lab_off', (0, 0))[1]
        dd.text((lx + 3, ly + 4), txt, font=fnt, fill=(20, 16, 16, 150), anchor='mm')
        dd.text((lx, ly), txt, font=fnt, fill=(232, 230, 228, 215), anchor='mm')
        rot = c.get('lab_rot', 0)
        if rot: ll = ll.rotate(rot, center=(lx, ly), resample=Image.BICUBIC)
        base.alpha_composite(ll)
    return poly, gpts


def build_scene(spec, cache):
    if os.path.exists(cache): return Image.open(cache).convert('RGBA'), spec.get('_meta')
    Wd, Hd = spec['size']; seed = spec.get('seed', 1); rng = random.Random(seed)
    # ground: cold grey with soft relief and smudges
    n1 = atlas.noise(Hd, Wd, [700, 260, 90], seed, .55)
    n2 = atlas.noise(Hd, Wd, [40, 14], seed + 1, .7)
    hgt = n1 * 60 + n2 * 1.5
    gy, gx = np.gradient(hgt)
    shade = np.clip(1 + (-gx * .55 - gy * .65) * 0.9, .7, 1.25)
    tone = spec.get('ground', (168, 170, 176))
    g = np.stack([np.full((Hd, Wd), v, np.float32) for v in tone], -1)
    sm = atlas.noise(Hd, Wd, [380, 150], seed + 5, .6)
    g *= (0.78 + 0.34 * sm)[..., None] * (0.92 + 0.14 * n1)[..., None] * shade[..., None]
    base = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(base)
    # roads
    for rd in spec.get('roads', []):
        pts = catmull(rd, 14); d.line(pts, fill=(118, 116, 118), width=7, joint='curve'); d.line(pts, fill=(150, 148, 150), width=3, joint='curve')
    for wl_ in spec.get('wagons', []):   # chained wagons (wagon fort)
        pts = catmull(wl_, 10); acc = 0.0
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            acc += math.dist((x0, y0), (x1, y1))
            if acc < 34: continue
            acc = 0; ang = math.atan2(y1 - y0, x1 - x0); ca, sa = math.cos(ang), math.sin(ang)
            box = [(x1 + ca * dx - sa * dy, y1 + sa * dx + ca * dy) for dx, dy in ((-15, -9), (15, -9), (15, 9), (-15, 9))]
            d.polygon([(x + 3, y + 4) for x, y in box], fill=(40, 34, 30)); d.polygon(box, fill=(122, 90, 58), outline=(54, 38, 26))
            d.line([(x1 - ca * 22, y1 - sa * 22), (x1 - ca * 12, y1 - sa * 12)], fill=(60, 52, 46), width=3)
    # rivers (frozen): dark bank, ice, streaks
    river_mask = Image.new('L', base.size, 0); rm = ImageDraw.Draw(river_mask)
    for rv in sorted(spec.get('rivers', []), key=lambda r: r['w']):
        pts = catmull(rv['pts'], 16); w = rv['w']
        wc = spec.get('water', ((84, 88, 98), (140, 146, 158), (180, 188, 202), (196, 204, 216), (226, 232, 240)))
        d.line(pts, fill=wc[0], width=int(w + 16), joint='curve'); d.line(pts, fill=wc[1], width=int(w + 6), joint='curve')
        d.line(pts, fill=wc[2], width=int(w), joint='curve'); d.line(pts, fill=wc[3], width=int(w * .6), joint='curve'); _polyline(rm, pts, w + 40, 255)
        for k in range(int(len(pts) / 3)):
            i = rng.randrange(1, len(pts) - 1); p, q = pts[i - 1], pts[i + 1]
            off = rng.uniform(-w * .3, w * .3); an = math.atan2(q[1] - p[1], q[0] - p[0])
            ox, oy = -math.sin(an) * off, math.cos(an) * off
            d.line([(p[0] + ox, p[1] + oy), (q[0] + ox, q[1] + oy)], fill=wc[4], width=rng.choice([2, 3, 4]))
        if rv.get('label'):
            i = int(len(pts) * rv.get('lab_at', .5)); p, q = pts[i - 1], pts[i + 1]
            an = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
            if an > 90: an -= 180
            if an < -90: an += 180
            ll = Image.new('RGBA', base.size, (0, 0, 0, 0)); dd = ImageDraw.Draw(ll)
            px, py = pts[i][0], pts[i][1] + w * .9 + 18
            dd.text((px, py), rv['label'], font=F('Almendra-Regular.ttf', 46), fill=(60, 64, 74, 235), anchor='mm')
            base.alpha_composite(ll.rotate(-an, center=(px, py), resample=Image.BICUBIC))
    # cities
    meta = {'cities': []}
    keep = Image.new('L', base.size, 0); kd = ImageDraw.Draw(keep)
    for c in spec.get('cities', []):
        kd.ellipse([c['center'][0] - c['rx'] * 1.35, c['center'][1] - c['ry'] * 1.35, c['center'][0] + c['rx'] * 1.35, c['center'][1] + c['ry'] * 1.35], fill=255)
    for cl in spec.get('clear', []):
        x, y, r = cl; kd.ellipse([x - r, y - r, x + r, y + r], fill=255)
    keep_a = np.asarray(keep.filter(ImageFilter.GaussianBlur(40)), np.float32) / 255
    riv_a = np.asarray(river_mask.filter(ImageFilter.GaussianBlur(20)), np.float32) / 255
    # trees: clumped grey woods
    fn = atlas.noise(Hd, Wd, [520, 200, 80], seed + 7, .6)
    dens = (fn - spec.get('forest', .52)) * 9 - keep_a * 4 - riv_a * 3
    spr = atlas.tree_sprites(spec.get('tree', 44)); step = int(spec.get('tree', 44) * .62)
    trees = []
    for y in range(0, Hd, step):
        for x in range(0, Wd, step):
            jx, jy = x + rng.uniform(-.45, .45) * step, y + rng.uniform(-.45, .45) * step
            if not (0 <= jx < Wd and 0 <= jy < Hd): continue
            p = clamp(dens[int(jy), int(jx)], 0, 1)
            if p > 0 and rng.random() < max(p, 0.015 if dens[int(jy), int(jx)] > -1.2 else 0): trees.append((jy, jx))
    trees.sort()
    tint = np.array(spec.get('tree_tint', (1.02, 1.02, 1.06)), np.float32)
    tinted = []
    for s in spr:
        a = np.asarray(s, np.float32); a[..., :3] = np.clip(a[..., :3] * tint, 0, 255); tinted.append(Image.fromarray(a.astype(np.uint8)))
    for jy, jx in trees:
        s = tinted[rng.randrange(len(tinted) - 3)]
        base.alpha_composite(s, (int(jx - s.width / 2), int(jy - s.height / 2))) if jx - s.width / 2 >= 0 and jy - s.height / 2 >= 0 and jx + s.width / 2 < Wd and jy + s.height / 2 < Hd else None
    d = ImageDraw.Draw(base)
    for c in spec.get('cities', []):
        poly, gates = _city(base, d, c, seed + 3); meta['cities'].append({'poly': poly, 'gates': gates})
    # bridges
    for b in spec.get('bridges', []):
        (x0, y0), (x1, y1) = b
        d.line([(x0, y0), (x1, y1)], fill=(40, 32, 28), width=26); d.line([(x0, y0), (x1, y1)], fill=(112, 92, 76), width=18)
    # vignette-ish grain
    base.save(cache); spec['_meta'] = meta
    return base, meta


# ---------------------------------------------------------------- sprites
@functools.lru_cache(None)
def tent(kind, s=34):
    from kit import KC
    col = {'mongol': (40, 58, 168), 'rus': (176, 36, 42)}.get(kind, KC[kind])
    hi = tuple(min(255, c + 70) for c in col); lo = tuple(int(c * .55) for c in col)
    im = Image.new('RGBA', (int(s * 1.6 * Z), int(s * 1.6 * Z)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = im.width / 2; S = s * Z
    if kind in ('mongol', 'abbasid'):  # ger: dome over drum
        d.ellipse([c - S * .5 + 5 * Z, c - S * .05 + 6 * Z, c + S * .5 + 5 * Z, c + S * .55 + 6 * Z], fill=(0, 0, 0, 110))
        d.rectangle([c - S * .46, c - S * .02, c + S * .46, c + S * .38], fill=lo, outline=(16, 18, 40), width=2 * Z)
        d.pieslice([c - S * .5, c - S * .52, c + S * .5, c + S * .44], 180, 360, fill=col, outline=(16, 18, 40), width=2 * Z)
        d.line([c - S * .3, c - S * .34, c - S * .05, c - S * .4], fill=hi, width=2 * Z)
        d.rectangle([c - S * .1, c + S * .08, c + S * .1, c + S * .38], fill=(30, 22, 18))
        # gold star
        pts = []
        if kind != 'mongol': return down(im)
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5; r = S * (.13 if i % 2 == 0 else .055)
            pts.append((c + S * .22 + r * math.cos(a), c - S * .22 + r * math.sin(a)))
        d.polygon(pts, fill=(246, 206, 80))
    else:  # pointed Rus tent
        d.polygon([(c + 5 * Z, c - S * .55 + 6 * Z), (c - S * .45 + 5 * Z, c + S * .38 + 6 * Z), (c + S * .45 + 5 * Z, c + S * .38 + 6 * Z)], fill=(0, 0, 0, 110))
        d.polygon([(c, c - S * .55), (c - S * .45, c + S * .38), (c, c + S * .38)], fill=col, outline=(40, 10, 10), width=2 * Z)
        d.polygon([(c, c - S * .55), (c + S * .45, c + S * .38), (c, c + S * .38)], fill=lo, outline=(40, 10, 10), width=2 * Z)
        d.polygon([(c, c), (c - S * .12, c + S * .38), (c + S * .12, c + S * .38)], fill=(36, 20, 16))
        d.line([c, c - S * .55, c, c - S * .78], fill=(60, 40, 30), width=2 * Z)
        d.polygon([(c, c - S * .78), (c + S * .2, c - S * .72), (c, c - S * .64)], fill=(236, 210, 120) if kind == 'rus' else (246, 244, 236))
    return down(im)


@functools.lru_cache(None)
def horse(s=30, flip=False, tone=0):
    cols = [(122, 86, 58), (96, 66, 46), (150, 118, 86)][tone]
    im = Image.new('RGBA', (int(s * 1.5 * Z), int(s * 1.2 * Z)), (0, 0, 0, 0)); d = ImageDraw.Draw(im); S = s * Z
    ox, oy = S * .2, S * .25
    def P(x, y): return (ox + x * S, oy + y * S)
    sh = [P(.05, .78), P(1.0, .78)]
    d.ellipse([*P(.05, .70), *P(1.0, .86)], fill=(0, 0, 0, 80))
    for lx in (.22, .32, .68, .78): d.line([P(lx, .45), P(lx + .02, .78)], fill=(40, 28, 20), width=int(S * .07))
    d.ellipse([*P(.12, .25), *P(.88, .58)], fill=cols, outline=(40, 28, 20), width=Z * 2)
    d.polygon([P(.72, .38), P(.84, .02), P(1.02, .04), P(1.06, .16), P(.92, .22), P(.86, .44)], fill=cols, outline=(40, 28, 20))
    d.line([P(.8, .06), P(.7, .34)], fill=(40, 28, 20), width=int(S * .06))  # mane
    d.line([P(.14, .36), P(.02, .62)], fill=(40, 28, 20), width=int(S * .07))  # tail
    d.ellipse([*P(.4, .22), *P(.58, .34)], fill=(70, 46, 30))  # saddle
    im = down(im)
    return im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im


@functools.lru_cache(None)
def rot_tile(kind, s, ang):
    return unit_tile(kind, s).rotate(ang, resample=Image.BICUBIC, expand=True)


@functools.lru_cache(None)
def smoke_puff(r):
    im = Image.new('RGBA', (int(r * 2.4), int(r * 2.4)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = im.width / 2; d.ellipse([c - r, c - r, c + r, c + r], fill=(44, 42, 44, 170))
    return im.filter(ImageFilter.GaussianBlur(r * .35))


def campfire(frame, pos, t, a=1.0, scale=.42):
    x, y = pos
    def fn(d, S):
        for r, al in ((14, 45), (8, 70)): d.ellipse([S((x - r, y - r)), S((x + r, y + r))], fill=(255, 150, 50, int(al * a)))
    local_draw(frame, (x - 30, y - 30, x + 30, y + 30), fn)
    flame(frame, pos, t, a, scale)


def smoke(frame, pos, t, a=1.0, size=1.0, seed=0):
    rng = random.Random(seed)
    for k in range(6):
        ph = (t * .35 + k / 6 + rng.random() * .1) % 1
        r = (18 + 40 * ph) * size
        px = pos[0] + (ph * 90 + rng.uniform(-10, 10)) * size; py = pos[1] - (20 + ph * 170) * size
        sp = smoke_puff(int(r)); al = a * (1 - ph) * .8
        if al > .02: paste(frame, sp, (px, py), 1.0, al)


# ---------------------------------------------------------------- scene + camera
class Tactical:
    def __init__(self, name, spec, keys):
        self.spec = spec
        self.base, self.meta = build_scene(spec, os.path.join(ROOT, f'build/tac_{name}.png'))
        self.keys = sorted(keys)  # (t, cx, cy, view_w) in base pixels
        rng = random.Random(spec.get('seed', 1) * 7)
        self.camps = []
        for cp in spec.get('camps', []):
            items = []
            x0, y0 = cp['center']; rx, ry = cp['r']
            def spot():
                for _ in range(60):
                    a = rng.uniform(0, 6.283); k = math.sqrt(rng.random())
                    p = (x0 + math.cos(a) * rx * k, y0 + math.sin(a) * ry * k)
                    if all(math.dist(p, q[1]) > 30 for q in items): return p
                return p
            for _ in range(cp.get('tents', 12)): items.append(('tent', spot(), rng.random()))
            for _ in range(cp.get('horses', 8)): items.append(('horse', spot(), rng.random()))
            for _ in range(cp.get('fires', 8)): items.append(('fire', spot(), rng.random()))
            for _ in range(cp.get('tiles', 6)): items.append(('tile', spot(), rng.random()))
            items.sort(key=lambda it: it[1][1])
            self.camps.append((cp, items))

    def view(self, t):
        ks = self.keys
        if t <= ks[0][0]: k = ks[0][1:]
        elif t >= ks[-1][0]: k = ks[-1][1:]
        else:
            for a, b in zip(ks, ks[1:]):
                if a[0] <= t <= b[0]:
                    u = ease_io(prog(t, a[0], b[0])); k = tuple(lerp(p, q, u) for p, q in zip(a[1:], b[1:])); break
        return k

    def frame(self, t):
        cx, cy, vw = self.view(t); vh = vw * H / W
        BW, BH = self.base.size; vw = min(vw, BW, BH * W / H); vh = vw * H / W
        cx = clamp(cx, vw / 2, BW - vw / 2); cy = clamp(cy, vh / 2, BH - vh / 2)
        box = (cx - vw / 2, cy - vh / 2, cx + vw / 2, cy + vh / 2)
        fr = self.base.resize((W, H), Image.BICUBIC, box=box)
        s = W / vw
        def sc(x, y): return ((x - box[0]) * s, (y - box[1]) * s)
        self.s = s
        return fr, sc

    def draw_camps(self, fr, sc, t):
        for cp, items in self.camps:
            t0 = cp.get('t0', -9); t1 = cp.get('t1', 1e9); kind = cp['kind']
            for typ, p, r in items:
                ti = t0 + r * cp.get('spread', .8)
                if t < ti or t > t1: continue
                k = back_out(prog(t, ti, ti + .35)) * (1 - ease_out(prog(t, t1 - .3, t1)))
                a = min(1, prog(t, ti, ti + .1) * 2)
                pos = sc(*p)
                if typ == 'tent': paste(fr, tent(kind, int(36 * cp.get('scale', 1))), pos, k, a)
                elif typ == 'horse': paste(fr, horse(28, r > .5, int(r * 3) % 3), pos, k, a)
                elif typ == 'fire': campfire(fr, pos, t + r * 3, a * k)
                elif typ == 'tile':
                    ang = (r * 997 % 1 - .5) * 70
                    paste(fr, rot_tile(kind, 40, round(ang)), pos, k, a)
                if cp.get('burn') and typ == 'tent' and t > cp['burn'] + r * .8:
                    flame(fr, (pos[0], pos[1] - 8), t + r, smooth(prog(t, cp['burn'] + r * .8, cp['burn'] + r * .8 + .4)), .55)

    def burn_city(self, fr, sc, t, t0, idx=0, n=10, seed=0, a=1.0):
        if t < t0: return
        poly = self.meta['cities'][idx]['poly'] if self.meta else None
        c = self.spec['cities'][idx]; cx, cy, rx, ry = c['center'][0], c['center'][1], c['rx'], c['ry']
        rng = random.Random(seed)
        pts = [(cx + rng.uniform(-.75, .75) * rx, cy + rng.uniform(-.7, .7) * ry) for _ in range(n)]
        for i, p in enumerate(pts):
            ti = t0 + i * .18
            if t < ti: continue
            k = smooth(prog(t, ti, ti + .5)) * a
            q = sc(*p)
            smoke(fr, q, t + i, k, 1.3 * self.s, seed + i)
        for i, p in enumerate(pts):
            ti = t0 + i * .18
            if t < ti: continue
            k = smooth(prog(t, ti, ti + .5)) * a
            flame(fr, sc(*p), t + i * .37, k, 1.5 * self.s)
