import sys, ast; sys.path.insert(0, '/mnt/user-data/outputs')
from independent_check import Group, TwoBlockCode, solve_depth, verify
name, orders, A, B = sys.argv[1], ast.literal_eval(sys.argv[2]), ast.literal_eval(sys.argv[3]), ast.literal_eval(sys.argv[4])
G = Group(orders); code = TwoBlockCode(G, A, B)
print(f'{name}: overlap multiplicities {sorted(code.overlap_multiplicities().values(), reverse=True)[:3]}', flush=True)
r, pi = solve_depth(code, 6)
if pi: verify(code, pi, '   found depth-6')
