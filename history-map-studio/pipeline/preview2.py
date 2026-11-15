"""Stills for review.  python3 preview2.py <slug> 5 20 'END-3'  (seconds; W(i), END, VEND allowed)
   python3 preview2.py <slug> --sheet [N]   contact sheet of N evenly spaced frames (default 12) -> build/<slug>/sheet.jpg"""
import sys, os, importlib, time
from PIL import Image, ImageDraw
slug = sys.argv[1]; ep = importlib.import_module('episodes.' + slug); BD = os.path.join('build', slug); os.makedirs(BD, exist_ok=True)
if '--sheet' in sys.argv:
    n = int(sys.argv[sys.argv.index('--sheet') + 1]) if len(sys.argv) > sys.argv.index('--sheet') + 1 else 12
    ts = [ep.END * (i + .5) / n for i in range(n)]
else:
    env = {'END': ep.END, 'VEND': getattr(ep, 'VEND', ep.END)}
    if hasattr(ep, 'W'): env['W'] = ep.W
    ts = [float(eval(x, env)) for x in sys.argv[2:]]
ims = []
for t in ts:
    t0 = time.time(); im = ep.render(t).convert('RGB'); ims.append(im); print(f'{t:7.2f}s rendered in {time.time() - t0:.1f}s', flush=True)
cols = 3 if len(ims) > 4 else 2; rows = -(-len(ims) // cols)
g = Image.new('RGB', (cols * 640, rows * 360)); d = ImageDraw.Draw(g)
for i, (t, im) in enumerate(zip(ts, ims)):
    x, y = (i % cols) * 640, (i // cols) * 360; g.paste(im.resize((640, 360), Image.LANCZOS), (x, y)); d.text((x + 8, y + 6), f'{t:.1f}s', fill=(255, 255, 0))
g.save(os.path.join(BD, 'sheet.jpg'), quality=88)
for t, im in zip(ts, ims): im.save(os.path.join(BD, f'still_{t:07.2f}.jpg'), quality=92)
print('->', os.path.join(BD, 'sheet.jpg'))
