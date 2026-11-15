"""Sheet transitions and the channel logo sting.

sheet(A, B, e, side)    the next scene arrives as a printed sheet: it slides in tilted with a slight perspective lift
                        (the leading edge comes toward the camera like a page rolling in), casts a soft shadow on the
                        old scene, and flattens as it lands. e = 0..1 progress. side = 'top' (default, falls from top to bottom) | 'bottom' | 'right' | 'left'.
                        glow=(r, g, b) adds a light bleeding from the leading edge (used for the logo sting).
Sting(brand)            channel logo card: dark slate, a gold gear that turns, an emblem in its centre and the channel
                        name in bevelled gold. .frame(t_local) -> RGB.

Own design only. Never trace another channel's logo: give your own PNG in BRAND['emblem'] (centre symbol, transparent)
or BRAND['logo'] (a whole static logo), otherwise a compass-star emblem is generated.
"""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

W, H = 1920, 1080
ROOT = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(ROOT, 'assets', 'fonts')


def _ease(x): x = min(1, max(0, x)); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2   # ease in-out: slow start, slow landing
def _smooth(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)


def _coeffs(dst, src):
    """perspective coeffs mapping output (dst) points back to input (src) points, for Image.transform"""
    A = []; b = []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); b.append(v)
    return np.linalg.solve(np.array(A, float), np.array(b, float)).tolist()


def _corners(e, side):
    """destination corners (TL, TR, BR, BL) of the incoming sheet at progress e"""
    k = 1 - _ease(e)                       # 1 -> 0
    lift = 0.10 * k                        # leading edge nearer the camera (bigger)
    if side == 'top':
        rot = math.radians(6 * k); dx, dy = -W * 0.04 * k, -H * 1.12 * k
        pts = [(0, 0), (W, 0), (W + W * lift, H + H * lift * .5), (-W * lift, H + H * lift * .5)]
    elif side == 'bottom':
        rot = math.radians(-7 * k); dx, dy = W * 0.04 * k, H * 1.12 * k
        pts = [(-W * lift, -H * lift * .5), (W + W * lift, -H * lift * .5), (W, H), (0, H)]
    elif side == 'right':
        rot = math.radians(5 * k); dx, dy = W * 1.10 * k, H * 0.06 * k
        pts = [(-W * lift * .5, -H * lift), (W, 0), (W, H), (-W * lift * .5, H + H * lift)]
    else:  # left
        rot = math.radians(-5 * k); dx, dy = -W * 1.10 * k, H * 0.06 * k
        pts = [(0, 0), (W + W * lift * .5, -H * lift), (W + W * lift * .5, H + H * lift), (0, H)]
    cx, cy = W / 2, H / 2; c, s = math.cos(rot), math.sin(rot)
    return [(cx + (x - cx) * c - (y - cy) * s + dx, cy + (x - cx) * s + (y - cy) * c + dy) for x, y in pts]


def sheet(A, B, e, side='top', glow=None):
    if e >= 1: return B.convert('RGB')
    A = A.convert('RGB'); B = B.convert('RGB')
    if e <= 0: return A
    dst = _corners(e, side); src = [(0, 0), (W, 0), (W, H), (0, H)]
    cf = _coeffs(dst, src)
    Bw = B.transform((W, H), Image.PERSPECTIVE, cf, Image.BICUBIC)
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).polygon(dst, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(0.8))
    a = np.asarray(A, np.float32); b = np.asarray(Bw, np.float32); mk = np.asarray(m, np.float32)[..., None] / 255
    # shadow cast forward onto the old scene
    sh = m.filter(ImageFilter.GaussianBlur(28)); off = {'top': (0, 18), 'bottom': (0, -18), 'right': (-22, 0), 'left': (22, 0)}[side]
    sh = ImageChops.offset(sh, *off)
    shd = np.asarray(sh, np.float32)[..., None] / 255 * (0.62 * (1 - _smooth(e) * .5))
    a = a * (1 - shd)
    # leading edge: highlight on the sheet (page curl) and optional light glow beyond it
    p0, p1 = {'top': (dst[3], dst[2]), 'bottom': (dst[0], dst[1]), 'right': (dst[0], dst[3]), 'left': (dst[1], dst[2])}[side]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    nx, ny = p1[1] - p0[1], -(p1[0] - p0[0]); nl = math.hypot(nx, ny) or 1; nx /= nl; ny /= nl
    d = (xx - p0[0]) * nx + (yy - p0[1]) * ny
    far = {'top': (W / 2, -H * 2), 'bottom': (W / 2, H * 2), 'right': (W * 2, H / 2), 'left': (-W, H / 2)}[side]   # a point deep on the sheet's side
    inside_sign = 1 if ((far[0] - p0[0]) * nx + (far[1] - p0[1]) * ny) > 0 else -1
    d = d * inside_sign                                  # >0 on the sheet, <0 ahead of it
    band = np.clip(1 - d / 70, 0, 1) * (d > 0)
    hi = (band ** 2 * 0.30 * (1 - e * .6))[..., None]
    b = b + (255 - b) * hi - b * (np.clip(1 - np.abs(d - 74) / 30, 0, 1) * .10 * (1 - e))[..., None]
    out = a * (1 - mk) + b * mk
    if glow is not None:
        g = np.array(glow, np.float32)
        gl = (np.clip(1 + d / 150, 0, 1) ** 2.2 * (d <= 0) * 0.85 + np.clip(1 - np.abs(d) / 5, 0, 1) * .9) * min(1, (1 - e) * 2.5)
        out = out + (g - out * .3) * gl[..., None] * .8
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


# ---------------------------------------------------------------- logo sting
GOLD = [(255, 236, 170), (246, 200, 104), (214, 150, 52), (150, 92, 24)]


def _gold_fill(mask, top=0, bot=None):
    """vertical gold gradient + bevel (lit from the top left) clipped to mask"""
    w, h = mask.size; bot = bot or h
    ys = np.linspace(0, 1, h)[:, None]
    stops = np.array(GOLD, np.float32); pos = np.linspace(0, 1, len(GOLD))
    col = np.stack([np.interp(ys[:, 0], pos, stops[:, c]) for c in range(3)], -1)[:, None, :].repeat(w, 1)
    m = np.asarray(mask, np.float32) / 255
    bl = np.asarray(mask.filter(ImageFilter.GaussianBlur(4)), np.float32) / 255
    gx = np.roll(bl, 3, 1) - np.roll(bl, -3, 1); gy = np.roll(bl, 3, 0) - np.roll(bl, -3, 0)
    shade = np.clip((gx + gy) * 1.6, -1, 1)[..., None]
    col = np.where(shade > 0, col + (255 - col) * shade * .8, col * (1 + shade * .55))
    grain = (np.random.default_rng(3).random((h, w)) - .5)[..., None] * 18
    col = np.clip(col + grain, 0, 255)
    rgba = np.concatenate([col, (m * 255)[..., None]], -1).astype(np.uint8)
    return Image.fromarray(rgba, 'RGBA')


def _shadowed(img, r=14, off=(0, 10), a=0.75):
    pad = r * 3; w, h = img.size
    out = Image.new('RGBA', (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    sh = Image.new('RGBA', out.size, (0, 0, 0, 0))
    al = img.split()[3].point(lambda v: int(v * a))
    blk = Image.new('RGBA', img.size, (8, 6, 4, 255)); blk.putalpha(al)
    sh.paste(blk, (pad + off[0], pad + off[1]), blk); sh = sh.filter(ImageFilter.GaussianBlur(r))
    out = Image.alpha_composite(out, sh); out.alpha_composite(img, (pad, pad)); return out


def gear_mask(R=250, teeth=26, inner=0.70, hole=0.55, tooth=0.11):
    S = int(R * 2.2); c = S / 2; ss = 3
    m = Image.new('L', (S * ss, S * ss), 0); d = ImageDraw.Draw(m)
    pts = []
    for i in range(teeth * 4):
        a = 2 * math.pi * i / (teeth * 4); ph = i % 4
        r = R * (1 if ph in (1, 2) else 1 - tooth)
        da = (math.pi / (teeth * 4)) * (.35 if ph in (1, 2) else -.35) * (1 if ph in (1, 3) else -1)
        pts.append(((c + r * math.cos(a + da)) * ss, (c + r * math.sin(a + da)) * ss))
    d.polygon(pts, fill=255)
    r2 = R * inner; d.ellipse([(c - r2) * ss, (c - r2) * ss, (c + r2) * ss, (c + r2) * ss], fill=0)
    r3 = R * (inner - .05); r4 = R * hole
    d.ellipse([(c - r3) * ss, (c - r3) * ss, (c + r3) * ss, (c + r3) * ss], fill=255)
    d.ellipse([(c - r4) * ss, (c - r4) * ss, (c + r4) * ss, (c + r4) * ss], fill=0)
    return m.resize((S, S), Image.LANCZOS)


def star_mask(S=300, n=8):
    ss = 3; m = Image.new('L', (S * ss, S * ss), 0); d = ImageDraw.Draw(m); c = S * ss / 2
    pts = []
    for i in range(n * 2):
        a = -math.pi / 2 + math.pi * i / n; r = (S * .48 if i % 4 == 0 else S * .30 if i % 2 == 0 else S * .11) * ss
        pts.append((c + r * math.cos(a), c + r * math.sin(a)))
    d.polygon(pts, fill=255); r = S * .07 * ss; d.ellipse([c - r, c - r, c + r, c + r], fill=0)
    return m.resize((S, S), Image.LANCZOS)


def _slate(seed=5):
    rng = np.random.default_rng(seed)
    n = np.zeros((H, W), np.float32)
    for s, a in ((8, .5), (32, .3), (128, .2)):
        g = rng.random((H // s + 2, W // s + 2)).astype(np.float32)
        n += np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((W + s * 2, H + s * 2), Image.BICUBIC), np.float32)[:H, :W] / 255 * a
    yy, xx = np.mgrid[0:H, 0:W]; r = np.hypot((xx - W / 2) / W, (yy - H * .42) / H)
    v = np.clip(1 - r * 1.3, 0, 1)
    base = 22 + n * 22 + v * 26
    img = np.stack([base, base * .98, base * .96], -1)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


class Sting:
    def __init__(self, brand):
        self.b = brand or {}
        self.bg = Image.new('RGB', (W, H), (0, 0, 0))   # pure black behind the logo (user 2026-11-15)
        logo = self.b.get('logo')
        if logo and os.path.exists(os.path.join(ROOT, 'assets', logo)):
            self.logo = _shadowed(Image.open(os.path.join(ROOT, 'assets', logo)).convert('RGBA')); self.gear = None
            return
        self.logo = None
        R = int(self.b.get('gear_r', 235))
        self.gear = _shadowed(_gold_fill(gear_mask(R)), 16, (0, 12))
        em = self.b.get('emblem')
        if em and os.path.exists(os.path.join(ROOT, 'assets', em)):
            e = Image.open(os.path.join(ROOT, 'assets', em)).convert('RGBA'); k = R * 1.0 / max(e.size); e = e.resize((int(e.width * k), int(e.height * k)), Image.LANCZOS)
            self.emblem = _shadowed(e, 10, (0, 8))
        else:
            self.emblem = _shadowed(_gold_fill(star_mask(int(R * 1.02))), 10, (0, 8))
        name = self.b.get('name', 'YOUR CHANNEL')
        f = ImageFont.truetype(os.path.join(FONTS, self.b.get('font', 'Rye-Regular.ttf')), int(self.b.get('size', 118)))
        bb = f.getbbox(name); tw, th = bb[2] - bb[0] + 40, bb[3] - bb[1] + 40
        tm = Image.new('L', (tw, th), 0); ImageDraw.Draw(tm).text((20 - bb[0], 20 - bb[1]), name, font=f, fill=255)
        out = tm.filter(ImageFilter.MaxFilter(7))
        dark = Image.new('RGBA', (tw, th), (40, 22, 6, 255)); dark.putalpha(out)
        dark.alpha_composite(_gold_fill(tm)); self.text = _shadowed(dark, 12, (0, 10))

    def frame(self, tl):
        """tl = seconds since the sting started"""
        fr = self.bg.copy().convert('RGBA')
        if self.logo is not None:
            lg = self.logo; fr.alpha_composite(lg, ((W - lg.width) // 2, (H - lg.height) // 2)); return fr.convert('RGB')
        cx, cy = W // 2, int(H * .40)
        # warm light behind the emblem
        halo = Image.new('L', (W, H), 0); r = 330
        ImageDraw.Draw(halo).ellipse([cx - r, cy - r, cx + r, cy + r], fill=int(46 + 18 * math.sin(tl * 2.2)))
        halo = halo.filter(ImageFilter.GaussianBlur(90)); glow = Image.new('RGBA', (W, H), (255, 190, 90, 0)); glow.putalpha(halo)
        fr.alpha_composite(glow)
        ang = -(tl * 38 + 22 * _ease(min(1, tl / 1.2)))   # the gear turns (a little kick as it lands, then a steady turn)
        g = self.gear.rotate(ang, Image.BICUBIC)
        fr.alpha_composite(g, (cx - g.width // 2, cy - g.height // 2))
        e = self.emblem; fr.alpha_composite(e, (cx - e.width // 2, cy - e.height // 2))
        tx = self.text; fr.alpha_composite(tx, (cx - tx.width // 2, int(H * .80) - tx.height // 2))
        # a glint sweeping across the name
        gx = int((tl - .9) / 1.1 * (tx.width + 400)) - 200
        if 0 < tl - .9 < 1.1:
            sw = Image.new('L', (W, H), 0); ImageDraw.Draw(sw).polygon([(cx - tx.width // 2 + gx, int(H * .70)), (cx - tx.width // 2 + gx + 70, int(H * .70)),
                                                                   (cx - tx.width // 2 + gx + 20, int(H * .90)), (cx - tx.width // 2 + gx - 50, int(H * .90))], fill=120)
            tm = Image.new('L', (W, H), 0); tm.paste(tx.split()[3], (cx - tx.width // 2, int(H * .80) - tx.height // 2))
            sw = ImageChops.multiply(sw.filter(ImageFilter.GaussianBlur(10)), tm)
            wl = Image.new('RGBA', (W, H), (255, 250, 220, 0)); wl.putalpha(sw); fr.alpha_composite(wl)
        return fr.convert('RGB')


if __name__ == '__main__':
    import sys
    st = Sting({'name': sys.argv[1] if len(sys.argv) > 1 else 'YOUR CHANNEL'})
    os.makedirs('/tmp/trans', exist_ok=True)
    A = Image.new('RGB', (W, H), (40, 70, 90)); B = Image.new('RGB', (W, H), (200, 180, 140))
    for i, e in enumerate((.25, .5, .75)): sheet(A, B, e, 'bottom').save(f'/tmp/trans/b{i}.jpg')
    for i, e in enumerate((.3, .6)): sheet(A, st.frame(e * .7), e, 'bottom', glow=(255, 200, 110)).save(f'/tmp/trans/g{i}.jpg')
    st.frame(1.5).save('/tmp/trans/sting.jpg'); print('ok')


def push(A, B, e, side='right'):
    """smooth push: the new view slides in from `side` and pushes the old one out, no gap, no backdrop; soft seam shadow"""
    A = A.convert('RGB'); B = B.convert('RGB')
    if e <= 0: return A
    if e >= 1: return B
    k = e * e * e * (e * (e * 6 - 15) + 10)            # smootherstep: gentle start and landing
    off = int(round(W * k)); out = Image.new('RGB', (W, H))
    if side == 'right':   # B enters from the right, moving right -> left
        out.paste(A, (-off, 0)); out.paste(B, (W - off, 0)); seam = W - off
    else:                 # B enters from the left, moving left -> right
        out.paste(A, (off, 0)); out.paste(B, (off - W, 0)); seam = off
    a = np.asarray(out, np.float32); xs = np.arange(W, dtype=np.float32)
    dist = (xs - seam) if side == 'right' else (seam - xs)      # >0 = on the outgoing view, just past the seam
    sh = np.clip(1 - np.abs(dist) / 40, 0, 1) * (dist > 0) * .28 * math.sin(math.pi * k)
    a *= (1 - sh)[None, :, None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def push_curve(A, B, e, side='left'):
    """competitor chapter transition: the new map slides across behind a slightly curved, slanted seam with motion blur and a dark streak"""
    A = np.asarray(A.convert('RGB'), np.float32); B = np.asarray(B.convert('RGB'), np.float32)
    if e <= 0: return Image.fromarray(A.astype(np.uint8))
    if e >= 1: return Image.fromarray(B.astype(np.uint8))
    k = e * e * e * (e * (e * 6 - 15) + 10); spd = 30 * e * e * (e - 1) ** 2      # smootherstep and its speed (0..1.9)
    ys = np.arange(H, dtype=np.float32)
    bend = (ys - H / 2) * 0.16 + 46 * np.sin(ys / H * math.pi)        # slanted, gently curved seam
    # v2.11: overscan the sweep so the seam AND its dark streak start fully off one edge and end fully off the other
    # (no sliver of seam/streak on the first or last pushed frame); out-of-frame columns are mirror-filled, never smeared
    M = 44; lo = 80 - float(bend.max()) - M; hi = W + 80 - float(bend.min()) + M
    off = lo + (hi - lo) * k
    def shift(a, dx):
        dx = int(round(dx))
        if dx == 0: return a
        p = min(abs(dx), W - 1)
        if dx > 0: return np.concatenate([a[:, 1:p + 1][:, ::-1], a[:, :W - p]], axis=1)
        return np.concatenate([a[:, p:], a[:, W - p - 1:W - 1][:, ::-1]], axis=1)
    sp = lambda x, s: s * math.log1p(math.exp(-abs(x) / s)) + max(x, 0.0)          # softplus: smooth max(0, x)
    bmax, bmin = float(bend.max()), float(bend.min())
    g = off - 80 + bmax + 30 - W               # B's leading edge stays >= 30 px ahead of the furthest seam point ...
    dB = -sp(-g, 40.0)                          # ... then eases to rest (0) while the slanted seam finishes its sweep
    dA = 0.35 * sp(off - 80 + bmin, 8.0)        # outgoing view starts drifting only once the seam is on screen
    if side == 'left':
        seam = off - 80 + bend; Bs = shift(B, dB); As = shift(A, dA)
        xs = np.arange(W, dtype=np.float32)[None, :]; onB = xs < seam[:, None]
    else:
        seam = W - off + 80 - bend; Bs = shift(B, -dB); As = shift(A, -dA)
        xs = np.arange(W, dtype=np.float32)[None, :]; onB = xs > seam[:, None]
    out = np.where(onB[..., None], Bs, As)
    d = np.abs(xs - seam[:, None])
    r = int(2 + 7 * min(1, spd))                                       # light motion blur, strongest near the seam only
    if r > 2:
        c = np.cumsum(np.pad(out, ((0, 0), (r, r), (0, 0)), mode='edge'), axis=1, dtype=np.float32)
        bl = (c[:, 2 * r:2 * r + W] - c[:, :W]) / (2 * r)
        wgt = (np.clip(1 - d / 320, 0, 1) * min(1, spd))[..., None]
        out = out + (bl - out) * wgt
    # dark streak along the seam
    band = np.clip(1 - d / 26, 0, 1) ** 1.5 * .55 * math.sin(math.pi * k)
    out = out * (1 - band[..., None])
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
