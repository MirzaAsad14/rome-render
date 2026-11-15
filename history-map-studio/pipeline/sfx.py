"""Mix a sound-effects bed from the user's SFX library (assets/sfx/<name>.*).
Episode module defines SFX = [(time_s, name, gain_db, max_len_s or None), ...]."""
import sys, os, glob, subprocess, importlib
import numpy as np
SR = 48000
ROOT = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ROOT)
def load(name):
    f = glob.glob(os.path.join(ROOT, 'assets/sfx', name + '.*'))[0]
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    a = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
    on = np.nonzero(np.abs(a).max(1) > 0.01 * (np.abs(a).max() or 1))[0]   # trim leading silence so cues land on time
    return a[max(0, on[0] - 240):] if len(on) else a
def main(ep, out):
    e = importlib.import_module('episodes.' + ep)
    n = int((e.END + 1) * SR); bed = np.zeros((n, 2), np.float32); cache = {}
    for ev in e.SFX:
        t, name, db = ev[:3]; ml = ev[3] if len(ev) > 3 else None
        if name not in cache: cache[name] = load(name)
        a = cache[name]
        if ml: a = a[:int(ml * SR)].copy(); f = min(len(a), int(.25 * SR)); a[-f:] *= np.linspace(1, 0, f)[:, None]
        pk = np.abs(a).max() or 1; a = a / pk * 10 ** (db / 20)
        i = int(t * SR); j = min(n, i + len(a)); bed[i:j] += a[:j - i]
    bed = np.tanh(bed * 1.1) / 1.1
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', out], input=bed.tobytes())
    print('sfx events', len(e.SFX))
if __name__ == '__main__': main(sys.argv[1], sys.argv[2])
