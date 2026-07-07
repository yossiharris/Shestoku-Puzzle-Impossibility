"""Instantiation v2: per-profile-group global pairing + pair-to-side matching."""
import json, sys, random, time
from collections import defaultdict

F_EDGES=[(0,2),(0,3),(0,5),(1,3),(1,4),(1,6),(2,5),(3,5),(3,6),(4,6)]
def dmask(x):
    m=0
    while x: m |= 1<<(x%10); x//=10
    return m
def clash(a,b,DM): return abs(a-b)==1 or (DM[a]&DM[b])!=0

def pair_up(P, DM, rnd, tries=40):
    """Partition list P (even) into digit-disjoint non-consecutive pairs; greedy by scarcity + retries."""
    n=len(P)
    for t in range(tries):
        rnd.shuffle(P)
        # adjacency: compatible if not clash
        remaining=set(range(n))
        # scarcity order: fewest compatible partners first (recompute cheaply on sample)
        pairs=[]
        ok=True
        items=sorted(remaining, key=lambda i: sum(1 for j in list(remaining)[:60] if j!=i and not clash(P[i],P[j],DM)))
        remaining=set(items)
        while remaining:
            i=min(remaining, key=lambda ii: sum(1 for j in remaining if j!=ii and not clash(P[ii],P[j],DM)) if len(remaining)<=80 else rnd.random())
            remaining.discard(i)
            partner=None
            cands=[j for j in remaining if not clash(P[i],P[j],DM)]
            if not cands: ok=False; break
            # choose partner with fewest own options (save flexible ones)
            if len(remaining)<=80:
                partner=min(cands, key=lambda j: sum(1 for k2 in remaining if k2!=j and not clash(P[j],P[k2],DM)))
            else:
                partner=rnd.choice(cands)
            remaining.discard(partner)
            pairs.append((P[i],P[partner]))
        if ok: return pairs
    return None

def build(N, tpl, seed=0, verbose=True):
    rnd=random.Random(seed)
    M=7*N
    DM=[dmask(x) for x in range(M+1)]
    byclass=defaultdict(list)
    for x in range(1,M+1): byclass[DM[x]].append(x)
    for m in byclass: rnd.shuffle(byclass[m])
    pool={m:list(v) for m,v in byclass.items()}
    y={int(k):v for k,v in tpl["y"].items()}
    aflow=defaultdict(int); bflow=defaultdict(int)
    for k,v in tpl["a"].items():
        m,T=map(int,k.split(",")); aflow[(m,T)]=v
    for k,v in tpl["b"].items():
        m,T=map(int,k.split(",")); bflow[(m,T)]=v
    groups={}
    for T,cnt in y.items():
        trip=[]
        for (m,TT),c in aflow.items():
            if TT!=T or c==0: continue
            take=pool[m][:c]; pool[m]=pool[m][c:]; trip+=take
        out=[]
        for (m,TT),c in bflow.items():
            if TT!=T or c==0: continue
            take=pool[m][:c]; pool[m]=pool[m][c:]; out+=take
        groups[T]=(cnt,trip,out)
    solution=[]; failed=[]
    for T,(cnt,trip,out) in sorted(groups.items(), key=lambda kv:-bin(kv[0]).count('1')):
        rnd.shuffle(trip)
        flowers=[]
        for i in range(cnt):
            t3=sorted(trip[3*i:3*i+3], key=lambda x:bin(DM[x]).count('1'))
            flowers.append(t3)  # [hub, w2, w4]
        pairs=pair_up(list(out), DM, rnd)
        if pairs is None:
            failed.append((T,cnt,"pairing")); continue
        # assign pairs to flower-sides via greedy matching with retries
        sides=[]  # (fi, 'L'/'R', forbidden_mask, hub, wing)
        for fi,(hub,w2,w4) in enumerate(flowers):
            sides.append((fi,'L',DM[hub]|DM[w2],hub,w2))
            sides.append((fi,'R',DM[hub]|DM[w4],hub,w4))
        def compat(pr, sd):
            (u,v)=pr; (_,_,F,hub,wing)=sd
            if (DM[u]|DM[v])&F: return False
            for z in (u,v):
                if abs(z-hub)==1 or abs(z-wing)==1: return False
            return True
        # bipartite: pairs -> sides ; use simple Kuhn's augmenting matching
        adj=[[si for si,sd in enumerate(sides) if compat(pr,sd)] for pr in pairs]
        matchL=[-1]*len(pairs); matchR=[-1]*len(sides)
        order=sorted(range(len(pairs)), key=lambda p2: len(adj[p2]))
        def try_kuhn(p2, vis):
            for si in adj[p2]:
                if vis[si]: continue
                vis[si]=True
                if matchR[si]==-1 or try_kuhn(matchR[si],vis):
                    matchL[p2]=si; matchR[si]=p2; return True
            return False
        okall=True
        for p2 in order:
            if not try_kuhn(p2,[False]*len(sides)):
                okall=False; break
        if not okall or -1 in matchR:
            failed.append((T,cnt,"matching")); continue
        cells_by_f={fi:[None]*7 for fi in range(cnt)}
        for fi,(hub,w2,w4) in enumerate(flowers):
            cells_by_f[fi][3]=hub; cells_by_f[fi][2]=w2; cells_by_f[fi][4]=w4
        for si,p2 in enumerate(matchR):
            fi,side,_,_,_=sides[si]
            u,v=pairs[p2]
            if side=='L': cells_by_f[fi][0]=u; cells_by_f[fi][5]=v
            else: cells_by_f[fi][1]=u; cells_by_f[fi][6]=v
        for fi in range(cnt): solution.append(cells_by_f[fi])
    return solution, DM, failed

def verify(N,sol,DM):
    seen=set(); assert len(sol)==N
    for cells in sol:
        for x in cells: assert 1<=x<=7*N and x not in seen; 
        seen.update(cells)
        for a,b in F_EDGES:
            x,y2=cells[a],cells[b]
            assert abs(x-y2)!=1 and (DM[x]&DM[y2])==0,(x,y2)
    assert len(seen)==7*N
    return True

if __name__=="__main__":
    N=int(sys.argv[1]); seed=int(sys.argv[2]) if len(sys.argv)>2 else 0
    tpl=json.load(open(f"results/template_{N}.json"))
    t0=time.time()
    sol,DM,failed=build(N,tpl,seed=seed)
    if not failed and len(sol)==N:
        verify(N,sol,DM)
        json.dump({"N":N,"flowers":sol},open(f"results/window_solution_{N}.json","w"))
        print(f"N={N}: WINDOW INSTANCE SOLVED AND VERIFIED in {time.time()-t0:.0f}s")
    else:
        tot=sum(c for _,c,_ in failed)
        print(f"N={N}: {len(failed)} groups failed ({tot} flowers): {[(hex(T),c,r) for T,c,r in failed[:8]]} ({time.time()-t0:.0f}s)")
