"""Stage 10: exact rational verification of the Farkas infeasibility certificates for
N = 1514..1517 (tier-augmented Chvatal-rounded system). Pure Fractions arithmetic."""
import json
from fractions import Fraction

certs = json.load(open('data/farkas_certificates_1514_1517.json'))
def dmask(x):
    m = 0
    while x: m |= 1 << (x % 10); x //= 10
    return m

def verify(Nstr):
    N = int(Nstr); M = 7*N
    DM = [dmask(x) for x in range(M+1)]
    Sd = [sum(1 for x in range(1, M+1) if (DM[x] >> d) & 1) for d in range(10)]
    s = [max(0, Sd[d] - 2*N) for d in range(10)]
    rows = {eval(k): Fraction(v) for k, v in certs[Nstr]['certificate'].items()}
    mu = rows.get(('total',), Fraction(0))
    dem = {k[1]: v for k, v in rows.items() if k[0] == 'demand'}
    caps = {tuple(sorted(k[1])): v for k, v in rows.items() if k[0] == 'cap'}
    tiers = {(tuple(sorted(k[1])), k[2]): v for k, v in rows.items() if k[0] == 'tier'}
    def cT(D):
        mk = sum(1 << d for d in D)
        return sum(1 for x in range(1, M+1) if (DM[x] & mk) == mk)
    def cU(D, j):
        mk = sum(1 << d for d in D)
        return sum(1 for x in range(1, M+1) if bin(DM[x] & mk).count('1') >= j)
    rhs = mu * N
    for d, y in dem.items(): rhs -= y * s[d]
    for D, y in caps.items(): rhs += y * (cT(D) // 3)
    for (D, j), y in tiers.items(): rhs += y * (cU(D, j) // 3)
    minc = None
    for Sm in range(1 << 10):
        c = mu
        for d, y in dem.items():
            if (Sm >> d) & 1: c -= y
        for D, y in caps.items():
            if all((Sm >> d) & 1 for d in D): c += y
        for (D, j), y in tiers.items():
            if sum((Sm >> d) & 1 for d in D) >= j: c += y
        if minc is None or c < minc: minc = c
    assert minc >= 0 and rhs < 0, (Nstr, rhs, minc)
    return rhs

for n in ('1514','1515','1516','1517'):
    r = verify(n)
    print(f"  N={n}: Farkas RHS = {r} < 0, all coefficients >= 0  -> exact infeasibility certified")
print("STAGE 10 PASS: all four rational Farkas certificates valid in exact arithmetic")
