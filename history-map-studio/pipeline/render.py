"""Parallel frame render -> chunk mp4s -> concat.
Usage: python3 render.py <slug> [workers] [--from S --to S] [--part i/n]
  --part i/n renders only chunk i of n (for splitting a long video across machines / Kaggle / Colab), output build/<slug>/part_i.mp4"""
import sys, os, subprocess, importlib, multiprocessing as mp
a = sys.argv[1:]; EP = a[0]
NW = int(a[1]) if len(a) > 1 and a[1].isdigit() else os.cpu_count()
def opt(k, d=None): return a[a.index(k) + 1] if k in a else d
BD = os.path.join('build', EP); os.makedirs(BD, exist_ok=True)
def work(args):
    i, f0, f1, tag = args
    ep = importlib.import_module('episodes.' + EP)
    out = os.path.join(BD, f'{tag}chunk_{i}.mp4')
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1920x1080', '-r', str(ep.FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        p.stdin.write(ep.render(f / ep.FPS).convert('RGB').tobytes())
        if (f - f0) % 240 == 0: print(f'worker {i}: frame {f - f0}/{f1 - f0}', flush=True)
    p.stdin.close(); p.wait(); return out
if __name__ == '__main__':
    ep = importlib.import_module('episodes.' + EP)
    N = int(ep.END * ep.FPS); F0, F1 = int(float(opt('--from', 0)) * ep.FPS), min(N, int(float(opt('--to', ep.END)) * ep.FPS))
    tag = ''
    if opt('--part'):
        i, n = map(int, opt('--part').split('/')); step = -(-N // n); F0, F1 = i * step, min(N, (i + 1) * step); tag = f'p{i}_'
    step = -(-(F1 - F0) // NW)
    chunks = [(i, F0 + i * step, min(F1, F0 + (i + 1) * step), tag) for i in range(NW) if F0 + i * step < F1]
    with mp.get_context('fork').Pool(len(chunks)) as pool: outs = pool.map(work, chunks)
    lst = os.path.join(BD, f'{tag}chunks.txt'); open(lst, 'w').write(''.join(f"file '{os.path.basename(o)}'\n" for o in outs))
    dst = os.path.join(BD, f'part_{opt("--part").split("/")[0]}.mp4' if opt('--part') else 'video.mp4')
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', dst], check=True)
    for o in outs: os.remove(o)
    print('video ok', F1 - F0, 'frames ->', dst)
