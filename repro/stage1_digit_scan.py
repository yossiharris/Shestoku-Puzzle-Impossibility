"""Stage 1: exact digit-bound scan for all N <= 150000.
Regenerates the digit-bound-violating intervals of Table 1 and saves S_d(7N) for later stages."""
import numpy as np, json

NMAX = 150000
M = 7 * NMAX
dm = np.zeros(M + 1, dtype=np.int16)
lo = 1
while lo <= M:
    hi = min(M, lo * 10 - 1)
    r = np.arange(lo, hi + 1)
    dm[lo:hi + 1] = dm[r // 10] | (1 << (r % 10)).astype(np.int16)
    lo *= 10
Ns = np.arange(1, NMAX + 1)
Sd_at = np.zeros((10, NMAX), dtype=np.int64)
for d in range(10):
    cum = np.cumsum(((dm[1:M + 1] >> d) & 1).astype(np.int64))
    Sd_at[d] = cum[7 * Ns - 1]
viol = (Sd_at > 3 * Ns).any(axis=0)
bad = Ns[viol].tolist()
def intervals(lst):
    out = []
    for n in lst:
        if out and out[-1][1] == n - 1: out[-1][1] = n
        else: out.append([n, n])
    return out
iv = intervals(bad)
np.save("results/Sd_at.npy", Sd_at)
json.dump({"digit_bound_violations": iv,
           "largest_passing": int(Ns[~viol].max()),
           "count_passing": int((~viol).sum())}, open("results/stage1.json", "w"), indent=1)

EXPECTED = [[3,3],[21,50],[183,680],[1641,11253],[11664,11934],[14763,150000]]
assert iv == EXPECTED, f"MISMATCH: {iv}"
assert int(Ns[~viol].max()) == 14762
assert int((~viol).sum()) == 4349
assert int(Sd_at[1, 2]) == 12   # S_1(21) = 12, the paper's N=3 certificate
print("STAGE 1 PASS: digit-bound intervals, largest passing N=14762, 4349 passing, S_1(21)=12 — all match the paper")
