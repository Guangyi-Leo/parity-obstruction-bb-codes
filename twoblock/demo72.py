import sys; sys.path.insert(0, '/mnt/user-data/outputs'); sys.path.insert(0, '.')
from independent_check import Group, TwoBlockCode, twisted_schedule, verify, solve_depth
from pullback_demo import class_schedule
G = Group((6, 6))
A = [(0,0),(4,3),(5,3)]; B = [(0,0),(1,5),(4,3)]
code = TwoBlockCode(G, A, B)
print('overlap multiplicities:', sorted(code.overlap_multiplicities().values(), reverse=True))
eps = lambda g: g[1] % 2
alpha = tuple(eps(a) for a in A); beta = tuple(eps(b) for b in B)
des = ((0, 2), (1, 0))   # a1+b3 = a2+b1
print('key:', alpha, beta, 'designated', des, 'dbar =', (alpha[1]-alpha[0]) % 2)
T = class_schedule(2, alpha, beta, des)
for c in (0, 1):
    print(f'  class {c}: ' + '  '.join(f'{k}={[T[(c,k,l)] for l in range(3)]}' for k in ('XL','XR','ZL','ZR')))
pi = twisted_schedule(code, eps, T)
verify(code, pi, '[[72,8,6]] C1 code, q=2 template pulled back along y mod 2')
