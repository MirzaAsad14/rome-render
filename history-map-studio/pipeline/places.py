"""Gazetteer: turn a place NAME into (lon, lat) so the AI never has to guess coordinates.

Lookup order: episode PLACES override -> historical_places.json (ancient cities, battlefields, ~300) ->
GeoNames cities15000 (34k modern cities, CC-BY 4.0, largest population wins) -> 'ISO:IRN' country centroid.
    python places.py Ctesiphon Isfahan "Kosovo Polje"      # check names from the shell
"""
import json, os, re, sys, difflib, functools
HERE = os.path.dirname(os.path.abspath(__file__)); GEO = os.path.join(HERE, 'assets/geo')

def _k(s): return re.sub(r'[^a-z0-9]', '', s.lower().replace('_', ' '))

@functools.lru_cache(None)
def _hist(): return {_k(k): tuple(v) for k, v in json.load(open(os.path.join(GEO, 'historical_places.json'))).items()}

@functools.lru_cache(None)
def _cities():
    out = {}
    for name, ascii_, lat, lon, cc, pop in json.load(open(os.path.join(GEO, 'cities.json'))):  # sorted by population desc
        for n in (name, ascii_):
            out.setdefault(_k(n), (lon, lat))
    return out

@functools.lru_cache(None)
def countries(): return json.load(open(os.path.join(GEO, 'countries.json')))

def country_polys(iso):
    c = countries().get(iso.upper())
    if not c: raise KeyError(f'unknown country code {iso} (use ISO-3 like IRN, IRQ, TUR)')
    return [[tuple(p) for p in poly] for poly in c['polys']]

def country_centroid(iso):
    from shapely.geometry import Polygon
    ps = sorted((Polygon(p) for p in country_polys(iso)), key=lambda p: -p.area)
    c = ps[0].representative_point(); return (round(c.x, 2), round(c.y, 2))

def lookup(name, extra=None):
    if isinstance(name, (tuple, list)) and len(name) == 2 and all(isinstance(v, (int, float)) for v in name): return tuple(name)
    if extra:
        for k, v in extra.items():
            if _k(k) == _k(name): return tuple(v)
    if name.upper().startswith('ISO:'): return country_centroid(name[4:])
    k = _k(name)
    if k in _hist(): return _hist()[k]
    if k in _cities(): return _cities()[k]
    raise KeyError(name)

def suggest(name, n=4):
    pool = list(_hist().keys()) + list(_cities().keys())[:20000]
    return difflib.get_close_matches(_k(name), pool, n=n, cutoff=.75)

if __name__ == '__main__':
    for a in sys.argv[1:]:
        try: print(f'{a:28s} {lookup(a)}')
        except KeyError: print(f'{a:28s} NOT FOUND  did you mean: {suggest(a)}  (or give (lon, lat) in PLACES)')
