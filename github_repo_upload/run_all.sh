#!/bin/sh
# Full reproduction of the impossibility spectrum and verification of all claims.
# Total runtime: stages 0-10 roughly 15-25 minutes; stage 11 adds ~30-40 minutes.
set -e
python3 digitdp.py                      # stage 0: exact-counting self-tests vs brute force
python3 stage1_digit_scan.py            # digit-bound intervals, all N <= 150000
python3 stage2_closed_form.py           # closed-form k-set saturation kills
python3 stage3_lp.py                    # LP relaxation of the saturation system
python3 stage4_integer_profile.py       # integer profile system -> final candidate set C
python3 stage5_exact_recert.py          # exact re-certification of every LP-level kill
python3 stage6_flow_system.py           # class-flow feasibility at all 262 candidates
python3 stage7_verify_solutions.py      # independent verification of the solution archive
python3 stage8_envelope_constants.py    # numeric anchors for the finiteness lemma
python3 stage9_tier_rescan.py           # tier bound: kills exactly {69,1514..1517} -> C (257)
python3 stage10_farkas_verify.py
python3 stage11_window_lp.py                # window relaxation feasible at all 127 open values (~30-40 min; accepts lo hi args for chunking)        # exact rational Farkas certificates for 1514..1517
echo "ALL STAGES PASS: every quantitative claim of the paper reproduced."
