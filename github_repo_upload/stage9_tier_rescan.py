"""Stage 9: tier-augmented integer profile system (Lemma 'tier bound', |D|<=5) over the
pre-tier candidate set. Expected: exactly {69, 1514, 1515, 1516, 1517} newly infeasible,
yielding the final candidate set C = {1,2} u [6,20] u [70,182] u [1387,1513] (257 values).
Runtime: ~10-15 minutes."""
import json, time
from itertools import combinations
from ortools.sat.python import cp_model
import numpy as np

Sd_at = np.load("results/Sd_at.npy")
def dmask(x):
    m = 0
    while x: m |= 1 << (x % 10); x //= 10
    return m

def check(N, maxD=5, timeout=60):
    M = 7*N
    s = [max(0, int(Sd_at[d, N-1]) - 2*N) for d in range(10)]
    H = [d for d in range(10) if s[d] > 0]
    if not H: return True
    Hm = sum(1 << d for d in H)
    K = {}
    for x in range(1, M+1):
        m2 = dmask(x) & Hm
        K[m2] = K.get(m2, 0) + 1
    subs = [frozenset(c) for k in range(len(H)+1) for c in combinations(H, k)]
    def cnt(pred):
        return sum(v for m2, v in K.items() if pred(m2))
    mdl = cp_model.CpModel()
    y = {S: mdl.NewIntVar(0, N, "") for S in subs}
    mdl.Add(sum(y.values()) == N)
    for d in H:
        mdl.Add(sum(y[S] for S in subs if d in S) >= s[d])
    for k in range(1, min(4, len(H)) + 1):
        for c in combinations(H, k):
            D = frozenset(c); mk = sum(1 << d for d in D)
            sup = sum(y[S] for S in subs if D <= S)
            mdl.Add(3 * sup <= cnt(lambda m2: (m2 & mk) == mk))
            mdl.Add(4 * sup <= cnt(lambda m2: (m2 & mk) == 0))
    for k in range(2, min(maxD, len(H)) + 1):
        for c in combinations(H, k):
            D = frozenset(c); mk = sum(1 << d for d in D)
            for j in range(2, k + 1):
                cap = cnt(lambda m2: bin(m2 & mk).count('1') >= j) // 3
                mdl.Add(sum(y[S] for S in subs if len(S & D) >= j) <= cap)
    slv = cp_model.CpSolver(); slv.parameters.max_time_in_seconds = timeout
    st = slv.Solve(mdl)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE): return True
    return False if st == cp_model.INFEASIBLE else None

if __name__ == "__main__":
    prev = [n for a, b in [(1,2),(6,20),(69,182),(1387,1517)] for n in range(a, b+1)]
    dead, alive, unk = [], [], []
    for N in prev:
        r = check(N)
        (alive if r is True else dead if r is False else unk).append(N)
    assert not unk, unk
    assert dead == [69, 1514, 1515, 1516, 1517], dead
    def iv(l):
        out = []
        for n in l:
            if out and out[-1][1] == n-1: out[-1][1] = n
            else: out.append([n, n])
        return out
    assert iv(alive) == [[1,2],[6,20],[70,182],[1387,1513]] and len(alive) == 257
    json.dump({"tier_kills": dead, "final_candidates": iv(alive)}, open("results/stage9.json", "w"))
    print("STAGE 9 PASS: tier bound kills exactly {69, 1514..1517}; final C has 257 members")
