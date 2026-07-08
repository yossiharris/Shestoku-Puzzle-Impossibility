"""Shared: integer profile system feasibility (Theorem 2, integer form), exact via CP-SAT."""
import numpy as np
from itertools import combinations
from ortools.sat.python import cp_model
from digitdp import A, T as Tcount

Sd_at = np.load("results/Sd_at.npy")
Ns = np.arange(1, Sd_at.shape[1] + 1)
sd_all = np.maximum(0, Sd_at - 2 * Ns)

def ip_status(N, timeout=20):
    """Returns True (feasible), False (INFEASIBLE, exact), or None (unknown)."""
    H = [d for d in range(10) if sd_all[d, N-1] > 0]
    if not H: return True
    subs = [frozenset(c) for k in range(len(H)+1) for c in combinations(H, k)]
    m7 = 7 * N
    mdl = cp_model.CpModel()
    y = {T2: mdl.NewIntVar(0, N, "") for T2 in subs}
    mdl.Add(sum(y.values()) == N)
    for d in H:
        mdl.Add(sum(y[T2] for T2 in subs if d in T2) >= int(sd_all[d, N-1]))
    for k in range(1, min(4, len(H)) + 1):
        for c in combinations(H, k):
            D = frozenset(c); mk = sum(1 << dd for dd in D)
            sup = sum(y[T2] for T2 in subs if D <= T2)
            mdl.Add(3 * sup <= Tcount(mk, m7))
            mdl.Add(4 * sup <= A(mk, m7))
    s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = timeout
    st = s.Solve(mdl)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE): return True
    return False if st == cp_model.INFEASIBLE else None
