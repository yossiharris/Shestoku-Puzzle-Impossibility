# Shestoku Impossibility Spectrum — reproduction package

Paper: *The Impossibility Spectrum of Shestoku: The Solvable Set Is Finite*, Yosef A. Harris (2026). arXiv preprint (math.CO) forthcoming; see also shestoku.com.

This repository accompanies the paper and regenerates every quantitative claim in it.

---

This package regenerates, from scratch, every quantitative claim in the paper:
the digit-bound intervals, every level of the saturation hierarchy, the final
257-element candidate set C, the exact re-certification of all excluded values,
and the verification of the solution archive. Each stage ends with hard
assertions against the numbers printed in the paper; any discrepancy aborts
with a nonzero exit code.

## Requirements

Python 3.10+, with:

    pip install -r requirements.txt

(numpy, scipy, ortools). No other dependencies. Total runtime is roughly 15-25 minutes for stages 0-10, plus ~30-40 minutes for stage 11 (the window-feasibility check); memory use stays under
a few GB.

## One-command reproduction

    ./run_all.sh

runs the twelve stages (0-11) below in order and prints `ALL STAGES PASS` on success.

## The stages

| stage | script | claim reproduced |
|---|---|---|
| 0 | `digitdp.py` | exact digit-counting routines self-tested against brute force on random ranges, plus the paper's small counts (e.g. S_1(21)=12) |
| 1 | `stage1_digit_scan.py` | digit-bound-violating intervals for all N <= 150000 (Table 1 rows labelled "digit bound"); largest passing N = 14762; 4349 passing values |
| 2 | `stage2_closed_form.py` | closed-form k-set saturation exclusions (Corollary 2), for all digit sets of size <= 4 |
| 3 | `stage3_lp.py` | LP relaxation of the saturation system (Theorem 2) on the stage-2 survivors |
| 4 | `stage4_integer_profile.py` | integer profile system (pre-tier); produces the intermediate candidate set {1,2} u [6,20] u [69,182] u [1387,1517] (262 values), refined by stage 9 |
| 5 | `stage5_exact_recert.py` | every value excluded at the (floating-point) LP level in stage 3 is re-proved infeasible by the exact integer solver, so no exclusion in the paper rests on floating point |
| 6 | `stage6_flow_system.py` | the class-flow relaxation is feasible at all 262 pre-tier candidates (historical check; the paper's final "no further exclusions" statement is stage 9) |
| 7 | `stage7_verify_solutions.py` | every archived solution (data/solutions.jsonl, 130 values of N covering {1,2} u [6,20] u [70,182]) is checked directly against the two rules on all ten flower edges, and against the pool {1,...,7N} |
| 8 | `stage8_envelope_constants.py` | numeric anchors of the finiteness lemma: Z_1(10^6)=531440=9^6-1, (9/10)^6 < 4/7, threshold N=142858, last-window edge N=14762 |
| 9 | `stage9_tier_rescan.py` | tier bounds (|D| <= 5) over the pre-tier candidates: kills exactly {69, 1514, 1515, 1516, 1517}; final candidate set C = {1,2} u [6,20] u [70,182] u [1387,1513] (257 values). Longest stage (~10-15 min) |
| 10 | `stage10_farkas_verify.py` | the four rational Farkas certificates for N=1514..1517 (data/farkas_certificates_1514_1517.json) verified in exact Fraction arithmetic: all coefficients >= 0, RHS = -3/2, -2, -9/4, -3 |
| 11 | `stage11_window_lp.py` | the augmented class-level relaxation (conservation, coverage, outer and total per-digit caps, pair digit-mass, one-fat-per-pair) is rationally feasible at every N in the open window [1387,1513] — the paper's Section 7.3 claim. Longest stage (~30-40 min); accepts `lo hi` arguments for chunked runs |

Stage outputs are written as JSON to `results/` so intermediate numbers can be
inspected directly.

## Exactness policy

All impossibility claims rest on integer arithmetic end to end:

- Stages 1-2 use int64 cumulative sums of digit indicators (exact for these magnitudes).
- Stages 4-6 use CP-SAT (Google OR-Tools), an exact integer solver; a verdict
  of INFEASIBLE is a proof, not a numerical judgement.
- Stage 3 uses a floating-point LP (HiGHS via SciPy) **only as a filter**:
  every exclusion it proposes is independently re-proved in exact integer
  arithmetic by stage 5. The LP is never the final word on any excluded N.
- `digitdp.py` provides an independent exact digit-position recursion,
  brute-force tested, used by stages 4-5 so those stages do not share code
  with the stage-1 scan.

## Solution archive and verifier

`data/solutions.jsonl` holds one JSON record per verified N: for each of the N
flowers, its seven numbers in cell order 0..6 (cell 3 is the hub). The
standalone `verify_solutions.py` re-checks the archive with no dependencies
beyond the Python standard library:

    python3 verify_solutions.py data/solutions.jsonl

## Search code (not required for verification)

The `search/` directory contains the heuristic construction programs used to
*find* the archived solutions (greedy with an embeddability lookup table,
profile-guided variants, local search). These are randomized and are included
for transparency only; the paper's solvability claims rest solely on the
archive plus the independent verifier above, not on the searches.

## Correspondence to the paper

- Table 1 rows "digit bound": stage 1.
- Table 1 rows "pair saturation" / "k-set saturation": stage 2.
- Table 1 rows "integer profile system", and [67,68]: stages 3-5 (with the
  hand-checkable certificates of Proposition 2 and Appendix A).
- Theorem 4 (the candidate set C): stages 4 and 9 (stage 9 applies the tier bound, removing 69 and 1514-1517).
- "The tier-augmented integer profile system was evaluated on all 257 members
  of C and found feasible on every one": stage 9.
- Table 1 row "[1514,1517] tier bound (rational Farkas)": stage 10.
- Proposition (N=69): constants recomputable by one-line loops; the tier kill
  is also reproduced inside stage 9.
- Section 7.2 (verified solvability): stage 7.
- Lemma 3 / Theorem 3 constants: stage 8 (the lemma itself is analytic and
  proved in the paper; stage 8 checks only its quoted constants).
