import sys, itertools; sys.path.insert(0, '/mnt/user-data/outputs')
from independent_check import *
# Bravyi et al. Table 5 (rounds 1..7 = CNOT layers): X L-edges A_s, X R-edges B_t, Z L-edges B_t^T, Z R-edges A_s^T
BRAVYI = {'XL': [6, 2, 7], 'XR': [4, 3, 5], 'ZL': [3, 4, 5], 'ZR': [1, 6, 2]}
TABLE_I = {'XL': [1, 2, 7], 'XR': [4, 3, 5], 'ZL': [5, 3, 4], 'ZR': [6, 7, 1]}
codes = bb_codes()
for name in ['[[72,12,6]]', '[[144,12,12]]']:
    verify(codes[name], ti_schedule(codes[name], BRAVYI), f'Bravyi Table 5 on {name}')

def orient(S):
    oL = [[int(S['XL'][s] < S['ZL'][t]) for t in range(3)] for s in range(3)]
    oR = [[int(S['XR'][t] < S['ZR'][s]) for t in range(3)] for s in range(3)]
    return oL, oR
print('Bravyi orientations (o_L, o_R):', orient(BRAVYI))
print('Table I orientations:', orient(TABLE_I))

def transforms(S, D=7):
    """all images under label perms, layer reversal, X/Z duality, block swap"""
    out = set()
    for rev in (False, True):
        for dual in (False, True):
            for swap in (False, True):
                T = {k: list(v) for k, v in S.items()}
                if rev: T = {k: [D + 1 - i for i in v] for k, v in T.items()}
                if dual: T = {'XL': T['ZR'], 'ZR': T['XL'], 'XR': T['ZL'], 'ZL': T['XR']}
                if swap: T = {'XL': T['XR'], 'XR': T['XL'], 'ZL': T['ZR'], 'ZR': T['ZL']}
                for sg in itertools.permutations(range(3)):
                    for tg in itertools.permutations(range(3)):
                        U = {'XL': tuple(T['XL'][sg[s]] for s in range(3)), 'ZR': tuple(T['ZR'][sg[s]] for s in range(3)),
                             'XR': tuple(T['XR'][tg[t]] for t in range(3)), 'ZL': tuple(T['ZL'][tg[t]] for t in range(3))}
                        out.add((U['XL'], U['XR'], U['ZL'], U['ZR']))
    return out
orb = transforms(BRAVYI)
key = (tuple(TABLE_I['XL']), tuple(TABLE_I['XR']), tuple(TABLE_I['ZL']), tuple(TABLE_I['ZR']))
print('Table I in the symmetry orbit of Bravyi Table 5:', key in orb, ' (orbit size', len(orb), ')')

# count all TI proper depth-7 schedules and their orbits under the same group
all_sched = []
for X in itertools.permutations(range(1, 8), 6):
    XL, XR = X[:3], X[3:]
    for Z in itertools.permutations(range(1, 8), 6):
        ZL, ZR = Z[:3], Z[3:]
        if set(XL) & set(ZL) or set(XR) & set(ZR): continue
        if all((XL[s] < ZL[t]) == (XR[t] < ZR[s]) for s in range(3) for t in range(3)):
            all_sched.append((XL, XR, ZL, ZR))
seen = set(); orbits = []
for S in all_sched:
    if S in seen: continue
    o = transforms({'XL': list(S[0]), 'XR': list(S[1]), 'ZL': list(S[2]), 'ZR': list(S[3])})
    seen |= o; orbits.append((S, len(o)))
print(f'translation-invariant proper depth-7 schedules: {len(all_sched)}; orbits under label perms x reversal x duality x block swap: {len(orbits)}')
for S, sz in orbits:
    d = {'XL': list(S[0]), 'XR': list(S[1]), 'ZL': list(S[2]), 'ZR': list(S[3])}
    oL, oR = orient(d)
    nx = sum(map(sum, oL))
    print(f'   rep XL={S[0]} XR={S[1]} ZL={S[2]} ZR={S[3]}  orbit size {sz}  X-first corners per X-check on L: {nx}',
          '  <- Table I' if key in transforms(d) else ('  <- Bravyi' if S in orb else ''))
