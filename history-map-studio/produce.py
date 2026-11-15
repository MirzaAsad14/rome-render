#!/usr/bin/env python3
"""History Map Studio - one entry point.

  python produce.py voice                         choose narration voice (free Edge, or premium ElevenLabs / HeyGen + API key)
  python produce.py new "<title>" [--minutes N]   scaffold an episode from your title
  python produce.py auto [--minutes N]            no title? pick the best next topic automatically and scaffold it
  python produce.py check <slug>                  quality gate: cues, places, pacing, respect rule, pronunciation (must pass)
  python produce.py preview <slug> [N]            contact sheet of N stills -> pipeline/build/<slug>/sheet.jpg (LOOK at it)
  python produce.py build <slug>                  render the finished episode (voice -> music -> map render -> SFX -> mix -> audio QA)
  python produce.py part <slug> i/n               render only part i of n (split a long video over several machines / Kaggle / Colab)
  python produce.py join <slug> n                 join part_0..part_{n-1} and mix (after `part` runs)
  python produce.py places <name> ...             look up coordinates
  python produce.py images "<search>"             licence-safe images on Wikimedia Commons; get: python pipeline/tools/commons.py get ...
  python produce.py list                          show episodes and topic bank

The AI assistant (Claude / ChatGPT / Grok / Codex ...) writes the script and the scene file between `new|auto` and `build`,
following CLAUDE.md and workflow/WORKFLOW.md. API keys live only in .env on your own machine (never commit or share it).
"""
import json, os, re, shutil, subprocess, sys, getpass

HERE = os.path.dirname(os.path.abspath(__file__)); PIPE = os.path.join(HERE, 'pipeline'); ENV = os.path.join(HERE, '.env')
TOPICS = os.path.join(HERE, 'workflow', 'topics.json')

def slug(s): return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')[:40]

def load_env():
    env = dict(os.environ)
    if os.path.exists(ENV):
        for line in open(ENV):
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1); env.setdefault(k, v)
    return env

def voice():
    print('Narration voice:\n  1) Free  - Microsoft Edge neural (en-GB-RyanNeural, documentary narrator)\n'
          '  2) Premium - ElevenLabs (needs API key, https://elevenlabs.io/app/settings/api-keys)\n'
          '  3) Premium - HeyGen Voice (needs API key, https://platform.heygen.com/api-keys; Turbo Free model available)')
    c = input('Choose 1/2/3 [1]: ').strip() or '1'
    lines = [l for l in (open(ENV).read().splitlines() if os.path.exists(ENV) else []) if not l.startswith(('VOICE_PROVIDER=', 'ELEVENLABS_API_KEY=', 'HEYGEN_API_KEY='))]
    if c == '2':
        k = getpass.getpass('ElevenLabs API key (hidden): ').strip(); lines += ['VOICE_PROVIDER=elevenlabs', f'ELEVENLABS_API_KEY={k}']
        print('Optional: set "eleven_voice_id" in the episode json (default is a deep male narrator voice).')
    elif c == '3':
        k = getpass.getpass('HeyGen API key (hidden): ').strip(); lines += ['VOICE_PROVIDER=heygen', f'HEYGEN_API_KEY={k}']
        print('Optional: set "heygen_voice_id" / "heygen_model" in the episode json (default: public voice, heygen-voice-1-turbo-free).')
    else:
        lines += ['VOICE_PROVIDER=edge']
    open(ENV, 'w').write('\n'.join(lines) + '\n'); os.chmod(ENV, 0o600)
    print('Saved to .env (local only).')

def scaffold(title, minutes):
    s = slug(title); ep = os.path.join(PIPE, 'episodes', s + '.json')
    if os.path.exists(ep): print('exists:', ep); return s
    tpl = json.load(open(os.path.join(PIPE, 'templates', 'episode_template.json')))
    tpl.update(title=title, text='WRITE THE NARRATION HERE', say={}, ipa={}, target_minutes=minutes, target_words=int(minutes * 130))
    json.dump(tpl, open(ep, 'w'), indent=1, ensure_ascii=False)
    src = open(os.path.join(PIPE, 'templates', 'story_template.py')).read().replace("SLUG = 'my_episode'", f"SLUG = '{s}'")
    open(os.path.join(PIPE, 'episodes', s + '.py'), 'w').write(src)
    brief = f"""# {title}
Target: {minutes} min, about {int(minutes * 130)} words of narration (one continuous voice pass).
Follow CLAUDE.md -> workflow/WORKFLOW.md steps 2-6, rules in workflow/RULES.md, look in workflow/STYLE.md.
Files: episodes/{s}.json (script, say, ipa, sources) and episodes/{s}.py (STORYBOARD data; copied from templates/story_template.py;
see episodes/demo_chaldiran.py for a complete working example).
Order: script -> python pipeline/voice.py pipeline/episodes/{s}.json -> storyboard -> python produce.py check {s} (0 errors)
       -> python produce.py preview {s} (look, fix) -> python produce.py build {s}
"""
    open(os.path.join(PIPE, 'episodes', s + '.BRIEF.md'), 'w').write(brief)
    print(brief); return s

def auto(minutes):
    t = json.load(open(TOPICS))
    for x in t['topics']:
        if x.get('status') == 'todo':
            x['status'] = 'in_progress'; json.dump(t, open(TOPICS, 'w'), indent=1)
            print('AUTO topic:', x['title']); return scaffold(x['title'], minutes)
    sys.exit('topic bank empty: add topics to workflow/topics.json')

def build(s, extra=()):
    extra = list(extra)
    env = load_env()
    for k in ('HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy'): env.pop(k, None)
    j = json.load(open(os.path.join(PIPE, 'episodes', s + '.json')))
    if 'WRITE THE NARRATION' in j.get('text', ''): sys.exit('Write the narration first (episodes/%s.json).' % s)
    subprocess.run(['bash', 'make_video.sh', s] + extra, cwd=PIPE, env=env, check=True)
    print('Done ->', os.path.join(PIPE, 'out', s + '_1080p.mp4'))

def run(*cmd): subprocess.run([sys.executable] + list(cmd), cwd=PIPE, check=False)

def join(s, n):
    bd = os.path.join(PIPE, 'build', s)
    open(os.path.join(bd, 'parts.txt'), 'w').write(''.join(f"file 'part_{i}.mp4'\n" for i in range(n)))
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', os.path.join(bd, 'parts.txt'), '-c', 'copy', os.path.join(bd, 'video.mp4')], check=True)
    build(s, ['--skip-voice', '--skip-render'])

if __name__ == '__main__':
    a = sys.argv[1:]
    mins = float(a[a.index('--minutes') + 1]) if '--minutes' in a else 1.0
    if not a or a[0] in ('-h', '--help'): print(__doc__)
    elif a[0] == 'voice': voice()
    elif a[0] == 'new': scaffold(a[1], mins)
    elif a[0] == 'auto': auto(mins)
    elif a[0] == 'build': build(a[1], a[2:])
    elif a[0] == 'check': run('qa.py', 'check', a[1])
    elif a[0] == 'preview': run('preview2.py', a[1], '--sheet', a[2] if len(a) > 2 else '12')
    elif a[0] == 'part': run('render.py', a[1], '--part', a[2])
    elif a[0] == 'join': join(a[1], int(a[2]))
    elif a[0] == 'places': run('places.py', *a[1:])
    elif a[0] == 'images': run('tools/commons.py', 'search', ' '.join(a[1:]))
    elif a[0] == 'list':
        print('episodes:', sorted(f[:-5] for f in os.listdir(os.path.join(PIPE, 'episodes')) if f.endswith('.json')))
        for x in json.load(open(TOPICS))['topics']: print(f"  [{x['status']}] {x['title']}")
    else: print(__doc__)
