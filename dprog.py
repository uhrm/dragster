
from itertools import product

ofs = 0  # global frame counter offset
m = 2*2*2*5*32*254+1  # size of state space
n = 60  # number of time steps

#
# dragster state x
#   x[0]: clutch (c = 0..1)
#   x[1]: gear (y = 0..4)
#   x[2]: motor speed (r = 0..31)
#   x[3]: dragster speed (v = 0..253)
#
# user inputs u
#   u[0]: throttle
#   u[1]: clutch
#

def idx(u, x):
    """Computes linearized index for (u,x)"""
    return (((((u[0]*2 + u[1])*2 + x[0])*5 + x[1])*32 + x[2])*254 + x[3]) if x else m-1

def frm(j, ofs):
    """Compute frame number from time step"""
    return 159 + 2*(j+ofs)

def stp(frame, ofs):
    """Compute time step from frame number"""
    return (frame-159)//2 - ofs

def nxt(j, ofs, u, x):
    """Computes x[j+1] = f(u[j+1],x[j])"""
    c = x[0]
    y = x[1]
    r = x[2]
    v = x[3]
    # motor speed (r)
    mask = (0x00, 0x00, 0x02, 0x06, 0x0E)
    rd = (3, 1, 1, 1, 1)
    k = (1-c)*y
    if frm(j, ofs) & mask[k] == 0:
        if u[0] == 1:
            r += rd[k]
        else:
            r -= rd[k]
        r = max(r, 0)
    if r > 31:
        return None
    # dragster speed (v)
    if y > 0 and c == 0:
        vr = ((1 << y) >> 1)*r + ((1 << y) >> 2)*(r >= 20)
        if vr < v:
            v -= 1
        elif vr > v:
            if vr - v >= 16:
                r -= 1
            v += 2
    # gear (y)
    if u[1] == 0 and c == 1:
        y = min(y+1, 4)
    # clutch (c)
    c = u[1]
    return (c, y, r, v)

# solve dynamic programming problem
Q = [None]*n
Q[n-1] = [0]*m
Q[n-1][m-1] = -1  # denoting infeasibility
for j in range(n-2, -1, -1):
    print(f"Frame {j}")
    Q[j] = [None]*m
    Q[j][m-1] = -1  # denoting infeasibility
    for (uth, ucl, c, y, r, v) in product(range(2), range(2), range(2), range(5), range(32), range(254)):
        xj = (c, y, r, v)
        i = idx((uth, ucl), xj)
        Qmax = max(Q[j+1][idx(u, nxt(j+1, ofs, u, xj))] for u in product(range(2),range(2)))
        Q[j][i] = v + Qmax

# read out solution
print("th  cl  r   Q")
for (th, cl, r) in product(range(2), range(2), range(0, 32, 3)):
    print(f"{th}   {cl}   {r:<2d}  {Q[0][idx((th, cl), (0, 0, r, 0))]}")
