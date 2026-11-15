"""Stage 2: procedural score. Dark drone + wind + taiko-style hits on story beats.
Usage: python3 music.py <duration> <hit_times_csv> out.wav"""
import sys, numpy as np, wave
dur = float(sys.argv[1]); hits = [float(x) for x in sys.argv[2].split(',') if x]; out = sys.argv[3]
sr = 48000; t = np.arange(int(dur * sr)) / sr; rng = np.random.default_rng(4)
def env(a, d): return np.clip(t / a, 0, 1) * np.clip((dur - t) / d, 0, 1)
mus = np.zeros_like(t)
for f, amp, lfo in ((36.7, .30, .07), (73.4, .22, .05), (110.0, .12, .09), (146.8, .07, .11), (174.6, .05, .13), (220.0, .03, .06)):
    detune = 1 + 0.002 * np.sin(2 * np.pi * 0.03 * t)
    mus += amp * np.sin(2 * np.pi * f * detune * t) * (0.7 + 0.3 * np.sin(2 * np.pi * lfo * t + f))
# low string swell: slowly rising fifth in the second half
sw = np.clip((t - dur * 0.55) / (dur * 0.3), 0, 1) * np.clip((dur - 6 - t) / 6, 0, 1)
mus += 0.10 * sw * np.sin(2 * np.pi * 164.8 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.2 * t))
# wind: filtered noise
n = rng.normal(0, 1, len(t)); k = 400; wind = np.convolve(n, np.ones(k) / k, 'same')
wind *= 0.9 + 0.6 * np.sin(2 * np.pi * 0.07 * t) ** 2
mus += 2.2 * wind
for h in hits:
    tt = t - h; m = tt >= 0
    boom = np.zeros_like(t)
    boom[m] = np.sin(2 * np.pi * (48 + 40 * np.exp(-tt[m] * 18)) * tt[m]) * np.exp(-tt[m] * 3.2)
    noise = rng.normal(0, 1, len(t)) * 0; 
    mus += 0.9 * boom
mus *= env(2.5, 3.5)
mus /= np.max(np.abs(mus)) * 1.15
st = np.stack([mus, np.roll(mus, 480)], 1)
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((st * 32767).astype(np.int16).tobytes())
print('music ok', dur)
