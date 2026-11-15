import collections
"""STORYBOARD ENGINE - write an episode as DATA, get the full History-Vanguard look.

An episode is episodes/<slug>.py containing only lists/dicts (see templates/story_template.py and episodes/demo_chaldiran.py),
ending with:      import story; story.compile(globals())

Times are CUES tied to the narration (build/<slug>/words.json from voice.py), never hand-typed seconds:
    'Then came Darius'            start of the first occurrence of that phrase
    'Then came Darius>'           end of the phrase
    'Then came Darius +0.5'       offset in seconds (space before the sign)
    'crowned Shah @ Chapter nine' first occurrence AFTER the anchor phrase
    'ch:3'  'end'  'vend'  12.5   chapter 3 start, video end, voice end, raw seconds
Places are NAMES (places.py gazetteer) or (lon, lat). Shapes are coordinate lists, 'ISO:IRN' country codes,
{'hull': [places], 'pad': 1.5} or {'circle': place, 'r': 3}.
"""
import hashlib, json, math, os, re, sys, difflib, importlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
ROOT = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ROOT)
import kit
from kit import *  # noqa
from kit import path_at, KC
import atlas, styles as ST, tactical as TAC, places as PL, world, tac_auto
import transitions as TR

W_ = 1920
KC['safavid'] = (40, 120, 112)   # teal: must read apart from Ottoman red on the same map
STYLE_NAMES = ST.STYLES
# Respect rule (user, 2026-11-14): ONLY the Prophet and the Sahaba (his Companions, 7th century CE) appear as noor light.
# Everyone later (Umayyads, Abbasids, sultans, shahs, ayatollahs ...) is shown normally with a real period image.
SAHABA = ['prophet muhammad', 'the prophet', 'abu bakr', 'umar ibn al-khattab', 'umar ibn al khattab', 'uthman ibn affan', 'ali ibn abi talib',
          'hasan ibn ali', 'husayn ibn ali', 'hussain ibn ali', 'fatima', 'aisha', 'khadija', 'khalid ibn al-walid', 'khalid ibn walid',
          "sa'd ibn abi waqqas", 'saad ibn abi waqqas', 'abu ubayda', 'amr ibn al-as', "amr ibn al-'as", "mu'awiya", 'muawiya', 'bilal',
          'zubayr', 'talha', 'abd al-rahman ibn awf', 'abu hurayra', 'salman al-farsi', 'abbas ibn abd al-muttalib', 'hamza', 'sahaba',
          'companion of the prophet', 'rashidun']

def is_religious(name, title=''):
    """True only for the Prophet and the Sahaba. Set noor=True on a PEOPLE entry for any other Companion this list misses,
    or noor=False to override a false match."""
    s = f'{name} {title}'.lower().replace('’', "'")
    if re.fullmatch(r'\s*(the )?(prophet )?muhammad( ibn abdullah)?\s*', name.lower()): return True
    return any(k in s for k in SAHABA)


class StoryError(Exception): pass


def _n(s): return re.sub(r"[^\w]", '', s).lower()


class Ctx:
    def __init__(self, slug, check=False):
        self.slug, self.check = slug, check
        self.bdir = os.path.join(ROOT, 'build', slug)
        wf = os.path.join(self.bdir, 'words.json')
        if not os.path.exists(wf): raise StoryError(f'no narration timing yet: run  python voice.py episodes/{slug}.json')
        self.WD = json.load(open(wf)); self.WS = [_n(w['w']) for w in self.WD['words']]
        self.END, self.VEND = self.WD['total'], self.WD['voice_end']; self.errors = []; self.chapters = []
    # ---------------- cues
    def idx(self, ph, after=0):
        toks = [_n(x) for x in ph.split() if _n(x)]
        for i in range(after, len(self.WS) - len(toks) + 1):
            if self.WS[i:i + len(toks)] == toks: return i
        raise KeyError(ph)
    def t(self, cue, default=None):
        if cue is None:
            if default is None: raise StoryError('missing cue')
            return default
        if isinstance(cue, (int, float)): return float(cue)
        c = cue.strip(); off = 0.0
        m = re.search(r'\s([+-]\d+(?:\.\d+)?)$', c)
        if m: off = float(m.group(1)); c = c[:m.start()].strip()
        if c in ('end',): return self.END + off
        if c in ('vend', 'voice end'): return self.VEND + off
        if c in ('start', '0'): return 0.0 + off
        if c.startswith('ch:'):
            k = int(c[3:]) - 1
            if k >= len(self.chapters): self.errors.append(f'cue {cue!r}: only {len(self.chapters)} chapters'); return 0.0
            return self.chapters[k] + off
        anchor = 0
        if '@' in c:
            c, a = [x.strip() for x in c.split('@', 1)]
            try: anchor = self.idx(a)
            except KeyError: self.errors.append(f'anchor phrase not in narration: {a!r}  {self._sug(a)}'); return 0.0
        end = c.endswith('>'); c = c.rstrip('>').strip()
        try: i = self.idx(c, anchor)
        except KeyError:
            self.errors.append(f'cue phrase not in narration: {c!r}  {self._sug(c)}'); return 0.0
        if end: return self.WD['words'][i + len([x for x in c.split() if _n(x)]) - 1]['t1'] + off
        return self.WD['words'][i]['t0'] + off
    def _sug(self, ph):
        n = len(ph.split()); grams = [' '.join(w['w'] for w in self.WD['words'][i:i + n]) for i in range(len(self.WS) - n + 1)]
        s = difflib.get_close_matches(ph, grams, n=2, cutoff=.5)
        return f'-> did you mean {s}' if s else ''


_LRU = collections.OrderedDict()
def _lru_get(key, loader, cap=int(os.environ.get('ATLAS_LRU', 10))):
    if key in _LRU: _LRU.move_to_end(key); return _LRU[key]
    v = loader(); _LRU[key] = v
    while len(_LRU) > cap: _LRU.popitem(last=False)
    return v
class LazyPyr:
    def __init__(self, cache): self.c = cache
    def __getitem__(self, i): return _lru_get((self.c, i), lambda: Image.open(f'{self.c}_{i}.png').convert('RGB'))
    def __len__(self): return 3
class LazyImg:
    def __init__(self, path): self.p = path
    def __getattr__(self, a): return getattr(_lru_get(self.p, lambda: Image.open(self.p).convert('L')), a)


def compile(g):
    """g = the episode module's globals(). Injects END, FPS, render, HITS, SFX."""
    slug = g.get('SLUG') or os.path.splitext(os.path.basename(g['__file__']))[0]
    check = os.environ.get('STORY_CHECK') == '1'
    X = Ctx(slug, check); T = X.t
    FPS = g.get('FPS', 24); PLACES = g.get('PLACES', {})
    for k, v in g.get('KINDS', {}).items(): KC[k] = tuple(v)
    def P(p):
        try: return PL.lookup(p, PLACES)
        except KeyError:
            X.errors.append(f'unknown place {p!r}: add it to PLACES as (lon, lat). close names: {PL.suggest(str(p))}'); return (0.0, 0.0)
    def kind_ok(k, where):
        if k not in KC: X.errors.append(f'{where}: unknown kind {k!r}; use one of {sorted(KC)} or define KINDS = {{"{k}": (r, g, b)}}')
        return k if k in KC else 'roman'
    def shape(s, where='shape'):
        if isinstance(s, str): s = [s]
        if isinstance(s, dict):
            from shapely.geometry import MultiPoint, Point
            if 'hull' in s:
                pts = [P(p) for p in s['hull']]; hull = MultiPoint(pts).convex_hull.buffer(s.get('pad', 1.5), join_style=1)
                return [list(hull.exterior.coords)]
            if 'circle' in s:
                c = P(s['circle']); return [list(Point(c).buffer(s.get('r', 3)).exterior.coords)]
            X.errors.append(f'{where}: bad shape dict {s}'); return []
        if all(isinstance(x, str) and x.upper().startswith('ISO:') for x in s):
            out = []
            for x in s:
                try: out += PL.country_polys(x[4:])
                except KeyError as e: X.errors.append(f'{where}: {e}')
            return out
        return [[P(p) for p in s]]

    # ---------------- chapters & styles
    CH = g.get('CHAPTERS', [])
    X.chapters = [T(c[0]) for c in CH]
    STY = [(0.0, g.get('STYLE', 'atlas'))] + [(T(c[0]), c[2]) for c in CH if len(c) > 2 and c[2]] + [(T(c), s) for c, s in g.get('STYLES', [])]
    STY.sort(key=lambda x: x[0])
    for _, s in STY:
        if s not in STYLE_NAMES: X.errors.append(f'unknown style {s!r}; use {STYLE_NAMES}')
    XS = 1.6
    def style_at(t):
        a = STY[0][1]
        for i, (t0, s) in enumerate(STY):
            if t >= t0 + XS: a = s
            elif t >= t0: return (STY[i - 1][1] if i else s), s, smooth(prog(t, t0, t0 + XS))
        return a, a, 1.0
    def sty(t): A, B, f = style_at(t); return B if f >= .5 else A

    # ---------------- camera & region
    raw = []
    for k in g.get('CAMERA', []):
        lon, lat = P(k[1]); raw.append((T(k[0]), lon, lat, float(k[2])) + ((k[3],) if len(k) > 3 and k[3] in ('cut', 'wipe') else ()))
    if not raw: X.errors.append('CAMERA is empty: give at least one (cue, place, width_deg) key'); raw = [(0.0, 0.0, 0.0, 40.0)]
    raw.sort(key=lambda k: k[0])
    for a, b in zip(raw, raw[1:]):
        if len(b) > 4: continue
        if math.hypot(b[1] - a[1], b[2] - a[2]) > max(a[3], b[3]) * .9 and b[0] - a[0] < 2.5:
            X.errors.append(f'camera jump at {b[0]:.1f}s ({math.hypot(b[1]-a[1], b[2]-a[2]):.0f} deg in {b[0]-a[0]:.1f}s) is a whip pan: add "cut"')
    if 'BOUNDS' in g: B = tuple(g['BOUNDS'])
    else:
        xs = [k[1] for k in raw]; ys = [k[2] for k in raw]; wmax = max(k[3] for k in raw)
        c0 = math.cos(math.radians(sum(ys) / len(ys)))
        hl = wmax / 2 + 1.5; hv = hl * 1080 / 1920 / c0 + 1.5
        B = (max(-180, min(xs) - hl), min(180, max(xs) + hl), max(-75, min(ys) - hv), min(80, max(ys) + hv))
    R = world.auto_region(B, [(k[1], k[2], k[3]) for k in raw], max_details=g.get('MAX_DETAILS', 8), crisp=g.get('DETAIL_CRISP', 1.5), merge=g.get('DETAIL_MERGE', (9000, 7000)), label_k=g.get('DETAIL_LABEL_K'))
    def L(lst): return lst or []
    MAPD = g.get('MAP') or {}
    terr = []
    for r in MAPD.get('realms', []):
        polys = shape(r['shape'], f"map realm {r.get('name')}") if 'shape' in r else [q for x in r['shapes'] for q in shape(x, f"map realm {r.get('name')}")]
        tint = tuple(r['tint']) if r.get('tint') else soft_tint(KC[kind_ok(r.get('kind', 'roman'), 'map realm')])
        labs = []
        for lb in r.get('labels', [None]):
            if lb is None:
                from shapely.geometry import Polygon
                pg = max((Polygon(p) for p in polys if len(p) > 2), key=lambda p: p.area); c = pg.representative_point()
                span = (pg.bounds[2] - pg.bounds[0]) * R['C0'] * R['K'] / R['CFG']['lsc']
                nm = r['name']; size = int(clamp(span * 1.15 / max(4, len(nm)), 120, 420))
                labs.append((nm, (c.x, c.y), size, size * 9, r.get('tilt', -14)))
            else: labs.append((lb[0], P(lb[1]), lb[2], lb[3] if len(lb) > 3 else lb[2] * 9, lb[4] if len(lb) > 4 else -14))
        for poly in polys: terr.append(dict(name=r['name'], tint=tint, poly=poly, hatch=r.get('hatch', False), labels=labs if poly is polys[0] else []))
    towns = []
    for tw in MAPD.get('towns', []):
        tw = (tw,) if isinstance(tw, str) else tuple(tw)
        nm = tw[0]; kind = tw[1] if len(tw) > 1 else 'town'; side = tw[2] if len(tw) > 2 else 'r'
        towns.append((nm, P(nm), kind, side) + tuple(tw[3:4]))
    R['CFG']['territories'] = terr; R['CFG']['towns'] = towns; R['CFG']['draw_towns'] = False; R['CFG']['soft_borders'] = True
    TOWNS = towns
    # a white ring turns on a city whenever the narrator names it
    RINGS = []
    wn = [_n(w['w']) for w in X.WD['words']]
    RGAP = g.get('RING_GAP', 6); RSKIP = {_n(x) for x in g.get('RING_SKIP', [])}
    for nm, ll, *_ in towns:
        toks = [_n(x) for x in nm.replace('-', ' ').split() if _n(x)]
        if not toks or _n(nm) in RSKIP: continue
        last = -1e9
        for i in range(len(wn) - len(toks) + 1):
            if wn[i:i + len(toks)] == toks and X.WD['words'][i]['t0'] - last > RGAP:
                last = X.WD['words'][i]['t0']; RINGS.append((last, ll))
    for c_, pl in L(g.get('RINGS')): RINGS.append((T(c_), P(pl)))
    MARKS = [(T(m[0]), P(m[1]), str(m[2])) for m in L(g.get('MARKS'))]      # crossed swords + year left on the map
    MARK_END = []
    for m in MARKS:   # MARK_LIFE='chapter': a battle mark stays until the next chapter slide (keeps long empire maps readable)
        nxt = [c for c in X.chapters if c > m[0] + 1] if g.get('MARK_LIFE') == 'chapter' else []
        MARK_END.append(min(nxt) + .4 if nxt else 1e9)
    # v2.11 opt-in declutter: MARK_HOLD = max seconds a mark stays; MARK_MAX marks at most within MARK_RADIUS deg
    # (the oldest fades as a new one lands); a new mark within MARK_OVERLAP deg of an older one replaces it
    mh, mm, mr, mo = g.get('MARK_HOLD'), g.get('MARK_MAX'), g.get('MARK_RADIUS', 4.5), g.get('MARK_OVERLAP', 1.6)
    order = sorted(range(len(MARKS)), key=lambda i: MARKS[i][0])
    for i in order:
        if mh: MARK_END[i] = min(MARK_END[i], MARKS[i][0] + mh)
    for i in order:
        t0, (lo_, la_), _ = MARKS[i]
        near = lambda j, r: math.hypot((MARKS[j][1][0] - lo_) * math.cos(math.radians(la_)), MARKS[j][1][1] - la_) < r
        vis = [j for j in order if MARKS[j][0] < t0 and MARK_END[j] > t0 + .6]
        for j in vis:
            if near(j, mo): MARK_END[j] = t0 + .6
        if mm:
            reg = [j for j in vis if MARK_END[j] > t0 + .6 and near(j, mr)]
            for j in reg[:max(0, len(reg) + 1 - mm)]: MARK_END[j] = t0 + .6
    FIRES = [(T(f[0]), P(f[1])) for f in L(g.get('FIRES'))]                  # a town burning from that cue on
    if 'forest' in MAPD: R['CFG']['forest_thr'] = MAPD['forest']
    keys = []
    for k in raw:
        t_, lon, lat, wl = k[:4]; hl = wl / 2; hv = hl * H / W_ / R['C0']
        lon = clamp(lon, B[0] + hl + .2, B[1] - hl - .2) if 2 * hl < B[1] - B[0] - .4 else (B[0] + B[1]) / 2
        lat = clamp(lat, B[2] + hv + .2, B[3] - hv - .2) if 2 * hv < B[3] - B[2] - .4 else (B[2] + B[3]) / 2
        keys.append((t_, lon, lat, wl) + tuple(k[4:]))

    # ---------------- elements
    REALMS = []
    OCC = g.get('REALM_MODE') == 'occlude'   # v2.11: later realms cover earlier ones (one tint per pixel), soft borders, no ink line
    for r in L(g.get('REALMS')):
        polys = shape(r['shape'], f"realm {r.get('name')}") if 'shape' in r else [q for x in r['shapes'] for q in shape(x, f"realm {r.get('name')}")]
        kd = kind_ok(r['kind'], f"realm {r.get('name')}")
        t0, t1 = T(r['at']), T(r['until'])
        if t1 <= t0: X.errors.append(f"realm {r.get('name')}: 'until' is before 'at'")
        at = P(r['label_at']) if r.get('label_at') else None
        if at is None and polys:
            from shapely.geometry import Polygon
            c = max((Polygon(p) for p in polys if len(p) > 2), key=lambda p: p.area).representative_point(); at = (c.x, c.y)
        grow = None
        if r.get('grow'):
            gr = r['grow']; c = P(gr['from']); ext = max(math.hypot(x - c[0], y - c[1]) for p in polys for x, y in p) + 1
            grow = (c, gr.get('r0', 2), ext, t0, T(gr['until']) if gr.get('until') else t0 + 4)
        rp = [atlas.rough(p, .35, .10) for p in polys if len(p) > 2]
        bb = (min(x for p in polys for x, y in p), max(x for p in polys for x, y in p), min(y for p in polys for x, y in p), max(y for p in polys for x, y in p)) if polys else (0, 0, 0, 0)
        REALMS.append(dict(t0=t0, t1=t1, polys=polys, rpolys=rp, bbox=bb, col=KC[kd], name=r.get('name'), at=at, grow=grow, size=r.get('size', 54), s=r.get('strength', .36),
                           tint=tuple(r['tint']) if r.get('tint') else soft_tint(KC[kd]), tilt=r.get('tilt', -14), group=r.get('group', r.get('name')),
                           lgap=(T(r['label_gap'][0]), T(r['label_gap'][1])) if r.get('label_gap') else None,
                           lt1=T(r['label_until']) if r.get('label_until') else t1, fin=r.get('fade', 1.0)))
    ARROWS = []; ARROW_LEAD = []; ARROW_CAV = []; ARROW_STY = []
    for a in L(g.get('ARROWS')):
        t0 = T(a['at']); t1 = T(a['to']) if a.get('to') else t0 + 2.0; tf = T(a['fade']) if a.get('fade') else t1 + 4.0
        w = a.get('width', (12, 28))
        ARROWS.append((t0, t1, tf, [P(p) for p in a['path']], kind_ok(a['kind'], 'arrow'), w[0], w[1], a.get('dashed', False)))
        ARROW_LEAD.append(a.get('leader')); ARROW_CAV.append(bool(a.get('cavalry'))); ARROW_STY.append(a.get('style', 'arrow'))
    LABELS = []
    for c in L(g.get('CITIES')):
        t0, t1, names = T(c[0]), T(c[1]), c[2]; size = c[3] if len(c) > 3 else 34
        for n in ([names] if isinstance(names, str) else names): LABELS.append((t0, t1, P(n), n, size))
    RIPPLES = [(T(a), T(b), P(p)) for a, b, p in L(g.get('RIPPLES'))]
    STRIKES = [(T(a), T(b), P(p)) for a, b, p in L(g.get('STRIKES'))]
    HATCH = [(T(h[0]), T(h[1]), ([q for x in h[2] for q in shape(x, 'hatch')] if isinstance(h[2], list) and h[2] and isinstance(h[2][0], list) else shape(h[2], 'hatch')), tuple(h[3]) if len(h) > 3 else (200, 30, 30)) for h in L(g.get('HATCH'))]
    PILLS = [(T(p[0]), T(p[1]), p[2], p[3], kind_ok(p[4], 'battle'), kind_ok(p[5], 'battle')) for p in L(g.get('BATTLES'))]
    YEARS = sorted([(T(c), s) for c, s in L(g.get('YEARS'))]) or [(0.0, '')]
    class Med2:
        def __init__(self, make): self.make = make; self.v = {}
        def draw(self, fr, pos, t, t0, t1, target=None, flip=True):
            if flip not in self.v: self.v[flip] = self.make(flip)
            self.v[flip].draw(fr, pos, t, t0, t1, target=target)
    MED = []
    for m in L(g.get('PEOPLE')):
        if m.get('show') is False: continue   # army-leader only (token on the march), no pop-up medallion
        kd = kind_ok(m.get('kind', 'roman'), f"person {m['name']}")
        noor = m['noor'] if 'noor' in m else is_religious(m['name'], m.get('title', ''))
        if noor and not m.get('noor'): print(f"respect rule: {m['name']} shown as noor light (Muslim religious figure)", file=sys.stderr)
        img = m.get('image')
        if img and not noor and not os.path.exists(os.path.join(ROOT, 'assets/img', img)):
            X.errors.append(f"person {m['name']}: image assets/img/{img} not found (fetch it: python tools/commons.py get ...)"); img = None
        if noor: mk = (lambda fl, m=m, kd=kd: NoorMedallion(m['name'], m.get('title', ''), kd, D=230, flip=fl))
        elif img: mk = (lambda fl, m=m, kd=kd, img=img: Medallion(img, m['name'], m.get('title', ''), kd, D=230, flip=fl, fallen=m.get('fallen', False), crop=tuple(m.get('crop', (0.12, 0.04, 0.88, 0.80)))))
        else: mk = (lambda fl, m=m, kd=kd: CrestMedallion(m['name'], m.get('title', ''), kd, D=230, flip=fl, mono=monogram(m['name']) if g.get('CREST_MONOGRAM') else None))
        MED.append((Med2(mk), T(m['at']), T(m['until']) if m.get('until') else T(m['at']) + 5, P(m['place']) if m.get('place') else None))
    PDISC = {}   # army commander's face rides at the head of his army
    def leader_disc(name, D=118):
        if name in PDISC: return PDISC[name]
        m = next((m for m in L(g.get('PEOPLE')) if m['name'] == name), None)
        if m is None: X.errors.append(f"leader {name!r} is not in PEOPLE"); PDISC[name] = None; return None
        noor = m['noor'] if 'noor' in m else is_religious(m['name'], m.get('title', ''))
        if noor: im = noor_disc(D)
        elif m.get('image') and os.path.exists(os.path.join(ROOT, 'assets/img', m['image'])): im = portrait_disc(m['image'], D, crop=tuple(m.get('crop', (0.12, 0.04, 0.88, 0.80))))
        else: im = crest_disc(m.get('kind', 'roman'), D, monogram(m['name']) if g.get('CREST_MONOGRAM') else None)   # no likeness: the army still carries its commander's crest (never an invented face)
        PDISC[name] = (im, m.get('kind', 'roman'), name.split(' ')[0] if len(name) > 12 else name); return PDISC[name]
    ARMY = {}
    for i, nm in enumerate(ARROW_LEAD):
        if nm and nm not in ARMY:
            dd = leader_disc(nm)
            m = next((m for m in L(g.get('PEOPLE')) if m['name'] == nm), {})
            if dd and dd[0] is not None: ARMY[nm] = ArmyToken(dd[0], nm, m.get('title', ''), ARROWS[i][4], cols=4, rows=3)
    PLATES = []
    for p in L(g.get('PLATES')):
        if not os.path.exists(os.path.join(ROOT, 'assets/img', p['image'])): X.errors.append(f"plate image assets/img/{p['image']} not found"); continue
        pa, pb = T(p['at']), T(p['until'])
        if pb - pa < 4.3: pb = pa + 4.3          # a real image stays up long enough to look at (>= ~3.5 s fully shown)
        PLATES.append((pa, pb, Plate(p['image'], crop=tuple(p['crop']) if p.get('crop') else None, caption=p.get('caption', ''))))
    TITLE = g.get('TITLE'); ROLL = g.get('ROLL'); QUOTE = g.get('QUOTE'); ONG = g.get('ONGOING'); ENDC = g.get('END_CARD', {})
    if TITLE: TITLE = dict(TITLE, t0=T(TITLE['at']), t1=T(TITLE['until']) if TITLE.get('until') else (X.chapters[0] - .2 if X.chapters else T(TITLE['at']) + 6),
                           t_sub=T(TITLE['sub_at']) if TITLE.get('sub_at') else T(TITLE['at']) + 1.2)
    if ROLL: ROLL = dict(ROLL, t0=T(ROLL['at']), t1=T(ROLL['until']), items=[(T(c), lab, kind_ok(k, 'roll')) for c, lab, k in ROLL['items']])
    if ONG: ONG = dict(text=ONG.get('text', 'ONGOING CONFLICT · REPORTS STILL DEVELOPING'), t0=T(ONG['at']), t1=T(ONG['until']))
    CYQ = None
    if QUOTE:
        try: i0 = X.idx(QUOTE['from']); i1 = X.idx(QUOTE['to'], i0) + len(QUOTE['to'].split()) - 1
        except KeyError: X.errors.append(f"QUOTE from/to phrase not found"); i0 = i1 = 0
        img = QUOTE.get('image') if QUOTE.get('image') and os.path.exists(os.path.join(ROOT, 'assets/img', QUOTE['image'])) else None
        CYQ = (SourceCard(img or _blank_img(), QUOTE.get('title', ''), QUOTE.get('sub', ''), [X.WD['words'][i]['w'] for i in range(i0, i1 + 1)],
                          [X.WD['words'][i]['t0'] for i in range(i0, i1 + 1)], box=tuple(QUOTE.get('box', (70, 430, 900, 520)))),
               X.WD['words'][i0]['t0'] - .6, T(QUOTE['until']) if QUOTE.get('until') else X.WD['words'][i1]['t1'] + 2.5)
    SIEGE = []
    for k, s in enumerate(L(g.get('SIEGES'))):
        t0, t1 = T(s['at']), T(s['until'])
        spec = s.get('spec') or tac_auto.make(s.get('city', ''), kind_ok(s.get('attacker', 'mongol'), 'siege'), s.get('defender'), s.get('climate', 'arid'),
                                              s.get('river', False), s.get('field', False), seed=s.get('seed', 11 + k), churches=s.get('churches', 0))
        if s.get('ancient'): spec = dict(spec); spec.pop('wagons', None)   # no wagon fort / gun smoke before gunpowder
        SIEGE.append(dict(s, t0=t0, t1=t1, spec=spec, burn_t=T(s['burn']) if isinstance(s.get('burn'), (str, int, float)) and not isinstance(s.get('burn'), bool) else (t0 + 1.2 if s.get('burn') else None)))
    if X.errors:
        msg = '\n  - '.join(dict.fromkeys(X.errors))
        if check: g['_ERRORS'] = list(dict.fromkeys(X.errors))
        else: raise StoryError(f'{len(X.errors)} problem(s) in episodes/{slug}.py:\n  - {msg}\n(run: python produce.py check {slug})')
    g.update(END=X.END, VEND=X.VEND, FPS=FPS, _CTX=X, _KEYS=keys, _B=B, _R=R, _REALMS=REALMS, _ARROWS=ARROWS, _PILLS=PILLS, _MED=MED, _LABELS=LABELS,
             _SIEGE=SIEGE, _PLATES=PLATES, _STY=STY, _CH=X.chapters,
             _CYQ_T=(CYQ[1], CYQ[2]) if CYQ else None, _EXTRA_EV=[r[0] for r in RINGS] + [m[0] for m in MARKS] + [r[0] for r in RIPPLES] + [h[0] for h in HATCH] + [y[0] for y in YEARS] + ([CYQ[1]] if CYQ else []))
    if check:
        g['render'] = None; return g

    # ---------------- atlases (cached per slug)
    def abuild(name, b, K, cfg):
        Pj = atlas.Proj(*b, K=K, c=R['C0']); hsh = hashlib.md5(repr((b, K, sorted((k, repr(v)) for k, v in cfg.items()))).encode()).hexdigest()[:8]; cache = os.path.join(X.bdir, f'atlas{name}_{hsh}')
        pyr = atlas.build(Pj, cfg, cache)
        if not os.path.exists(cache + '_desert.png'): world.desert_mask(Pj, cache + '_desert.png', R['DESERTS'], atlas.rough)
        if name:   # detail atlases load lazily (LRU): many close-up regions without holding them all in RAM
            del pyr; return Pj, LazyPyr(cache), LazyImg(cache + '_land.png'), LazyImg(cache + '_desert.png')
        return Pj, pyr, Image.open(cache + '_land.png').convert('L'), Image.open(cache + '_desert.png').convert('L')
    main = abuild('', B, R['K'], R['CFG'])
    dets = [abuild(n, b, Kd, R['dcfg'](Kd)) for n, b, Kd in R['DETAILS']]
    cam = Camera(main[0], main[1], keys, details=[(d[0], d[1]) for d in dets])
    cam.fade = g.get('ATLAS_FADE', 0.12)   # wider = slower cross-fade between the overview and a detail atlas
    LANDS = [main[2]] + [d[2] for d in dets]; DESS = [main[3]] + [d[3] for d in dets]

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

    def year_at(t):
        y = YEARS[0][1]
        for t0, s in YEARS:
            if t >= t0: y = s
        return y

    def realms_occlude(fr, sc, land, t, wl):
        lon, lat, _ = cam.at(t); hl = wl * .75; hv = hl * H / W_ / R['C0'] + 1
        act = []
        for r in REALMS:
            if not (r['t0'] - .05 < t < r['t1'] + .05): continue
            b = r['bbox']
            if b[1] < lon - hl or b[0] > lon + hl or b[3] < lat - hv or b[2] > lat + hv: continue
            a = life(t, r['t0'], r['t1'], r['fin'], 1.0)
            if a <= .003: continue
            act.append((r, a))
        if not act: return
        S = 2; w2, h2 = W_ // S, H // S   # masks at half resolution (soft edges anyway), upsampled once
        landh = np.asarray(Image.fromarray((land * 255).astype(np.uint8)).resize((w2, h2), Image.BILINEAR), np.float32) / 255
        ms = []
        for r, a in act:
            m = Image.new('L', (w2, h2), 0); dm = ImageDraw.Draw(m)
            for p in r['rpolys']: dm.polygon([(x / S, y / S) for x, y in (sc(*q) for q in p)], fill=255)
            mm = np.asarray(m.filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255
            if r['grow']:
                c, r0, r1, g0, g1 = r['grow']; rad = lerp(r0, r1, ease_io(prog(t, g0, g1)))
                if rad < r1 - .01:
                    cx, cy = sc(*c); ppd = max(1e-3, (sc(c[0] + 1, c[1])[0] - cx)) / S
                    yy, xx = np.ogrid[0:h2, 0:w2]; d = np.sqrt((xx - cx / S) ** 2 + (yy - cy / S) ** 2) / ppd
                    mm = mm * np.clip((rad - d) / 0.6, 0, 1)
            ms.append(mm * landh * a)
        cover = np.zeros((h2, w2), np.float32); ks = [None] * len(ms)
        for i in range(len(ms) - 1, -1, -1):
            ks[i] = ms[i] * (1 - cover); cover = cover + ks[i]
        f = np.ones((h2, w2, 3), np.float32) - cover[..., None]
        groups = {}
        for (r, a), k in zip(act, ks):
            tn = np.array(r['tint'], np.float32) / 255
            f += k[..., None] * ((0.18 + 0.82 * tn) * 1.04)
            groups.setdefault(r['group'], np.zeros((h2, w2), np.float32)); groups[r['group']] += k
        for gm in groups.values():   # soft border: each realm deepens its own colour a touch at its edge (competitor look, no ink line)
            if gm.max() < .05: continue
            e = Image.fromarray((np.clip(gm, 0, 1) * 255).astype(np.uint8))
            ed = np.asarray(e.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(5)), np.float32) / 255
            gl = np.clip(ed * 3.2, 0, 1) * np.clip(gm, 0, 1)
            f *= (1 - 0.20 * gl)[..., None]
        F = np.asarray(Image.fromarray(np.clip(f * 100, 0, 255).astype(np.uint8)).resize((W_, H), Image.BILINEAR), np.float32) / 100
        arr = np.asarray(fr, np.float32).copy(); arr[..., :3] = np.clip(arr[..., :3] * F, 0, 255)
        fr.paste(Image.fromarray(arr.astype(np.uint8), 'RGBA'))

    def overlays(fr, sc, wl, t, style, land):
        zf = clamp(18 / wl, 0.7, 1.3)
        if OCC and style == 'atlas': realms_occlude(fr, sc, land, t, wl)
        for r in ([] if (OCC and style == 'atlas') else REALMS):
            if not (r['t0'] - .1 < t < r['t1'] + .1): continue
            a = life(t, r['t0'], r['t1'], 1.0, 1.0); circ = None
            if r['grow']:
                c, r0, r1, g0, g1 = r['grow']; rad = lerp(r0, r1, ease_io(prog(t, g0, g1)))
                if rad < r1 - .01: circ = (c, rad)
            for poly in r['polys']:
                if style == 'atlas': wash_tint(fr, sc, land, poly, r['tint'], a, circle=circ)
                else: wash(fr, sc, land, poly, r['col'], a, circle=circ, strength=r['s'] * (.8 if style == 'modern' else 1))
        for r in REALMS:
            if r['name'] and r['t0'] < t < r['lt1'] and r['at'] and r['size'] and not (r['lgap'] and r['lgap'][0] - .6 < t < r['lgap'][1] + .6):
                if style == 'atlas': realm_arc(fr, sc, r['name'], r['at'], r['size'] * 2.1 * clamp(zf, .75, 1.25), life(t, r['t0'] + .8, r['lt1'], .8, .6), r['tilt'])
                else: realm_label(fr, sc, r['name'], r['at'], r['size'] * clamp(zf, .75, 1.2), life(t, r['t0'] + .8, r['t1'], .8, .6), style)
        tsz = int(clamp(24 * (16 / wl) ** .35, 19, 30))
        for nm, ll, kind, side, *sub in TOWNS:
            x, y = sc(*ll)
            if kind == 'minor' and wl > 26: continue   # small places only when the camera is close
            if -150 < x < W_ + 150 and -40 < y < H + 40: town_small(fr, (x, y), nm, 'town' if kind == 'minor' else kind, side, tsz)
        for (t0, ll, yr), te in zip(MARKS, MARK_END):
            if t0 < t < te:
                im = swords_year(yr); x, y = sc(*ll); paste(fr, im, (x + im.width / 2 - 18, y + 26), 1, smooth(prog(t, t0, t0 + .4)) * (1 - smooth(prog(t, te - .4, te))))
        for t0, ll in FIRES:
            if t > t0: flame(fr, sc(*ll), t, smooth(prog(t, t0, t0 + .5)), .55)
        for t0, ll in RINGS:
            if t0 <= t <= t0 + 2.4: city_ring(fr, sc(*ll), t, t0)
        for t0, t1, ll, n, s in LABELS:
            if t0 - .1 < t < t1 + .1: town(fr, sc, ll, n, life(t, t0, t1, .4, .4), style, s)
        for i, (t0, t1, tf, pts, kind, w0, w1, dashed) in enumerate(ARROWS):
            if t < t0 or t > tf + 1: continue
            spts = [sc(*p) for p in pts]; k = ease_io(prog(t, t0, t1)); aa = 1 - smooth(prog(t, tf, tf + 1))
            if ARROW_STY[i] == 'raid':
                raid_arrow(fr, spts, k, aa)
                if k >= .999: city_ring(fr, spts[-1], t, t1, dur=max(.1, tf - t1 + 1))
            elif ARROW_LEAD[i] and ARROW_STY[i] != 'arrow!': footprints(fr, spts, k, aa, ARROW_CAV[i])   # a commander's march: small hoof / foot prints, no big arrow
            else: arrow(fr, spts, k, kind, w0, w1, aa, dashed=dashed)
            tok = ARMY.get(ARROW_LEAD[i]) if ARROW_LEAD[i] else None
            if tok:
                (hx, hy) = path_at(spts, max(.02, k))[0]; (bx, by) = path_at(spts, max(.0, k - .04))[0]
                tok.draw(fr, (hx, hy), t, max(.01, back_out(prog(t, t0, t0 + .5))), aa, heading=(hx - bx, hy - by))
        for t0, t1, ll in RIPPLES:
            if t0 < t < t1: ripples(fr, sc(*ll), t, t0, t1, R=70)
        for t0, t1, ll in STRIKES:
            if t0 < t < t1: missile_hit(fr, sc(*ll), t, t0, t1)
        for a0, a1, polys, col in HATCH:
            for poly in polys: hatch(fr, sc, poly, t, a0, a1, col)
        for med, t0, t1, ll in MED:
            if t0 - .1 < t < t1 + .5:
                tgt = sc(*ll) if ll else None; right = (tgt[0] if tgt else 0) < W_ * .55
                pos = (W_ - 330, 380) if right else (330, 380)
                med.draw(fr, pos, t, t0, t1, target=(tgt[0], tgt[1] - 6) if tgt else None, flip=right)
        for t0, t1, ti, sb, lk, rk in PILLS: draw_pill3(fr, (W_ / 2, 110), t, t0, t1, ti, sb, lk, rk)

    NOCH = [False]
    def chapters_on(base, t):
        for i, c in enumerate(CH):
            t0 = X.chapters[i]
            if t0 - .1 < t < t0 + 3.6: chapter(base, t, t0, t0 + 3.6, NUM[i] if c[1] != 'Epilogue' else '·', c[1])
        return base

    def map_layer(t):
        fr, sc, wl = cam.frame(t); land, des = crop_masks(t)
        A, Bs, f = style_at(t); lon, lat, _ = cam.at(t); view = (lon, lat, wl, sc)
        base = ST.stylize(fr, land, des, A, view, t)
        if f < 1 and A != Bs: base = Image.blend(base, ST.stylize(fr, land, des, Bs, view, t), f)
        style = Bs if f >= .5 else A
        overlays(base, sc, wl, t, style, land)
        base = Image.blend(ST.finish(base.copy(), A), ST.finish(base, Bs), f) if (f < 1 and A != Bs) else ST.finish(base, style)
        if TITLE: title_card(base, t, TITLE)
        if ONG: ongoing_tag(base, t, ONG)
        if ROLL: roll_card(base, t, ROLL)
        if CYQ and CYQ[1] < t < CYQ[2] + .5: CYQ[0].draw(base, t, CYQ[1], CYQ[2])
        if not NOCH[0]: chapters_on(base, t)
        if YEARS[0][1]: paste(base, year_badge(year_at(t)), (W_ - 160, 86), 1, 1)
        return base

    def map_dissolve(t):
        d = cam.dissolve(t)
        if not d: return map_layer(t)
        a, b, f = d
        if b[4] == 'wipe' and SHEET:   # ONLY explicit 'wipe' keys (big jumps): hold on the old view, then the new view rolls in as a sheet in the last WIPE_D seconds
            f = prog(t, b[0] - WIPE_D, b[0])
            try:
                cam.force = a; A = map_layer(t)
                if f <= 0: return A
                NOCH[0] = True; A = map_layer(t); cam.force = b; Bm = map_layer(t)
            finally: cam.force = None; NOCH[0] = False
            side = 'left' if any(abs(b[0] - c) < 2.5 for c in X.chapters) else 'right'
            return chapters_on(TR.push_curve(A, Bm, f, side).convert('RGBA'), t)   # chapter bar stays put, drawn once on top
        try:
            cam.force = a; A = map_layer(t).convert('RGBA'); cam.force = b; Bm = map_layer(t).convert('RGBA')
        finally: cam.force = None
        return Image.blend(A, Bm, f)

    NOVIG = g.get('VIGNETTE', False) is False
    SHEET = g.get('TRANSITION', 'sheet') == 'sheet'; INTRO = g.get('INTRO', 'sheet'); WIPE_D = 1.6; STG_IN = 1.5
    STG = None; SG = g.get('STING')
    if SG is not None and SG is not False:
        SG = {} if SG is True else SG
        t0 = T(SG['at']) if SG.get('at') else X.WD.get('sting_t')
        if t0 is None: print('STING: no "at" cue and no sting_after gap in the narration; skipped', file=sys.stderr)
        else:
            hold = SG.get('hold', (X.WD.get('sting_gap') or 3.2) - .2)
            STG = dict(t0=t0, t1=t0 + hold, t2=t0 + hold + 1.2, card=TR.Sting(dict(g.get('BRAND', {}), **SG)))
    TACS = []
    for k, s in enumerate(SIEGE):
        tc = TAC.Tactical(f'{slug}_{k}', s['spec'], [(s['t0'], 1500, 900, 2800), (s['t1'], 1500, 860, 2000)])
        for cp in tc.camps: cp[0].update(t0=s['t0'] + .2, spread=1.0)
        def seg(t, s=s, tc=tc):
            fr, sc = tc.frame(t); tc.draw_camps(fr, sc, t)
            if s['spec'].get('field'):  # open battle: defenders charge, attackers' guns / volleys answer
                d0 = s['t0'] + 1.0; d1 = s['t0'] + (s['t1'] - s['t0']) * .55
                arrow(fr, [sc(*p) for p in ((950, 760), (1350, 900), (1800, 1040))], ease_io(prog(t, d0, d1)), s.get('defender') or 'rus', 18, 40)
                if t > d1 - .6: ripples(fr, sc(1850, 1060), t, d1 - .6, s['t1'], R=90)
                if s.get('ancient'):   # both lines close: the attacker answers the charge, the clash ripples
                    arrow(fr, [sc(*p) for p in ((2150, 1120), (1900, 1000), (1600, 900))], ease_io(prog(t, d0 + .5, d1 - .2)), s.get('attacker', 'roman'), 18, 40)
                    if t > d1 - .4: ripples(fr, sc(1650, 930), t, d1 - .4, s['t1'], R=110)
                else:
                    for i, (x, y) in enumerate(((1900, 980), (2050, 1010), (2200, 1060), (1980, 1150))):
                        TAC.smoke(fr, sc(x, y), t + i, smooth(prog(t, d1 - .8 + i * .2, d1 + .4 + i * .2)) * .8, 1.0 * tc.s, i)
            for side_, (x, y) in (('attacker', (2080, 820)), ('defender', (880, 600))):
                nm = (s.get('leaders') or {}).get(side_); dd = leader_disc(nm, 150) if nm else None
                if dd and dd[0] is not None:
                    px, py = sc(x, y); a_ = smooth(prog(t, s['t0'] + .9, s['t0'] + 1.5))
                    key_ = ('tac', nm)
                    if key_ not in ARMY:
                        m = next((m for m in L(g.get('PEOPLE')) if m['name'] == nm), {}); ARMY[key_] = ArmyToken(dd[0], nm, m.get('title', ''), m.get('kind', 'roman'), flip=(side_ == 'attacker'))
                    ARMY[key_].draw(fr, (px, py), t, max(.01, back_out(prog(t, s['t0'] + .9, s['t0'] + 1.4))), a_, blocks=False)
            if s['burn_t'] is not None and s['spec'].get('cities'): tc.burn_city(fr, sc, t, s['burn_t'], idx=0, n=12, seed=3)
            if s.get('title'): draw_pill3(fr, (W_ / 2, 110), t, s['t0'] + .3, s['t1'] - .2, s['title'], s.get('sub', ''), s.get('attacker', 'mongol'), s.get('defender') or s.get('attacker', 'mongol'))
            if s.get('year') or YEARS[0][1]: paste(fr, year_badge(s.get('year') or year_at(t)), (W_ - 160, 86), 1, 1)
            return ST.finish(fr, s.get('style') or sty(t))
        TACS.append((s['t0'], s['t1'], seg))
    XF = 1.0 if not SHEET else 1.5
    TAC_FNS = {fn: (a, b) for a, b, fn in TACS}

    def render(t):
        segs = [(t0, t1, (lambda tt, pl=pl, a=t0, b=t1: pl.render(tt, a, b))) for t0, t1, pl in PLATES] + TACS
        segs.sort(key=lambda s_: s_[0]); act = []
        for t0, t1, fn in segs:
            xf = XF if fn in TAC_FNS else .4            # plates: quick 0.4 s fade, then they HOLD (no 1-second flash)
            a = min(smooth(prog(t, t0, t0 + xf)) if t0 > 0 else 1.0, 1 - smooth(prog(t, t1 - xf, t1)))
            if a > 0: act.append((a, fn))
        full = [i for i, (a, _) in enumerate(act) if a >= .999]
        if full: fr = act[full[-1]][1](t); act = act[full[-1] + 1:]
        else: fr = map_dissolve(t)
        for a, fn in act:
            if SHEET and fn in TAC_FNS and t < TAC_FNS[fn][0] + XF:   # a close-up slides in from the right; it leaves with a smooth dissolve
                fr = Image.blend(fr.convert('RGB'), fn(t).convert('RGB'), smooth(prog(t, TAC_FNS[fn][0], TAC_FNS[fn][0] + XF)))   # close-up dissolves in (no slide on every scene)
            else: fr = Image.blend(fr.convert('RGBA'), fn(t).convert('RGBA'), a)
        if STG and STG['t0'] <= t < STG['t2']:
            tl = t - STG['t0']; card = STG['card'].frame(tl)
            if tl < STG_IN: fr = TR.sheet(fr, card, tl / STG_IN, 'top', glow=(255, 196, 110))
            elif t < STG['t1']: fr = card
            else: fr = Image.blend(card, fr.convert('RGB'), smooth(prog(t, STG['t1'], STG['t2'])))
        fr = end_card(fr.convert('RGBA'), t, X.VEND, ENDC)
        out = sharpen(fr.convert('RGB') if NOVIG else grade(fr))
        if INTRO == 'sheet': out = TR.sheet(Image.new('RGB', out.size), out, prog(t, 0, 1.6), 'top') if t < 1.6 else out
        else: out = drop_in(out, t, 0.8)
        fb = 1 - smooth(prog(t, X.END - 0.8, X.END))
        return Image.blend(Image.new('RGB', out.size), out, fb) if fb < 1 else out

    # ---------------- sound: automatic, era-appropriate (no gunfire before gunpowder, nothing meme-like)
    HITS = sorted(set(round(x, 2) for x in X.chapters + [r[0] for r in RIPPLES[:12]] + [s[0] for s in STRIKES[:6]]))
    ev = []
    if g.get('AUTO_SFX', True):
        e0 = sty(1)
        ev += [(0.0, 'px_horn_drums' if e0 not in ('modern', 'pahlavi') else 'trailer1', -8, 5)]
        for t0 in X.chapters:
            e = sty(t0 + 2)
            ev += [(t0 - .2, 'subdrop', -9, 3), (t0, 'hud2', -11, 2)] if e == 'modern' else [(t0 - .2, 'px_braam', -9, 4), (t0 + .1, 'paper_flip', -13, 1.5)]
        for i, (t0, t1, tf, pts, kind, *_) in enumerate(ARROWS):
            e = sty(t0)
            if e == 'modern': ev.append((t0, 'jet_pass' if kind in ('usa', 'israel', 'britain') else 'rocket', -11, 3))
            elif e in ('pahlavi', 'qajar'): ev.append((t0, 'px_march', -13, 3))
            else: ev.append((t0, 'px_gallop' if (ARROW_CAV[i] if i < len(ARROW_CAV) else i % 2) else 'px_march', -13, 3))
        for t0, t1, ll in RIPPLES: ev.append((t0, 'cine_boom' if sty(t0) in ('pahlavi', 'modern') else 'lowhit', -14, 2.5))
        for t0, t1, ll in STRIKES: ev.append((t0, 'boom_impact', -9, 3))
        for t0, t1, *_ in PILLS:
            e = sty(t0); ev.append((t0, 'hud_sel' if e in ('modern', 'pahlavi') else ('low_horn' if e == 'qajar' else 'px_horn'), -12, 3))
        for med, t0, t1, ll in MED: ev.append((t0, 'swoosh', -19, 1.2))
        for t0, t1, pl in PLATES: ev.append((t0, 'whoosh6', -19, 2))
        for s in SIEGE:
            ev += [(s['t0'], 'px_battle_drums', -13, s['t1'] - s['t0']), (s['t0'] + .8, 'px_medieval_war' if sty(s['t0']) not in ('modern', 'pahlavi') else 'cine_boom', -11, 4)]
            if s['burn_t'] is not None: ev.append((s['burn_t'], 'fire_big', -12, 6))
        if ENDC is not None: ev.append((X.VEND + .3, 'trailer1', -10, 5))
        if INTRO == 'sheet': ev.append((0.05, 'gear_tick', -12, 1))
        if SHEET:
            for k in keys:
                if len(k) > 4 and k[4] == 'wipe': ev += [(k[0] - WIPE_D + .15, 'whoosh_cine', -11, 2)]   # one clean whoosh on every slide
            for a, b, fn in TACS: ev.append((a, 'paper_flip', -22, 1.0))
        if STG:
            ev += [(STG['t0'], 'logo_shimmer', -9, 3.5), (STG['t0'] + .5, 'gears', -15, STG['t1'] - STG['t0']), (STG['t1'], 'whoosh_metal', -16, 2)]
    for c, nm, db, *ml in L(g.get('SFX_EXTRA')): ev.append((T(c), nm, db, ml[0] if ml else 4))
    ev.sort(); SFX = []
    FAM = lambda n: n.replace('px_', '').split('_')[0]   # gallop / gallop_near, boom / thud ... never two of one family together
    for t0, nm, db, ml in ev:
        if any(abs(t0 - e[0]) < .6 and (FAM(e[1]) == FAM(nm) or {FAM(e[1]), FAM(nm)} <= {'boom', 'thud', 'lowhit'}) for e in SFX): continue
        SFX.append((round(max(0, t0), 2), nm, db, round(ml, 2)))
    g.update(render=render, HITS=HITS, SFX=SFX, cam=cam)
    return g


# ====================================================================== drawing helpers (from the Iran episode)
NUM = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII', 'XIX', 'XX']

def _blank_img():
    p = os.path.join(ROOT, 'assets/img/_parchment.png')
    if not os.path.exists(p): Image.new('RGB', (600, 600), (214, 196, 160)).save(p)
    return '_parchment.png'

def wash(fr, sc, land, poly, col, a, circle=None, line=True, strength=.36):
    if a <= 0 or len(poly) < 3: return
    m = Image.new('L', (W_, H), 0); ImageDraw.Draw(m).polygon([sc(*p) for p in atlas.rough(poly, .35, .10)], fill=255)
    mm = np.asarray(m, np.float32) / 255
    if circle is not None:
        (clon, clat), rad = circle; cx, cy = sc(clon, clat); ppd = sc(clon + 1, clat)[0] - cx
        yy, xx = np.ogrid[0:H, 0:W_]; d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / max(1e-3, ppd)
        mm = mm * np.clip((rad - d) / 1.2, 0, 1)
    mm = mm * land
    if mm.max() <= 0.01: return
    arr = np.asarray(fr, np.float32); k = (mm * a * strength)[..., None]
    arr[..., :3] = arr[..., :3] * (1 - k) + np.array(col, np.float32) * k
    if line:
        e = np.asarray(Image.fromarray((mm * 255).astype(np.uint8)).filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(3)), np.float32) / 255
        ke = (np.clip(e * 1.5, 0, 1) * a * .85)[..., None]
        arr[..., :3] = arr[..., :3] * (1 - ke) + np.array(tuple(int(c * .55) for c in col), np.float32) * ke
    fr.paste(Image.fromarray(arr.astype(np.uint8), 'RGBA'))

def town(fr, sc, ll, name, a, style, size=34):
    x, y = sc(*ll)
    if not (-100 < x < W_ + 100 and -60 < y < H + 60): return
    lay = Image.new('RGBA', (W_, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    dc = {'modern': (110, 230, 250), 'pahlavi': (200, 30, 40), 'qajar': (20, 20, 20), 'safavid': (150, 30, 24), 'ancient': (90, 40, 16)}.get(style, (30, 22, 20))
    r = 7
    d.ellipse([x - r - 3, y - r - 3, x + r + 3, y + r + 3], fill=(250, 246, 236, int(230 * a))); d.ellipse([x - r, y - r, x + r, y + r], fill=dc + (int(255 * a),))
    ST.label(d, (x, y - 16), str(name).replace('_', ' '), style, size, anchor='md', alpha=a)
    fr.alpha_composite(lay)

def realm_label(fr, sc, text, pos, size, a, style):
    x, y = sc(*pos)
    if not (-300 < x < W_ + 300): return
    font, col = ST.REALM[style]
    lay = Image.new('RGBA', (W_, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    s = ' '.join(text) if text.isupper() and len(text) < 14 else text
    d.text((x, y), s, font=ST.F(font, size), fill=col[:3] + (int(col[3] * a),), anchor='mm', stroke_width=2,
           stroke_fill=(250, 246, 236, int(120 * a)) if style not in ('modern', 'medieval', 'atlas') else (10, 10, 14, int(140 * a)))
    fr.alpha_composite(lay)

def missile_hit(fr, pos, t, t0, t1):
    a = life(t, t0, t1, .15, .5)
    if a <= 0: return
    k = prog(t, t0, t0 + .7)
    def fn(d, S):
        for i in range(3):
            ph = ((t - t0) * .8 + i / 3) % 1; r = 20 + 70 * ph
            d.ellipse([S((pos[0] - r, pos[1] - r)), S((pos[0] + r, pos[1] + r))], outline=(255, 120, 60, int(220 * a * (1 - ph))), width=int(4 * Z))
        L, gg = 34, 14
        for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            cx, cy = pos[0] + sx * L, pos[1] + sy * L
            d.line([S((cx, cy)), S((cx - sx * gg, cy))], fill=(110, 230, 250, int(255 * a)), width=int(3 * Z))
            d.line([S((cx, cy)), S((cx, cy - sy * gg))], fill=(110, 230, 250, int(255 * a)), width=int(3 * Z))
        rr = 18 * (1 - k) + 6
        d.ellipse([S((pos[0] - rr, pos[1] - rr)), S((pos[0] + rr, pos[1] + rr))], fill=(255, 230, 160, int(255 * a * (1 - k * .6))))
    local_draw(fr, (pos[0] - 110, pos[1] - 110, pos[0] + 110, pos[1] + 110), fn)
    flame(fr, (pos[0], pos[1] + 4), t, a * smooth(prog(t, t0 + .2, t0 + .6)), .8)

def hatch(fr, sc, poly, t, t0, t1, col=(200, 30, 30)):
    a = life(t, t0, t1, .5, .5)
    if a <= 0: return
    m = Image.new('L', (W_, H), 0); ImageDraw.Draw(m).polygon([sc(*p) for p in poly], fill=int(150 * a))
    lines = Image.new('L', (W_, H), 0); dl = ImageDraw.Draw(lines)
    for x in range(-H, W_, 26): dl.line([(x, H), (x + H, 0)], fill=255, width=7)
    al = Image.fromarray((np.asarray(m, np.float32) * np.asarray(lines, np.float32) / 255).astype(np.uint8))
    lay = Image.new('RGBA', (W_, H), col + (0,)); lay.putalpha(al); fr.alpha_composite(lay)

def title_card(fr, t, C):
    a = life(t, C['t0'], C['t1'], .6, .5)
    if a <= 0: return
    fr.alpha_composite(Image.new('RGBA', (W_, H), (8, 6, 4, int(120 * a))))
    lay = Image.new('RGBA', (W_, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    k = ease_out(prog(t, C['t0'], C['t0'] + 1.2)); title = C.get('title', '')
    sp = '  '.join(title) if len(title) <= 8 else title
    d.text((W_ / 2, 440 + 20 * (1 - k)), sp, font=ST.F('Cinzel.ttf', 168 if len(title) <= 8 else 110), fill=(246, 230, 196, int(255 * a)), anchor='mm',
           stroke_width=4, stroke_fill=(40, 24, 10, int(220 * a)))
    a2 = a * smooth(prog(t, C['t_sub'], C['t_sub'] + .6))
    if C.get('sub'): d.text((W_ / 2, 570), C['sub'], font=ST.F('EBGaramond-Italic.ttf', 54), fill=(236, 220, 190, int(255 * a2)), anchor='mm', stroke_width=2, stroke_fill=(20, 12, 6, int(200 * a2)))
    if C.get('dates'): d.text((W_ / 2, 650), C['dates'], font=ST.F('Cinzel.ttf', 44), fill=(214, 190, 140, int(255 * a2)), anchor='mm')
    fr.alpha_composite(lay)

def ongoing_tag(fr, t, C):
    a = life(t, C['t0'], C['t1'], .5, .5)
    if a <= 0: return
    lay = Image.new('RGBA', (W_, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); blink = .65 + .35 * math.sin(t * 4)
    f = ST.F('RobotoCondensed.ttf', 26); w = d.textlength(C['text'], font=f)
    d.rounded_rectangle([48, 950, 120 + w, 1010], radius=8, fill=(10, 18, 26, int(200 * a)), outline=(240, 70, 60, int(255 * a)), width=2)
    d.ellipse([66, 968, 90, 992], fill=(240, 60, 50, int(255 * a * blink)))
    d.text((104, 980), C['text'], font=f, fill=(230, 240, 246, int(255 * a)), anchor='lm'); fr.alpha_composite(lay)

def roll_card(fr, t, C):
    a = life(t, C['t0'] - .6, C['t1'], .5, .5)
    if a <= 0: return
    lay = Image.new('RGBA', (W_, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([960, 120, 1860, 960], radius=24, fill=(18, 14, 12, int(200 * a)), outline=(214, 172, 70, int(220 * a)), width=3)
    d.text((1410, 180), C.get('title', ''), font=ST.F('Cinzel.ttf', 44), fill=(240, 222, 180, int(255 * a)), anchor='mm')
    per = 12 if len(C['items']) > 12 else len(C['items'])
    for n, (t0, nm, kd) in enumerate(C['items']):
        k = smooth(prog(t, t0 - .05, t0 + .25)) * a
        if k <= 0: continue
        col, row = n // 12, n % 12; x, y = 1000 + col * 440, 240 + row * 58
        d.ellipse([x, y + 8, x + 26, y + 34], fill=KC[kd] + (int(255 * k),), outline=(240, 230, 210, int(255 * k)), width=2)
        d.text((x + 40, y + 21), f'{n + 1:>2}  {nm}', font=ST.F('EBGaramond-Italic.ttf', 40), fill=(244, 236, 220, int(255 * k)), anchor='lm')
    fr.alpha_composite(lay)

def end_card(fr, t, vend, C):
    if C is None: return fr
    a = smooth(prog(t, vend + .4, vend + 1.5))
    if a <= 0: return fr
    fr.alpha_composite(Image.new('RGBA', fr.size, (14, 12, 16, int(195 * a))))
    lay = Image.new('RGBA', fr.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    if C.get('title'): d.text((W_ / 2, 450), C['title'], font=ST.F('Cinzel.ttf', 120 if len(C['title']) < 14 else 80), fill=(244, 232, 206, int(255 * a)), anchor='mm')
    if C.get('sub'): d.text((W_ / 2, 560), C['sub'], font=ST.F('EBGaramond-Italic.ttf', 54), fill=(214, 200, 176, int(255 * a)), anchor='mm')
    a2 = smooth(prog(t, vend + 1.5, vend + 2.3))
    for i, n in enumerate(C.get('notes', [])):
        d.text((W_ / 2, 690 + 50 * i), n, font=ST.F('IMFeENit28P.ttf', 32), fill=(200, 190, 176, int(255 * a2)), anchor='mm')
    fr.alpha_composite(lay); return fr


import functools
@functools.lru_cache(None)
def crest_disc(kind, D, mono=None):
    """medallion for a person with no public-domain likeness: a heraldic crest (or the person's initials), never an invented face"""
    R = D * Z / 2; r = R * 0.80; pad = int(R * 0.5); W2 = int(2 * R + 2 * pad)
    im = Image.new('RGBA', (W2, W2), (0, 0, 0, 0)); d = ImageDraw.Draw(im); cx = cy = W2 / 2
    d.ellipse([cx - R + 6 * Z, cy - R + 9 * Z, cx + R + 6 * Z, cy + R + 9 * Z], fill=(0, 0, 0, 90))
    ring(d, cx, cy, R, r - 2 * Z)
    col = KC.get(kind, (120, 100, 80)); d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    for i in range(int(r), 0, -int(4 * Z)):
        k = i / r; d.ellipse([cx - i, cy - i, cx + i, cy + i], outline=tuple(int(c * (0.75 + 0.25 * (1 - k))) for c in col), width=int(4 * Z))
    if mono:   # initials in Roman capitals, like a coin legend
        fn = F('Cinzel.ttf', r * (0.95 if len(mono) == 1 else 0.72)); bb = d.textbbox((0, 0), mono, font=fn); tw, th = bb[2] - bb[0], bb[3] - bb[1]
        x0, y0 = cx - tw / 2 - bb[0], cy - th / 2 - bb[1]
        d.text((x0 + 3 * Z, y0 + 4 * Z), mono, font=fn, fill=(20, 16, 12, 150)); d.text((x0, y0), mono, font=fn, fill=(246, 226, 168))
        d.ellipse([cx - r * .86, cy - r * .86, cx + r * .86, cy + r * .86], outline=(246, 226, 168), width=int(2 * Z))
    else: emblem(d, kind, cx, cy, r * 1.25)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(40, 44, 60), width=int(3 * Z))
    out = down(im); out.info['cy_off'] = 0; return out

def monogram(name):
    w = [x for x in re.split(r'[\s-]+', name) if x and x[0].isupper()]
    return (w[0][0] + w[-1][0]) if len(w) > 1 else (w[0][0] if w else None)

class CrestMedallion(PopMedallion):
    def __init__(self, name, title, side=None, D=250, flip=False, mono=None):
        self.disc = crest_disc(side or 'roman', D, mono); self.D = D; self.sh = None
        self.rib = cloth_ribbon(name, title, flip); self.flip = flip


def soft_tint(col):
    """a kind colour -> a light multiply tint like the competitor's political map"""
    return tuple(int(255 * (.46 + .54 * c / 255)) for c in col)

def wash_tint(fr, sc, land, poly, tint, a, circle=None):
    """multiply tint (trees and relief take the realm colour) + dark border, matching the baked atlas"""
    if a <= 0 or len(poly) < 3: return
    m = Image.new('L', (W_, H), 0); ImageDraw.Draw(m).polygon([sc(*p) for p in atlas.rough(poly, .35, .10)], fill=255)
    mm = np.asarray(m, np.float32) / 255
    if circle is not None:
        (clon, clat), rad = circle; cx, cy = sc(clon, clat); ppd = sc(clon + 1, clat)[0] - cx
        yy, xx = np.ogrid[0:H, 0:W_]; d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / max(1e-3, ppd)
        mm = mm * np.clip((rad - d) / 1.2, 0, 1)
    mm = mm * land
    if mm.max() <= 0.01: return
    arr = np.asarray(fr, np.float32); k = (mm * a)[..., None]; tn = np.array(tint, np.float32) / 255
    arr[..., :3] = arr[..., :3] * (1 - k) + np.clip(arr[..., :3] * (0.18 + 0.82 * tn) * 1.04, 0, 255) * k
    e = np.asarray(Image.fromarray((mm * 255).astype(np.uint8)).filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(3)), np.float32) / 255
    ke = (np.clip(e * 1.5, 0, 1) * a * .8)[..., None]
    arr[..., :3] = arr[..., :3] * (1 - ke) + np.array((40, 22, 22), np.float32) * ke
    fr.paste(Image.fromarray(arr.astype(np.uint8), 'RGBA'))

def realm_arc(fr, sc, text, pos, size, a, tilt=-14):
    """huge translucent curved realm name (title case), like the competitor"""
    if a <= 0: return
    x, y = sc(*pos)
    if not (-600 < x < W_ + 600 and -300 < y < H + 300): return
    txt = text.title() if text.isupper() else text
    lay = Image.new('RGBA', (W_, H), (0, 0, 0, 0))
    atlas.arc_text(lay, (x, y), txt, ST.F('IMFeENrm28P.ttf', size), size * 16, tilt, (250, 246, 244, int(190 * a)), shadow=(30, 15, 20, int(110 * a)))
    fr.alpha_composite(lay)

def name_tag(fr, pos, text, a=1.0):
    if a <= .02: return
    lay = Image.new('RGBA', (W_, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); f = ST.F('Almendra-Regular.ttf', 30)
    d.text(pos, text, font=f, fill=(250, 246, 238, int(255 * a)), anchor='mb', stroke_width=3, stroke_fill=(30, 20, 18, int(220 * a)))
    fr.alpha_composite(lay)


_COG = {}
def town_small(fr, pos, name, kind, side, size):
    """competitor-style town: small bronze cog + small white name (capital gets a gold star); constant screen size"""
    if size not in _COG: _COG[size] = (atlas.cog_icon(size * .5), atlas.star_icon(size * .42))
    cog, star = _COG[size]; x, y = pos
    fr.alpha_composite(cog, (int(x - cog.width / 2), int(y - cog.height / 2)))
    f = ST.F('Almendra-Regular.ttf', size); off = size * .75
    anchor, p = {'r': ('lm', (x + off, y)), 'l': ('rm', (x - off, y)), 'u': ('mb', (x, y - off)), 'd': ('mt', (x, y + off))}[side]
    d = ImageDraw.Draw(fr)
    d.text((p[0] + 2, p[1] + 3), name, font=f, fill=(10, 6, 6, 170), anchor=anchor)
    d.text(p, name, font=f, fill=(250, 246, 238, 255), anchor=anchor, stroke_width=1, stroke_fill=(40, 26, 22, 220))
    if kind == 'cap':
        bb = d.textbbox(p, name, font=f, anchor=anchor)
        sx = bb[2] + 6 if side != 'l' else bb[0] - star.width - 6
        fr.alpha_composite(star, (int(sx), int((bb[1] + bb[3]) / 2 - star.height / 2)))
