"""Stage 2: procedural score. Dark drone + wind + taiko-style hits on story beats.
Usage: python3 music.py <duration> <hit_times_csv> out.wav
v2.11: computed in time chunks (same sound, ~10x less RAM: a 23 min score no longer needs >8 GB)."""
import sys, numpy as np, wave
dur = float(sys.argv[1]); hits = [float(x) for x in sys.argv[2].split(',') if x]; out = sys.argv[3]
sr = 48000; N = int(dur * sr); rng = np.random.default_rng(4)
mus = np.zeros(N)
CH = sr * 30
for a in range(0, N, CH):
    t = np.arange(a, min(N, a + CH)) / sr; m = np.zeros_like(t)
    for f, amp, lfo in ((36.7, .30, .07), (73.4, .22, .05), (110.0, .12, .09), (146.8, .07, .11), (174.6, .05, .13), (220.0, .03, .06)):
        detune = 1 + 0.002 * np.sin(2 * np.pi * 0.03 * t)
        m += amp * np.sin(2 * np.pi * f * detune * t) * (0.7 + 0.3 * np.sin(2 * np.pi * lfo * t + f))
    # low string swell: slowly rising fifth in the second half
    sw = np.clip((t - dur * 0.55) / (dur * 0.3), 0, 1) * np.clip((dur - 6 - t) / 6, 0, 1)
    m += 0.10 * sw * np.sin(2 * np.pi * 164.8 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.2 * t))
    mus[a:a + len(t)] = m
# wind: filtered noise (moving average of k samples, same alignment as np.convolve(..., 'same'))
n = rng.normal(0, 1, N); k = 400
c = np.concatenate([[0.0], np.cumsum(n)]); del n
i = np.arange(N); s0 = np.clip(i - (k - 1) + (k - 1) // 2, 0, N); s1 = np.clip(i + (k - 1) // 2 + 1, 0, N)
wind = (c[s1] - c[s0]) / k; del c, i, s0, s1
for a in range(0, N, CH):
    t = np.arange(a, min(N, a + CH)) / sr
    wind[a:a + len(t)] *= 0.9 + 0.6 * np.sin(2 * np.pi * 0.07 * t) ** 2
mus += 2.2 * wind; del wind
for h in hits:   # each boom decays to < 1e-7 within 6 s
    a = max(0, int(np.ceil(h * sr))); b = min(N, int(h * sr) + 6 * sr)
    if a >= b: continue
    tt = np.arange(a, b) / sr - h
    mus[a:b] += 0.9 * np.sin(2 * np.pi * (48 + 40 * np.exp(-tt * 18)) * tt) * np.exp(-tt * 3.2)
for a in range(0, N, CH):
    t = np.arange(a, min(N, a + CH)) / sr
    mus[a:a + len(t)] *= np.clip(t / 2.5, 0, 1) * np.clip((dur - t) / 3.5, 0, 1)
mus /= np.max(np.abs(mus)) * 1.15
pcm = (mus * 32767).astype(np.int16); del mus
st = np.stack([pcm, np.roll(pcm, 480)], 1)
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(st.tobytes())
print('music ok', dur)
