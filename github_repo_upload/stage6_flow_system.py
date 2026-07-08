"""Stage 6: class-flow system feasibility on every member of the final candidate set C.
The paper asserts feasibility at all 262 candidates (no further exclusions)."""
import json
import numpy as np
from ortools.sat.python import cp_model

Sd_at = np.load("results/Sd_at.npy")
def dmask(x):
    m = 0
    while x: m |= 1 << (x % 10); x //= 10
    return m
def heavy(N):
    return [d for d in range(10) if Sd_at[d, N-1] - 2*N > 0]
def flow_feasible(N, Hp):
    Hm = sum(1 << d for d in Hp); M = 7*N
    K = {}
    for x in range(1, M+1):
        m2 = dmask(x) & Hm; K[m2] = K.get(m2, 0) + 1
    subm = []; mm = Hm
    while True:
        subm.append(mm)
        if mm == 0: break
        mm = (mm - 1) & Hm
    mdl = cp_model.CpModel()
    y = {T: mdl.NewIntVar(0, N, "") for T in subm}
    mdl.Add(sum(y.values()) == N)
    a = {}; b = {}
    for m2 in subm:
        for T in subm:
            if (m2 & T) == T: a[(m2, T)] = mdl.NewIntVar(0, 3*N, "")
            if (m2 & T) == 0: b[(m2, T)] = mdl.NewIntVar(0, 4*N, "")
    for m2 in subm:
        mdl.Add(sum(a.get((m2, T), 0) for T in subm) + sum(b.get((m2, T), 0) for T in subm) == K.get(m2, 0))
    for T in subm:
        mdl.Add(sum(a[(m2, T)] for m2 in subm if (m2 & T) == T) == 3*y[T])
        mdl.Add(sum(b[(m2, T)] for m2 in subm if (m2 & T) == 0) == 4*y[T])
        for d in Hp:
            if not (T >> d) & 1:
                mdl.Add(sum(b[(m2, T)] for m2 in subm if (m2 & T) == 0 and (m2 >> d) & 1) <= 2*y[T])
    s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = 20
    st = s.Solve(mdl)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE): return True
    return False if st == cp_model.INFEASIBLE else None

cands = [n for a2, b2 in json.load(open("results/stage4.json"))["final_candidates"] for n in range(a2, b2+1)]
infeasible, unknown = [], []
for N in cands:
    H = heavy(N)
    Hp = H if len(H) <= 5 else sorted(sorted(H, key=lambda d: -(Sd_at[d, N-1] - 2*N))[:5])
    r = flow_feasible(N, Hp)
    if r is False: infeasible.append(N)
    elif r is None: unknown.append(N)
json.dump({"checked": len(cands), "infeasible": infeasible, "unknown": unknown},
          open("results/stage6.json", "w"), indent=1)
assert not infeasible and not unknown, (infeasible, unknown)
print(f"STAGE 6 PASS: class-flow system feasible at all {len(cands)} candidates, as the paper states")
