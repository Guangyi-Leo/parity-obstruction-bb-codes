import sys, time
sys.path.insert(0, '.')
from struct_lib import solve_with_typing
from keys16 import representatives
q = int(sys.argv[1]); h = q // 2; des = ((0, 0), (1, 1))
hyps = {
  'c mod 2, floor(8c/q)':   lambda c: (c % 2, (8 * c) // q),
  'c mod 4, floor(4c/q)':   lambda c: (c % 4, (4 * c) // q),
  'c mod 4, floor(8c/q)':   lambda c: (c % 4, (8 * c) // q),
  'c mod 8, floor(4c/q)':   lambda c: (c % 8, (4 * c) // q),
}
reps = representatives(q)
for name, typ in hyps.items():
    t0 = time.time(); n = 0
    for key, (a3, b3) in sorted(reps.items()):
        n += bool(solve_with_typing(q, (0, h, a3), (0, h, b3), des, typ))
    print(f'q={q} T depends only on ({name}): {n}/{len(reps)} keys SAT  [{time.time()-t0:.0f}s]', flush=True)
