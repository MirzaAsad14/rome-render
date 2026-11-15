"""Era map styles: the same illustrated atlas re-coloured per frame so the map itself 'ages forward' through a long video.
ancient (clay & papyrus) -> medieval (illuminated parchment, the native atlas look) -> safavid (Persian miniature: lapis & gold)
-> qajar (19th-c. engraved survey) -> pahlavi (20th-c. printed atlas) -> modern (digital military display).
stylize(img, land, desert, style, view) works on a 1920x1080 RGB frame; land/desert are float masks of the same size."""
import functools, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); FD = os.path.join(HERE, 'assets/fonts')
W, H = 1920, 1080
STYLES = ('atlas', 'ancient', 'medieval', 'safavid', 'qajar', 'pahlavi', 'modern')

def F(name, size): return ImageFont.truetype(os.path.join(FD, name), int(size))

# label look per style: (font, fill, stroke, stroke_fill, uppercase, tracking)
LABEL = {
    'atlas':    ('Almendra-Regular.ttf', (250, 246, 238), 2, (40, 26, 22, 210), False, 0.0),
    'ancient':  ('Cinzel.ttf', (74, 40, 18), 3, (238, 214, 170, 210), True, 0.18),
    'medieval': ('Almendra-Regular.ttf', (250, 246, 238), 2, (40, 26, 22, 210), False, 0.0),
    'safavid':  ('EBGaramond-Italic.ttf', (120, 24, 20), 3, (250, 236, 196, 230), False, 0.02),
    'qajar':    ('IMFeENrm28P.ttf', (30, 28, 26), 3, (244, 240, 230, 220), False, 0.04),
    'pahlavi':  ('RobotoCondensed.ttf', (24, 28, 34), 3, (250, 250, 246, 220), True, 0.10),
    'modern':   ('RobotoCondensed.ttf', (214, 240, 248), 3, (4, 14, 22, 230), True, 0.14),
}
REALM = {  # realm-name label look
    'atlas': ('IMFeENrm28P.ttf', (250, 246, 244, 210)),
    'ancient': ('Cinzel.ttf', (96, 44, 20, 200)), 'medieval': ('IMFeENrm28P.ttf', (250, 246, 244, 210)),
    'safavid': ('EBGaramond-Italic.ttf', (150, 30, 24, 210)), 'qajar': ('IMFeENsc28P.ttf', (40, 36, 34, 200)),
    'pahlavi': ('RobotoCondensed.ttf', (40, 44, 52, 170)), 'modern': ('RobotoCondensed.ttf', (120, 220, 240, 190)),
}


@functools.lru_cache(None)
def _paper(seed, warm=(1.0, 1.0, 1.0), amp=10):
    rng = np.random.default_rng(seed)
    a = np.zeros((H, W), np.float32)
    for cells, w in ((8, 1.0), (24, .55), (90, .3), (300, .18)):
        n = rng.random((max(2, H * cells // W), cells)).astype(np.float32)
        a += np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255 * w
    a = (a - a.mean()) / (a.std() + 1e-6)
    return (a * amp)[..., None] * np.array(warm, np.float32)


@functools.lru_cache(None)
def _vignette(strength, col):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    v = np.clip((d - 0.62) / 0.75, 0, 1) ** 1.6 * strength
    return v[..., None], np.array(col, np.float32)


def _ramp(L, lo, hi, gamma=1.0):
    L = np.clip(L, 0, 1) ** gamma
    return np.array(lo, np.float32) + (np.array(hi, np.float32) - np.array(lo, np.float32)) * L[..., None]


def _edges(mask, grow=3, blur=1.0):
    m = Image.fromarray((np.clip(mask, 0, 1) * 255).astype(np.uint8))
    e = m.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(grow))
    if blur: e = e.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(e, np.float32) / 255


def _coast_bands(land, n=4, gap=9):
    """engraved water-lines parallel to the coast (Victorian survey maps)"""
    m = Image.fromarray((np.clip(land, 0, 1) * 255).astype(np.uint8)).resize((W // 2, H // 2), Image.BILINEAR)
    out = np.zeros((H // 2, W // 2), np.float32)
    for i in range(1, n + 1):
        g = np.asarray(m.filter(ImageFilter.MaxFilter(2 * (i * gap // 2) + 1)), np.float32) / 255
        e = np.asarray(Image.fromarray((g * 255).astype(np.uint8)).filter(ImageFilter.FIND_EDGES), np.float32) / 255
        out = np.maximum(out, e * (1.0 - i / (n + 1.5)))
    o = Image.fromarray((out * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
    return np.asarray(o, np.float32) / 255 * (1 - np.clip(land, 0, 1))


def graticule(fr, view, step, col, width=1, labels=False, font=None):
    """lat/lon grid for the current camera view = (lon, lat, wl, sc) where sc(lon, lat)->screen"""
    lon, lat, wl, sc = view
    if wl > 60: step *= 2
    d = ImageDraw.Draw(fr, 'RGBA')
    lon0, lon1 = lon - wl, lon + wl; lat0, lat1 = lat - wl * .7, lat + wl * .7
    g0 = math.floor(lon0 / step) * step
    x = g0
    while x <= lon1:
        pts = [sc(x, la) for la in np.linspace(lat0, lat1, 12)]
        d.line(pts, fill=col, width=width)
        if labels and font is not None:
            px, py = sc(x, lat)
            d.text((px + 6, 30), f'{abs(int(x))}°E', font=font, fill=col[:3] + (min(255, col[3] * 2),))
        x += step
    y = math.floor(lat0 / step) * step
    while y <= lat1:
        pts = [sc(lo, y) for lo in np.linspace(lon0, lon1, 12)]
        d.line(pts, fill=col, width=width)
        if labels and font is not None:
            px, py = sc(lon, y)
            d.text((30, py - 26), f'{abs(int(y))}°N', font=font, fill=col[:3] + (min(255, col[3] * 2),))
        y += step


@functools.lru_cache(None)
def frame_overlay(style):
    """static border ornament per era (RGBA 1920x1080)"""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if style == 'ancient':
        for i, a in enumerate((150, 90, 40)):
            d.rectangle([14 + i * 6, 14 + i * 6, W - 15 - i * 6, H - 15 - i * 6], outline=(70, 36, 14, a), width=3)
        # stepped (Achaemenid crenellation) frieze top & bottom
        for y0, sgn in ((22, 1), (H - 22, -1)):
            for x in range(40, W - 40, 36):
                d.polygon([(x, y0), (x + 8, y0), (x + 8, y0 + 8 * sgn), (x + 16, y0 + 8 * sgn), (x + 16, y0 + 14 * sgn), (x + 20, y0 + 14 * sgn),
                           (x + 20, y0 + 8 * sgn), (x + 28, y0 + 8 * sgn), (x + 28, y0), (x + 36, y0)], fill=(96, 50, 20, 120))
    elif style in ('medieval', 'atlas'):
        d.rectangle([12, 12, W - 13, H - 13], outline=(120, 86, 30, 150), width=4)
        d.rectangle([22, 22, W - 23, H - 23], outline=(196, 160, 70, 110), width=2)
    elif style == 'safavid':
        B = 26
        d.rectangle([0, 0, W, B], fill=(18, 40, 100, 235)); d.rectangle([0, H - B, W, H], fill=(18, 40, 100, 235))
        d.rectangle([0, 0, B, H], fill=(18, 40, 100, 235)); d.rectangle([W - B, 0, W, H], fill=(18, 40, 100, 235))
        for x in range(B, W - B, 44):  # gold arabesque buds
            for y in (B / 2, H - B / 2):
                d.ellipse([x + 14, y - 6, x + 30, y + 6], fill=(214, 172, 70, 230)); d.ellipse([x + 19, y - 3, x + 25, y + 3], fill=(40, 150, 150, 230))
        for y in range(B, H - B, 44):
            for x in (B / 2, W - B / 2):
                d.ellipse([x - 6, y + 14, x + 6, y + 30], fill=(214, 172, 70, 230)); d.ellipse([x - 3, y + 19, x + 3, y + 25], fill=(40, 150, 150, 230))
        d.rectangle([B, B, W - B, H - B], outline=(214, 172, 70, 255), width=4)
        d.rectangle([B + 7, B + 7, W - B - 7, H - B - 7], outline=(150, 40, 30, 200), width=2)
    elif style == 'qajar':
        d.rectangle([18, 18, W - 19, H - 19], outline=(30, 28, 26, 220), width=3)
        d.rectangle([28, 28, W - 29, H - 29], outline=(30, 28, 26, 160), width=1)
        for x in range(28, W - 28, 60):  # alternating scale bar ticks
            d.rectangle([x, 18, x + 30, 28], fill=(30, 28, 26, 200)); d.rectangle([x, H - 29, x + 30, H - 19], fill=(30, 28, 26, 200))
    elif style == 'pahlavi':
        d.rectangle([16, 16, W - 17, H - 17], outline=(20, 24, 30, 200), width=2)
    elif style == 'modern':
        c = (90, 220, 240, 200); L = 70
        for (x, y, sx, sy) in ((30, 30, 1, 1), (W - 30, 30, -1, 1), (30, H - 30, 1, -1), (W - 30, H - 30, -1, -1)):
            d.line([(x, y + sy * L), (x, y), (x + sx * L, y)], fill=c, width=4)
        for y in range(0, H, 3): d.line([(0, y), (W, y)], fill=(0, 0, 0, 22))
        f = F('RobotoCondensed.ttf', 22)
        d.text((48, H - 58), 'SAT // ISR // LIVE', font=f, fill=(90, 220, 240, 170))
    return im


def stylize(img, land, desert, style, view=None, t=0.0):
    """img: PIL RGB/RGBA map frame; land, desert: HxW float in [0,1]; returns PIL RGBA"""
    a = np.asarray(img.convert('RGB'), np.float32)
    L = (a[..., 0] * .30 + a[..., 1] * .55 + a[..., 2] * .15) / 255
    ld = np.clip(land, 0, 1)[..., None]; ds = (np.clip(desert, 0, 1) * np.clip(land, 0, 1))[..., None]
    if style == 'atlas':      # DEFAULT: the native coloured atlas - green/olive land, embossed coloured trees, blue sea, untouched
        out = a   # native atlas: realm tints, coloured trees, grey-white unclaimed land like the competitor
        v, c = _vignette(.45, (20, 16, 10)); out = out * (1 - v) + c * v
    elif style == 'medieval':   # aged parchment, not white: land toned warm tan/umber, relief and trees kept
        lnd = _ramp(L, (62, 50, 36), (212, 190, 148), 1.15)
        lnd = lnd * (1 - ds * .35) + np.array((220, 196, 146), np.float32) * ds * .35 * (0.65 + 0.45 * L[..., None])
        sea = a * np.array([.80, .86, .90], np.float32)
        out = lnd * ld + sea * (1 - ld) + _paper(17, (1.0, .92, .78), 7)
        v, c = _vignette(.65, (46, 32, 20)); out = out * (1 - v) + c * v
    elif style == 'ancient':
        lnd = _ramp(L, (70, 40, 22), (232, 204, 158), 1.05)
        lnd = lnd * (1 - ds * .45) + np.array((236, 208, 160), np.float32) * ds * .45 * (0.6 + 0.5 * L[..., None])
        sea = _ramp(L, (66, 78, 72), (150, 156, 136), 1.2)
        out = lnd * ld + sea * (1 - ld) + _paper(11, (1.0, .9, .7), 9)
        v, c = _vignette(.75, (60, 30, 12)); out = out * (1 - v) + c * v
    elif style == 'safavid':
        lnd = _ramp(L, (110, 62, 36), (246, 228, 190), 1.0)
        lnd = lnd * (1 - ds * .5) + np.array((240, 214, 160), np.float32) * ds * .5 * (0.6 + 0.5 * L[..., None])
        sea = _ramp(L, (12, 30, 86), (54, 92, 168), 1.4)
        e = _edges(land, 3, 1.2)[..., None]
        out = lnd * ld + sea * (1 - ld)
        out = out * (1 - e * .9) + np.array((214, 172, 70), np.float32) * e * .9          # gilded coastline
        out += _paper(23, (1.0, .95, .8), 6)
    elif style == 'qajar':
        lnd = _ramp(L, (40, 38, 34), (240, 236, 224), .85)
        lnd = lnd * (1 - ds * .25) + np.array((236, 226, 200), np.float32) * ds * .25
        sea = np.array((214, 226, 230), np.float32) * np.ones_like(a)
        out = lnd * ld + sea * (1 - ld)
        wl = _coast_bands(land)[..., None]
        out = out * (1 - wl * .55) + np.array((70, 96, 112), np.float32) * wl * .55
        e = _edges(land, 3, .8)[..., None]; out = out * (1 - e * .9) + np.array((26, 26, 28), np.float32) * e * .9
        out += _paper(37, (1, 1, .96), 5)
    elif style == 'pahlavi':
        hill = np.clip((L - .55) * 1.6, -1, 1)[..., None]
        base = np.array((204, 212, 172), np.float32) * (1 - ds) + np.array((236, 220, 172), np.float32) * ds
        lnd = base * (1.0 + .32 * hill)
        sea = np.array((168, 206, 230), np.float32) * np.ones_like(a)
        near = _edges(land, 9, 6)[..., None] * (1 - ld)
        sea = sea * (1 - near * .35) + np.array((120, 168, 206), np.float32) * near * .35
        out = lnd * ld + sea * (1 - ld)
        e = _edges(land, 3, .7)[..., None]; out = out * (1 - e * .8) + np.array((40, 80, 120), np.float32) * e * .8
    elif style == 'modern':
        lnd = _ramp(L, (12, 20, 28), (70, 88, 100), 1.15)
        lnd = lnd * (1 - ds * .35) + np.array((74, 70, 62), np.float32) * ds * .35
        sea = _ramp(L, (3, 8, 16), (10, 22, 36), 1.0)
        out = lnd * ld + sea * (1 - ld)
        g = _edges(land, 5, 4)[..., None]; e = _edges(land, 3, .6)[..., None]
        out = out + np.array((40, 170, 210), np.float32) * g * .35
        out = out * (1 - e) + np.array((110, 230, 250), np.float32) * e
        v, c = _vignette(.8, (0, 0, 0)); out = out * (1 - v) + c * v
    else:
        out = a
    fr = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).convert('RGBA')
    if view is not None:
        if style == 'qajar': graticule(fr, view, 5, (40, 40, 40, 70), 1)
        elif style == 'pahlavi': graticule(fr, view, 5, (60, 90, 120, 80), 1)
        elif style == 'modern': graticule(fr, view, 2, (50, 160, 200, 46), 1)
    return fr


def finish(fr, style):
    """frame ornament on top of everything map-side (the competitor-style 'atlas' map has none: full-bleed, no edge darkening)"""
    if style == 'atlas': return fr
    fr.alpha_composite(frame_overlay(style))
    return fr


def label(d, xy, text, style, size, anchor='mm', alpha=1.0):
    font, fill, sw, sf, up, tr = LABEL[style]
    f = F(font, size); s = text.upper() if up else text
    if tr:
        s = (' ' if tr > .12 else '\u200a').join(s) if False else s
    fill = tuple(fill[:3]) + (int(255 * alpha),); sf = tuple(sf[:3]) + (int(sf[3] * alpha),)
    d.text(xy, s, font=f, fill=fill, anchor=anchor, stroke_width=sw, stroke_fill=sf)
