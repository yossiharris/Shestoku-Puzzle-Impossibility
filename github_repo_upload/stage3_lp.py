"""Stage 3: LP relaxation of the saturation system (Theorem 2) on the stage-2 survivors."""
import numpy as np, json
from scipy.optimize import linprog
from itertools import combinations

Sd_at = np.load("results/Sd_at.npy"); NMAX = Sd_at.shape[1]; M = 7*NMAX
dm = np.zeros(M+1, dtype=np.int16); lo = 1
while lo <= M:
    hi = min(M, lo*10-1); r = np.arange(lo, hi+1)
    dm[lo:hi+1] = dm[r//10] | (1 << (r % 10)).astype(np.int16); lo *= 10
cum = {}
def T_of(D, m):
    mk = sum(1 << d for d in D)
    if ('T', mk) not in cum:
        cum[('T', mk)] = np.cumsum(((dm[1:M+1] & mk) == mk).astype(np.int64))
    return int(cum[('T', mk)][m-1])
def Z_of(D, m):
    mk = sum(1 << d for d in D)
    if ('Z', mk) not in cum:
        cum[('Z', mk)] = np.cumsum(((dm[1:M+1] & mk) == 0).astype(np.int64))
    return int(cum[('Z', mk)][m-1])
surv = json.load(open("results/stage2.json"))["survivors"]
Ns = [n for a, b in surv for n in range(a, b+1)]
Nsarr = np.arange(1, NMAX+1)
sd_all = np.maximum(0, Sd_at - 2*Nsarr)
cache = {}
def lp_feasible(N):
    H = tuple(d for d in range(10) if sd_all[d, N-1] > 0)
    if not H: return True
    if H not in cache:
        subs = []
        for k in range(0, len(H)+1):
            for c in combinations(H, k): subs.append(frozenset(c))
        rows_cov = {d: np.array([1.0 if d in S_ else 0.0 for S_ in subs]) for d in H}
        Dlist = [frozenset(c) for k in (1,2,3) if k <= len(H) for c in combinations(H, k)]
        rows_sup = {D: np.array([1.0 if D <= S_ else 0.0 for S_ in subs]) for D in Dlist}
        cache[H] = (subs, rows_cov, Dlist, rows_sup)
    subs, rows_cov, Dlist, rows_sup = cache[H]
    m = 7*N; A_ub = []; b_ub = []
    for d in H:
        A_ub.append(-rows_cov[d]); b_ub.append(-float(sd_all[d, N-1]))
    for D in Dlist:
        A_ub.append(3.0*rows_sup[D]); b_ub.append(float(T_of(D, m)))
        A_ub.append(4.0*rows_sup[D]); b_ub.append(float(Z_of(D, m)))
    res = linprog(c=np.zeros(len(subs)), A_ub=np.vstack(A_ub), b_ub=np.array(b_ub),
                  A_eq=np.ones((1, len(subs))), b_eq=[float(N)],
                  bounds=[(0, None)]*len(subs), method="highs")
    return res.status == 0
alive, dead = [], []
for N in Ns:
    (alive if lp_feasible(N) else dead).append(N)
def iv(l):
    out = []
    for n in l:
        if out and out[-1][1] == n-1: out[-1][1] = n
        else: out.append([n, n])
    return out
json.dump({"lp_kills": iv(dead), "survivors": iv(alive)}, open("results/stage3.json", "w"), indent=1)
EXPECTED_KILLS = [[67,68],[996,1030],[1057,1299],[1594,1605]]
EXPECTED_SURV  = [[1,2],[6,20],[69,182],[1300,1593]]
assert iv(dead) == EXPECTED_KILLS, iv(dead)
assert iv(alive) == EXPECTED_SURV, iv(alive)
print("STAGE 3 PASS: LP-relaxation kills and survivors match the paper")
