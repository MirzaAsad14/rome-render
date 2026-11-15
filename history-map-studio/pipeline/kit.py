"""kit: screen-space motion graphics in the History Vanguard idiom.
Everything is pre-rendered once at 3x and downsampled (crisp, anti-aliased),
then animated per frame with cheap scale/alpha/crop transforms."""
import math, os, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, 'assets/fonts'); IMG = os.path.join(HERE, 'assets/img')
W, H = 1920, 1080
Z = 3  # supersample for sprites


@functools.lru_cache(None)
def F(name, size): return ImageFont.truetype(os.path.join(FD, name), int(size))

# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, t0, t1): return clamp((t - t0) / max(1e-6, t1 - t0))
def smooth(x): x = clamp(x); return x * x * (3 - 2 * x)
def ease_io(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def back_out(x, s=1.9): x = clamp(x); x -= 1; return x * x * ((s + 1) * x + s) + 1
def lerp(a, b, k): return a + (b - a) * k
def life(t, t0, t1, fin=0.35, fout=0.3):
    """0..1 envelope for an element living from t0 to t1"""
    return min(smooth(prog(t, t0, t0 + fin)), 1 - smooth(prog(t, t1 - fout, t1)))

def down(im): return im.resize((max(1, im.width // Z), max(1, im.height // Z)), Image.LANCZOS)


# ---------------------------------------------------------------- camera
class Camera:
    """details: optional list of (P, pyr) high-resolution atlases sharing the main projection's c.
    frame() uses the sharpest atlas that fully contains the view; self.cur is (P, index) of the one used."""
    def __init__(self, P, pyr, keys, details=()):
        self.P, self.pyr, self.keys = P, pyr, sorted(keys)
        self.atl = [(P, pyr)] + list(details); self.cur = (P, 0)
    def dissolve(self, t):
        """(a_key, b_key, f) if t is inside a segment whose end key is flagged 'cut' (a dissolve instead of a whip pan)"""
        if getattr(self, 'force', None) is not None: return None
        k = self.keys
        for a, b in zip(k, k[1:]):
            if a[0] <= t < b[0] and len(b) > 4 and b[4] in ('cut', 'wipe'):
                return a, b, ease_io((t - a[0]) / max(1e-6, b[0] - a[0]))
        return None
    def at(self, t):
        if getattr(self, 'force', None) is not None:
            key = self.force
            return key[1] + 0.010 * math.sin(t * 0.19), key[2] + 0.006 * math.cos(t * 0.15), key[3]
        d = self.dissolve(t)
        if d:
            a, b, f = d; key = a if f < 0.5 else b
            return key[1] + 0.010 * math.sin(t * 0.19), key[2] + 0.006 * math.cos(t * 0.15), key[3]
        k = self.keys
        if t <= k[0][0]: a = b = k[0]; f = 0
        elif t >= k[-1][0]: a = b = k[-1]; f = 0
        else:
            i = max(j for j in range(len(k)) if k[j][0] <= t); a, b = k[i], k[min(i + 1, len(k) - 1)]
            f = ease_io((t - a[0]) / max(1e-6, b[0] - a[0]))
        lon, lat = lerp(a[1], b[1], f), lerp(a[2], b[2], f)
        wl = math.exp(lerp(math.log(a[3]), math.log(b[3]), f))
        dist = math.hypot(b[1] - a[1], b[2] - a[2])                    # long pans lift the camera a little mid-move (smooth flight, no whip)
        if dist > .35 * min(a[3], b[3]): wl *= 1 + min(.55, .35 * dist / max(a[3], b[3])) * math.sin(math.pi * f) ** 2
        lon += 0.010 * math.sin(t * 0.19); lat += 0.006 * math.cos(t * 0.15)
        return lon, lat, wl
    def fit(self, i, lon, lat, wl):
        """0..1: how comfortably atlas i contains the view (fades to 0 before an edge is reached)"""
        if i == 0: return 1.0
        Pd = self.atl[i][0]; hl = wl / 2; hv = hl * H / W / self.P.c
        m = min(lon - hl - Pd.lon0, Pd.lon1 - lon - hl, lat - hv - Pd.lat0, Pd.lat1 - lat - hv)
        res = wl * Pd.c * Pd.K / W  # need >= ~1 px per screen px to be worth it (it always is, by design)
        return max(0.0, min(1.0, m / max(0.4, wl * getattr(self, 'fade', 0.12))))
    def pick(self, lon, lat, wl):
        best = 0
        for i in range(1, len(self.atl)):
            if self.fit(i, lon, lat, wl) > 0.999 and self.atl[i][0].K > self.atl[best][0].K: best = i
        return best
    def _render(self, ai, lon, lat, wl):
        P, pyr = self.atl[ai]
        cx, cy = P.xy(lon, lat); vw = wl * P.c * P.K; vh = vw * H / W
        lvl = 0
        while lvl < 2 and vw / (2 ** (lvl + 1)) > W * 1.05: lvl += 1
        s = 2 ** lvl
        box = ((cx - vw / 2) / s, (cy - vh / 2) / s, (cx + vw / 2) / s, (cy + vh / 2) / s)
        ss = vw / s / W
        if ss > 1.15:   # more atlas pixels than screen pixels: sample big, then shrink with Lanczos (sharp, no shimmer)
            q = min(ss, 1.6)
            return pyr[lvl].transform((int(W * q), int(H * q)), Image.EXTENT, box, Image.BICUBIC, fillcolor=(150, 140, 130)).resize((W, H), Image.LANCZOS)
        return pyr[lvl].transform((W, H), Image.EXTENT, box, Image.BICUBIC, fillcolor=(150, 140, 130))
    def layers(self, lon, lat, wl):
        """[(atlas index, weight)] - sharpest partially-fitting atlas blended over the next best"""
        cands = sorted(range(len(self.atl)), key=lambda i: -self.atl[i][0].K)
        out = []; rem = 1.0
        for i in cands:
            f = self.fit(i, lon, lat, wl)
            if f <= 0: continue
            w = rem * f; out.append((i, w)); rem -= w
            if rem <= 1e-3: break
        return out
    def _view(self, lon, lat, wl):
        img = None; acc = 0.0
        for i, w in reversed(self.layers(lon, lat, wl)):
            im = self._render(i, lon, lat, wl)
            if img is None: img = im; acc = w
            else: acc += w; img = Image.blend(img, im, w / acc)
        return img
    def frame(self, t):
        d = self.dissolve(t)
        if d:
            a, b, f = d
            A = self._view(a[1], a[2], a[3]); B = self._view(b[1], b[2], b[3])
            lon, lat, wl = self.at(t); ai = self.layers(lon, lat, wl)[0][0]; P = self.atl[ai][0]; self.cur = (P, ai)
            img = Image.blend(A, B, f)
            cx, cy = P.xy(lon, lat); vw = wl * P.c * P.K; vh = vw * H / W; k = W / vw
            def sc(lon, lat):
                x, y = P.xy(lon, lat); return ((x - cx + vw / 2) * k, (y - cy + vh / 2) * k)
            return img.convert('RGBA'), sc, wl
        lon, lat, wl = self.at(t)
        ls = self.layers(lon, lat, wl)
        ai = ls[0][0]; P = self.atl[ai][0]; self.cur = (P, ai)
        img = None; acc = 0.0
        for i, w in reversed(ls):  # start from the least sharp, blend sharper ones on top
            im = self._render(i, lon, lat, wl)
            if img is None: img = im; acc = w
            else:
                acc += w; img = Image.blend(img, im, w / acc)
        cx, cy = P.xy(lon, lat); vw = wl * P.c * P.K; vh = vw * H / W; k = W / vw
        def sc(lon, lat):
            x, y = P.xy(lon, lat); return ((x - cx + vw / 2) * k, (y - cy + vh / 2) * k)
        return img.convert('RGBA'), sc, wl


def paste(frame, spr, center, scale=1.0, alpha=1.0):
    if alpha <= 0.003 or scale <= 0.01: return
    if abs(scale - 1) > 0.002: spr = spr.resize((max(1, int(spr.width * scale)), max(1, int(spr.height * scale))), Image.BICUBIC)
    if alpha < 0.999:
        a = spr.getchannel('A').point(lambda v: int(v * alpha)); spr = spr.copy(); spr.putalpha(a)
    frame.alpha_composite(spr, (int(center[0] - spr.width / 2), int(center[1] - spr.height / 2))) if -spr.width < center[0] < W + spr.width and -spr.height < center[1] < H + spr.height else None


def local_draw(frame, bbox, fn, alpha=1.0):
    """anti-aliased vector drawing on a 3x local canvas clipped to bbox"""
    x0, y0, x1, y1 = [int(v) for v in bbox]
    x0, y0 = max(-50, x0), max(-50, y0); x1, y1 = min(W + 50, x1), min(H + 50, y1)
    if x1 <= max(0, x0) + 1 or y1 <= max(0, y0) + 1 or x0 >= W or y0 >= H: return
    c = Image.new('RGBA', ((x1 - x0) * Z, (y1 - y0) * Z), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    fn(d, lambda p: ((p[0] - x0) * Z, (p[1] - y0) * Z))
    c = down(c)
    if alpha < 0.999: c.putalpha(c.getchannel('A').point(lambda v: int(v * alpha)))
    fx, fy = max(0, x0), max(0, y0)
    crop = c.crop((fx - x0, fy - y0, min(W, x1) - x0, min(H, y1) - y0))
    frame.alpha_composite(crop, (fx, fy))


# ---------------------------------------------------------------- heraldry
def shield_poly(cx, top, w, h):
    """heater shield outline"""
    pts = [(cx - w / 2 + w * i / 16, top + 0.035 * h * math.sin(math.pi * i / 16)) for i in range(17)]
    side = top + h * 0.42
    for i in range(1, 21):
        a = i / 20; pts.append((cx + (w / 2) * (1 - a ** 1.6), side + (top + h - side) * math.sin(a * math.pi / 2)))
    for i in range(19, -1, -1):
        a = i / 20; pts.append((cx - (w / 2) * (1 - a ** 1.6), side + (top + h - side) * math.sin(a * math.pi / 2)))
    return pts


KC = {'rus': (176, 34, 40), 'mongol': (36, 70, 150), 'umayyad': (28, 112, 70), 'abbasid': (34, 34, 38), 'byz': (112, 40, 122), 'frank': (40, 78, 168)}


def emblem(d, kind, cx, cy, s):
    if kind in ('umayyad', 'abbasid', 'byz', 'frank'):
        g = (238, 196, 70) if kind in ('byz', 'frank') else (246, 244, 236)
        if kind == 'umayyad':  # eight-point rosette
            pts = []
            for i in range(16):
                a = i * math.pi / 8; r = s * (.5 if i % 2 == 0 else .3); pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
            d.polygon(pts, fill=g)
        elif kind == 'abbasid':  # plain banner disc
            d.ellipse([cx - s * .36, cy - s * .36, cx + s * .36, cy + s * .36], outline=g, width=max(2, int(s * .12)))
        else:
            d.polygon([(cx, cy - s * .5), (cx + s * .32, cy), (cx, cy + s * .5), (cx - s * .32, cy)], fill=g)
        return
    if kind == 'rus':  # Rurikid trident in gold
        g = (238, 196, 70); o = (110, 70, 10)
        def poly(p): d.polygon(p, fill=g, outline=o, width=max(1, int(s * .04)))
        poly([(cx - s * .07, cy - s * .55), (cx + s * .07, cy - s * .55), (cx + s * .07, cy + s * .35), (cx - s * .07, cy + s * .35)])
        for sg in (-1, 1):
            poly([(cx + sg * s * .5, cy - s * .5), (cx + sg * s * .38, cy - s * .5), (cx + sg * s * .3, cy + s * .2), (cx + sg * s * .05, cy + s * .35), (cx + sg * s * .1, cy + s * .5), (cx + sg * s * .45, cy + s * .3)])
        poly([(cx - s * .2, cy + s * .35), (cx + s * .2, cy + s * .35), (cx, cy + s * .62)])
    elif kind == 'mongol':  # crescent + sun
        wcol = (245, 245, 250)
        R = s * .42; cy2 = cy + s * .12
        d.arc([cx - R, cy2 - R, cx + R, cy2 + R], 10, 170, fill=wcol, width=max(2, int(R * .38)))
        r2 = s * .16; d.ellipse([cx - r2, cy - s * .52 - r2, cx + r2, cy - s * .52 + r2], fill=wcol)
        d.polygon([(cx, cy - s * .92), (cx + s * .08, cy - s * .7), (cx - s * .08, cy - s * .7)], fill=wcol)
    else:
        emblem_extra(d, kind, cx, cy, s)


KC.update({'persian': (150, 40, 110), 'mede': (120, 70, 40), 'greek': (40, 96, 170), 'roman': (150, 30, 30), 'parthian': (170, 110, 30),
           'sasanian': (110, 30, 70), 'caliph': (30, 110, 60), 'turk': (40, 120, 130), 'timurid': (60, 80, 140), 'safavid': (190, 60, 40),
           'ottoman': (170, 26, 36), 'uzbek': (110, 110, 40), 'afghan': (40, 40, 44), 'mughal': (30, 120, 90), 'afshar': (160, 90, 30),
           'russia': (230, 230, 236), 'britain': (30, 40, 110), 'iran': (30, 130, 70), 'usa': (40, 60, 130), 'israel': (40, 90, 190),
           'iraq': (40, 40, 40), 'portugal': (30, 90, 40), 'elam': (130, 100, 60), 'qajar': (160, 120, 40), 'pakistan': (20, 100, 50)})


def _star(d, cx, cy, r, n=5, fill=(246, 244, 236), inner=.42, rot=-math.pi / 2):
    d.polygon([(cx + r * (1 if i % 2 == 0 else inner) * math.cos(rot + i * math.pi / n), cy + r * (1 if i % 2 == 0 else inner) * math.sin(rot + i * math.pi / n)) for i in range(2 * n)], fill=fill)


def emblem_extra(d, kind, cx, cy, s):
    g = (238, 200, 80); w = (246, 244, 236); k = (20, 20, 24)
    if kind in ('persian', 'mede', 'parthian', 'elam'):  # winged disc (faravahar-like ring with wings)
        r = s * .16; d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=g, width=max(2, int(s * .07)))
        for sg in (-1, 1):
            for i in range(3):
                y = cy - s * .02 + i * s * .09; L = s * (.46 - i * .08)
                d.polygon([(cx + sg * r * 1.1, y - s * .035), (cx + sg * (r + L), y - s * .06 + i * s * .02), (cx + sg * (r + L * .9), y + s * .03), (cx + sg * r * 1.1, y + s * .035)], fill=g)
        d.polygon([(cx - s * .1, cy + r * 1.2), (cx + s * .1, cy + r * 1.2), (cx, cy + s * .42)], fill=g)
    elif kind == 'greek':  # Vergina sun
        d.ellipse([cx - s * .1, cy - s * .1, cx + s * .1, cy + s * .1], fill=g)
        for i in range(16):
            a = i * math.pi / 8; d.polygon([(cx + s * .12 * math.cos(a - .12), cy + s * .12 * math.sin(a - .12)), (cx + s * .45 * math.cos(a), cy + s * .45 * math.sin(a)), (cx + s * .12 * math.cos(a + .12), cy + s * .12 * math.sin(a + .12))], fill=g)
    elif kind == 'roman':
        d.text((cx, cy), 'SPQR', font=F('Cinzel.ttf', max(8, int(s * .34))), fill=g, anchor='mm')
    elif kind == 'sasanian':  # crescent + globe crown
        R = s * .34; d.ellipse([cx - R, cy - R * .7, cx + R, cy + R * 1.3], fill=w); d.ellipse([cx - R * .8, cy - R * 1.0, cx + R * .8, cy + R * .9], fill=KC['sasanian'])
        d.ellipse([cx - s * .14, cy - s * .44, cx + s * .14, cy - s * .16], fill=g)
    elif kind in ('caliph', 'mughal', 'pakistan'):
        R = s * .36; d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=w); d.ellipse([cx - R * .62, cy - R * 1.02, cx + R * 1.1, cy + R * .7], fill=KC[kind])
        _star(d, cx + s * .16, cy - s * .12, s * .1, fill=w)
    elif kind in ('turk', 'ottoman', 'uzbek', 'timurid'):
        R = s * .34; d.ellipse([cx - R * 1.1, cy - R, cx + R * .9, cy + R], fill=w); d.ellipse([cx - R * .75, cy - R * .8, cx + R * 1.05, cy + R * .8], fill=KC[kind])
        if kind == 'timurid':
            for (ox, oy) in ((0, -.22), (-.2, .14), (.2, .14)): d.ellipse([cx + ox * s - s * .1, cy + oy * s - s * .1, cx + ox * s + s * .1, cy + oy * s + s * .1], outline=g, width=max(2, int(s * .06)))
        else: _star(d, cx + s * .22, cy, s * .14, fill=w, rot=0)
    elif kind in ('safavid', 'qajar', 'afshar'):  # lion-and-sun reduced to the sun
        _star(d, cx, cy, s * .42, n=12, fill=g, inner=.62)
        d.ellipse([cx - s * .2, cy - s * .2, cx + s * .2, cy + s * .2], fill=(250, 220, 120), outline=(130, 80, 20), width=max(1, int(s * .03)))
    elif kind == 'afghan':
        d.polygon([(cx - s * .3, cy + s * .3), (cx, cy - s * .38), (cx + s * .3, cy + s * .3)], outline=w, width=max(2, int(s * .07)))
    elif kind == 'russia':
        for i, c in enumerate(((246, 246, 246), (40, 70, 160), (190, 30, 40))): d.rectangle([cx - s * .4, cy - s * .3 + i * s * .2, cx + s * .4, cy - s * .1 + i * s * .2], fill=c)
    elif kind == 'britain':
        d.line([(cx - s * .4, cy - s * .3), (cx + s * .4, cy + s * .3)], fill=w, width=max(2, int(s * .14))); d.line([(cx - s * .4, cy + s * .3), (cx + s * .4, cy - s * .3)], fill=w, width=max(2, int(s * .14)))
        d.rectangle([cx - s * .42, cy - s * .07, cx + s * .42, cy + s * .07], fill=w); d.rectangle([cx - s * .07, cy - s * .32, cx + s * .07, cy + s * .32], fill=w)
        d.rectangle([cx - s * .42, cy - s * .035, cx + s * .42, cy + s * .035], fill=(190, 30, 40)); d.rectangle([cx - s * .035, cy - s * .32, cx + s * .035, cy + s * .32], fill=(190, 30, 40))
    elif kind == 'usa':
        _star(d, cx, cy, s * .36, fill=w)
    elif kind == 'israel':
        for rot in (-math.pi / 2, math.pi / 2):
            pts = [(cx + s * .36 * math.cos(rot + i * 2 * math.pi / 3), cy + s * .36 * math.sin(rot + i * 2 * math.pi / 3)) for i in range(3)]
            d.polygon(pts, outline=w, width=max(2, int(s * .07)))
    elif kind == 'iraq':
        for i, c in enumerate(((190, 30, 40), (246, 246, 246), (20, 20, 20))): d.rectangle([cx - s * .4, cy - s * .3 + i * s * .2, cx + s * .4, cy - s * .1 + i * s * .2], fill=c)
        for ox in (-.18, 0, .18): _star(d, cx + ox * s, cy, s * .06, fill=(30, 120, 60))
    elif kind == 'iran':
        for i, c in enumerate(((40, 150, 80), (246, 246, 246), (200, 30, 40))): d.rectangle([cx - s * .4, cy - s * .3 + i * s * .2, cx + s * .4, cy - s * .1 + i * s * .2], fill=c)
    elif kind == 'portugal':
        d.ellipse([cx - s * .22, cy - s * .22, cx + s * .22, cy + s * .22], fill=g); d.rectangle([cx - s * .1, cy - s * .12, cx + s * .1, cy + s * .14], fill=w)


def shield(kind, w):
    """standalone heater shield sprite"""
    h = w * 1.18; im = Image.new('RGBA', (int(w * 1.3 * Z), int(h * 1.3 * Z)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx, top = im.width / 2, h * .12 * Z; ww, hh = w * Z, h * Z
    col = KC[kind]
    d.polygon([(x + 4 * Z, y + 5 * Z) for x, y in shield_poly(cx, top, ww, hh)], fill=(0, 0, 0, 110))
    d.polygon(shield_poly(cx, top, ww + 10 * Z, hh + 10 * Z), fill=(70, 78, 96))
    d.polygon(shield_poly(cx, top + 2 * Z, ww + 5 * Z, hh + 5 * Z), fill=(210, 218, 230))
    d.polygon(shield_poly(cx, top + 4 * Z, ww, hh), fill=col)
    # gloss
    d.polygon(shield_poly(cx - ww * .12, top + 6 * Z, ww * .45, hh * .5), fill=tuple(min(255, c + 22) for c in col))
    emblem(d, kind, cx, top + hh * .46, ww * .5)
    return down(im)


# ---------------------------------------------------------------- medallion
def ring(d, cx, cy, R, r, palette=((60, 72, 100), (205, 214, 232), (120, 136, 170), (52, 62, 88))):
    """metallic bevel ring between radius r and R"""
    n = int((R - r)); cols = palette
    for i in range(n):
        f = i / max(1, n - 1); k = f * (len(cols) - 1); j = min(len(cols) - 2, int(k)); u = k - j
        c = tuple(int(lerp(cols[j][q], cols[j + 1][q], u)) for q in range(3))
        rr = R - i; d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=c)


@functools.lru_cache(None)
def portrait_disc(path, D, fallen=False, crop=(0.12, 0.04, 0.88, 0.80)):
    src = Image.open(os.path.join(IMG, path)).convert('RGB')
    w, h = src.size; box = (int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h))
    face = src.crop(box)
    if fallen:
        face = ImageOps.grayscale(face).convert('RGB'); face = ImageEnhance.Brightness(face).enhance(0.7)
        face = Image.blend(face, Image.new('RGB', face.size, (120, 20, 20)), 0.25)
    s = D * Z; R = s / 2; r = R * 0.80
    im = Image.new('RGBA', (int(s + 16 * Z), int(s + 16 * Z)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx = cy = im.width / 2
    d.ellipse([cx - R + 6 * Z, cy - R + 8 * Z, cx + R + 6 * Z, cy + R + 8 * Z], fill=(0, 0, 0, 120))
    pal = ((60, 72, 100), (205, 214, 232), (120, 136, 170), (52, 62, 88)) if not fallen else ((40, 20, 20), (150, 60, 60), (90, 30, 30), (30, 10, 10))
    ring(d, cx, cy, R, r - 2 * Z, pal)
    f = face.resize((int(2 * r), int(2 * r)), Image.LANCZOS)
    m = Image.new('L', f.size, 0); ImageDraw.Draw(m).ellipse([0, 0, f.width - 1, f.height - 1], fill=255)
    im.paste(f, (int(cx - r), int(cy - r)), m)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(28, 32, 44), width=int(3 * Z))
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(28, 32, 44), width=int(3 * Z))
    if fallen:  # orthodox cross badge
        bx, by, u = cx + r * .62, cy - r * .62, r * .2
        d.ellipse([bx - u * 1.6, by - u * 1.6, bx + u * 1.6, by + u * 1.6], fill=(25, 15, 15), outline=(200, 190, 180), width=Z * 2)
        d.rectangle([bx - u * .16, by - u * 1.1, bx + u * .16, by + u * 1.1], fill=(235, 225, 210))
        d.rectangle([bx - u * .7, by - u * .55, bx + u * .7, by - u * .3], fill=(235, 225, 210))
        d.polygon([(bx - u * .5, by + u * .35), (bx + u * .5, by + u * .6), (bx + u * .5, by + u * .8), (bx - u * .5, by + u * .55)], fill=(235, 225, 210))
    return down(im)


@functools.lru_cache(None)
def ribbon(name, title, flip=False, fill=(214, 208, 234), edge=(64, 58, 104)):
    fn, ft = F('Almendra-Bold.ttf', 44 * Z), F('Almendra-Regular.ttf', 27 * Z)
    tw = max(fn.getlength(name), ft.getlength(title)) if title else fn.getlength(name)
    L = tw + 150 * Z; Hh = (86 if title else 62) * Z
    im = Image.new('RGBA', (int(L + 40 * Z), int(Hh + 40 * Z)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x0, y0 = 10 * Z, 15 * Z; x1, y1 = x0 + L, y0 + Hh
    notch = 26 * Z
    body = [(x0, y0)]
    for i in range(1, 21): body.append((x0 + (x1 - x0) * i / 20, y0 + 5 * Z * math.sin(math.pi * i / 20)))
    body += [(x1 + 24 * Z, y0 - 6 * Z), (x1 - notch + 24 * Z, (y0 + y1) / 2), (x1 + 24 * Z, y1 + 6 * Z)]
    for i in range(20, -1, -1): body.append((x0 + (x1 - x0) * i / 20, y1 + 5 * Z * math.sin(math.pi * i / 20)))
    d.polygon([(x + 5 * Z, y + 7 * Z) for x, y in body], fill=(0, 0, 0, 100))
    d.polygon(body, fill=edge)
    inner = [(x + (0 if i in (0, len(body) - 1) else 0), y) for i, (x, y) in enumerate(body)]
    # inset fill
    sh = 4 * Z; ins = [(lerp(x, (x0 + x1) / 2, sh / (L / 2)), lerp(y, (y0 + y1) / 2, sh / (Hh / 2))) for x, y in body]
    d.polygon(ins, fill=fill)
    d.line([(x0 + 40 * Z, y0 + 12 * Z), (x1 - 20 * Z, y0 + 14 * Z)], fill=tuple(min(255, c + 22) for c in fill), width=3 * Z)
    if flip:
        im = ImageOps.mirror(im); d = ImageDraw.Draw(im); tx = im.width - (x0 + 100 * Z + tw / 2)
    else:
        tx = x0 + 100 * Z + tw / 2
    if title:
        d.text((tx, y0 + Hh * .40), name, font=fn, fill=(34, 28, 58), anchor='mm')
        d.text((tx, y0 + Hh * .78), title, font=ft, fill=(74, 64, 98), anchor='mm')
    else:
        d.text((tx, (y0 + y1) / 2), name, font=fn, fill=(34, 28, 58), anchor='mm')
    return down(im)


class Medallion:
    """portrait disc + shield + ribbon; pops in with overshoot, ribbon unrolls"""
    def __init__(self, portrait, name, title, side=None, D=200, flip=False, fallen=False, crop=(0.12, 0.04, 0.88, 0.80)):
        self.disc = portrait_disc(portrait, D, fallen, crop); self.D = D
        self.sh = shield(side, D * .42) if side else None
        self.rib = ribbon(name, title, flip); self.flip = flip
    def draw(self, frame, pos, t, t0, t1, target=None):
        if t < t0 or t > t1 + 0.4: return
        pin = back_out(prog(t, t0, t0 + 0.5)); pout = 1 - ease_out(prog(t, t1 - 0.35, t1))
        s = pin * pout; a = min(1, prog(t, t0, t0 + 0.15) * 1.5) * pout
        if s <= 0.01: return
        x, y = pos
        if target is not None and s > 0.5:
            def fn(d, S):
                ang = math.atan2(target[1] - y, target[0] - x); dist = math.dist(target, (x, y))
                b1 = (x + math.cos(ang + 0.5) * self.D * .45, y + math.sin(ang + 0.5) * self.D * .45)
                b2 = (x + math.cos(ang - 0.5) * self.D * .45, y + math.sin(ang - 0.5) * self.D * .45)
                ln = min(dist, self.D * .95) * min(1, (s - .5) * 2)
                tip = (x + math.cos(ang) * ln, y + math.sin(ang) * ln)
                d.polygon([S((p[0] + 3, p[1] + 4)) for p in (b1, tip, b2)], fill=(0, 0, 0, 90))
                d.polygon([S(b1), S(tip), S(b2)], fill=(245, 245, 250, 245), outline=(40, 44, 60, 255), width=Z * 2)
            local_draw(frame, (x - self.D * 1.2, y - self.D * 1.2, x + self.D * 1.2, y + self.D * 1.2), fn, a)
        # ribbon unroll (behind disc)
        k = ease_out(prog(t, t0 + 0.22, t0 + 0.8)) * pout
        if k > 0.02:
            rb = self.rib; cw = max(1, int(rb.width * k))
            part = rb.crop((rb.width - cw, 0, rb.width, rb.height)) if self.flip else rb.crop((0, 0, cw, rb.height))
            ry = y + self.D * 0.14
            rx = x + self.D * 0.30 if not self.flip else x - self.D * 0.30 - part.width
            if a < 0.999: part = part.copy(); part.putalpha(part.getchannel('A').point(lambda v: int(v * a)))
            frame.alpha_composite(part, (int(rx), int(ry - rb.height / 2))) if 0 <= ry - rb.height / 2 and rx > -part.width else None
        paste(frame, self.disc, (x, y), s, a)
        if self.sh is not None:
            ks = back_out(prog(t, t0 + 0.15, t0 + 0.6)) * pout
            paste(frame, self.sh, (x, y + self.D * 0.52 * s), ks * s, a)


# ---------------------------------------------------------------- frames & cards
def steel_frame(d, box, r, Zs=Z):
    x0, y0, x1, y1 = box
    for i, c in enumerate([(40, 48, 66), (150, 164, 192), (210, 220, 236), (96, 112, 146), (52, 62, 86)]):
        o = (4 - i) * 2.2 * Zs
        d.rounded_rectangle([x0 - o, y0 - o, x1 + o, y1 + o], radius=r + o, fill=c)


@functools.lru_cache(None)
def year_badge(text):
    w, h = 210, 92
    im = Image.new('RGBA', ((w + 40) * Z, (h + 40) * Z), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    b = (20 * Z, 18 * Z, (w + 20) * Z, (h + 18) * Z)
    d.rounded_rectangle([b[0] + 5 * Z, b[1] + 7 * Z, b[2] + 5 * Z, b[3] + 7 * Z], radius=24 * Z, fill=(0, 0, 0, 110))
    steel_frame(d, b, 22 * Z)
    d.rounded_rectangle(b, radius=20 * Z, fill=(58, 66, 86))
    d.rounded_rectangle([b[0] + 6 * Z, b[1] + 6 * Z, b[2] - 6 * Z, b[1] + 30 * Z], radius=14 * Z, fill=(72, 82, 104))
    fs = 66
    while fs > 30 and F('IMFeENrm28P.ttf', fs * Z).getlength(text) > (w - 26) * Z: fs -= 2
    d.text(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2 + 2 * Z), text, font=F('IMFeENrm28P.ttf', fs * Z), fill=(232, 236, 244), anchor='mm')
    return down(im)


def wood(w, h, seed=3):
    rng = np.random.default_rng(seed)
    g = rng.random((max(2, h // 6), max(2, w // 120))).astype(np.float32)
    g = np.asarray(Image.fromarray(g, 'F').resize((w, h), Image.BICUBIC))
    yy = np.linspace(0, 1, h)[:, None]
    streak = 0.5 + 0.5 * np.sin(yy * 60 + g * 7)
    base = np.array([96, 62, 40]); hi = np.array([150, 104, 66])
    a = base + (hi - base) * (streak[..., None] * 0.6 + g[..., None] * 0.4)
    a *= (0.85 + 0.25 * np.sin(np.linspace(0, math.pi, h)))[:, None, None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert('RGBA')


@functools.lru_cache(None)
def chapter_parts(numeral, title):
    bw, bh = 1240, 118
    bar = Image.new('RGBA', ((bw + 60) * Z, (bh + 60) * Z), (0, 0, 0, 0)); d = ImageDraw.Draw(bar)
    b = (30 * Z, 30 * Z, (bw + 30) * Z, (bh + 30) * Z)
    d.rounded_rectangle([b[0] + 6 * Z, b[1] + 9 * Z, b[2] + 6 * Z, b[3] + 9 * Z], radius=18 * Z, fill=(0, 0, 0, 120))
    steel_frame(d, b, 16 * Z)
    wd = wood(b[2] - b[0], b[3] - b[1]); m = Image.new('L', wd.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, wd.width - 1, wd.height - 1], radius=14 * Z, fill=255)
    bar.paste(wd, (b[0], b[1]), m)
    d.text(((b[0] + b[2]) / 2 + 60 * Z + 3 * Z, (b[1] + b[3]) / 2 + 4 * Z), title, font=F('IMFeENrm28P.ttf', 64 * Z), fill=(30, 18, 10, 200), anchor='mm')
    d.text(((b[0] + b[2]) / 2 + 60 * Z, (b[1] + b[3]) / 2), title, font=F('IMFeENrm28P.ttf', 64 * Z), fill=(246, 238, 222), anchor='mm')
    coinD = 168; coin = Image.new('RGBA', ((coinD + 30) * Z, (coinD + 30) * Z), (0, 0, 0, 0)); cd = ImageDraw.Draw(coin)
    c = coin.width / 2; R = coinD * Z / 2
    cd.ellipse([c - R + 5 * Z, c - R + 8 * Z, c + R + 5 * Z, c + R + 8 * Z], fill=(0, 0, 0, 120))
    ring(cd, c, c, R, R * 0.70)
    rr = R * 0.70
    for i in range(int(rr)):
        g = int(lerp(225, 150, i / rr)); cd.ellipse([c - rr + i, c - rr + i, c + rr - i, c + rr - i], fill=(g, g + 4, g + 12)) if i % 2 == 0 else None
    cd.ellipse([c - rr, c - rr, c + rr, c + rr], outline=(40, 46, 64), width=3 * Z)
    nfs = 96
    while nfs > 40 and F('IMFeENrm28P.ttf', nfs * Z).getlength(numeral) > rr * 1.5: nfs -= 4
    cd.text((c, c + 2 * Z), numeral, font=F('IMFeENrm28P.ttf', nfs * Z), fill=(48, 54, 74), anchor='mm')
    return down(bar), down(coin)


def chapter(frame, t, t0, t1, numeral, title):
    a = life(t, t0, t1, 0.5, 0.4)
    if a <= 0: return
    bar, coin = chapter_parts(numeral, title)
    cx, cy = W / 2, H - 120
    k = ease_out(prog(t, t0, t0 + 0.6)) * (1 - ease_out(prog(t, t1 - 0.4, t1)))
    cw = max(2, int(bar.width * k)); part = bar.crop(((bar.width - cw) // 2, 0, (bar.width + cw) // 2, bar.height))
    paste(frame, part, (cx, cy + 24 * (1 - k)), 1, a)
    paste(frame, coin, (cx - 470, cy), back_out(prog(t, t0 + 0.3, t0 + 0.8)) * (1 - ease_out(prog(t, t1 - 0.4, t1))), a)


@functools.lru_cache(None)
def pill(title, sub, lk='mongol', rk='rus'):
    ft, fs = F('IMFeENsc28P.ttf', 40 * Z), F('IMFeENit28P.ttf', 28 * Z)
    tw = max(ft.getlength(title), fs.getlength(sub)); w = tw / Z + 170; h = 96
    im = Image.new('RGBA', (int((w + 80) * Z), int((h + 90) * Z)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    b = (40 * Z, 45 * Z, (w + 40) * Z, (h + 45) * Z)
    d.rounded_rectangle([b[0] + 5 * Z, b[1] + 8 * Z, b[2] + 5 * Z, b[3] + 8 * Z], radius=h * Z / 2, fill=(0, 0, 0, 110))
    steel_frame(d, b, h * Z / 2)
    d.rounded_rectangle(b, radius=h * Z / 2, fill=(214, 208, 234))
    d.text(((b[0] + b[2]) / 2, b[1] + h * Z * .40), title, font=ft, fill=(34, 28, 58), anchor='mm')
    d.text(((b[0] + b[2]) / 2, b[1] + h * Z * .76), sub, font=fs, fill=(80, 70, 104), anchor='mm')
    out = down(im)
    for kind, x in ((lk, 40), (rk, w + 40)):
        sh = shield(kind, 64); out.alpha_composite(sh, (int(x - sh.width / 2), int(45 + h / 2 - sh.height / 2 + 6)))
    return out


def draw_pill(frame, pos, t, t0, t1, title, sub, lk='mongol', rk='rus'):
    if t < t0 or t > t1: return
    s = back_out(prog(t, t0, t0 + 0.5)) * (1 - ease_out(prog(t, t1 - 0.35, t1)))
    paste(frame, pill(title, sub, lk, rk), pos, s, min(1, prog(t, t0, t0 + .15) * 2))


@functools.lru_cache(None)
def quote_box(w, h):
    im = Image.new('RGBA', ((w + 40) * Z, (h + 40) * Z), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    b = (20 * Z, 20 * Z, (w + 20) * Z, (h + 20) * Z)
    d.rounded_rectangle([b[0] + 7 * Z, b[1] + 10 * Z, b[2] + 7 * Z, b[3] + 10 * Z], radius=26 * Z, fill=(0, 0, 0, 120))
    steel_frame(d, b, 24 * Z)
    rng = np.random.default_rng(4)
    pw, ph = b[2] - b[0], b[3] - b[1]
    n = rng.random((ph // 40, pw // 40)).astype(np.float32)
    n = np.asarray(Image.fromarray(n, 'F').resize((pw, ph), Image.BICUBIC))
    pap = np.array([232, 220, 196]) * (0.94 + 0.08 * n[..., None])
    pap = Image.fromarray(np.clip(pap, 0, 255).astype(np.uint8)).convert('RGBA')
    m = Image.new('L', pap.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=22 * Z, fill=255)
    im.paste(pap, (b[0], b[1]), m)
    return down(im)


def layout_words(words, font, maxw):
    lines = [[]]; cur = 0; sp = font.getlength(' ')
    for i, w in enumerate(words):
        lw = font.getlength(w)
        if lines[-1] and cur + sp + lw > maxw: lines.append([]); cur = 0
        lines[-1].append((i, w, cur if not lines[-1] else cur + sp)); cur = (cur if not lines[-1][:-1] else cur + sp) + lw
    return lines


class SourceCard:
    def __init__(self, portrait, name, title, quote_words, word_times, box=(70, 470, 860, 470)):
        self.med = Medallion(portrait, name, title, None, D=210)
        self.words = quote_words; self.times = word_times; self.box = box
        self.font = F('UnifrakturMaguntia-Book.ttf', 46)
        self.lines = layout_words(['\u201c' + quote_words[0]] + quote_words[1:-1] + [quote_words[-1] + '\u201d'], self.font, box[2] - 90)
    def draw(self, frame, t, t0, t1):
        if t < t0 or t > t1: return
        a = life(t, t0, t1, 0.4, 0.35)
        # darken left side of map for legibility
        g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
        for i in range(0, 1100, 20): gd.rectangle([i, 0, i + 20, H], fill=(10, 10, 16, int(150 * a * (1 - i / 1100) ** 1.4)))
        frame.alpha_composite(g)
        x, y, w, h = self.box
        qb = quote_box(w, h); k = back_out(prog(t, t0 + 0.25, t0 + 0.75), 1.2) * (1 - ease_out(prog(t, t1 - 0.35, t1)))
        paste(frame, qb, (x + w / 2, y + h / 2 + 30 * (1 - k)), 0.9 + 0.1 * k, a * min(1, k * 1.5))
        if k > 0.5:
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
            lh = 64; ty = y + 50
            for li, line in enumerate(self.lines):
                for idx, word, xoff in line:
                    wa = smooth(prog(t, self.times[idx] - 0.05, self.times[idx] + 0.25)) * a
                    if wa > 0: d.text((x + 45 + xoff, ty + li * lh), word, font=self.font, fill=(44, 30, 26, int(255 * wa)))
            frame.alpha_composite(lay)
        self.med.draw(frame, (x + 150, y - 150), t, t0, t1)


# ---------------------------------------------------------------- plates (real images)
@functools.lru_cache(None)
def torn_mask(w, h, seed=1, inset=34):
    rng = np.random.default_rng(seed)
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([inset, inset, w - inset, h - inset], radius=30, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(inset * 0.7))
    n = rng.random((h // 9, w // 9)).astype(np.float32); n = np.asarray(Image.fromarray(n, 'F').resize((w, h), Image.BICUBIC))
    n2 = rng.random((h // 3, w // 3)).astype(np.float32); n2 = np.asarray(Image.fromarray(n2, 'F').resize((w, h), Image.BILINEAR))
    a = np.asarray(m, np.float32) / 255 + (n - .5) * .55 + (n2 - .5) * .25
    a = np.clip((a - 0.5) * 9 + 0.5, 0, 1)
    return Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))


@functools.lru_cache(None)
def mist_tex():
    rng = np.random.default_rng(9); w, h = 2600, 1500
    acc = np.zeros((h, w), np.float32)
    for c, a in ((300, 1), (120, .5), (50, .25)):
        g = rng.random((h // c + 2, w // c + 2)).astype(np.float32); acc += np.asarray(Image.fromarray(g, 'F').resize((w, h), Image.BICUBIC)) * a
    acc = np.clip((acc / 1.75 - 0.45) * 2.2, 0, 1)
    return Image.fromarray((acc * 255).astype(np.uint8))


def mist(frame, t, alpha=0.18, speed=18):
    m = mist_tex(); ox = int((t * speed) % 600); oy = int(40 + 20 * math.sin(t * .2))
    a = m.crop((ox, oy, ox + W, oy + H)).point(lambda v: int(v * alpha))
    lay = Image.new('RGBA', (W, H), (236, 230, 220, 0)); lay.putalpha(a); frame.alpha_composite(lay)


class Plate:
    """a real image cut-away: blurred sepia backdrop + torn-edge plate + slow Ken Burns + mist + caption"""
    def __init__(self, path, crop=None, caption=None, full=False, sharpen=True, zoom=(1.0, 1.08), pan=(0, 0)):
        src = Image.open(os.path.join(IMG, path)).convert('RGB')
        if crop: src = src.crop(tuple(int(v * (src.width if i % 2 == 0 else src.height)) for i, v in enumerate(crop)))
        self.full = full; self.caption = caption; self.zoom = zoom; self.pan = pan
        if full:
            r = max(W * 1.12 / src.width, H * 1.12 / src.height)
            self.img = src.resize((int(src.width * r), int(src.height * r)), Image.LANCZOS).convert('RGBA')
            m = torn_mask(self.img.width, self.img.height, 3, inset=60)
            self.img.putalpha(m)
            self.bg = Image.new('RGBA', (W, H), (34, 26, 20, 255))
        else:
            ph = 940; r = ph / src.height
            im = src.resize((int(src.width * r), ph), Image.LANCZOS)
            if sharpen and r > 1.3: im = im.filter(ImageFilter.UnsharpMask(2.2, 90, 2))
            im = ImageEnhance.Color(im).enhance(0.85)
            pad = 40; can = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
            can.paste(im, (pad, pad)); m = torn_mask(can.width, can.height, 2, inset=pad + 10); can.putalpha(m)
            sh = Image.new('RGBA', can.size, (0, 0, 0, 0)); sh.putalpha(m.point(lambda v: int(v * .65)).filter(ImageFilter.GaussianBlur(16)))
            self.img = can; self.shadow = sh
            r2 = max(W * 1.15 / src.width, H * 1.15 / src.height)
            bg = src.resize((int(src.width * r2), int(src.height * r2)), Image.LANCZOS).filter(ImageFilter.GaussianBlur(28))
            bg = ImageOps.grayscale(bg).convert('RGB'); bg = ImageOps.colorize(ImageOps.grayscale(bg), (24, 18, 14), (150, 120, 88))
            self.bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H)).convert('RGBA')
    def render(self, t, t0, t1):
        k = prog(t, t0 - 0.6, t1 + 0.6); z = lerp(self.zoom[0], self.zoom[1], k)
        out = self.bg.copy()
        if self.full:
            im = self.img.resize((int(self.img.width * z), int(self.img.height * z)), Image.BICUBIC)
            out.alpha_composite(im, (int(W / 2 - im.width / 2 + self.pan[0] * k), int(H / 2 - im.height / 2 + self.pan[1] * k)))
        else:
            im = self.img.resize((int(self.img.width * z), int(self.img.height * z)), Image.BICUBIC)
            sh = self.shadow.resize(im.size, Image.BILINEAR)
            px, py = int(W / 2 - im.width / 2 + self.pan[0] * k), int(H / 2 - im.height / 2 + self.pan[1] * k)
            out.alpha_composite(sh, (px + 14, py + 20)); out.alpha_composite(im, (px, py))
        mist(out, t, 0.16)
        if self.caption:
            d = ImageDraw.Draw(out); f = F('IMFeENit28P.ttf', 30)
            d.text((60, H - 60), self.caption, font=f, fill=(240, 232, 218, 235), anchor='ls', stroke_width=3, stroke_fill=(20, 14, 10, 200))
        return out


# ---------------------------------------------------------------- map marks
@functools.lru_cache(None)
def flame_frames(n=12, h=64):
    out = []
    for f in range(n):
        im = Image.new('RGBA', (int(h * .9 * Z), int(h * 1.4 * Z)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        cx, by = im.width / 2, im.height * 0.92
        ph = f / n * 2 * math.pi
        for k, (col, wk, hk) in enumerate((((120, 24, 8), .30, 1.0), ((226, 74, 18), .22, .86), ((255, 160, 40), .14, .66), ((255, 236, 160), .07, .40))):
            Hh = h * Z * hk * (0.9 + 0.12 * math.sin(ph * 2 + k)); Wd = h * Z * wk
            left = []; right = []
            for i in range(25):
                u = i / 24; y = by - Hh * u
                sway = math.sin(u * 4.2 - ph * 1.0 + k * .4) * Wd * 0.75 * u
                wdt = Wd * (math.sin(math.pi * min(1, u * 1.25 + 0.05)) ** 0.7) * (1 - u) ** 0.35
                left.append((cx + sway - wdt, y)); right.append((cx + sway + wdt, y))
            poly = left + right[::-1]
            if k == 0: d.polygon([(x, y) for x, y in poly], fill=col + (255,), outline=(50, 8, 4, 255), width=Z * 2)
            else: d.polygon(poly, fill=col + (255,))
        out.append(down(im))
    return out


def flame(frame, pos, t, a=1.0, scale=1.0):
    if a <= 0.01: return
    g = Image.new('RGBA', (220, 220), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    fl = 0.85 + 0.15 * math.sin(t * 7.3 + pos[0])
    for r, al in ((70, 30), (42, 55), (22, 80)):
        rr = r * fl * scale; gd.ellipse([110 - rr, 120 - rr * .7, 110 + rr, 120 + rr * .7], fill=(255, 120, 30, int(al * a)))
    g = g.filter(ImageFilter.GaussianBlur(18))
    frame.alpha_composite(g, (int(pos[0] - 110), int(pos[1] - 120))) if -200 < pos[0] < W + 200 and -200 < pos[1] < H + 200 else None
    pos = (pos[0] - 8, pos[1] - 4)
    fr = flame_frames()[int(t * 16 + pos[0]) % 12]
    paste(frame, fr, (pos[0], pos[1] - fr.height * .40 * scale), scale * (0.6 + 0.4 * back_out(min(1, a * 1.2))), a)


def ripples(frame, pos, t, t0, t1, col=(255, 255, 255), R=70):
    a = life(t, t0, t1, .3, .5)
    if a <= 0: return
    def fn(d, S):
        for k in range(3):
            ph = ((t - t0) * 0.7 + k / 3) % 1.0; r = R * (0.25 + ph)
            al = int(255 * a * (1 - ph) ** 1.2)
            d.ellipse([S((pos[0] - r, pos[1] - r * .62)), S((pos[0] + r, pos[1] + r * .62))], outline=col + (al,), width=int(4 * Z))
    local_draw(frame, (pos[0] - R * 1.4, pos[1] - R, pos[0] + R * 1.4, pos[1] + R), fn)


@functools.lru_cache(None)
def unit_tile(kind, s=50):
    im = Image.new('RGBA', ((s + 24) * Z, (s + 24) * Z), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    b = (10 * Z, 10 * Z, (s + 10) * Z, (s + 10) * Z)
    col = KC[kind]
    d.rounded_rectangle([b[0] + 4 * Z, b[1] + 6 * Z, b[2] + 4 * Z, b[3] + 6 * Z], radius=6 * Z, fill=(0, 0, 0, 120))
    d.rounded_rectangle([b[0] - 3 * Z, b[1] - 3 * Z, b[2] + 3 * Z, b[3] + 3 * Z], radius=8 * Z, fill=(36, 40, 54))
    d.rounded_rectangle([b[0] - 1 * Z, b[1] - 1 * Z, b[2] + 1 * Z, b[3] + 1 * Z], radius=7 * Z, fill=(220, 226, 236))
    d.rounded_rectangle(b, radius=6 * Z, fill=col)
    emblem(d, kind, (b[0] + b[2]) / 2, (b[1] + b[3]) / 2 + 2 * Z, s * Z * 0.62)
    return down(im)


def tile(frame, pos, kind, t, t0, t1=1e9, s=50, crossed=0.0):
    if t < t0 or t > t1: return
    k = back_out(prog(t, t0, t0 + 0.45)) * (1 - ease_out(prog(t, t1 - 0.3, t1)))
    paste(frame, unit_tile(kind, s), pos, k, min(1, prog(t, t0, t0 + .12) * 2))
    if crossed > 0:
        def fn(d, S):
            r = s * .62 * crossed
            for sg in (1, -1):
                d.line([S((pos[0] - r, pos[1] - r * sg)), S((pos[0] + r, pos[1] + r * sg))], fill=(20, 16, 16, 255), width=int(9 * Z))
                d.line([S((pos[0] - r, pos[1] - r * sg)), S((pos[0] + r, pos[1] + r * sg))], fill=(230, 220, 210, 255), width=int(3 * Z))
        local_draw(frame, (pos[0] - s, pos[1] - s, pos[0] + s, pos[1] + s), fn)


def catmull(pts, n=20):
    if len(pts) == 2: return [(lerp(pts[0][0], pts[1][0], i / n), lerp(pts[0][1], pts[1][1], i / n)) for i in range(n + 1)]
    p = [pts[0]] + list(pts) + [pts[-1]]; out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for j in range(n):
            t = j / n; t2, t3 = t * t, t ** 3
            out.append(tuple(0.5 * ((2 * p1[c]) + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2 + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in (0, 1)))
    out.append(pts[-1]); return out


def path_at(pts, k):
    path = catmull(pts, 24); L = [0]
    for i in range(len(path) - 1): L.append(L[-1] + math.dist(path[i], path[i + 1]))
    cut = L[-1] * clamp(k); j = max(1, next((i for i, l in enumerate(L) if l >= cut), len(L) - 1))
    seg = L[j] - L[j - 1]; f = (cut - L[j - 1]) / seg if seg else 0
    return (lerp(path[j - 1][0], path[j][0], f), lerp(path[j - 1][1], path[j][1], f)), path, L, j


def arrow(frame, pts, k, kind='mongol', w0=16, w1=30, a=1.0, dashed=False):
    if k <= 0.002 or a <= 0.01: return
    tipp, path, L, j = path_at(pts, k)
    pp = path[:j] + [tipp]
    if len(pp) < 2: return
    col = KC[kind]
    def fn(d, S):
        head = w1 * 1.9; body = list(pp); ln = 0
        while len(body) > 2 and ln < head * .75: ln += math.dist(body[-1], body[-2]); body.pop()
        base = body[-1]; tip = pp[-1]; ang = math.atan2(tip[1] - base[1], tip[0] - base[0])
        if dashed:
            acc = 0
            for i in range(len(body) - 1):
                acc += math.dist(body[i], body[i + 1])
                if int(acc / 22) % 2 == 0:
                    d.line([S(body[i]), S(body[i + 1])], fill=(30, 20, 20, int(255 * a)), width=int((w0 * .55 + 4) * Z))
                    d.line([S(body[i]), S(body[i + 1])], fill=col + (int(255 * a),), width=int(w0 * .55 * Z))
            hw = w1 * .8
        else:
            left, right = [], []; n = len(body)
            for i, p in enumerate(body):
                q = body[min(i + 1, n - 1)]; o = body[max(i - 1, 0)]; an = math.atan2(q[1] - o[1], q[0] - o[0])
                ww = lerp(w0, w1, (i / max(1, n - 1)) ** .7) / 2
                left.append((p[0] + ww * math.sin(an), p[1] - ww * math.cos(an))); right.append((p[0] - ww * math.sin(an), p[1] + ww * math.cos(an)))
            hw = w1 * 1.15
        hl = (base[0] + hw * math.sin(ang), base[1] - hw * math.cos(ang)); hr = (base[0] - hw * math.sin(ang), base[1] + hw * math.cos(ang))
        poly = (left + [hl, tip, hr] + right[::-1]) if not dashed else [hl, tip, hr]
        d.polygon([S((x + 6, y + 8)) for x, y in poly], fill=(0, 0, 0, int(90 * a)))
        d.polygon([S(p) for p in poly], fill=col + (int(235 * a),), outline=(250, 250, 252, int(255 * a)), width=int(3.5 * Z))
        if not dashed:  # inner highlight stroke
            hi = tuple(min(255, c + 60) for c in col)
            d.line([S(p) for p in body[:-1]], fill=hi + (int(120 * a),), width=int(max(2, w0 * .18) * Z), joint='curve')
    xs = [p[0] for p in pp]; ys = [p[1] for p in pp]
    local_draw(frame, (min(xs) - w1 * 2, min(ys) - w1 * 2, max(xs) + w1 * 2, max(ys) + w1 * 2), fn)


def river_glow(frame, pts_screen, a):
    if a <= 0: return
    def fn(d, S):
        d.line([S(p) for p in pts_screen], fill=(170, 220, 255, int(140 * a)), width=int(16 * Z), joint='curve')
        d.line([S(p) for p in pts_screen], fill=(240, 250, 255, int(255 * a)), width=int(5 * Z), joint='curve')
    xs = [p[0] for p in pts_screen]; ys = [p[1] for p in pts_screen]
    local_draw(frame, (min(xs) - 20, min(ys) - 20, max(xs) + 20, max(ys) + 20), fn)


@functools.lru_cache(None)
def vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    return np.clip(1.04 - 0.22 * r ** 2.4, 0.6, 1.0)[..., None]


def grade(frame):
    a = np.asarray(frame.convert('RGB'), np.float32) * vignette()
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


# ================================================================ v3 additions
CUTS = {  # cutout portrait framing: (face-centre x frac, helmet-top y frac, chin y frac)
    'batu_cut.png': (0.50, 0.02, 0.58), 'yuri_cut.png': (0.50, 0.03, 0.56), 'burundai_cut.png': (0.58, 0.00, 0.58),
}


@functools.lru_cache(None)
def popout_disc(path, D, fallen=False):
    """portrait whose helmet breaks out of the top of the ring (the competitor's signature look)"""
    cut = Image.open(os.path.join(IMG, path)).convert('RGBA')
    fx, top, chin = CUTS[path]
    if fallen:
        g = ImageOps.grayscale(cut).convert('RGB'); g = ImageEnhance.Brightness(g).enhance(0.75)
        g = Image.blend(g, Image.new('RGB', g.size, (120, 20, 20)), 0.22); g.putalpha(cut.getchannel('A')); cut = g
    R = D * Z / 2; r = R * 0.80
    S = (1.75 * R) / (chin - top)
    cut = cut.resize((int(S), int(S)), Image.LANCZOS)
    pad = int(R * 0.9)
    W2 = int(2 * R + 2 * pad); im = Image.new('RGBA', (W2, W2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx = W2 / 2; cy = W2 / 2 + pad * 0.35
    ox = int(cx - fx * S); oy = int(cy - 1.3 * R - top * S)
    d.ellipse([cx - R + 6 * Z, cy - R + 9 * Z, cx + R + 6 * Z, cy + R + 9 * Z], fill=(0, 0, 0, 130))
    pal = ((60, 72, 100), (205, 214, 232), (120, 136, 170), (52, 62, 88)) if not fallen else ((40, 20, 20), (150, 60, 60), (90, 30, 30), (30, 10, 10))
    ring(d, cx, cy, R, r - 2 * Z, pal)
    # inner backdrop: deep steel-blue radial
    bd = Image.new('RGBA', im.size, (0, 0, 0, 0)); bdd = ImageDraw.Draw(bd)
    for i in range(int(r), 0, -2):
        f = i / r; bdd.ellipse([cx - i, cy - i, cx + i, cy + i], fill=(int(lerp(150, 70, f)), int(lerp(165, 84, f)), int(lerp(190, 112, f)), 255))
    lay = Image.new('RGBA', im.size, (0, 0, 0, 0)); lay.alpha_composite(cut, (ox, oy))
    circ = Image.new('L', im.size, 0); ImageDraw.Draw(circ).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    inside = Image.alpha_composite(bd, lay); im.paste(inside, (0, 0), circ)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(28, 32, 44), width=int(3 * Z))
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(28, 32, 44), width=int(3 * Z))
    # pop-out: everything of the figure above the ring's centre that lies outside the inner circle
    yy = np.arange(im.height)[:, None]; upper = (yy < cy - r * 0.15).astype(np.float32) * np.ones((1, im.width), np.float32)
    al = np.asarray(lay.getchannel('A'), np.float32) / 255 * upper * (1 - np.asarray(circ, np.float32) / 255)
    pop = lay.copy(); pop.putalpha(Image.fromarray((al * 255).astype(np.uint8)))
    shadow = Image.new('RGBA', im.size, (0, 0, 0, 0)); shadow.putalpha(Image.fromarray((al * 140).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5 * Z)))
    im.alpha_composite(shadow, (4 * Z, 6 * Z)); im.alpha_composite(pop)
    if fallen:
        bx, by, u = cx + r * .66, cy + r * .45, r * .2
        d = ImageDraw.Draw(im)
        d.ellipse([bx - u * 1.6, by - u * 1.6, bx + u * 1.6, by + u * 1.6], fill=(25, 15, 15), outline=(200, 190, 180), width=Z * 2)
        d.rectangle([bx - u * .16, by - u * 1.1, bx + u * .16, by + u * 1.1], fill=(235, 225, 210))
        d.rectangle([bx - u * .7, by - u * .55, bx + u * .7, by - u * .3], fill=(235, 225, 210))
        d.polygon([(bx - u * .5, by + u * .35), (bx + u * .5, by + u * .6), (bx + u * .5, by + u * .8), (bx - u * .5, by + u * .55)], fill=(235, 225, 210))
    out = down(im)
    out.info['cy_off'] = (cy - W2 / 2) / Z
    return out


@functools.lru_cache(None)
def cloth_ribbon(name, title, flip=False):
    """parchment-cloth banner with folds, gradient and fibre texture"""
    fn, ft = F('Almendra-Bold.ttf', 50 * Z), F('Almendra-Regular.ttf', 30 * Z)
    tw = max(fn.getlength(name), ft.getlength(title) if title else 0)
    L = tw + 170 * Z; Hh = (98 if title else 70) * Z
    Wc, Hc = int(L + 60 * Z), int(Hh + 60 * Z)
    x0, y0 = 10 * Z, 25 * Z; x1, y1 = x0 + L, y0 + Hh
    wave = lambda x: 7 * Z * math.sin((x - x0) / L * math.pi * 1.6)
    top = [(x0 + (x1 - x0) * i / 30, y0 + wave(x0 + (x1 - x0) * i / 30)) for i in range(31)]
    bot = [(x, y + Hh) for x, y in top][::-1]
    tail = [(x1 + 34 * Z, y0 + wave(x1) - 10 * Z), (x1 - 4 * Z, (y0 + y1) / 2 + wave(x1)), (x1 + 34 * Z, y1 + wave(x1) + 10 * Z)]
    poly = top + tail + bot
    m = Image.new('L', (Wc, Hc), 0); ImageDraw.Draw(m).polygon(poly, fill=255)
    rng = np.random.default_rng(len(name))
    yy, xx = np.mgrid[0:Hc, 0:Wc].astype(np.float32)
    fib = rng.random((Hc // (2 * Z) + 1, Wc // (14 * Z) + 1)).astype(np.float32)
    fib = np.asarray(Image.fromarray(fib, 'F').resize((Wc, Hc), Image.BICUBIC))
    fold = 0.86 + 0.14 * np.cos((xx - x0) / L * math.pi * 3.2)
    vg = 1.05 - 0.22 * np.abs((yy - (y0 + y1) / 2) / (Hh / 2))
    base = np.array([214, 210, 236], np.float32)
    rgb = base * (fold * vg * (0.93 + 0.12 * fib))[..., None]
    im = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0))
    sh = m.filter(ImageFilter.GaussianBlur(5 * Z)); shl = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0)); shl.putalpha(sh.point(lambda v: int(v * .5)))
    im.alpha_composite(shl, (5 * Z, 8 * Z))
    edge = Image.new('RGBA', (Wc, Hc), (58, 54, 96, 255)); im.paste(edge, (0, 0), m.filter(ImageFilter.MaxFilter(3 * Z + 1 if (3 * Z) % 2 == 0 else 3 * Z)))
    tex = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert('RGBA'); im.paste(tex, (0, 0), m)
    if flip:
        im = ImageOps.mirror(im); tx = Wc - (x0 + 110 * Z + tw / 2)
    else:
        tx = x0 + 110 * Z + tw / 2
    d = ImageDraw.Draw(im); wy = wave(x0 + 110 * Z + tw / 2)
    col, col2 = (150, 92, 40), (122, 82, 48)
    if title:
        d.text((tx, y0 + Hh * .38 + wy), name, font=fn, fill=col, anchor='mm', stroke_width=Z, stroke_fill=(70, 40, 20))
        d.text((tx, y0 + Hh * .76 + wy), title, font=ft, fill=col2, anchor='mm')
    else:
        d.text((tx, (y0 + y1) / 2 + wy), name, font=fn, fill=col, anchor='mm', stroke_width=Z, stroke_fill=(70, 40, 20))
    return down(im)


class PopMedallion(Medallion):
    def __init__(self, cut, name, title, side=None, D=250, flip=False, fallen=False):
        self.disc = popout_disc(cut, D, fallen); self.D = D
        self.sh = shield(side, D * .34) if side else None
        self.rib = cloth_ribbon(name, title, flip); self.flip = flip
    def draw(self, frame, pos, t, t0, t1, target=None):
        if t < t0 or t > t1 + 0.4: return
        pin = back_out(prog(t, t0, t0 + 0.45), 2.2); pout = 1 - ease_out(prog(t, t1 - 0.3, t1))
        s = pin * pout; a = min(1, prog(t, t0, t0 + 0.12) * 1.5) * pout
        if s <= 0.01: return
        x, y = pos; off = self.disc.info.get('cy_off', 0)
        if target is not None and s > 0.5:
            def fn(d, S):
                ang = math.atan2(target[1] - y, target[0] - x); dist = math.dist(target, (x, y))
                b1 = (x + math.cos(ang + 0.42) * self.D * .44, y + math.sin(ang + 0.42) * self.D * .44)
                b2 = (x + math.cos(ang - 0.42) * self.D * .44, y + math.sin(ang - 0.42) * self.D * .44)
                k = min(1, (s - .5) * 2); tip = (x + math.cos(ang) * dist * k, y + math.sin(ang) * dist * k)
                d.polygon([S((p[0] + 3, p[1] + 5)) for p in (b1, tip, b2)], fill=(0, 0, 0, 90))
                d.polygon([S(b1), S(tip), S(b2)], fill=(240, 242, 248, 250), outline=(40, 44, 60, 255), width=Z * 2)
            local_draw(frame, (x - self.D * 1.2, y - self.D * 1.2, x + self.D * 1.2, y + self.D * 1.2), fn, a)
        k = ease_out(prog(t, t0 + 0.18, t0 + 0.7)) * pout
        if k > 0.02:
            rb = self.rib; cw = max(1, int(rb.width * k))
            part = rb.crop((rb.width - cw, 0, rb.width, rb.height)) if self.flip else rb.crop((0, 0, cw, rb.height))
            ry = y + self.D * 0.02
            rx = x + self.D * 0.28 if not self.flip else x - self.D * 0.28 - part.width
            if a < 0.999: part = part.copy(); part.putalpha(part.getchannel('A').point(lambda v: int(v * a)))
            if rx > -part.width and rx < W: frame.alpha_composite(part, (int(max(rx, -part.width + 1)), int(max(0, ry - rb.height / 2)))) if rx >= 0 else frame.alpha_composite(part.crop((int(-rx), 0, part.width, part.height)), (0, int(max(0, ry - rb.height / 2))))
        paste(frame, self.disc, (x, y - off * s), s, a)
        if self.sh is not None:
            ks = back_out(prog(t, t0 + 0.12, t0 + 0.55)) * pout
            paste(frame, self.sh, (x, y + self.D * 0.47 * s), ks * s, a)


@functools.lru_cache(None)
def round_shield(kind, D, wreath=False):
    im = Image.new('RGBA', (int(D * 1.5 * Z), int(D * 1.5 * Z)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = im.width / 2; R = D * Z / 2
    if wreath:
        for side in (-1, 1):
            for i in range(9):
                a = math.radians(110 + i * 17) if side < 0 else math.radians(70 - i * 17)
                rr = R * 1.18; lx, ly = c + rr * math.cos(a), c + rr * math.sin(a) * -1 + R * .05
                L_ = R * .30; ang = a + side * math.pi / 2 * -1
                pts = [(lx + L_ * math.cos(ang + q) * (0.5 if abs(q) > 0 else 1), ly - L_ * math.sin(ang + q) * (0.5 if abs(q) > 0 else 1)) for q in (0, 0.55, math.pi, -0.55)]
                d.polygon(pts, fill=(222, 178, 60), outline=(110, 74, 20), width=Z * 2)
    d.ellipse([c - R + 4 * Z, c - R + 6 * Z, c + R + 4 * Z, c + R + 6 * Z], fill=(0, 0, 0, 120))
    ring(d, c, c, R, R * .80)
    col = KC[kind]
    rr = R * .80
    for i in range(int(rr), 0, -2):
        f = i / rr; d.ellipse([c - i, c - i, c + i, c + i], fill=tuple(int(cc * (1.25 - .35 * f)) if cc * (1.25 - .35 * f) < 255 else 255 for cc in col))
    emblem(d, kind, c, c + R * .05, R * .9)
    d.ellipse([c - rr, c - rr, c + rr, c + rr], outline=(25, 30, 44), width=Z * 2)
    return down(im)


@functools.lru_cache(None)
def pill3(title, sub, lk='mongol', rk='rus'):
    ft, fs = F('IMFeENsc28P.ttf', 44 * Z), F('IMFeENrm28P.ttf', 34 * Z)
    tw = max(ft.getlength(title), fs.getlength(sub)); w = tw / Z + 230; h = 96
    im = Image.new('RGBA', (int((w + 160) * Z), int((h + 120) * Z)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    b = (80 * Z, 60 * Z, int((w + 80) * Z), (h + 60) * Z)
    d.rounded_rectangle([b[0] + 5 * Z, b[1] + 8 * Z, b[2] + 5 * Z, b[3] + 8 * Z], radius=24 * Z, fill=(0, 0, 0, 110))
    steel_frame(d, b, 22 * Z)
    pw, ph = b[2] - b[0], b[3] - b[1]
    yy = np.linspace(0, 1, ph)[:, None] * np.ones((1, pw))
    g = (232 - 40 * np.abs(yy - 0.35)).astype(np.float32)
    fill = Image.fromarray(np.dstack([g, g * 0.985, g * 1.02]).clip(0, 255).astype(np.uint8)).convert('RGBA')
    mk = Image.new('L', (pw, ph), 0); ImageDraw.Draw(mk).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=20 * Z, fill=255)
    im.paste(fill, (b[0], b[1]), mk)
    d.text(((b[0] + b[2]) / 2, b[1] + h * Z * .36), title, font=ft, fill=(30, 28, 46), anchor='mm')
    d.text(((b[0] + b[2]) / 2, b[1] + h * Z * .76), sub, font=fs, fill=(30, 28, 46), anchor='mm')
    out = down(im)
    for kind, x, wr in ((lk, 80, True), (rk, w + 80, False)):
        sh = round_shield(kind, 112, wr); out.alpha_composite(sh, (int(x - sh.width / 2), int(60 + h / 2 - sh.height / 2)))
    return out


def draw_pill3(frame, pos, t, t0, t1, title, sub, lk='mongol', rk='rus'):
    if t < t0 or t > t1: return
    s = back_out(prog(t, t0, t0 + 0.45), 2.0) * (1 - ease_out(prog(t, t1 - 0.3, t1)))
    paste(frame, pill3(title, sub, lk, rk), pos, s, min(1, prog(t, t0, t0 + .12) * 2))


@functools.lru_cache(None)
def unit_block(kind, cols=4, rows=3, bw=50, bh=30, gap=6):
    Wd, Hd = cols * (bw + gap) + 20, rows * (bh + gap) + 20
    im = Image.new('RGBA', (Wd * Z, Hd * Z), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = KC[kind]; hi = tuple(min(255, c + 70) for c in col)
    for r in range(rows):
        for c in range(cols):
            x0 = (10 + c * (bw + gap)) * Z; y0 = (10 + r * (bh + gap)) * Z; x1 = x0 + bw * Z; y1 = y0 + bh * Z
            d.rectangle([x0 + 3 * Z, y0 + 4 * Z, x1 + 3 * Z, y1 + 4 * Z], fill=(0, 0, 0, 110))
            d.rectangle([x0, y0, x1, y1], fill=(20, 22, 40))
            d.rectangle([x0 + 2 * Z, y0 + 2 * Z, x1 - 2 * Z, y1 - 2 * Z], fill=col)
            d.rectangle([x0 + 2 * Z, y0 + 2 * Z, x1 - 2 * Z, y0 + 9 * Z], fill=hi)
            d.line([(x0 + 2 * Z, y0 + 2 * Z), (x1 - 2 * Z, y1 - 2 * Z)], fill=(18, 20, 36), width=int(2.5 * Z))
            d.line([(x0 + 2 * Z, y1 - 2 * Z), (x1 - 2 * Z, y0 + 2 * Z)], fill=(18, 20, 36), width=int(2.5 * Z))
    return down(im)


def block(frame, pos, kind, t, t0, t1=1e9, scale=1.0, cols=4, rows=3, crossed=0.0):
    if t < t0 or t > t1: return
    k = back_out(prog(t, t0, t0 + 0.4)) * (1 - ease_out(prog(t, t1 - 0.3, t1)))
    spr = unit_block(kind, cols, rows)
    paste(frame, spr, pos, k * scale, min(1, prog(t, t0, t0 + .12) * 2))
    if crossed > 0:
        def fn(d, S):
            r = spr.width * scale * .42 * crossed; rh = spr.height * scale * .45 * crossed
            for sg in (1, -1):
                d.line([S((pos[0] - r, pos[1] - rh * sg)), S((pos[0] + r, pos[1] + rh * sg))], fill=(16, 12, 12, 255), width=int(12 * Z))
                d.line([S((pos[0] - r, pos[1] - rh * sg)), S((pos[0] + r, pos[1] + rh * sg))], fill=(236, 226, 214, 255), width=int(4 * Z))
        local_draw(frame, (pos[0] - spr.width, pos[1] - spr.height, pos[0] + spr.width, pos[1] + spr.height), fn)


@functools.lru_cache(None)
def swords_icon(s=46):
    im = Image.new('RGBA', (s * 2 * Z, s * 2 * Z), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = s * Z
    for sg in (1, -1):
        a = math.radians(45 * sg); ca, sa = math.cos(a), math.sin(a)
        def P(u, v): return (c + u * sa * s * Z + v * ca * s * Z * 0.0 + v * s * Z * ca * 0, c - u * ca * s * Z)
        tip = (c + sg * s * Z * .8, c - s * Z * .8); hilt = (c - sg * s * Z * .55, c + s * Z * .55)
        d.line([tip, hilt], fill=(20, 20, 26), width=int(9 * Z)); d.line([tip, hilt], fill=(226, 230, 238), width=int(5 * Z))
        gx, gy = c - sg * s * Z * .38, c + s * Z * .38
        d.line([(gx - s * Z * .2, gy - sg * s * Z * .2 * -1 * -1), (gx + s * Z * .2, gy + sg * s * Z * .2 * -1 * -1)], fill=(20, 20, 26), width=int(8 * Z))
        d.line([(gx - s * Z * .2, gy - s * Z * .2 * sg * -1 * -1), (gx + s * Z * .2, gy + s * Z * .2 * sg * -1 * -1)], fill=(200, 160, 70), width=int(4 * Z))
    return down(im)


def scorch(frame, pts, k, t, width=60, a=0.62, seed=0):
    """dark burned trail left behind the horde, revealed along its path"""
    if k <= 0.003: return
    tip, path, L, j = path_at(pts, k); pp = path[:j] + [tip]
    if len(pp) < 2: return
    rng = np.random.default_rng(seed)
    blobs = [(rng.uniform(-.5, .5), rng.uniform(.35, .75), rng.uniform(-.6, .6)) for _ in range(400)]
    def fn(d, S):
        d.line([S(p) for p in pp], fill=(66, 44, 36, int(255 * a)), width=int(width * .55 * Z), joint='curve')
        acc = 0; bi = 0
        for i in range(len(pp) - 1):
            seg = math.dist(pp[i], pp[i + 1]); acc += seg
            n = max(1, int(seg / (width * .35)))
            an = math.atan2(pp[i + 1][1] - pp[i][1], pp[i + 1][0] - pp[i][0])
            for q in range(n):
                f = q / n; x = lerp(pp[i][0], pp[i + 1][0], f); y = lerp(pp[i][1], pp[i + 1][1], f)
                o, rr, o2 = blobs[bi % 400]; bi += 1
                x += -math.sin(an) * o * width; y += math.cos(an) * o * width; r = rr * width * .6
                d.ellipse([S((x - r, y - r * .8)), S((x + r, y + r * .8))], fill=(70, 46, 38, int(255 * a)))
    xs = [p[0] for p in pp]; ys = [p[1] for p in pp]
    lay = Image.new('RGBA', frame.size, (0, 0, 0, 0))
    local_draw(lay, (min(xs) - width * 1.5, min(ys) - width * 1.5, max(xs) + width * 1.5, max(ys) + width * 1.5), fn)
    # multiply-ish: darken the map underneath
    al = lay.getchannel('A').filter(ImageFilter.GaussianBlur(2.5))
    dark = Image.new('RGBA', frame.size, (58, 36, 28, 0)); dark.putalpha(al)
    frame.alpha_composite(dark)


def _persp_coeffs(src, dst):
    A = []; B = []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def drop_in(img, t, dur=0.8):
    """opening move: the map plate falls from above on a tilt and lands flat"""
    if t >= dur: return img
    k = ease_out(prog(t, 0, dur)) ** 0.9; k2 = back_out(prog(t, 0.1, dur), 1.1)
    dy = -H * 1.05 * (1 - k)
    tilt = (1 - k2) * 0.10  # perspective lean: top edge narrower
    rot = (1 - k2) * -3.0
    corners = [(0, 0), (W, 0), (W, H), (0, H)]
    cx, cy = W / 2, H / 2
    out = []
    for i, (x, y) in enumerate(corners):
        x2 = cx + (x - cx) * (1 - tilt if y == 0 else 1 + tilt * 0.3)
        y2 = y + dy
        a = math.radians(rot); xr = cx + (x2 - cx) * math.cos(a) - (y2 - cy) * math.sin(a); yr = cy + (x2 - cx) * math.sin(a) + (y2 - cy) * math.cos(a)
        out.append((xr, yr))
    co = _persp_coeffs(corners, out)
    bg = Image.new('RGB', (W, H), (18, 18, 22))
    warped = img.transform((W, H), Image.PERSPECTIVE, co, Image.BICUBIC, fillcolor=(8, 8, 10))
    m = Image.new('L', (W, H), 255).transform((W, H), Image.PERSPECTIVE, co, Image.BILINEAR, fillcolor=0)
    bg.paste(warped, (0, 0), m)
    return bg


def sharpen(img): return img.filter(ImageFilter.UnsharpMask(1.1, 40, 2))


# ---------------------------------------------------------------- noor medallion (religious figures: no face, only light)
@functools.lru_cache(None)
def noor_disc(D, ring_pal=((150, 120, 50), (250, 226, 150), (190, 150, 70), (110, 84, 30))):
    R = D * Z / 2; r = R * 0.80; pad = int(R * 0.5); W2 = int(2 * R + 2 * pad)
    im = Image.new('RGBA', (W2, W2), (0, 0, 0, 0)); d = ImageDraw.Draw(im); cx = cy = W2 / 2
    # outer glow
    gl = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(gl).ellipse([cx - R * 1.18, cy - R * 1.18, cx + R * 1.18, cy + R * 1.18], fill=(255, 246, 214, 150))
    im.alpha_composite(gl.filter(ImageFilter.GaussianBlur(R * .16)))
    d.ellipse([cx - R + 6 * Z, cy - R + 9 * Z, cx + R + 6 * Z, cy + R + 9 * Z], fill=(0, 0, 0, 90))
    ring(d, cx, cy, R, r - 2 * Z, ring_pal)
    # inner: pure radiant light, white core to soft gold, with rays; no figure at all
    n = int(r); yy, xx = np.mgrid[0:W2, 0:W2].astype(np.float32)
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r; ang = np.arctan2(yy - cy, xx - cx)
    rays = 0.5 + 0.5 * np.cos(ang * 16) ** 8
    f = np.clip(dist, 0, 1)
    lum = np.clip(1.0 - 0.12 * f ** 1.6 + 0.05 * rays * f, 0, 1)
    rgb = np.dstack([255 * lum, (250 - 26 * f ** 2) * lum, (236 - 70 * f ** 2) * lum])
    lightI = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert('RGBA')
    circ = Image.new('L', im.size, 0); ImageDraw.Draw(circ).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    im.paste(lightI, (0, 0), circ)
    core = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(core).ellipse([cx - r * .55, cy - r * .55, cx + r * .55, cy + r * .55], fill=(255, 255, 255, 255))
    im.alpha_composite(core.filter(ImageFilter.GaussianBlur(r * .22)))
    d = ImageDraw.Draw(im)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(120, 90, 30), width=int(3 * Z))
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(90, 66, 20), width=int(3 * Z))
    out = down(im); out.info['cy_off'] = 0
    return out


class NoorMedallion(PopMedallion):
    """Medallion for a religious personality: the face is entirely replaced by white light (noor)."""
    def __init__(self, name, title, side=None, D=250, flip=False):
        self.disc = noor_disc(D); self.D = D
        self.sh = shield(side, D * .34) if side else None
        self.rib = cloth_ribbon(name, title, flip); self.flip = flip


# ---------------------------------------------------------------- v2.5: waving cloth, army tokens, city rings, raid arrows
def wave(img, t, amp=3.0, wl=70.0, speed=2.2, phase=0.0):
    """gentle cloth flutter: every pixel column slides up/down on a travelling sine (like a banner in light wind)"""
    a = np.asarray(img); H_, W2 = a.shape[:2]; pad = int(amp) + 2
    out = np.zeros((H_ + 2 * pad, W2, a.shape[2]), a.dtype)
    xs = np.arange(W2); off = (amp * np.sin(xs / wl * 2 * math.pi - t * speed + phase) * np.clip(xs / max(1, W2 * .25), 0.25, 1)).astype(int)
    for x in range(0, W2):
        o = pad + off[x]; out[o:o + H_, x] = a[:, x]
    return Image.fromarray(out, img.mode)

_med_draw = Medallion.draw
def _med_draw_wave(self, frame, pos, t, t0, t1, target=None):
    rb0 = self.rib
    self.rib = wave(rb0, t, amp=2.6, wl=90)
    try: _med_draw(self, frame, pos, t, t0, t1, target)
    finally: self.rib = rb0
Medallion.draw = _med_draw_wave


class ArmyToken:
    """commander portrait + waving name ribbon + his army's unit blocks, travelling together (competitor style)"""
    def __init__(self, disc, name, title, kind, cols=4, rows=2, flip=False):
        self.disc = disc; self.kind = kind; self.flip = flip
        self.rib = cloth_ribbon(name, title, flip=flip); self.rib = self.rib.resize((int(self.rib.width * .62), int(self.rib.height * .62)), Image.LANCZOS)
        self.blk = unit_block(kind, cols=cols, rows=rows, bw=36, bh=22, gap=5)
    def draw(self, frame, pos, t, s=1.0, a=1.0, ribbon=True, blocks=True, heading=None):
        if a <= .02 or s <= .02: return
        x, y = pos
        if blocks:
            hx, hy = heading if heading and math.hypot(*heading) > 1e-3 else (1, 0); n = math.hypot(hx, hy); hx, hy = hx / n, hy / n
            back = self.disc.width * .55 + max(self.blk.width, self.blk.height) * .55
            paste(frame, self.blk, (x - hx * back, y - hy * back), s, a)      # his army marches in formation right behind him
        dy = y
        if ribbon:
            rb = wave(self.rib, t, amp=2.4, wl=80)
            if a < .999: rb = rb.copy(); rb.putalpha(rb.getchannel('A').point(lambda v: int(v * a)))
            rx = x + self.disc.width * .32 if not self.flip else x - self.disc.width * .32 - rb.width
            k = min(1.0, s)
            if k > .3: frame.alpha_composite(rb, (int(rx), int(dy - rb.height / 2 + 6)))
        paste(frame, self.disc, (x, dy), s, a)


def city_ring(frame, pos, t, t0, dur=2.4, r=34):
    """white partial ring that pops onto a city when the narrator names it, turning slowly"""
    if not (t0 <= t <= t0 + dur): return
    a = min(1, prog(t, t0, t0 + .25) * 1.2) * (1 - smooth(prog(t, t0 + dur - .5, t0 + dur)))
    s = back_out(prog(t, t0, t0 + .45)); R = r * (0.6 + 0.4 * s)
    rot = (t - t0) * 28            # slow turn; three arcs with gaps so it never reads as a loading spinner
    def fn(d, S):
        x, y = pos
        for dx, dy, col, wd in ((1.5, 2.5, (0, 0, 0, 100), 8), (0, 0, (250, 250, 252, 255), 6)):
            bb = [S((x - R + dx, y - R + dy)), S((x + R + dx, y + R + dy))]
            for k in range(3):
                d.arc([bb[0][0], bb[0][1], bb[1][0], bb[1][1]], rot + k * 120 + 14, rot + k * 120 + 106, fill=col, width=int(wd * Z))
    local_draw(frame, (pos[0] - R - 14, pos[1] - R - 14, pos[0] + R + 14, pos[1] + R + 14), fn, a)


def raid_arrow(frame, pts, k, a=1.0, seg=13, gap=7, w=11):
    """white dashed raid arrow with a solid white head, the dashes growing along the path"""
    if k <= 0 or a <= 0: return
    (hx, hy), path, L, j = path_at(pts, k); total = L[-1] * clamp(k)
    if total < 4: return
    xs = [p[0] for p in path]; ys = [p[1] for p in path]
    def pt(dist):
        i = max(1, next((i for i, l in enumerate(L) if l >= dist), len(L) - 1)); sg = L[i] - L[i - 1]; f = (dist - L[i - 1]) / sg if sg else 0
        return (lerp(path[i - 1][0], path[i][0], f), lerp(path[i - 1][1], path[i][1], f))
    def fn(d, S):
        dist = 0.0; head_len = 30
        while dist < total - head_len:
            p0 = pt(dist); p1 = pt(min(total - head_len, dist + seg))
            d.line([S((p0[0] + 2, p0[1] + 3)), S((p1[0] + 2, p1[1] + 3))], fill=(0, 0, 0, 90), width=int((w + 2) * Z))
            d.line([S(p0), S(p1)], fill=(250, 250, 252, 255), width=int(w * Z)); dist += seg + gap
        b = pt(max(0, total - head_len)); ang = math.atan2(hy - b[1], hx - b[0])
        tri = [(hx + math.cos(ang) * 6, hy + math.sin(ang) * 6), (b[0] + math.cos(ang + 1.57) * 20, b[1] + math.sin(ang + 1.57) * 20),
               (b[0] + math.cos(ang - 1.57) * 20, b[1] + math.sin(ang - 1.57) * 20)]
        d.polygon([S((x + 2, y + 3)) for x, y in tri], fill=(0, 0, 0, 100)); d.polygon([S(p) for p in tri], fill=(250, 250, 252, 255))
    local_draw(frame, (min(xs) - 40, min(ys) - 40, max(xs) + 40, max(ys) + 40), fn, a)


@functools.lru_cache(None)
def swords_year(year, s=40):
    """crossed swords + year written on the map at a battle or siege site"""
    sw = swords_icon(s); f = F('Almendra-Regular.ttf', int(s * .62))
    tw = int(f.getlength(year)) + 10; im = Image.new('RGBA', (sw.width + tw + 6, max(sw.height, int(s * .9))), (0, 0, 0, 0))
    im.alpha_composite(sw, (0, (im.height - sw.height) // 2)); d = ImageDraw.Draw(im)
    d.text((sw.width + 3, im.height / 2 + 4), year, font=f, fill=(236, 232, 226, 240), anchor='lm', stroke_width=2, stroke_fill=(40, 30, 26, 200))
    return im



@functools.lru_cache(None)
def _print_sprite(cav, col=(58, 40, 30)):
    s = 14 * Z; im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if cav:   # horseshoe
        d.arc([2 * Z, 2 * Z, s - 2 * Z, s - 2 * Z], 200, 340 + 180, fill=col + (230,), width=int(2.6 * Z))
    else:     # boot print
        d.ellipse([4 * Z, 1 * Z, s - 4 * Z, s * .62], fill=col + (220,)); d.ellipse([5 * Z, s * .66, s - 5 * Z, s - 1 * Z], fill=col + (220,))
    return down(im)


def footprints(frame, pts, k, a=1.0, cav=True, step=26):
    """the march as a trail of small hoof (cavalry) or foot prints, alternating left/right, fading at the tail"""
    if k <= 0 or a <= 0: return
    (hx, hy), path, L, j = path_at(pts, k); total = L[-1] * clamp(k)
    spr = _print_sprite(bool(cav)); dist = 0.0; n = 0
    def pt(dd):
        i = max(1, next((i for i, l in enumerate(L) if l >= dd), len(L) - 1)); sg = L[i] - L[i - 1]; f = (dd - L[i - 1]) / sg if sg else 0
        return (lerp(path[i - 1][0], path[i][0], f), lerp(path[i - 1][1], path[i][1], f)), math.atan2(path[i][1] - path[i - 1][1], path[i][0] - path[i - 1][0])
    while dist < total - 40:
        (px, py), ang = pt(dist); side = 7 if n % 2 else -7
        px += -math.sin(ang) * side; py += math.cos(ang) * side
        fade = a * (0.35 + 0.65 * clamp(dist / max(1, total)))
        im = spr.rotate(-math.degrees(ang) - 90, Image.BICUBIC, expand=True)
        if fade < .999: im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * fade)))
        frame.alpha_composite(im, (int(px - im.width / 2), int(py - im.height / 2))) if 0 <= px < W and 0 <= py < H else None
        dist += step; n += 1
