"""Exact digit counting machinery for the Shestoku N-flower problem.
A(E, M) = #{x in [1,M] : x uses no digit from set E}
S_d(M)  = M - A({d}, M)   (numbers containing digit d)
T(D, M) = #{x in [1,M] : x contains every digit in D} via inclusion-exclusion.
"""
from functools import lru_cache

def A(E_mask, M):
    """Count integers in [1, M] whose decimal digits avoid all digits in E_mask (bitmask)."""
    if M <= 0: return 0
    s = str(M)
    L = len(s)
    allowed = [d for d in range(10) if not (E_mask >> d) & 1]
    a = len(allowed)               # allowed digits incl 0 maybe
    a_nz = len([d for d in allowed if d != 0])  # allowed nonzero (leading)
    # numbers with fewer digits than L
    total = 0
    p = 1
    for length in range(1, L):
        total += a_nz * p
        p *= a
    # numbers with exactly L digits, <= M
    prefix_ok = True
    for i, ch in enumerate(s):
        d = int(ch)
        # choices strictly less than d at position i (nonzero if i==0)
        lo = 1 if i == 0 else 0
        cnt_less = len([x for x in allowed if lo <= x < d])
        total += cnt_less * (a ** (L - 1 - i))
        if (E_mask >> d) & 1:
            prefix_ok = False
            break
    if prefix_ok:
        total += 1  # M itself
    return total

def S(d, M):
    return M - A(1 << d, M)

def T(D_mask, M):
    """Numbers in [1,M] containing ALL digits in D_mask; inclusion-exclusion over subsets avoided."""
    # |contain all D| = sum_{E subset D} (-1)^{|E|} A(E, M)
    total = 0
    E = D_mask
    # iterate subsets of D_mask
    sub = D_mask
    while True:
        bits = bin(sub).count('1')
        total += (-1)**bits * A(sub, M)
        if sub == 0: break
        sub = (sub - 1) & D_mask
    return total

if __name__ == "__main__":
    # brute-force test
    import random
    def brute_A(E_mask, M):
        c = 0
        for x in range(1, M+1):
            if all(not (E_mask >> int(ch)) & 1 for ch in str(x)): c += 1
        return c
    def brute_T(D_mask, M):
        D = [d for d in range(10) if (D_mask>>d)&1]
        return sum(1 for x in range(1, M+1) if all(str(d) in str(x) for d in D))
    random.seed(1)
    for _ in range(300):
        M = random.randint(1, 30000)
        E = random.randint(0, 1023)
        assert A(E, M) == brute_A(E, M), (E, M)
    for _ in range(100):
        M = random.randint(1, 20000)
        D = random.choice([1<<1, (1<<1)|(1<<2), (1<<1)|(1<<2)|(1<<3), (1<<2)|(1<<7)])
        assert T(D, M) == brute_T(D, M), (D, M)
    # sanity vs paper's numbers
    assert S(1, 21) == 12 and S(1, 28) == 12 and S(2, 28) == 11
    assert S(1, 35) == 13 and S(2, 35) == 13
    print("all digit-DP tests pass; paper's small counts confirmed")
