import json, random, time, sys
from profile_solver import get_profile, embed_assign, verify_and_cells, F_EDGES, ADJ, CBAR, PAIRS, PIDX, EMB, dmask
import numpy as np

def solve_profiled2(N, tries=40, seed0=0, verbose=False):
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
        rnd=random.Random(seed0+7919*t+N)
        pool=set(range(1,M+1))
        plist=[]
        for T2,c in prof: plist+=[T2]*c
        plist.sort(key=lambda T2:(-len(T2), rnd.random()))
        flowers=[]; ok=True
        for T2 in plist:
            Tm=sum(1<<d for d in T2)
            cand=[x for x in pool if (DM[x]&Tm)==Tm]
            if len(cand)<3: ok=False; break
            cand.sort(key=lambda x:(bin(DM[x]&Hmask).count('1'),-conf[x],rnd.random()))
            trip=cand[:3]
            for x in trip: pool.remove(x)
            flowers.append((T2,list(trip)))
        if not ok: continue
        members=[fl[1][:] for fl in flowers]
        Tmasks=[sum(1<<d for d in fl[0]) for fl in flowers]
        gmask=[0]*N
        for f in range(N):
            g=0; mem=members[f]
            for a2 in range(3):
                for b2 in range(a2+1,3):
                    if clash(mem[a2],mem[b2]): g|=1<<PIDX[(a2,b2)]
            gmask[f]=g
        # heavy-digit quota per flower: for d in H, d notin T(f): capacity 2 among outers
        hcount=[[0]*10 for _ in range(N)]
        rest=sorted(pool,key=lambda x:(-bin(DM[x]&Hmask).count('1'),-conf[x],rnd.random()))
        fail=[]
        for x in rest:
            h=DM[x]&Hmask
            best=-1; bestsc=-1; bestg=0
            for f in range(N):
                mem=members[f]; k=len(mem)
                if k>=7: continue
                if Tmasks[f]&h: continue
                bad=False; sc=0
                for d in range(10):
                    if (h>>d)&1:
                        if hcount[f][d]>=2: bad=True; break
                        sc += (2-hcount[f][d])
                if bad: continue
                cb=0
                for i in range(k):
                    if clash(x,mem[i]): cb|=1<<PIDX[(i,k)]
                if not EMB[gmask[f]|cb]: continue
                sc=sc*100 + (7-k)*3 + rnd.random()
                if sc>bestsc: bestsc=sc; best=f; bestg=gmask[f]|cb
            if best>=0:
                k=len(members[best]); members[best].append(x); gmask[best]=bestg
                for d in range(10):
                    if (h>>d)&1: hcount[best][d]+=1
            else: fail.append(x)
        # ejection-chain repair with depth 2
        def try_place(x, depth, banned):
            h=DM[x]&Hmask
            order=sorted(range(N), key=lambda f:(len(members[f])>=7, rnd.random()))
            for f in order:
                if Tmasks[f]&h: continue
                if any(((h>>d)&1) and hcount[f][d]>=2 for d in range(10)): pass_quota=False
                else: pass_quota=True
                mem=members[f]; k=len(mem)
                if k<7 and pass_quota:
                    cb=0
                    for i in range(k):
                        if clash(x,mem[i]): cb|=1<<PIDX[(i,k)]
                    if EMB[gmask[f]|cb]:
                        members[f].append(x); gmask[f]|=cb
                        for d in range(10):
                            if (h>>d)&1: hcount[f][d]+=1
                        return True
                if depth>0:
                    for i in range(3,len(mem)):
                        y=mem[i]
                        if y in banned: continue
                        hy=DM[y]&Hmask
                        newmem=mem[:i]+mem[i+1:]+[x]
                        # quota check replacing y with x
                        okq=True
                        for d in range(10):
                            c2=hcount[f][d]-(1 if (hy>>d)&1 else 0)+(1 if (h>>d)&1 else 0)
                            if (h>>d)&1 and (Tmasks[f]>>d)&1: okq=False;break
                            if c2>2: okq=False; break
                        if not okq: continue
                        g=0; feas=True
                        for a2 in range(len(newmem)):
                            for b2 in range(a2+1,len(newmem)):
                                if clash(newmem[a2],newmem[b2]): g|=1<<PIDX[(a2,b2)]
                        if not EMB[g]: continue
                        # commit tentatively
                        oldmem=mem[:]; oldg=gmask[f]; oldh=hcount[f][:]
                        members[f]=newmem; gmask[f]=g
                        for d in range(10):
                            if (hy>>d)&1: hcount[f][d]-=1
                            if (h>>d)&1: hcount[f][d]+=1
                        if try_place(y, depth-1, banned|{x}):
                            return True
                        members[f]=oldmem; gmask[f]=oldg; hcount[f]=oldh
            return False
        still=[]
        for x in fail:
            if not try_place(x,2,{x}): still.append(x)
        if not still and all(len(m)==7 for m in members):
            return members, DM
        if verbose: print(f"  try {t}: {len(still)} unplaced (of {len(fail)} after greedy)")
    return None,None

if __name__=="__main__":
    for N in [int(a) for a in sys.argv[1:]] or [69,70,71,100]:
        t0=time.time()
        sol,DM=solve_profiled2(N,tries=40,verbose=True)
        if sol:
            verify_and_cells(N,sol,DM)
            print(f"N={N}: SOLVED+VERIFIED in {time.time()-t0:.1f}s")
        else: print(f"N={N}: failed ({time.time()-t0:.1f}s)")
