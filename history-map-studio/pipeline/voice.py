"""Narration in ONE continuous pass with word-level timings (no inserted pauses).

usage: python voice.py episodes/<ep>.json            -> build/<slug>/narration.wav + build/<slug>/words.json

Providers (episode json "provider", or env VOICE_PROVIDER):
  edge        free Microsoft Edge neural voices (default), needs no key
  elevenlabs  premium; env ELEVENLABS_API_KEY, json "eleven_voice_id" (default: Adam-like narrator id below)
  heygen      premium; env HEYGEN_API_KEY, json "heygen_voice_id", "heygen_model" (default heygen-voice-1-turbo-free)

Pronunciation of names:
  "say": {"Muawiya": "Mu'aawiya", ...}   respelling used by edge / elevenlabs (spoken text only; captions and
                                         words.json keep the real spelling, word indices stay the same)
  "ipa": {"Muawiya": "/muˈʕaːwija/"}     heygen pronunciation_dictionary (IPA between slashes)
Logo sting gap:
  "sting_after": "last words of the hook", "sting_gap": 3.2   -> the one deliberate silence, where the channel logo plays
Keys are read from the environment only. Never write a key into a file.
"""
import asyncio, base64, json, os, re, subprocess, sys, urllib.request

EP = json.load(open(sys.argv[1]))
PROV = os.environ.get('VOICE_PROVIDER', EP.get('provider', 'edge')).lower()
LEAD, TAIL = EP.get('lead_in', 2.1), EP.get('tail', 4.5)   # 2.1 s: the intro sheet lands (1.6 s) before the first word
SLUG = os.path.splitext(os.path.basename(sys.argv[1]))[0]
BD = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build', SLUG); os.makedirs(BD, exist_ok=True)

TOK = re.compile(r"\S+")
def norm(s): return re.sub(r"[^\w'-]", '', s).strip("'-").lower()

def display_tokens(text):
    return [m.group(0) for m in TOK.finditer(text) if re.search(r'\w', m.group(0))]

def spoken_text(text, say):
    if not say: return text
    def sub(m):
        w = m.group(0); core = re.sub(r"^[^\w]+|[^\w]+$", '', w)
        if core in say: return w.replace(core, say[core])
        return w
    return TOK.sub(sub, text)

def words_from_chars(spoken, starts, ends):
    """char-level alignment (one start/end per char of `spoken`) -> word times in order"""
    out = []
    for m in TOK.finditer(spoken):
        if not re.search(r'\w', m.group(0)): continue
        idx = [i for i in range(m.start(), m.end()) if i < len(starts) and spoken[i].strip()]
        if not idx: continue
        out.append((min(starts[i] for i in idx), max(ends[i] for i in idx)))
    return out

def _align(disp, times, texts):
    """map timed boundary texts onto display tokens with difflib on normalised forms; gaps are interpolated"""
    import difflib
    say = EP.get('say') or {}
    def key(tok):
        core = re.sub(r"^[^\w]+|[^\w]+$", '', tok)
        return norm(say.get(core, core).split()[0]) if core else ''
    A = [key(d) for d in disp]; B = [norm(x.split()[0]) if x.strip() else '' for x in texts]
    T = [None] * len(disp)
    for blk in difflib.SequenceMatcher(None, A, B, autojunk=False).get_matching_blocks():
        for k in range(blk.size): T[blk.a + k] = times[blk.b + k]
    known = [i for i, x in enumerate(T) if x]
    print(f'aligned {len(known)}/{len(disp)} words exactly', file=sys.stderr)
    for i in range(len(T)):
        if T[i]: continue
        lo = max([k for k in known if k < i], default=None); hi = min([k for k in known if k > i], default=None)
        if lo is None: T[i] = T[hi]; continue
        if hi is None: T[i] = T[lo]; continue
        a, b = T[lo][1], T[hi][0]; f0 = (i - lo) / (hi - lo); f1 = (i - lo + 1) / (hi - lo)
        T[i] = (a + (b - a) * f0, a + (b - a) * f1)
    return T

def finish(audio_path, times, texts=None):
    disp = display_tokens(EP['text'])
    if texts and len(texts) == len(times): times = _align(disp, times, texts)
    elif len(times) != len(disp):
        print(f'WARNING: {len(times)} timed words vs {len(disp)} script words; aligning by order', file=sys.stderr)
    n = min(len(times), len(disp))
    words = [dict(w=disp[i].strip('.,;:!?"'), t0=round(times[i][0] + LEAD, 3), t1=round(times[i][1] + LEAD, 3), i=i) for i in range(n)]
    dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', audio_path]))
    sting_t = None
    if EP.get('sting_after'):   # the ONE deliberate gap: after the hook, the channel logo sting plays (same single TTS pass, split once)
        ph = [norm(x) for x in EP['sting_after'].split() if norm(x)]; keys = [norm(w['w']) for w in words]
        hit = [i for i in range(len(keys) - len(ph) + 1) if keys[i:i + len(ph)] == ph]
        if not hit: sys.exit(f"sting_after phrase not found in the text: {EP['sting_after']!r}")
        i = hit[0] + len(ph) - 1; gap = float(EP.get('sting_gap', 3.2))
        nxt = words[i + 1]['t0'] if i + 1 < len(words) else words[i]['t1'] + .3
        tc = (words[i]['t1'] + nxt) / 2 - LEAD; sting_t = round(words[i]['t1'] + .15, 3)
        cut = os.path.join(BD, 'vo_gap.wav')
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', audio_path, '-filter_complex',
                        f'[0]atrim=0:{tc:.3f},asetpts=N/SR/TB,apad=pad_dur={gap}[a];[0]atrim={tc:.3f},asetpts=N/SR/TB[b];[a][b]concat=n=2:v=0:a=1',
                        '-ar', '48000', cut], check=True)
        for w in words[i + 1:]: w['t0'] = round(w['t0'] + gap, 3); w['t1'] = round(w['t1'] + gap, 3)
        audio_path = cut; dur += gap
    total = LEAD + dur + TAIL; ms = int(LEAD * 1000)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', audio_path, '-af', f'adelay={ms}|{ms},apad=whole_dur={total}',
                    '-ar', '48000', '-ac', '2', os.path.join(BD, 'narration.wav')], check=True)
    json.dump(dict(total=total, voice_end=LEAD + dur, provider=PROV, words=words, sting_t=sting_t, sting_gap=EP.get('sting_gap', 3.2) if sting_t else None), open(os.path.join(BD, 'words.json'), 'w'), indent=0)
    print(f'{PROV}: voice {dur:.2f}s  words {len(words)}  wpm {len(words) / dur * 60:.0f}')

# ---------------- edge (free) ----------------
async def edge():
    import edge_tts
    c = edge_tts.Communicate(spoken_text(EP['text'], EP.get('say')), EP.get('voice', 'en-GB-RyanNeural'),
                             rate=EP.get('rate', '-2%'), pitch=EP.get('pitch', '-4Hz'), boundary='WordBoundary')
    audio = bytearray(); times = []; texts = []
    async for ch in c.stream():
        if ch['type'] == 'audio': audio += ch['data']
        elif ch['type'] == 'WordBoundary':
            t0 = ch['offset'] / 1e7; times.append((t0, t0 + ch['duration'] / 1e7)); texts.append(ch.get('text', ''))
    open(os.path.join(BD, 'vo.mp3'), 'wb').write(audio)
    finish(os.path.join(BD, 'vo.mp3'), times, texts)

def post(url, headers, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={**headers, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=600) as r: return json.loads(r.read())

# ---------------- ElevenLabs (premium) ----------------
def elevenlabs():
    key = os.environ.get('ELEVENLABS_API_KEY') or sys.exit('Set ELEVENLABS_API_KEY in your environment (never in a file).')
    vid = EP.get('eleven_voice_id', 'pNInz6obpgDQGcFmaJgB')
    spoken = spoken_text(EP['text'], EP.get('say'))
    r = post(f'https://api.elevenlabs.io/v1/text-to-speech/{vid}/with-timestamps?output_format=mp3_44100_192',
             {'xi-api-key': key}, {'text': spoken, 'model_id': EP.get('eleven_model', 'eleven_multilingual_v2'),
                                   'voice_settings': EP.get('eleven_settings', {'stability': 0.55, 'similarity_boost': 0.8, 'style': 0.25})})
    open(os.path.join(BD, 'vo.mp3'), 'wb').write(base64.b64decode(r['audio_base64']))
    al = r['alignment']
    finish(os.path.join(BD, 'vo.mp3'), words_from_chars(''.join(al['characters']), al['character_start_times_seconds'], al['character_end_times_seconds']))

# ---------------- HeyGen (premium) ----------------
def heygen():
    key = os.environ.get('HEYGEN_API_KEY') or sys.exit('Set HEYGEN_API_KEY in your environment (never in a file).')
    body = {'model': EP.get('heygen_model', 'heygen-voice-1-turbo-free'), 'voice_id': EP.get('heygen_voice_id', '83548de556df48ba8c09c42a57c51d85'),
            'text': EP['text'], 'language': EP.get('language', 'en'), 'with_timestamps': True}
    if EP.get('ipa') and body['model'] != 'heygen-voice-1-turbo-free': body['pronunciation_dictionary'] = EP['ipa']
    elif EP.get('say'): body['text'] = spoken_text(EP['text'], EP['say'])
    r = post('https://api.heygen.com/v3/models/audio/tts', {'X-Api-Key': key}, body)
    r = r.get('data', r)
    urllib.request.urlretrieve(r['audio_url'], os.path.join(BD, 'vo.wav'))
    ch = r['original_characters']
    finish(os.path.join(BD, 'vo.wav'), words_from_chars(''.join(c['text'] for c in ch), [c['start_time'] for c in ch], [c['end_time'] for c in ch]))

if __name__ == '__main__':
    {'edge': lambda: asyncio.run(edge()), 'elevenlabs': elevenlabs, 'heygen': heygen}[PROV]()
