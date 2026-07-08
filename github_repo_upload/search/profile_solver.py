"""Profile-guided constructor: seed each flower's saturated triple per the integer
saturation profile, then fill the 4 outer slots greedily with embeddability-table checks."""
import json, random, time, sys
from itertools import combinations
from ortools.sat.python import cp_model
import numpy as np
from digitdp import A, T as Tcount

F_EDGES=[(0,2),(0,3),(0,5),(1,3),(1,4),(1,6),(2,5),(3,5),(3,6),(4,6)]
ADJ=[set() for _ in range(7)]
for a,b in F_EDGES: ADJ[a].add(b); ADJ[b].add(a)
CBAR=[[(i!=j) and (j not in ADJ[i]) for j in range(7)] for i in range(7)]
PAIRS=[(i,j) for i in range(7) for j in range(i+1,7)]
PIDX={}
for k,(i,j) in enumerate(PAIRS): PIDX[(i,j)]=k; PIDX[(j,i)]=k
EMB=open("embtable.bin","rb").read()
Sd_at=np.load("Sd_at.npy"); NsA=np.arange(1,Sd_at.shape[1]+1)
sd_all=np.maximum(0,Sd_at-2*NsA)

def dmask(x):
    m=0
    while x: m|=1<<(x%10); x//=10
    return m

def get_profile(N, seed=0):
    H=[d for d in range(10) if sd_all[d,N-1]>0]
    subs=[frozenset(c) for k in range(len(H)+1) for c in combinations(H,k)]
    m7=7*N; mdl=cp_model.CpModel()
    y={T2:mdl.NewIntVar(0,N,"") for T2 in subs}
    mdl.Add(sum(y.values())==N)
    for d in H:
        mdl.Add(sum(y[T2] for T2 in subs if d in T2)>=int(sd_all[d,N-1]))
    for k in range(1,min(4,len(H))+1):
        for c in combinations(H,k):
            D=frozenset(c); mk=sum(1<<dd for dd in D)
            sup=sum(y[T2] for T2 in subs if D<=T2)
            mdl.Add(3*sup<=Tcount(mk,m7)); mdl.Add(4*sup<=A(mk,m7))
    rnd=random.Random(seed)
    mdl.Minimize(sum(rnd.randint(0,7)*v for v in y.values()))
    s=cp_model.CpSolver(); s.parameters.max_time_in_seconds=10; s.parameters.random_seed=seed
    st=s.Solve(mdl)
    if st not in (cp_model.OPTIMAL,cp_model.FEASIBLE): return None,H
    return [(T2,s.Value(y[T2])) for T2 in subs if s.Value(y[T2])>0],H

def solve_profiled(N, tries=30, seed0=0, verbose=False):
    M=7*N
    DM=[0]*(M+1)
    for x in range(1,M+1): DM[x]=dmask(x)
    def clash(a,b): return abs(a-b)==1 or (DM[a]&DM[b])!=0
    cnt=[0]*10
    for x in range(1,M+1):
        for d in range(10):
            if (DM[x]>>d)&1: cnt[d]+=1
    conf=[0]*(M+1)
    for x in range(1,M+1): conf[x]=sum(cnt[d] for d in range(10) if (DM[x]>>d)&1)
    for t in range(tries):
        prof,H=get_profile(N,seed=seed0+t)
        if prof is None: return None,None
        Hmask=sum(1<<d for d in H)
        rnd=random.Random(seed0+1000*t)
        # --- seed triples ---
        pool=set(range(1,M+1))
        flowers=[]; ok=True
        plist=[]
        for T2,c in prof: plist += [T2]*c
        # larger profiles first
        plist.sort(key=lambda T2:(-len(T2), rnd.random()))
        for T2 in plist:
            Tm=sum(1<<d for d in T2)
            cand=[x for x in pool if (DM[x]&Tm)==Tm]
            if len(cand)<3: ok=False; break
            # prefer exact heavy-match, then high conflict (burn awkward numbers)
            cand.sort(key=lambda x:(bin(DM[x]&Hmask).count('1'), -conf[x], rnd.random()))
            trip=cand[:3]
            for x in trip: pool.remove(x)
            flowers.append(list(trip))
        if not ok: continue
        rest=sorted(pool,key=lambda x:(-bin(DM[x]&Hmask).count('1'),-conf[x],rnd.random()))
        members=[fl[:] for fl in flowers]
        gmask=[0]*N
        for f in range(N):
            g=0; mem=members[f]
            for a2 in range(len(mem)):
                for b2 in range(a2+1,len(mem)):
                    if clash(mem[a2],mem[b2]): g|=1<<PIDX[(a2,b2)]
            gmask[f]=g
        order=list(range(N)); fail=[]
        for x in rest:
            rnd.shuffle(order); placed=False
            for f in order:
                mem=members[f]; k=len(mem)
                if k>=7: continue
                cb=0
                for i in range(k):
                    if clash(x,mem[i]): cb|=1<<PIDX[(i,k)]
                if EMB[gmask[f]|cb]:
                    members[f].append(x); gmask[f]|=cb; placed=True; break
            if not placed: fail.append(x)
        # swap repair among outers
        for x in list(fail):
            done=False
            for f in rnd.sample(range(N),N):
                mem=members[f]; k=len(mem)
                if k<7:
                    cb=0
                    for i in range(k):
                        if clash(x,mem[i]): cb|=1<<PIDX[(i,k)]
                    if EMB[gmask[f]|cb]:
                        members[f].append(x); gmask[f]|=cb; fail.remove(x); done=True; break
                else:
                    for i in range(3,7):
                        y=mem[i]; newmem=mem[:i]+mem[i+1:]+[x]
                        g=0; bad=False
                        for a2 in range(7):
                            for b2 in range(a2+1,7):
                                if clash(newmem[a2],newmem[b2]): g|=1<<PIDX[(a2,b2)]
                        if not EMB[g]: continue
                        for f2 in range(N):
                            if f2==f: continue
                            mm=members[f2]; kk=len(mm)
                            if kk>=7: continue
                            cb=0
                            for t2 in range(kk):
                                if clash(y,mm[t2]): cb|=1<<PIDX[(t2,kk)]
                            if EMB[gmask[f2]|cb]:
                                members[f]=newmem; gmask[f]=g
                                members[f2].append(y); gmask[f2]|=cb
                                fail.remove(x); done=True; break
                        if done: break
                if done: break
        if not fail and all(len(m)==7 for m in members):
            return members, DM
        if verbose: print(f"  try {t}: {len(fail)} unplaced")
    return None,None

def embed_assign(nums,DM):
    k=len(nums)
    cl=[[(abs(nums[i]-nums[j])==1 or (DM[nums[i]]&DM[nums[j]])!=0) for j in range(k)] for i in range(k)]
    order=sorted(range(k),key=lambda i:-sum(cl[i]))
    used=[False]*7; pos=[-1]*k
    def bt(t):
        if t==k: return True
        i=order[t]
        for v in range(7):
            if used[v]: continue
            if all((not cl[i][order[t2]]) or CBAR[v][pos[order[t2]]] for t2 in range(t)):
                used[v]=True; pos[i]=v
                if bt(t+1): return True
                used[v]=False; pos[i]=-1
        return False
    if not bt(0): return None
    return {nums[i]:pos[i] for i in range(k)}

def verify_and_cells(N,members,DM):
    M=7*N; seen=set(); out=[]
    assert len(members)==N
    for mem in members:
        assert len(mem)==7
        for x in mem: assert 1<=x<=M and x not in seen; 
        seen.update(mem)
        asg=embed_assign(mem,DM); assert asg is not None
        cells=[None]*7
        for x,cc in asg.items(): cells[cc]=x
        for a,b in F_EDGES:
            x,y=cells[a],cells[b]
            assert abs(x-y)!=1 and (DM[x]&DM[y])==0
        out.append(cells)
    assert len(seen)==M
    return out

if __name__=="__main__":
    for N in [69,70,71,100,182]:
        t0=time.time()
        sol,DM=solve_profiled(N,tries=25,verbose=True)
        if sol:
            verify_and_cells(N,sol,DM)
            print(f"N={N}: PROFILED SOLVE+VERIFY in {time.time()-t0:.1f}s")
        else:
            print(f"N={N}: failed ({time.time()-t0:.1f}s)")
