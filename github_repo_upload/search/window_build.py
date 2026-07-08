"""Instantiate a window template into an actual verified solution."""
import json, sys, random, time
from collections import defaultdict, Counter

F_EDGES=[(0,2),(0,3),(0,5),(1,3),(1,4),(1,6),(2,5),(3,5),(3,6),(4,6)]
def dmask(x):
    m=0
    while x: m |= 1<<(x%10); x//=10
    return m
def digs_disjoint(a,b,DM): return (DM[a]&DM[b])==0
def clash(a,b,DM): return abs(a-b)==1 or (DM[a]&DM[b])!=0

def build(N, tpl, seed=0, verbose=True):
    rnd = random.Random(seed)
    M = 7*N
    DM=[dmask(x) for x in range(M+1)]
    byclass = defaultdict(list)
    for x in range(1,M+1): byclass[DM[x]].append(x)
    for m in byclass: rnd.shuffle(byclass[m])
    pool = {m: list(v) for m,v in byclass.items()}
    y = {int(k): v for k,v in tpl["y"].items()}
    aflow = defaultdict(int); bflow = defaultdict(int)
    for k,v in tpl["a"].items():
        m,T = map(int,k.split(",")); aflow[(m,T)] = v
    for k,v in tpl["b"].items():
        m,T = map(int,k.split(",")); bflow[(m,T)] = v
    # --- materialize triples per profile ---
    flowers=[]  # each: dict(T=, trip=[3 nums], outer=[4 nums])
    for T,cnt in sorted(y.items(), key=lambda kv:-bin(kv[0]).count('1')):
        # gather triple numbers for this profile
        tripnums=[]
        for (m,TT),c in list(aflow.items()):
            if TT!=T: continue
            take = pool[m][:c]; pool[m] = pool[m][c:]
            assert len(take)==c, (m,T,c,len(take))
            tripnums += take
        assert len(tripnums)==3*cnt, (T,len(tripnums),3*cnt)
        rnd.shuffle(tripnums)
        for i in range(cnt):
            trip = tripnums[3*i:3*i+3]
            trip.sort(key=lambda x: bin(DM[x]).count('1'))  # hub = smallest digit set
            flowers.append({"T":T, "trip":trip, "outer":None})
    # --- outer pools per profile ---
    outerpool = defaultdict(list)
    for (m,T),c in bflow.items():
        take = pool[m][:c]; pool[m]=pool[m][c:]
        assert len(take)==c
        outerpool[T]+=take
    assert all(len(v)==0 for v in pool.values()), "pool leftover"
    # --- assign outers per flower: two digit-disjoint pairs avoiding forbidden sets ---
    unplaced=[]
    for fl in flowers:
        T=fl["T"]; hub,w2,w4 = fl["trip"][0],fl["trip"][1],fl["trip"][2]
        FL = DM[hub]|DM[w2]; FR = DM[hub]|DM[w4]
        P = outerpool[T]
        # pick 4 numbers forming two disjoint pairs
        chosen=None
        idxs=list(range(len(P)))
        # greedy: pick a1 for left, find a2 disjoint; b1,b2 for right
        for attempt in range(60):
            rnd.shuffle(idxs)
            sel=[]
            fL=[i for i in idxs if (DM[P[i]]&FL)==0]
            fR=[i for i in idxs if (DM[P[i]]&FR)==0]
            ok=False
            for i1 in fL[:30]:
                for i2 in fL[:30]:
                    if i2<=i1: continue
                    x,y2=P[i1],P[i2]
                    if clash(x,y2,DM): continue
                    rem=[j for j in fR[:40] if j!=i1 and j!=i2]
                    for j1i in range(len(rem)):
                        for j2i in range(j1i+1,len(rem)):
                            u,v=P[rem[j1i]],P[rem[j2i]]
                            if clash(u,v,DM): continue
                            # consecutive checks vs triple
                            if abs(x-hub)==1 or abs(y2-hub)==1 or abs(x-w2)==1 or abs(y2-w2)==1: continue
                            if abs(u-hub)==1 or abs(v-hub)==1 or abs(u-w4)==1 or abs(v-w4)==1: continue
                            chosen=(i1,i2,rem[j1i],rem[j2i]); ok=True; break
                        if ok: break
                    if ok: break
                if ok: break
            if ok: break
        if chosen is None:
            unplaced.append(fl); continue
        picks=sorted(chosen, reverse=True)
        vals=[P[i] for i in chosen]
        for i in picks: P.pop(i)
        fl["outer"]=vals  # [cell0, cell5, cell1, cell6]
    if verbose: print(f"flowers needing repair: {len(unplaced)} of {len(flowers)}; leftover outers: {sum(len(v) for v in outerpool.values())}")
    if unplaced: return None, DM, len(unplaced)
    # assemble cells: 0,1,2,3,4,5,6
    sol=[]
    for fl in flowers:
        hub,w2,w4=fl["trip"]; o=fl["outer"]
        cells=[o[0], o[2], w2, hub, w4, o[1], o[3]]
        sol.append(cells)
    return sol, DM, 0

def verify(N, sol, DM):
    seen=set()
    assert len(sol)==N
    for cells in sol:
        for x in cells:
            assert 1<=x<=7*N and x not in seen; seen.add(x)
        for a,b in F_EDGES:
            x,y=cells[a],cells[b]
            assert abs(x-y)!=1 and (DM[x]&DM[y])==0, (x,y)
    assert len(seen)==7*N
    return True

if __name__=="__main__":
    N=int(sys.argv[1]); seed=int(sys.argv[2]) if len(sys.argv)>2 else 0
    tpl=json.load(open(f"results/template_{N}.json"))
    t0=time.time()
    sol,DM,bad=build(N,tpl,seed=seed)
    if sol:
        verify(N,sol,DM)
        json.dump({"N":N,"flowers":sol}, open(f"results/window_solution_{N}.json","w"))
        print(f"N={N}: WINDOW INSTANCE SOLVED AND VERIFIED in {time.time()-t0:.0f}s")
    else:
        print(f"N={N}: {bad} flowers unfilled ({time.time()-t0:.0f}s)")
