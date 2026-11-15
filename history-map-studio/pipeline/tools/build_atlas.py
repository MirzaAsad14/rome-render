import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from atlas import *
from regions.rus_1238 import *
P = Proj(*BOUNDS[:2], *BOUNDS[2:], K=1300); build(P, CFG, 'build/atlas_rus1238')
