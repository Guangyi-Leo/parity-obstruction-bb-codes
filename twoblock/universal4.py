import sys; sys.path.insert(0, '.')
from universal_sigma import joint
cands = {'A: L=(13)(24)(56), R=(12)(36)(45)': {'XL': (3,4,1,2,6,5), 'ZL': (3,4,1,2,6,5), 'XR': (2,1,6,5,4,3), 'ZR': (2,1,6,5,4,3)},
         'B: L=(14)(23)(56), R=(12)(35)(46)': {'XL': (4,3,2,1,6,5), 'ZL': (4,3,2,1,6,5), 'XR': (2,1,5,6,3,4), 'ZR': (2,1,5,6,3,4)}}
for q in [int(v) for v in sys.argv[1:]]:
    for name, S in cands.items():
        r = joint(q, list(range(q)), forced=S)
        print(f'q={q} {name}: {"SAT for all b" if r else "UNSAT"}', flush=True)
