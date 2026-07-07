"""Full exact-class flow template for a window instance.
Classes = exact digit sets (<=4 distinct digits). Profiles T with |T|<=4.
a[(m,T)]: class-m numbers on triples of T-flowers (m >= T)
b[(m,T)]: class-m numbers on outers of T-flowers (m cap T = 0)
Constraints: conservation, 3/4 per flower, coverage, outer digit caps, supply implicit."""
import json, sys, time
from itertools import combinations
from ortools.sat.python import cp_model
import numpy as np

Sd_at = np.load("results/Sd_at.npy")
def dmask(x):
    m=0
    while x: m |= 1<<(x%10); x//=10
    return m

def build_template(N, seed=0, timeout=120):
    M = 7*N
    from collections import Counter
    K = Counter(dmask(x) for x in range(1, M+1))
    classes = sorted(K)
    s = [max(0, int(Sd_at[d,N-1]) - 2*N) for d in range(10)]
    H = [d for d in range(10) if s[d] > 0]
    Hm = sum(1<<d for d in H)
    profiles = [0]
    for k in (1,2,3,4):
        for c in combinations(H, k):
            profiles.append(sum(1<<d for d in c))
    mdl = cp_model.CpModel()
    y = {T: mdl.NewIntVar(0, N, "") for T in profiles}
    mdl.Add(sum(y.values()) == N)
    a = {}; b = {}
    for m in classes:
        for T in profiles:
            if (m & T) == T: a[(m,T)] = mdl.NewIntVar(0, 3*N, "")
            if (m & T) == 0: b[(m,T)] = mdl.NewIntVar(0, 4*N, "")
    for m in classes:
        mdl.Add(sum(a.get((m,T),0) for T in profiles) + sum(b.get((m,T),0) for T in profiles) == K[m])
    for T in profiles:
        mdl.Add(sum(a[(m,T)] for m in classes if (m&T)==T) == 3*y[T])
        mdl.Add(sum(b[(m,T)] for m in classes if (m&T)==0) == 4*y[T])
        for d in range(10):
            if not (T>>d)&1:
                mdl.Add(sum(b[(m,T)] for m in classes if (m&T)==0 and (m>>d)&1) <= 2*y[T])
    for d in H:
        mdl.Add(sum(y[T] for T in profiles if (T>>d)&1) >= s[d])
    # --- pairability constraints for the outer pools ---
    for T in profiles:
        alpha = 10 - bin(T).count('1')
        # digit-mass: each pair uses <= alpha distinct digits total
        mdl.Add(sum(bin(m).count('1')*b[(m,T)] for m in classes if (m&T)==0) <= 2*y[T]*alpha)
        # at most one 'fat' member (popcount > alpha//2) per pair
        mdl.Add(sum(b[(m,T)] for m in classes if (m&T)==0 and bin(m).count('1') > alpha//2) <= 2*y[T])
    import random
    rnd = random.Random(seed)
    # steer: fat-digit numbers to triples; triple sets close to T; light outers
    obj = []
    for (m,T),v in b.items(): obj.append(bin(m).count('1')*v)
    for (m,T),v in a.items(): obj.append(2*(bin(m).count('1')-bin(T).count('1'))*v + rnd.randint(0,1)*v)
    mdl.Minimize(sum(obj))
    slv = cp_model.CpSolver(); slv.parameters.max_time_in_seconds = timeout
    slv.parameters.num_search_workers = 6
    st = slv.Solve(mdl)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE): return None
    out = {"N": N,
           "y": {str(T): slv.Value(v) for T,v in y.items() if slv.Value(v)>0},
           "a": {f"{m},{T}": slv.Value(v) for (m,T),v in a.items() if slv.Value(v)>0},
           "b": {f"{m},{T}": slv.Value(v) for (m,T),v in b.items() if slv.Value(v)>0}}
    return out

if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv)>1 else 1450
    t0=time.time()
    tpl = build_template(N, seed=int(sys.argv[2]) if len(sys.argv)>2 else 0)
    if tpl:
        json.dump(tpl, open(f"results/template_{N}.json","w"))
        ys = {int(k): v for k,v in tpl["y"].items()}
        sizes = {}
        for T,c in ys.items(): sizes[bin(T).count('1')] = sizes.get(bin(T).count('1'),0)+c
        print(f"template for N={N} in {time.time()-t0:.0f}s; profiles used: {len(ys)}; flowers by |T|: {sizes}")
    else:
        print("template FAILED")
