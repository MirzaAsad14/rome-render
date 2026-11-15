"""Quality gate. Run it; do not skip it.
  python3 qa.py check <slug>      script + storyboard lint (cues, places, pacing, respect rule, pronunciation, camera)
  python3 qa.py audio <slug>      loudness of the finished mix (YouTube -14 LUFS, true peak, voice clarity)
  python3 qa.py describe <slug>   YouTube description: chapters with timestamps, sources, image credits, disclaimers
Exit code 1 = must fix before rendering."""
import importlib, json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); os.chdir(HERE)
COMMON = set('the a an and of in to was were is his her their its by for with on at from as that this it he she they but or not had has have be been '
             'into than then when where which who whom whose after before during under over between through against about around until while '
             'chapter one two three four five six seven eight nine ten first second third last new old great king queen emperor empire army '
             'river sea war battle city kingdom north south east west i ii iii iv v iran ottoman ottomans persian roman'.split())


def load(slug, check=True):
    if check: os.environ['STORY_CHECK'] = '1'
    try: return importlib.import_module('episodes.' + slug)
    finally: os.environ.pop('STORY_CHECK', None)


def check(slug):
    errs, warns = [], []
    J = json.load(open(f'episodes/{slug}.json')); text = J['text']
    words = re.findall(r"[\w'’-]+", text); n = len(words)
    tgt = J.get('target_words')
    if tgt and abs(n - tgt) / tgt > .2: warns.append(f'script is {n} words, target {tgt} (~130 wpm): {"trim" if n > tgt else "expand"} it')
    if re.search(r'\[|\]|\(pause|\*', text): errs.append('script contains stage directions / brackets / markdown: narration text only')
    say = J.get('say', {})
    caps = {}
    for m in re.finditer(r"(?<![.!?]\s)(?<!^)\b([A-Z][a-z’']+(?:-[A-Za-z]+)?)", text):
        w = m.group(1)
        if w.lower() in COMMON or w in say: continue
        if re.search(r"(q[^u]|kh|zh|gh|dh|[’']|aa|ii|uu|yy|ae|^[A-Z][a-z]*(id|ids|an|stan|abad|ar|ur|ez|es)$)", w): caps[w] = caps.get(w, 0) + 1
    if caps: warns.append('check pronunciation, add to "say" if Edge mispronounces: ' + ', '.join(sorted(caps)[:40]))
    wf = f'build/{slug}/words.json'
    if not os.path.exists(wf):
        errs.append(f'no narration yet: python3 voice.py episodes/{slug}.json'); return report(errs, warns)
    WD = json.load(open(wf)); wpm = len(WD['words']) / WD['voice_end'] * 60
    if not 115 <= wpm <= 150: warns.append(f'narration pace {wpm:.0f} wpm (aim 125-140): adjust "rate" in the json')
    try: E = load(slug)
    except Exception as e:
        errs.append(f'episode file failed to load: {type(e).__name__}: {e}'); return report(errs, warns)
    if not hasattr(E, '_CTX'):
        warns.append('legacy hand-written episode (no storyboard lint); prefer the storyboard format (templates/story_template.py)')
        return report(errs, warns)
    errs += getattr(E, '_ERRORS', [])
    END = E.END; ev = []
    ev += [k[0] for k in E._KEYS] + [r['t0'] for r in E._REALMS] + [a[0] for a in E._ARROWS] + [p[0] for p in E._PILLS]
    ev += [m[1] for m in E._MED] + [l[0] for l in E._LABELS] + [s['t0'] for s in E._SIEGE] + [p[0] for p in E._PLATES] + E._CH
    ev += getattr(E, '_EXTRA_EV', [])   # rings, battle marks, ripples, hatching, year changes, quote card are on-screen events too
    ev = sorted(set(round(x, 1) for x in ev if 0 <= x <= END))
    cover = [(s_['t0'], s_['t1']) for s_ in E._SIEGE] + [(p[0], p[0] + 6.0) for p in E._PLATES] + ([(E._CYQ_T[0], E._CYQ_T[1])] if getattr(E, '_CYQ_T', None) else [])
    def busy(a, b):   # a close-up, a plate (first 6 s) or the quote card keeps the screen alive; only the uncovered part of a gap counts
        segs = [(max(a, x), min(b, y)) for x, y in cover if y > a and x < b]; segs.sort(); free = 0.0; cur = a
        for x, y in segs:
            if x > cur: free = max(free, x - cur)
            cur = max(cur, y)
        return max(free, b - cur)
    gaps = [(a, b) for a, b in zip([0.0] + ev, ev + [E.VEND]) if b - a > 9 and busy(a, b) > 9]
    for a, b in gaps: warns.append(f'nothing new on screen from {a:.0f}s to {b:.0f}s ({b - a:.0f}s): add a camera move, label, arrow, medallion or plate')
    dens = len(ev) / max(1, END / 60)
    if dens < 10: warns.append(f'visual density {dens:.0f} events/min (good videos: 12-25). Add more beats.')
    P = sorted(E._PILLS)
    for x, y in zip(P, P[1:]):
        if y[0] < x[1] - .2: warns.append(f'battle pills overlap at {y[0]:.1f}s ("{x[2]}" / "{y[2]}"): end the first earlier')
    M = sorted(E._MED, key=lambda m: m[1])
    for x, y in zip(M, M[1:]):
        if y[1] < x[2] - .3: warns.append(f'two medallions on screen at {y[1]:.1f}s: shorten the first')
    for m in E._MED:
        for p in E._PLATES:
            if m[1] < p[1] - .1 and p[0] + .1 < m[2]: warns.append(f'medallion at {m[1]:.1f}s overlaps the plate at {p[0]:.1f}s: a medallion must not cover a real image')
        for s_ in E._SIEGE:
            if m[1] + .3 < s_['t1'] and s_['t0'] + .3 < m[2] and (min(m[2], s_['t1']) - max(m[1], s_['t0'])) > .6: warns.append(f'medallion at {m[1]:.1f}s is hidden by the close-up at {s_["t0"]:.1f}s')
    P2 = sorted(E._PLATES, key=lambda p: p[0])
    for x, y in zip(P2, P2[1:]):
        if y[0] < x[1]: warns.append(f'plates overlap at {y[0]:.1f}s')
    for m in E._MED:
        if m[2] - m[1] < 2: warns.append(f'medallion at {m[1]:.1f}s shows for only {m[2] - m[1]:.1f}s (min ~2.5s)')
    B = E._B
    for k in E._KEYS:
        if k[3] > (B[1] - B[0]) * 1.01: warns.append(f'camera at {k[0]:.1f}s wider ({k[3]}) than the map ({B[1] - B[0]:.0f} deg)')
        if k[3] < 2.5: warns.append(f'camera at {k[0]:.1f}s is {k[3]} deg wide: very close; use a SIEGE close-up instead')
    if len(E._CH) == 0 and END > 150: warns.append('long video with no CHAPTERS: add chapter cards every 1-3 minutes')
    if len(E._SIEGE) == 0 and END > 60: warns.append('no SIEGES close-ups: rule = cut to a tactical close-up when narration is at a city, siege or camp')
    R = E._R; print(f'map {B} K={R["K"]} detail atlases {len(R["DETAILS"])}; {len(ev)} visual events, {dens:.0f}/min; {END:.0f}s')
    return report(errs, warns)


def report(errs, warns):
    for w in warns: print('WARN ', w)
    for e in errs: print('ERROR', e)
    print(f'{len(errs)} error(s), {len(warns)} warning(s)')
    if errs: sys.exit(1)


def ebur(path, extra=''):
    out = subprocess.run(['ffmpeg', '-nostats', '-i', path, '-af', 'ebur128=peak=true' + extra, '-f', 'null', '-'], capture_output=True, text=True).stderr
    I = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', out)[-1]); tp = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', out)
    return I, (float(tp[-1]) if tp else None)


def audio(slug):
    f = f'out/{slug}_1080p.mp4'
    I, tp = ebur(f); print(f'final mix: {I:.1f} LUFS integrated, true peak {tp} dBFS')
    errs = []
    if not -16 <= I <= -12: errs.append(f'mix loudness {I:.1f} LUFS: YouTube target is -14')
    if tp is not None and tp > -0.5: errs.append(f'true peak {tp} dBFS: clipping risk')
    # voice clarity: SFX bed must sit well under narration
    try:
        vo, _ = ebur(f'build/{slug}/narration.wav'); fx, _ = ebur(f'build/{slug}/sfx.wav')
        print(f'raw narration {vo:.1f} LUFS, raw SFX bed {fx:.1f} LUFS (mix applies -7 dB + ducking)')
        # narration is loudnormed to -14 LUFS in the mix; the SFX bed only gets -7 dB, so keep it 8 dB under
        if fx - 7 > -14 - 8: errs.append('SFX bed too loud versus narration: lower SFX gains (-12 dB typical, combat -6..-8)')
    except Exception: pass
    for e in errs: print('ERROR', e)
    print('audio OK' if not errs else 'fix audio before upload')


def describe(slug):
    J = json.load(open(f'episodes/{slug}.json'))
    os.environ.pop('STORY_CHECK', None); E = load(slug)
    print(J.get('title', slug)); print()
    print(J.get('description', '').strip()); print()
    if hasattr(E, '_CH') and E._CH:
        print('Chapters'); print('0:00 Introduction')
        CH = [c[1] for c in getattr(E, 'CHAPTERS', [])]
        for t, ti in zip(E._CH, CH): print(f'{int(t // 60)}:{int(t % 60):02d} {ti}')
        print()
    if J.get('sources'): print('Sources'); [print('-', s) for s in J['sources']]; print()
    cred = []; src = open(f'episodes/{slug}.py').read()
    for root, _, files in os.walk('assets/img'):
        if 'CREDITS.json' in files:
            for k, c in json.load(open(os.path.join(root, 'CREDITS.json'))).items():
                if k in src: cred.append(f"{k}: {c.get('title', '')} - {c.get('license', '')} {c.get('artist', '')[:60]} {c.get('page', '')}")
    if cred: print('Image credits (Wikimedia Commons)'); [print('-', c) for c in cred]; print()
    print('Borders, army routes and numbers are approximate; arrows are illustrative.')
    print('Religious figures are shown as light, without faces, out of respect.')


if __name__ == '__main__':
    cmd, slug = sys.argv[1], sys.argv[2]
    {'check': check, 'audio': audio, 'describe': describe}[cmd](slug)
