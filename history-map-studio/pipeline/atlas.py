"""atlas: illustrated strategy-map renderer (History Vanguard look).
paper + relief -> stamped tree icons -> political tint -> hatching -> rivers/lakes ->
borders with inner glow -> curved territory names -> town icons + labels.
Rendered once per region at high resolution and cached as a pyramid."""
import math, os
import numpy as np
import shapefile
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, 'assets/fonts')
def F(name, size): return ImageFont.truetype(os.path.join(FD, name), int(size))


class Proj:
    def __init__(self, lon0, lon1, lat0, lat1, K, c=None):
        self.lon0, self.lon1, self.lat0, self.lat1, self.K = lon0, lon1, lat0, lat1, K
        self.c = c if c is not None else math.cos(math.radians((lat0 + lat1) / 2))
        self.w = int((lon1 - lon0) * self.c * K); self.h = int((lat1 - lat0) * K)
    def xy(self, lon, lat): return ((lon - self.lon0) * self.c * self.K, (self.lat1 - lat) * self.K)


def noise(h, w, cells_list, seed, amp_decay=0.55):
    rng = np.random.default_rng(seed); acc = np.zeros((h, w), np.float32); a = 1; tot = 0
    for cells in cells_list:
        g = rng.random((max(2, int(h / cells)), max(2, int(w / cells)))).astype(np.float32)
        acc += np.asarray(Image.fromarray(g, mode='F').resize((w, h), Image.BICUBIC), np.float32) * a
        tot += a; a *= amp_decay
    return acc / tot


def geo_noise(P, h, w, q, cells_deg, seed, amp_decay=0.55):
    """value noise fixed to the EARTH (lon/lat), so every atlas zoom level gets the same forests in the same places"""
    ys = (np.arange(h, dtype=np.float64) + .5) * q; xs = (np.arange(w, dtype=np.float64) + .5) * q
    lat = P.lat1 - ys / P.K; lonc = (P.lon0 * P.c + xs / P.K)          # lon scaled by cos(lat0): square cells on the map
    acc = np.zeros((h, w), np.float32); a = 1; tot = 0
    def hsh(i, j, o): return np.modf(np.abs(np.sin(i * 127.1 + j * 311.7 + o * 74.7 + seed * 19.3) * 43758.5453))[0]
    for o, cd in enumerate(cells_deg):
        u = lonc / cd; v = lat / cd
        i0 = np.floor(u); j0 = np.floor(v); fu = u - i0; fv = v - j0
        fu = fu * fu * (3 - 2 * fu); fv = fv * fv * (3 - 2 * fv)
        I0, J0 = np.meshgrid(i0, j0); FU, FV = np.meshgrid(fu, fv)
        n = (hsh(I0, J0, o) * (1 - FU) + hsh(I0 + 1, J0, o) * FU) * (1 - FV) + (hsh(I0, J0 + 1, o) * (1 - FU) + hsh(I0 + 1, J0 + 1, o) * FU) * FV
        acc += n.astype(np.float32) * a; tot += a; a *= amp_decay
    return (acc / tot - .483) * (.171 / .133) + .578      # same spread as the old pixel noise, so forest_thr keeps its meaning


def catmull(pts, n=20):
    if len(pts) < 3: return list(pts)
    p = [pts[0]] + list(pts) + [pts[-1]]; out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for j in range(n):
            t = j / n; t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[c]) + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2 + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in (0, 1)))
    out.append(pts[-1]); return out


def meander(pts, amp=0.010):
    sm = catmull(pts, 40); out = []; acc = 0
    for i, p in enumerate(sm):
        q = sm[min(i + 1, len(sm) - 1)]; o = sm[max(i - 1, 0)]
        an = math.atan2(q[1] - o[1], q[0] - o[0]); acc += math.dist(p, o)
        m = amp * math.sin(acc * 24) + amp * 0.4 * math.sin(acc * 61 + 1)
        out.append((p[0] - m * math.sin(an), p[1] + m * math.cos(an)))
    return out


def rough(poly, step=0.03, amp=0.07):
    """densify polygon and displace by a position-based smooth field, so shared edges stay shared"""
    pts = list(poly) + [poly[0]]; out = []
    def f(x, y, s):
        return (math.sin(x * 3.1 * s + y * 1.7) + 0.6 * math.sin(x * 7.3 * s - y * 5.9 * s + 1.3) + 0.3 * math.sin(x * 17.0 - y * 13.0 * s))
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        n = max(1, int(math.dist((x0, y0), (x1, y1)) / step))
        for i in range(n):
            x, y = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n
            out.append((x + amp * f(x, y, 1.0) * 0.5, y + amp * f(y, x, 1.13) * 0.35))
    return out


# ------------------------------------------------------------------ sprites
def tree_sprites(S, n=14):
    """embossed, leaf-textured tree clusters (grey; tinted later). Height-field shaded like a relief."""
    out = []; rng = np.random.default_rng(11); Z = 3; s = int(S * Z); size = int(s * 1.7)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    leaf = rng.random((size // 4 + 1, size // 4 + 1)).astype(np.float32)
    leaf = np.asarray(Image.fromarray(leaf, 'F').resize((size, size), Image.BICUBIC))
    leaf2 = rng.random((size // 2 + 1, size // 2 + 1)).astype(np.float32)
    leaf2 = np.asarray(Image.fromarray(leaf2, 'F').resize((size, size), Image.BILINEAR))
    for v in range(n):
        cx, cy = size * 0.48, size * 0.46
        hgt = np.zeros((size, size), np.float32)
        nb = rng.integers(5, 10) if v < n - 3 else 1
        conifer = v >= n - 3
        if conifer:
            for k in range(4):
                ty = cy - s * 0.5 + k * s * 0.24; w = s * (0.14 + k * 0.08)
                inside = (yy > ty) & (yy < ty + s * 0.34)
                frac = (yy - ty) / (s * 0.34)
                half = w * frac + 1e-3
                d = np.abs(xx - cx) / half
                hgt = np.maximum(hgt, np.where(inside & (d < 1), (1 - d) * s * 0.25 * (0.6 + 0.4 * frac), 0))
        else:
            for k in range(nb):
                bx = cx + rng.uniform(-.24, .24) * s; by = cy + rng.uniform(-.22, .14) * s
                r = rng.uniform(.15, .23) * s
                d2 = (xx - bx) ** 2 + (yy - by) ** 2
                hgt = np.maximum(hgt, np.sqrt(np.clip(r * r - d2, 0, None)))
        mask = hgt > 0
        hgt = hgt + mask * (leaf * s * 0.09 + leaf2 * s * 0.04)
        gy, gx = np.gradient(hgt)
        nx, ny, nz = -gx, -gy, np.ones_like(gx) * 1.4
        ln = np.sqrt(nx * nx + ny * ny + nz * nz)
        L = np.array([-0.55, -0.65, 0.52]); L /= np.linalg.norm(L)
        lam = np.clip((nx * L[0] + ny * L[1] + nz * L[2]) / ln, 0, 1)
        shade = 0.22 + 1.05 * lam ** 1.7
        # ambient occlusion toward the rim and bottom
        ao = np.clip(hgt / (s * 0.18), 0, 1) ** 0.35
        g = np.clip(255 * shade * (0.55 + 0.45 * ao) * 0.82, 0, 255)
        m = Image.fromarray((mask * 255).astype(np.uint8))
        rim = np.asarray(m.filter(ImageFilter.MaxFilter(Z * 2 + 1)), np.float32) / 255
        shadow = np.asarray(m.filter(ImageFilter.GaussianBlur(Z * 2.5)), np.float32) / 255
        sh = np.zeros_like(shadow); o = int(s * 0.10); sh[o:, o:] = shadow[:-o, :-o]
        if not conifer or True:
            trunk = (np.abs(xx - cx) < s * .035) & (yy > cy + s * .05) & (yy < cy + s * .45) & ~mask
        rgb = np.zeros((size, size, 3), np.float32); a = np.zeros((size, size), np.float32)
        a = np.maximum(a, sh * 0.55); rgb[:] = 0
        tr = trunk.astype(np.float32); rgb = rgb * (1 - tr[..., None]) + np.array([60, 52, 46]) * tr[..., None]; a = np.maximum(a, tr)
        rimo = np.clip(rim - mask, 0, 1); rgb = rgb * (1 - rimo[..., None]) + 40 * rimo[..., None]; a = np.maximum(a, rimo * 0.95)
        mk = mask.astype(np.float32); rgb = rgb * (1 - mk[..., None]) + g[..., None] * mk[..., None]; a = np.maximum(a, mk)
        im = Image.fromarray(np.dstack([rgb, a * 255]).clip(0, 255).astype(np.uint8), 'RGBA')
        out.append(im.resize((size // Z, size // Z), Image.LANCZOS))
    return out


def ridged(h, w, seed, ns=1.0):
    n = noise(h, w, [max(6, int(c * ns)) for c in (900, 320, 120, 45)], seed, 0.6)
    return 1 - np.abs(n - 0.5) * 2


def cog_icon(r, Z=4):
    s = int(r * 2.8 * Z); im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = s / 2; R = r * Z
    pts = []
    for i in range(36):
        a = i / 36 * 2 * math.pi; rr = R * (1.0 if (i // 2) % 2 == 0 else 0.74)
        pts.append((c + rr * math.cos(a), c + rr * math.sin(a)))
    d.polygon([(x + Z * 3, y + Z * 3) for x, y in pts], fill=(0, 0, 0, 120))
    d.polygon(pts, fill=(52, 40, 34, 255))
    for k in range(12):  # bevelled bronze body
        f = k / 11; rr = R * (0.86 - f * 0.5); col = (int(120 + 90 * f), int(92 + 70 * f), int(66 + 40 * f))
        d.ellipse([c - rr - R * .08 * f, c - rr - R * .08 * f, c + rr - R * .08 * f, c + rr - R * .08 * f], fill=col)
    rr = R * 0.24; d.ellipse([c - rr, c - rr, c + rr, c + rr], fill=(50, 38, 30, 255))
    return im.resize((s // Z, s // Z), Image.LANCZOS)


def star_icon(r, Z=4):
    s = int(r * 2.4 * Z); im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = s / 2
    pts = [(c + (r * Z if i % 2 == 0 else r * Z * .45) * math.cos(-math.pi / 2 + i * math.pi / 5), c + (r * Z if i % 2 == 0 else r * Z * .45) * math.sin(-math.pi / 2 + i * math.pi / 5)) for i in range(10)]
    d.polygon(pts, fill=(250, 214, 60, 255), outline=(90, 60, 10, 255), width=Z * 2)
    return im.resize((s // Z, s // Z), Image.LANCZOS)


# ------------------------------------------------------------------ text on an arc
def arc_text(layer, center, text, font, radius, tilt_deg, fill, shadow=(40, 20, 20, 90)):
    """draw text glyph-by-glyph along a circular arc; radius>0 bulges upward"""
    widths = [font.getlength(ch) + font.size * 0.07 for ch in text]; total = sum(widths)
    cx, cy = center; tilt = math.radians(tilt_deg); acc = 0
    asc = font.getbbox('Hg')[3]
    for ch, w in zip(text, widths):
        mid = acc + w / 2 - total / 2; acc += w
        if ch == ' ': continue
        a = mid / radius
        px, py = radius * math.sin(a), -radius * (1 - math.cos(a))
        x = cx + px * math.cos(tilt) - py * math.sin(tilt); y = cy + px * math.sin(tilt) + py * math.cos(tilt)
        g = Image.new('RGBA', (int(w + asc * 2), int(asc * 2.4)), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
        gc = (g.width / 2, g.height / 2)
        gd.text((gc[0] + 4, gc[1] + 5), ch, font=font, fill=shadow, anchor='mm')
        gd.text(gc, ch, font=font, fill=fill, anchor='mm')
        g = g.rotate(-math.degrees(a + tilt), resample=Image.BICUBIC, expand=True)
        layer.alpha_composite(g, (int(x - g.width / 2), int(y - g.height / 2)))


# ------------------------------------------------------------------ build
def build(P, cfg, cache, tactical=False):
    if os.path.exists(cache + '_0.png'):
        return [Image.open(f'{cache}_{i}.png').convert('RGB') for i in range(3)]
    h, w, K = P.h, P.w, P.K
    NS = cfg.get('nsc', 1.0)
    def NC(cells): return [max(4, int(c * NS)) for c in cells]
    sc = K / 1300.0
    lsc = cfg.get('lsc', sc); tsc = cfg.get('tsc', sc); rsc = cfg.get('rsc', sc); rrank = cfg.get('river_rank', 99)
    print('atlas: paper', w, h, flush=True)
    paper = np.array([238, 229, 210], np.float32) if not tactical else np.array([228, 230, 232], np.float32)
    n1 = noise(h, w, NC([1800, 700, 260, 90]), 3); n2 = np.asarray(Image.fromarray((np.random.default_rng(5).random((h // 2, w // 2)) * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR), np.float32) / 255
    rel = noise(h, w, NC([1300, 520, 200]), 8) * 260 + ridged(h, w, 12, NS) * 120 + noise(h, w, NC([40, 14]), 13, .7) * 9
    gy, gx = np.gradient(rel); del rel
    shade = np.clip(0.5 + (-gx - gy) * 0.55, 0, 1)
    rs = cfg.get('relief', 0.24); img = paper * (0.93 + 0.08 * n1[..., None]) * (1.0 - rs * 0.58 + rs * shade[..., None])
    img += (n2[..., None] - 0.5) * 7
    del n2, gx, gy, shade
    base = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA'); del img, n1

    land = None
    if cfg.get('land'):
        lm = Image.new('L', (w, h), 0); lmd = ImageDraw.Draw(lm)
        for shp in shapefile.Reader(os.path.join(HERE, 'assets/geo/ne_10m_land')).shapes():
            bb = shp.bbox
            if bb[2] < P.lon0 - 1 or bb[0] > P.lon1 + 1 or bb[3] < P.lat0 - 1 or bb[1] > P.lat1 + 1: continue
            pts = shp.points; parts = list(shp.parts) + [len(pts)]
            for a, b in zip(parts[:-1], parts[1:]):
                ring = pts[a:b]
                if len(ring) > 2:
                    ar = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]))
                    lmd.polygon([P.xy(*p) for p in ring], fill=0 if ar > 0 else 255)   # ccw ring = hole (e.g. the Caspian)
        for lon, lat, rx, ry in cfg.get('seas', []):  # inland seas not in land layer are already holes
            pass
        land = np.asarray(lm) > 127
        lm.resize((w // 2, h // 2), Image.BILINEAR).save(cache + '_land.png'); del lm, lmd
    # river geometry (needed for tree clearing)
    rivers = []
    r = shapefile.Reader(os.path.join(HERE, 'assets/geo/ne_10m_rivers_lake_centerlines'))
    for srec in r.iterShapeRecords():
        if 'Canal' in srec.record['featurecla']: continue
        if (srec.record['scalerank'] or 99) > rrank: continue
        bb = srec.shape.bbox
        if bb[2] < P.lon0 or bb[0] > P.lon1 or bb[3] < P.lat0 or bb[1] > P.lat1: continue
        nm = srec.record['name'] or ''
        wd = {'Volga': 9, 'Oka': 8, 'Nile': 9, 'Euphrates': 8, 'Tigris': 8, 'Indus': 9, 'Amu Darya': 8}.get(nm, 5)
        pts = srec.shape.points; parts = list(srec.shape.parts) + [len(pts)]
        for a, b in zip(parts[:-1], parts[1:]): rivers.append(([P.xy(*p) for p in catmull(pts[a:b], 3)], wd))
    for pts, wd in cfg['hand_rivers']: rivers.append(([P.xy(*p) for p in meander(pts)], wd))
    lakes = []
    lk = shapefile.Reader(os.path.join(HERE, 'assets/geo/ne_10m_lakes'))
    for srec in lk.iterShapeRecords():
        if srec.record['featurecla'] != 'Lake': continue
        if (srec.record['scalerank'] or 99) > cfg.get('lake_rank', 99): continue
        bb = srec.shape.bbox
        if bb[2] < P.lon0 or bb[0] > P.lon1 or bb[3] < P.lat0 or bb[1] > P.lat1: continue
        pts = srec.shape.points; parts = list(srec.shape.parts) + [len(pts)]
        lakes.append([P.xy(*p) for p in pts[parts[0]:parts[1]]])
    for lon, lat, rx, ry in cfg['lakes']:
        lakes.append([P.xy(lon + rx * math.cos(a) * (1 + .12 * math.sin(3 * a)), lat + ry * math.sin(a)) for a in np.linspace(0, 6.283, 60)])

    # clearing mask (rivers, lakes, towns)
    print('atlas: trees', flush=True)
    q = 4; clear = Image.new('L', (w // q, h // q), 0); cd = ImageDraw.Draw(clear)
    for pts, wd in rivers: cd.line([(x / q, y / q) for x, y in pts], fill=255, width=int(max(3, wd * 7 * rsc / q)))
    for pl in lakes: cd.polygon([(x / q, y / q) for x, y in pl], fill=255)
    for name, (lon, lat), *_ in cfg['towns']:
        x, y = P.xy(lon, lat); rr = 70 * lsc / q; cd.ellipse([x / q - rr, y / q - rr, x / q + rr, y / q + rr], fill=255)
    for poly in cfg.get('clear_polys', []): cd.polygon([tuple(v / q for v in P.xy(*p)) for p in poly], fill=255)   # deserts: no trees
    clear = np.asarray(clear.filter(ImageFilter.GaussianBlur(6)), np.float32) / 255
    fnoise = geo_noise(P, h // q, w // q, q, cfg.get('forest_cells', (1.5, 0.6, 0.21)), 7)   # same forests at every zoom
    fmask = (fnoise - cfg.get('forest_thr', 0.27)) * 10 - clear * 6.0
    for lon, lat, rad in cfg.get('forest_boost', []):
        x0, y0 = P.xy(lon, lat); yy, xx = np.mgrid[0:h // q, 0:w // q]
        fmask += cfg.get('boost_amp', 2.0) * np.exp(-(((xx * q - x0) ** 2 + (yy * q - y0) ** 2) / (rad * P.c * K) ** 2)); del xx, yy
    fmask = np.maximum(fmask, cfg.get('forest_floor', 0.025))
    if land is not None:
        lq = np.asarray(Image.fromarray((land * 255).astype(np.uint8)).resize((w // q, h // q), Image.BILINEAR), np.float32) / 255
        fmask = np.where(lq > .9, fmask, -1)
    S = int(58 * tsc); spr = tree_sprites(S); step = int(S * 0.52)
    rng = np.random.default_rng(21)
    ys = np.arange(0, h, step); xs = np.arange(0, w, step)
    trees = []
    for y in ys:
        for x in xs:
            jx, jy = x + rng.uniform(-.45, .45) * step, y + rng.uniform(-.45, .45) * step
            ix, iy = int(min(w // q - 1, max(0, jx / q))), int(min(h // q - 1, max(0, jy / q)))
            if fmask[iy, ix] > rng.random(): trees.append((jy, jx, rng.integers(0, 14 if fnoise[iy, ix] > .55 else 11)))
    trees.sort()
    ink = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for y, x, v in trees:
        t = spr[v]; ink.alpha_composite(t, (int(x - t.width * .48), int(y - t.height * .55)))
    print('atlas: trees placed', len(trees), flush=True)

    # political tint (multiply)
    print('atlas: territories', flush=True)
    idm = Image.new('L', (w, h), 0); idd = ImageDraw.Draw(idm)
    for k, terr in enumerate(cfg['territories'], 1):
        idd.polygon([P.xy(*p) for p in rough(terr['poly'])], fill=k)
    ida = np.asarray(idm)
    lut = np.ones((256, 3), np.float32)
    for k, terr in enumerate(cfg['territories'], 1): lut[k] = np.array(terr['tint'], np.float32) / 255
    if tactical: lut[:] = 1.0
    if land is not None: ida = np.where(land, ida, 0).astype(np.uint8)
    base_np = np.asarray(base.convert('RGB')); del base
    ink_np = np.asarray(ink); del ink
    rgb = np.empty((h, w, 3), np.float32)
    seab = None
    if land is not None and cfg.get('flat_sea'):
        sm = Image.fromarray(base_np[..., :3]).resize((max(1, w // 8), max(1, h // 8)), Image.BILINEAR).filter(ImageFilter.GaussianBlur(6)).resize((w, h), Image.BILINEAR)
        seab = np.asarray(sm); del sm
    for y0 in range(0, h, 512):  # strip-wise to keep memory low
        y1 = min(h, y0 + 512)
        tint = lut[ida[y0:y1]]
        g = base_np[y0:y1].astype(np.float32) * (0.18 + 0.82 * tint) * 0.97
        ia = ink_np[y0:y1, :, 3:4].astype(np.float32) / 255
        tr = ink_np[y0:y1, :, :3].astype(np.float32) * tint ** 1.9 * 1.25
        rgb[y0:y1] = g * (1 - ia) + tr * ia
        if land is not None:
            sea = ~land[y0:y1]
            src = (seab[y0:y1] if seab is not None else base_np[y0:y1, :, :3])
            rgb[y0:y1][sea] = src[sea].astype(np.float32) * np.array(cfg.get('sea', (0.60, 0.70, 0.76)), np.float32)
    del base_np, ink_np, tint, g, ia, tr
    # hatching
    hk = [k for k, terr in enumerate(cfg['territories'], 1) if terr.get('hatch')]
    for y0 in range(0, h, 512):
        y1 = min(h, y0 + 512); yy, xx = np.mgrid[y0:y1, 0:w]
        hm = (((xx + yy) // int(26 * lsc)) % 2 == 0) & np.isin(ida[y0:y1], hk)
        sub = rgb[y0:y1]; sub[hm] = sub[hm] * 0.55 + np.array([235, 238, 245]) * 0.45
    del yy, xx, hm
    # borders: edge of id raster -> dark line + inner shade
    e = np.zeros((h, w), bool)
    e[:-1] |= ida[:-1] != ida[1:]; e[:, :-1] |= ida[:, :-1] != ida[:, 1:]
    em = Image.fromarray((e * 255).astype(np.uint8)); del e
    glow = np.asarray(em.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(int(22 * lsc))))
    line = np.asarray(em.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.2)))
    for y0 in range(0, h, 512):
        y1 = min(h, y0 + 512)
        gl = np.clip(glow[y0:y1].astype(np.float32) / 255 * 3.0, 0, 1)[..., None]
        ln = line[y0:y1].astype(np.float32)[..., None] / 255 * 0.75
        if cfg.get('soft_borders'):   # competitor look: no ink line, no black fade; each realm just deepens its own colour a touch at its edge
            rgb[y0:y1] = rgb[y0:y1] * (1 - 0.12 * gl)
        else:
            rgb[y0:y1] = rgb[y0:y1] * (1 - 0.45 * gl) * (1 - ln) + np.array([60, 30, 34]) * ln
    del glow, line, ida
    if land is not None:
        print('atlas: coast', flush=True)
        lmI = Image.fromarray((land * 255).astype(np.uint8))
        ed = np.asarray(lmI.filter(ImageFilter.FIND_EDGES))
        edI = Image.fromarray(ed).filter(ImageFilter.MaxFilter(3))
        cl = np.asarray(edI.filter(ImageFilter.GaussianBlur(1.0)), np.float32) / 255
        halo = np.asarray(edI.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(int(26 * lsc))), np.float32) / 255
        for y0 in range(0, h, 512):
            y1 = min(h, y0 + 512); sea = (~land[y0:y1])[..., None]
            hl = np.clip(halo[y0:y1] * 2.2, 0, 1)[..., None]; c_ = np.clip(cl[y0:y1] * 1.6, 0, 1)[..., None]
            rgb[y0:y1] = rgb[y0:y1] * (1 - 0.30 * hl * sea) + np.array([238, 244, 246]) * 0.30 * hl * sea
            rgb[y0:y1] = rgb[y0:y1] * (1 - c_) + np.array([46, 52, 58]) * c_
        del cl, halo, ed, edI, lmI
    np.clip(rgb, 0, 255, out=rgb); base = Image.fromarray(rgb.astype(np.uint8)).convert('RGBA'); del rgb

    # rivers & lakes on top
    print('atlas: water', flush=True)
    d = ImageDraw.Draw(base)
    for pts, wd in rivers: d.line(pts, fill=(205, 214, 220, 255), width=int(wd * 2.4 * rsc), joint='curve')
    for pl in lakes: d.polygon(pl, fill=(70, 85, 100, 255))
    for pts, wd in rivers: d.line(pts, fill=(78, 96, 116, 255), width=int(wd * 1.25 * rsc), joint='curve')
    for pl in lakes: d.polygon([(x, y) for x, y in pl], fill=(176, 196, 208, 255))

    # labels
    print('atlas: labels', flush=True)
    lab = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for terr in cfg['territories']:
        for txt, (lon, lat), size, radius, tilt in terr.get('labels', []):
            arc_text(lab, P.xy(lon, lat), txt, F('IMFeENrm28P.ttf', size * lsc), radius * lsc, tilt, (250, 246, 244, 200), shadow=(30, 15, 20, 120))
    for txt, (lon, lat), size, radius, tilt in cfg.get('river_labels', []):
        arc_text(lab, P.xy(lon, lat), txt, F('IMFeENit28P.ttf', size * lsc), radius * lsc, tilt, (52, 78, 104, 235), shadow=(240, 236, 226, 160))
    base.alpha_composite(lab); del lab
    cog = cog_icon(29 * lsc); star = star_icon(29 * lsc)
    sh = Image.new('RGBA', (w, h), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    tx = Image.new('RGBA', (w, h), (0, 0, 0, 0)); td = ImageDraw.Draw(tx)
    stars = []
    for name, (lon, lat), kind, side, *sub in (cfg['towns'] if cfg.get('draw_towns', True) else []):
        x, y = P.xy(lon, lat)
        base.alpha_composite(cog, (int(x - cog.width / 2), int(y - cog.height / 2)))
        fnt = F('Almendra-Regular.ttf', (92 if kind == 'cap' else 84) * lsc); fs = F('Almendra-Regular.ttf', 52 * lsc)
        off = 50 * lsc
        anchor, pos = {'r': ('lm', (x + off, y)), 'l': ('rm', (x - off, y)), 'u': ('mb', (x, y - off)), 'd': ('mt', (x, y + off))}[side]
        for dx, dy in ((4, 5),):
            sd.text((pos[0] + dx * lsc, pos[1] + dy * lsc), name, font=fnt, fill=(10, 6, 6, 230), anchor=anchor)
        td.text(pos, name, font=fnt, fill=(250, 246, 238, 255), anchor=anchor, stroke_width=max(1, int(1.5 * lsc)), stroke_fill=(40, 26, 22, 200))
        bb = td.textbbox(pos, name, font=fnt, anchor=anchor)
        if sub:
            sp = ((bb[0] + bb[2]) / 2, bb[3] + 4 * lsc)
            sd.text((sp[0] + 3 * lsc, sp[1] + 4 * lsc), sub[0], font=fs, fill=(10, 6, 6, 220), anchor='mt')
            td.text(sp, sub[0], font=fs, fill=(240, 234, 224, 255), anchor='mt')
        if kind == 'cap':
            sx = bb[2] + 10 * lsc if side != 'l' else bb[0] - star.width - 10 * lsc
            stars.append((int(sx), int((bb[1] + bb[3]) / 2 - star.height / 2)))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(4 * lsc))); del sh
    base.alpha_composite(tx); del tx
    for p in stars: base.alpha_composite(star, p)
    base = base.convert('RGB')
    pyr = [base, base.resize((w // 2, h // 2), Image.LANCZOS), base.resize((w // 4, h // 4), Image.LANCZOS)]
    for i, im in enumerate(pyr): im.save(f'{cache}_{i}.png')
    print('atlas: done', flush=True)
    return pyr
