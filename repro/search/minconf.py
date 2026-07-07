"""Min-conflicts local search: maintain a full cell assignment (N flowers x 7 cells),
objective = number of flower-edges whose endpoint numbers conflict; swap moves with
best-of-K candidate selection and noise. Verified independently on success."""
import random, sys, time

F_EDGES = [(0,2),(0,3),(0,5),(1,3),(1,4),(1,6),(2,5),(3,5),(3,6),(4,6)]
CELL_NB = [[] for _ in range(7)]
for a,b in F_EDGES: CELL_NB[a].append(b); CELL_NB[b].append(a)

def dmask(x):
    m=0
    while x: m |= 1<<(x%10); x//=10
    return m

def solve_minconf(N, time_budget=60.0, seed=0, init=None):
    M=7*N
    DM=[0]*(M+1)
    for x in range(1,M+1): DM[x]=dmask(x)
    rnd=random.Random(seed)
    def clash(a,b): return abs(a-b)==1 or (DM[a]&DM[b])!=0
    # slots: slot s = flower s//7, cell s%7 ; neighbors of slot
    NB=[[] for _ in range(M)]
    for f in range(N):
        for c in range(7):
            NB[f*7+c]=[f*7+c2 for c2 in CELL_NB[c]]
    if init is None:
        arr=list(range(1,M+1)); rnd.shuffle(arr)
    else:
        arr=init[:]
    slot_of=[0]*(M+1)
    for s,x in enumerate(arr): slot_of[x]=s
    def slot_viol(s, val=None):
        x = arr[s] if val is None else val
        v=0
        for t in NB[s]:
            if clash(x, arr[t]): v+=1
        return v
    viol=set()
    total=0
    for f in range(N):
        for a,b in F_EDGES:
            if clash(arr[f*7+a], arr[f*7+b]):
                viol.add((f*7+a, f*7+b)); total+=1
    def swap(s1,s2):
        nonlocal total
        for s in (s1,s2):
            for t in NB[s]:
                e=(min(s,t),max(s,t))
                if e in viol: viol.remove(e); total-=1
        arr[s1],arr[s2]=arr[s2],arr[s1]
        slot_of[arr[s1]]=s1; slot_of[arr[s2]]=s2
        for s in (s1,s2):
            for t in NB[s]:
                e=(min(s,t),max(s,t))
                if e not in viol and clash(arr[s],arr[t]):
                    viol.add(e); total+=1
    t0=time.time(); K=12
    best=total
    while total>0 and time.time()-t0 < time_budget:
        e = rnd.choice(tuple(viol))
        s = e[rnd.random()<0.5]
        # candidate partners: K random slots + K slots of numbers "digit-disjoint-ish"
        bestd=None; bs=None
        for _ in range(K):
            s2 = rnd.randrange(M)
            if s2==s: continue
            # delta = new viol - old viol around both slots
            old = slot_viol(s)+slot_viol(s2) - (1 if (min(s,s2),max(s,s2)) in viol and s2 in NB[s] else 0)
            x1,x2 = arr[s],arr[s2]
            arr[s],arr[s2]=x2,x1
            new = slot_viol(s)+slot_viol(s2) - (1 if s2 in NB[s] and clash(arr[s],arr[s2]) else 0)
            arr[s],arr[s2]=x1,x2
            d = new-old
            if bestd is None or d<bestd: bestd=d; bs=s2
        if bs is not None and (bestd<=0 or rnd.random()<0.15):
            swap(s,bs)
        if total<best: best=total
    return (arr if total==0 else None), DM, total

def embed_check(arr,N,DM):
    M=7*N
    assert sorted(arr)==list(range(1,M+1))
    for f in range(N):
        for a,b in F_EDGES:
            x,y=arr[f*7+a],arr[f*7+b]
            assert abs(x-y)!=1 and (DM[x]&DM[y])==0
    return True

if __name__=="__main__":
    for N in [69,71,100]:
        t0=time.time()
        arr,DM,rem = solve_minconf(N, time_budget=70, seed=1)
        if arr: embed_check(arr,N,DM); print(f"N={N}: SOLVED in {time.time()-t0:.1f}s")
        else: print(f"N={N}: stuck with {rem} violations after {time.time()-t0:.1f}s")
