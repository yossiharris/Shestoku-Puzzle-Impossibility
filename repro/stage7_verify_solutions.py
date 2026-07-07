"""Stage 7: independent verification of the solution archive against the raw rules,
plus consistency with the paper's verified list."""
import json
F_EDGES = [(0,2),(0,3),(0,5),(1,3),(1,4),(1,6),(2,5),(3,5),(3,6),(4,6)]
def digs(x): return set(str(x))
Ns = []
for line in open("data/solutions.jsonl"):
    line = line.strip()
    if not line: continue
    rec = json.loads(line); N = rec["N"]; fl = rec["flowers"]
    assert len(fl) == N
    seen = set()
    for cells in fl:
        assert len(cells) == 7
        for x in cells:
            assert isinstance(x, int) and 1 <= x <= 7*N and x not in seen
            seen.add(x)
        for a, b in F_EDGES:
            x, y = cells[a], cells[b]
            assert abs(x - y) != 1 and digs(x).isdisjoint(digs(y))
    assert len(seen) == 7*N
    Ns.append(N)
Ns = sorted(set(Ns))
def iv(l):
    out = []
    for n in l:
        if out and out[-1][1] == n-1: out[-1][1] = n
        else: out.append([n, n])
    return out
EXPECTED = [[1,2],[6,20],[70,182]]
assert iv(Ns) == EXPECTED and len(Ns) == 130, (iv(Ns), len(Ns))
# every verified N must lie inside the candidate set (consistency check)
cands = set(n for a, b in json.load(open("results/stage4.json"))["final_candidates"] for n in range(a, b+1))
assert all(n in cands for n in Ns)
print(f"STAGE 7 PASS: all {len(Ns)} archived solutions verified against the raw rules; intervals match the paper")
