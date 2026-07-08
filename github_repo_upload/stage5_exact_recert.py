"""Stage 5: exact re-certification. Every N excluded at the LP level in stage 3 is
re-verified INFEASIBLE by the exact integer solver, so all Table-1 'integer profile
system' rows rest on exact arithmetic (LP floating point is only a filter, never the proof)."""
import json, time
from _ip_common import ip_status
lpk = json.load(open("results/stage3.json"))["lp_kills"]
targets = [n for a, b in lpk for n in range(a, b+1)]
bad = []
t0 = time.time()
for N in targets:
    if ip_status(N) is not False: bad.append(N)
json.dump({"recertified": len(targets) - len(bad), "failures": bad},
          open("results/stage5.json", "w"), indent=1)
assert not bad, bad
print(f"STAGE 5 PASS: all {len(targets)} LP-level exclusions re-certified exactly infeasible "
      f"({time.time()-t0:.0f}s)")
