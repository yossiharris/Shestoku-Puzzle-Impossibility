import numpy as np
from itertools import permutations

F_EDGES = [(0,2),(0,3),(0,5),(1,3),(1,4),(1,6),(2,5),(3,5),(3,6),(4,6)]
ADJ = [set() for _ in range(7)]
for a,b in F_EDGES: ADJ[a].add(b); ADJ[b].add(a)
CBAR = [[(i!=j) and (j not in ADJ[i]) for j in range(7)] for i in range(7)]
PAIRS = [(i,j) for i in range(7) for j in range(i+1,7)]

mark = np.zeros(1<<21, dtype=np.uint8)
masks = set()
for perm in permutations(range(7)):
    m = 0
    for k,(i,j) in enumerate(PAIRS):
        if CBAR[perm[i]][perm[j]]: m |= 1 << k
    masks.add(m)
print("distinct permutation masks:", len(masks))
for m in masks: mark[m] = 1
# downward closure: g embeddable iff subset of some mask -> superset-OR DP
for b in range(21):
    m2 = mark.reshape(-1, 2, 1 << b)
    m2[:, 0, :] |= m2[:, 1, :]
print("embeddable labeled graphs:", int(mark.sum()), "of", 1<<21)
mark.tofile("embtable.bin")
# sanity: empty graph embeddable; full clique K7 not; triangle on {any 3} embeddable (via 2,3,4)
assert mark[0] == 1 and mark[(1<<21)-1] == 0
tri = 0
for k,(i,j) in enumerate(PAIRS):
    if i in (0,1,2) and j in (0,1,2): tri |= 1<<k
assert mark[tri] == 1
# K4 on {0,1,2,3} should NOT embed (max clique in CBAR is 3)
k4 = 0
for k,(i,j) in enumerate(PAIRS):
    if i < 4 and j < 4: k4 |= 1<<k
assert mark[k4] == 0
print("sanity checks pass")
