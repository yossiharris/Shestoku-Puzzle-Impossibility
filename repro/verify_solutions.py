#!/usr/bin/env python3
"""Independent verifier for the Shestoku N-flower solution archive.
Usage: python3 verify_solutions.py solutions.jsonl
Checks, for every record: the numbers used are exactly {1..7N}; and for each
flower, listed in cell order 0..6, every edge of the flower graph joins two
numbers that are neither consecutive nor share a decimal digit."""
import json, sys

F_EDGES=[(0,2),(0,3),(0,5),(1,3),(1,4),(1,6),(2,5),(3,5),(3,6),(4,6)]
def digs(x): return set(str(x))
ok=0
for line in open(sys.argv[1] if len(sys.argv)>1 else "solutions.jsonl"):
    line=line.strip()
    if not line: continue
    rec=json.loads(line); N=rec["N"]; fl=rec["flowers"]
    assert len(fl)==N, N
    seen=set()
    for cells in fl:
        assert len(cells)==7
        for x in cells:
            assert isinstance(x,int) and 1<=x<=7*N and x not in seen, (N,x)
            seen.add(x)
        for a,b in F_EDGES:
            x,y=cells[a],cells[b]
            assert abs(x-y)!=1, (N,x,y,"consecutive")
            assert digs(x).isdisjoint(digs(y)), (N,x,y,"shared digit")
    assert len(seen)==7*N, N
    ok+=1
print(f"all {ok} archived solutions verified against the raw rules")
