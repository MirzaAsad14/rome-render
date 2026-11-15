import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from atlas import *
from regions.caliphate_750 import *
which = sys.argv[1:] or ['main'] + [n for n, *_ in DETAILS]
if 'main' in which: build(Proj(*BOUNDS[:2], *BOUNDS[2:], K=K, c=C0), CFG, 'build/atlas_cal750')
for n, b, Kd in DETAILS:
    if n in which: build(Proj(*b, K=Kd, c=C0), dcfg(Kd), f'build/atlas_cal750{n}')
