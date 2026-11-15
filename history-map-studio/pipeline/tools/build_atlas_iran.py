import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image, ImageDraw, ImageFilter
import atlas
from regions import iran as R
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def desert(P, path):
    w, h = P.w // 2, P.h // 2; m = Image.new('L', (w, h), 0); d = ImageDraw.Draw(m)
    for poly in R.DESERTS: d.polygon([(x / 2, y / 2) for x, y in (P.xy(*p) for p in atlas.rough(poly, .3, .12))], fill=255)
    m.filter(ImageFilter.GaussianBlur(max(4, P.K * .25))).save(path)
jobs = [('', R.BOUNDS, R.K, R.CFG)] + [(n, b, k, R.dcfg(k)) for n, b, k in R.DETAILS]
for n, b, k, cfg in jobs:
    P = atlas.Proj(b[0], b[1], b[2], b[3], K=k, c=R.C0)
    cache = os.path.join(ROOT, f'build/atlas_iran{n}')
    atlas.build(P, cfg, cache); desert(P, cache + '_desert.png'); print('built', n, flush=True)
