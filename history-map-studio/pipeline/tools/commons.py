"""Real, licence-safe images from Wikimedia Commons (no API key).
  python3 tools/commons.py search "Shah Abbas portrait"            -> 8 candidates with licence + size
  python3 tools/commons.py get "File:Shah Abbas I.jpg" <folder>/<name>   -> assets/img/<folder>/<name>.jpg + CREDITS.json entry
Only public domain / CC0 / CC BY / CC BY-SA are accepted. Never use another YouTuber's artwork.
Respect rule: do NOT fetch depictions of the Prophet, Sahaba, Imams or caliphs; people{} entries for them become noor light."""
import json, os, re, sys, urllib.parse, urllib.request
API = 'https://commons.wikimedia.org/w/api.php'; UA = {'User-Agent': 'HistoryMapStudio/2.0 (educational video pipeline)'}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OK = re.compile(r'public domain|^pd|cc0|cc[- ]by(-sa)?', re.I)
def q(**p):
    p.update(format='json'); req = urllib.request.Request(API + '?' + urllib.parse.urlencode(p), headers=UA)
    return json.loads(urllib.request.urlopen(req, timeout=60).read())
def info(titles):
    r = q(action='query', titles='|'.join(titles), prop='imageinfo', iiprop='url|size|extmetadata', iiurlwidth=1600)
    out = []
    for pg in r['query']['pages'].values():
        if 'imageinfo' not in pg: continue
        ii = pg['imageinfo'][0]; md = ii.get('extmetadata', {})
        lic = md.get('LicenseShortName', {}).get('value', ''); art = re.sub('<[^>]+>', '', md.get('Artist', {}).get('value', ''))[:80]
        out.append(dict(title=pg['title'], license=lic, artist=art.strip(), w=ii['width'], h=ii['height'], url=ii.get('thumburl') or ii['url'], page=ii['descriptionurl']))
    return out
def search(text):
    r = q(action='query', list='search', srsearch=text + ' filetype:bitmap', srnamespace=6, srlimit=12)
    for x in info([s['title'] for s in r['query']['search']])[:8]:
        print(('OK  ' if OK.search(x['license']) else 'NO  ') + f"{x['title']}  [{x['license']}] {x['w']}x{x['h']}  {x['artist'][:40]}")
def get(title, dest):
    x = info([title if title.startswith('File:') else 'File:' + title])
    if not x: sys.exit('not found: ' + title)
    x = x[0]
    if not OK.search(x['license']): sys.exit(f"licence '{x['license']}' not allowed (need PD / CC0 / CC BY / CC BY-SA)")
    folder, name = os.path.split(dest); d = os.path.join(ROOT, 'assets/img', folder); os.makedirs(d, exist_ok=True)
    fn = name if '.' in name else name + '.jpg'
    data = urllib.request.urlopen(urllib.request.Request(x['url'], headers=UA), timeout=120).read()
    from PIL import Image; import io
    Image.open(io.BytesIO(data)).convert('RGB').save(os.path.join(d, fn), quality=92)
    cf = os.path.join(d, 'CREDITS.json'); c = json.load(open(cf)) if os.path.exists(cf) else {}
    c[os.path.splitext(fn)[0]] = dict(file=fn, title=x['title'], license=x['license'], artist=x['artist'], page=x['page']); json.dump(c, open(cf, 'w'), indent=1)
    print(f"saved assets/img/{folder + '/' if folder else ''}{fn}  [{x['license']}]  use image='{folder + '/' if folder else ''}{fn}'")
if __name__ == '__main__':
    {'search': lambda: search(' '.join(sys.argv[2:])), 'get': lambda: get(sys.argv[2], sys.argv[3])}[sys.argv[1]]()
