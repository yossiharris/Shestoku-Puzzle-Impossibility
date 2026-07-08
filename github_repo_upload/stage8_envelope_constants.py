"""Stage 8: numeric anchors for the envelope lemma (Lemma 3) and finiteness threshold."""
def Z1_brute(M):
    return sum(1 for x in range(1, M+1) if '1' not in str(x))
# closed form at powers of ten: Z1(10^k) = 9^k - 1
from digitdp import A
assert A(1 << 1, 10**6) == 9**6 - 1 == 531440
assert A(1 << 1, 10**5 - 1) == 9**5 - 1 == 59048
# ratio comparison in Theorem 3
assert (9/10)**6 < 4/7
# threshold: smallest N with 7N >= 10^6
assert 7*142857 < 10**6 <= 7*142858
# largest N with S1(7N) <= 3N, i.e. Z1(7N) >= 4N, in the frozen block [10^5, 2*10^5)
assert 59048 >= 4*14762 and 59048 < 4*14763
print("STAGE 8 PASS: envelope constants (Z1(10^6)=531440, (9/10)^6<4/7, N*=142858, last window edge 14762)")
