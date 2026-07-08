"""Stage 4: integer profile system on stage-3 survivors -> final candidate set."""
import json
from _ip_common import ip_status
surv = json.load(open("results/stage3.json"))["survivors"]
Ns = [n for a, b in surv for n in range(a, b+1)]
alive, dead, unk = [], [], []
for N in Ns:
    r = ip_status(N)
    (alive if r is True else dead if r is False else unk).append(N)
def iv(l):
    out = []
    for n in l:
        if out and out[-1][1] == n-1: out[-1][1] = n
        else: out.append([n, n])
    return out
json.dump({"ip_kills": iv(dead), "final_candidates": iv(alive), "unknown": unk},
          open("results/stage4.json", "w"), indent=1)
assert not unk, unk
assert iv(dead) == [[1300,1386],[1518,1593]], iv(dead)
assert iv(alive) == [[1,2],[6,20],[69,182],[1387,1517]], iv(alive)
assert sum(b-a+1 for a,b in iv(alive)) == 262
print("STAGE 4 PASS: integer-profile kills and final candidate set C (262 values) match the paper")
