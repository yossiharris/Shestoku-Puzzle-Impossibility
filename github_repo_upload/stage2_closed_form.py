"""Stage 2: closed-form k-set saturation bounds (Corollary 2 of the paper) on all
digit-bound-passing N. Regenerates the closed-form exclusion intervals."""
import numpy as np, json
from itertools import combinations

Sd_at = np.load("results/Sd_at.npy"); NMAX = Sd_at.shape[1]; M = 7 * NMAX
dm = np.zeros(M + 1, dtype=np.int16); lo = 1
while lo <= M:
    hi = min(M, lo * 10 - 1); r = np.arange(lo, hi + 1)
    dm[lo:hi + 1] = dm[r // 10] | (1 << (r % 10)).astype(np.int16); lo *= 10
Ns = np.arange(1, NMAX + 1)
viol = (Sd_at > 3 * Ns).any(axis=0)
passing = Ns[~viol]; Mp = 7 * passing
sd_p = np.maximum(0, Sd_at - 2 * Ns)[:, passing - 1]
killed = np.zeros(len(passing), dtype=bool)
for k in (2, 3, 4):
    for c in combinations(range(10), k):
        L = sd_p[list(c)].sum(axis=0) - (k - 1) * passing
        pos = L > 0
        if not pos.any(): continue
        mk = sum(1 << d for d in c)
        T = np.cumsum(((dm[1:M+1] & mk) == mk).astype(np.int64))[Mp - 1]
        Z = np.cumsum(((dm[1:M+1] & mk) == 0).astype(np.int64))[Mp - 1]
        killed |= pos & ((3 * L > T) | (4 * L > Z))
for d in range(10):
    L = sd_p[d]; mk = 1 << d
    Z = np.cumsum(((dm[1:M+1] & mk) == 0).astype(np.int64))[Mp - 1]
    killed |= (L > 0) & (4 * L > Z)
def intervals(lst):
    out = []
    for n in lst:
        if out and out[-1][1] == n - 1: out[-1][1] = n
        else: out.append([n, n])
    return out
kl = intervals(sorted(int(passing[i]) for i in np.where(killed)[0]))
sv = intervals(sorted(int(passing[i]) for i in np.where(~killed)[0]))
json.dump({"closed_form_kills": kl, "survivors": sv}, open("results/stage2.json", "w"), indent=1)
EXPECTED_KILLS = [[4,5],[51,66],[681,995],[1031,1056],[1606,1640],[11254,11663],[11935,14762]]
EXPECTED_SURV  = [[1,2],[6,20],[67,182],[996,1030],[1057,1605]]
assert kl == EXPECTED_KILLS, kl
assert sv == EXPECTED_SURV, sv
print("STAGE 2 PASS: closed-form saturation kills and survivors match the paper")
