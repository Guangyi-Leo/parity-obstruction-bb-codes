import sys, time; sys.path.insert(0, '.')
from sigma_struct import solve_typed
S = {'XL': (3,4,1,2,6,5), 'ZL': (3,4,1,2,6,5), 'XR': (2,1,6,5,4,3), 'ZR': (2,1,6,5,4,3)}
q = int(sys.argv[1]); t0 = time.time(); ok = []
for b in range(q):
    r = solve_typed(q, b, fixed_sigma=S)
    ok.append(bool(r))
    print(f'q={q} b={b}: {"SAT" if r else "UNSAT"}  [{time.time()-t0:.0f}s]', flush=True)
print(f'q={q} block-dependent universal sigma A: {sum(ok)}/{q} SAT')
