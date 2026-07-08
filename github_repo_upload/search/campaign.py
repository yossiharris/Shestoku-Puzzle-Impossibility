"""Construction campaign over all 425 candidate N.
Greedy with embeddability-table lookups, clash-concentration heuristic,
full-probe fallback, swap repair, escalating restarts. Every solution is
re-verified by an independent checker against the flower graph directly."""
import json, gzip, os, random, sys, time

F_EDGES = [(0,2),(0,3),(0,5),(1,3),(1,4),(1,6),(2,5),(3,5),(3,6),(4,6)]
ADJ = [set() for _ in range(7)]
for a,b in F_EDGES: ADJ[a].add(b); ADJ[b].add(a)
CBAR = [[(i!=j) and (j not in ADJ[i]) for j in range(7)] for i in range(7)]
PAIRS = [(i,j) for i in range(7) for j in range(i+1,7)]
PIDX = {}
for k,(i,j) in enumerate(PAIRS): PIDX[(i,j)] = k; PIDX[(j,i)] = k
EMB = open("embtable.bin","rb").read()

def dmask(x):
    m = 0
    while x: m |= 1 << (x % 10); x //= 10
    return m

def solve_instance(N, max_restarts=200, seed0=12345):
    M = 7*N
    DM = [0]*(M+1)
    for x in range(1, M+1): DM[x] = dmask(x)
    # digit class sizes and conflict degree
    cnt = [0]*10
    for x in range(1, M+1):
        m = DM[x]
        for d in range(10):
            if (m>>d)&1: cnt[d] += 1
    Ns_ = N
    sd = [max(0, c - 2*Ns_) for c in cnt]
    H = [d for d in range(10) if sd[d] > 0]
    Hmask = sum(1<<d for d in H)
    def heavy_load(x): return bin(DM[x] & Hmask).count('1')
    conf = [0]*(M+1)
    for x in range(1, M+1):
        conf[x] = sum(cnt[d] for d in range(10) if (DM[x]>>d)&1)
    def clash(a,b): return abs(a-b)==1 or (DM[a]&DM[b])!=0

    for r in range(max_restarts):
        rnd = random.Random(seed0 + r*7919 + N)
        nums = sorted(range(1, M+1), key=lambda x: (-heavy_load(x), -conf[x], rnd.random()))
        members = [[] for _ in range(N)]
        gmask = [0]*N
        order_probe = list(range(N))
        fail = []
        for x in nums:
            best = -1; best_sc = -1
            rnd.shuffle(order_probe)
            for f in order_probe:
                mem = members[f]
                k = len(mem)
                if k >= 7: continue
                cb = 0; sc = 0
                for i in range(k):
                    if clash(x, mem[i]):
                        cb |= 1 << PIDX[(i,k)]; sc += 1
                g2 = gmask[f] | cb
                if EMB[g2]:
                    # prefer concentrating clashes; among zero-clash prefer emptier flowers
                    score = sc*10 + (7-k) if sc>0 else (7-k)
                    if score > best_sc:
                        best_sc = score; best = f; bestg = g2
                        if sc >= 2: break
            if best >= 0:
                members[best].append(x); gmask[best] = bestg
            else:
                fail.append(x)
        # swap repair
        for x in list(fail):
            done = False
            fl_order = sorted(range(N), key=lambda f: len(members[f]))
            for f in fl_order:
                mem = members[f]; k = len(mem)
                if k < 7:
                    cb = 0
                    for i in range(k):
                        if clash(x, mem[i]): cb |= 1 << PIDX[(i,k)]
                    if EMB[gmask[f] | cb]:
                        members[f].append(x); gmask[f] |= cb; fail.remove(x); done = True; break
                else:
                    for i in range(7):
                        y = mem[i]
                        newmem = mem[:i]+mem[i+1:]+[x]
                        g = 0; ok = True
                        for a in range(7):
                            for b in range(a+1,7):
                                if clash(newmem[a], newmem[b]): g |= 1 << PIDX[(a,b)]
                        if not EMB[g]: continue
                        # relocate y
                        for g2f in range(N):
                            if g2f == f: continue
                            mm = members[g2f]; kk = len(mm)
                            if kk >= 7: continue
                            cb = 0
                            for t in range(kk):
                                if clash(y, mm[t]): cb |= 1 << PIDX[(t,kk)]
                            if EMB[gmask[g2f] | cb]:
                                members[f] = newmem; gmask[f] = g
                                members[g2f].append(y); gmask[g2f] |= cb
                                fail.remove(x); done = True; break
                        if done: break
                if done: break
            if not done: break
        if not fail and all(len(m)==7 for m in members):
            return members, DM
    return None, None

def embed_assign(nums, DM):
    k = len(nums)
    cl = [[(abs(nums[i]-nums[j])==1 or (DM[nums[i]]&DM[nums[j]])!=0) for j in range(k)] for i in range(k)]
    order = sorted(range(k), key=lambda i: -sum(cl[i]))
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
    return {nums[i]: pos[i] for i in range(k)}

def verify(N, members, DM):
    M = 7*N; seen=set()
    assert len(members)==N
    out=[]
    for mem in members:
        assert len(mem)==7
        for x in mem:
            assert 1<=x<=M and x not in seen; seen.add(x)
        asg = embed_assign(mem, DM); assert asg is not None
        cells=[None]*7
        for x,c in asg.items(): cells[c]=x
        for a,b in F_EDGES:
            x,y=cells[a],cells[b]
            assert abs(x-y)!=1 and (DM[x]&DM[y])==0
        out.append(cells)
    assert len(seen)==M
    return out

CANDS = [1,2]+list(range(6,21))+list(range(69,183))+list(range(1300,1594))
done = set()
if os.path.exists("solutions.jsonl"):
    for line in open("solutions.jsonl"):
        try: done.add(json.loads(line)["N"])
        except: pass
log = open("campaign.log","a")
for N in CANDS:
    if N in done: continue
    t0=time.time()
    sol, DM = solve_instance(N)
    if sol is None:
        log.write(f"{N} FAIL {time.time()-t0:.1f}s\n"); log.flush(); continue
    cells = verify(N, sol, DM)
    with open("solutions.jsonl","a") as f:
        f.write(json.dumps({"N":N,"flowers":cells})+"\n")
    log.write(f"{N} OK {time.time()-t0:.1f}s\n"); log.flush()
log.write("CAMPAIGN COMPLETE\n"); log.close()
