"""Stage 11: the augmented class-level relaxation (conservation, per-flower 3/4 split,
coverage, per-digit outer caps, TOTAL per-digit caps incl. triples, pair digit-mass,
one-fat-per-pair) is rationally FEASIBLE at every N in the open window [1387,1513].
This is the paper's Section 7.3 claim that no new obstruction issues from these
constraints. Profiles are restricted to |T|<=4; feasibility of the restricted system
implies feasibility of the full system (zero-padding). Runtime ~25-35 minutes total;
accepts optional lo hi arguments for chunked runs."""
import sys, json, time
import numpy as np
from itertools import combinations
from collections import Counter
from scipy.optimize import linprog
from scipy.sparse import lil_matrix

def dmask(x):
    m=0
    while x: m|=1<<(x%10); x//=10
    return m

def feasible(N):
    M=7*N
    K=Counter(dmask(x) for x in range(1,M+1))
    classes=sorted(K)
    Sd=[0]*10
    for m,v in K.items():
        for d in range(10):
            if (m>>d)&1: Sd[d]+=v
    s=[max(0,Sd[d]-2*N) for d in range(10)]
    H=[d for d in range(10) if s[d]>0]
    profiles=[0]+[sum(1<<d for d in c) for k in (1,2,3,4) for c in combinations(H,k)]
    vid={}; n=0
    for T in profiles: vid[("y",T)]=n; n+=1
    for m in classes:
        for T in profiles:
            if (m&T)==T: vid[("a",m,T)]=n; n+=1
            if (m&T)==0: vid[("b",m,T)]=n; n+=1
    rows_eq=[];rhs_eq=[];rows_ub=[];rhs_ub=[]
    rows_eq.append([(vid[("y",T)],1.0) for T in profiles]); rhs_eq.append(float(N))
    for m in classes:
        rows_eq.append([(vid[("a",m,T)],1.0) for T in profiles if (m&T)==T]+
                       [(vid[("b",m,T)],1.0) for T in profiles if (m&T)==0]); rhs_eq.append(float(K[m]))
    for T in profiles:
        rows_eq.append([(vid[("a",m,T)],1.0) for m in classes if (m&T)==T]+[(vid[("y",T)],-3.0)]); rhs_eq.append(0.0)
        rows_eq.append([(vid[("b",m,T)],1.0) for m in classes if (m&T)==0]+[(vid[("y",T)],-4.0)]); rhs_eq.append(0.0)
        for d in range(10):
            if not (T>>d)&1:
                co=[(vid[("a",m,T)],1.0) for m in classes if (m&T)==T and (m>>d)&1]+\
                   [(vid[("b",m,T)],1.0) for m in classes if (m&T)==0 and (m>>d)&1]
                if co: rows_ub.append(co+[(vid[("y",T)],-2.0)]); rhs_ub.append(0.0)
        alpha=10-bin(T).count('1')
        rows_ub.append([(vid[("b",m,T)],float(bin(m).count('1'))) for m in classes if (m&T)==0]+
                       [(vid[("y",T)],-2.0*alpha)]); rhs_ub.append(0.0)
        rows_ub.append([(vid[("b",m,T)],1.0) for m in classes if (m&T)==0 and bin(m).count('1')>alpha//2]+
                       [(vid[("y",T)],-2.0)]); rhs_ub.append(0.0)
    for d in H:
        rows_ub.append([(vid[("y",T)],-1.0) for T in profiles if (T>>d)&1]); rhs_ub.append(-float(s[d]))
    def sp(rows):
        A=lil_matrix((len(rows),n))
        for i,co in enumerate(rows):
            for j,v in co: A[i,j]+=v
        return A.tocsr()
    res=linprog(c=np.zeros(n),A_eq=sp(rows_eq),b_eq=np.array(rhs_eq),
                A_ub=sp(rows_ub),b_ub=np.array(rhs_ub),bounds=[(0,None)]*n,method="highs")
    return res.status==0

if __name__=="__main__":
    lo=int(sys.argv[1]) if len(sys.argv)>1 else 1387
    hi=int(sys.argv[2]) if len(sys.argv)>2 else 1513
    bad=[]; t0=time.time()
    for N in range(lo,hi+1):
        if not feasible(N): bad.append(N)
    json.dump({"range":[lo,hi],"infeasible":bad},open(f"results/stage11_{lo}_{hi}.json","w"))
    assert not bad, bad
    print(f"STAGE 11 PASS [{lo},{hi}]: augmented relaxation rationally feasible at all {hi-lo+1} values ({time.time()-t0:.0f}s)")
