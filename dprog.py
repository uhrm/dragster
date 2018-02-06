
import sys
from datetime import datetime
from itertools import product
from time import perf_counter

ofs = 0  # global frame counter offset
m = 2*5*32*254+1  # size of state space
n = 167  # number of time steps

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

def idx(x):
    """Computes linearized index for system state x"""
    return (((x[0]*5 + x[1])*32 + x[2])*254 + x[3]) if x else m-1

def frm(j, ofs):
    """Compute frame number from time step"""
    return 159 + 2*(j+ofs)

def stp(frame, ofs):
    """Compute time step from frame number"""
    return (frame-159)//2 - ofs

def nxt(j, ofs, u, x):
    """Computes x[j+1] = f(u[j],x[j])"""
    # unpack variables
    c, y, r, v = x
    th, cl = u
    # motor speed (r)
    mask = (0x00, 0x00, 0x02, 0x06, 0x0E)
    rd = (3, 1, 1, 1, 1)
    k = (1-c)*y
    if frm(j, ofs) & mask[k] == 0:
        r = max(r + (2*th-1)*rd[k], 0)
    if r > 31:
        return None
    # dragster speed (v)
    if y > 0 and c == 0:
        vref = ((1 << y) >> 1)*r + ((1 << y) >> 2)*(r >= 20)
        if vref < v:
            v -= 1
        elif vref > v:
            if vref >= v + 16:
                r -= 1
            v += 2
    # gear (y)
    if cl == 0 and c == 1:
        y = min(y+1, 4)
    # clutch (c)
    c = cl
    return c, y, r, v

def fmtspan(d, prec=3):
    """Format a time span (in fractional seconds) into hrs/min/sec components"""
    p = 10**prec
    d = round(p*d)
    p = p*60*60
    h = d//p
    d = d - p*h
    p = p//60
    m = d//p
    d = d - p*m
    p = p//60
    s = d//p
    d = d - p*s
    if h > 0:
        return "{}h {:02d}m {:02d}.{:0{}}s".format(h, m, s, d, prec)
    elif m > 0:
        return "{}m {:02d}.{:0{}}s".format(m, s, d, prec)
    else:
        return "{}.{:0{}}s".format(s, d, prec)


# solve dynamic programming problem
tbeg = perf_counter()
u = [None]*(n-1)
Q = [None]*n
Q[n-1] = [0]*m
Q[n-1][m-1] = -sys.maxsize  # denoting infeasibility
for j in range(n-2, -1, -1):
    print(f"Frame {j} (eta: {fmtspan((perf_counter()-tbeg)/(n-2-j)*(j+1), prec=1) if j < n-2 else 'n/a'})")
    u[j] = [None]*(m-1)
    Q[j] = [None]*m
    Q[j][m-1] = -sys.maxsize  # denoting infeasibility
    for xj in product(range(2), range(5), range(32), range(254)):
        i = idx(xj)
        umax = max(product(range(2),range(2)), key=lambda u: Q[j+1][idx(nxt(j+1, ofs, u, xj))])
        u[j][i] = umax
        Qmax = Q[j+1][idx(nxt(j+1, ofs, umax, xj))]
        Q[j][i] = xj[3] + Qmax
print(f"Solver finished: {datetime.now().strftime('%Y-%m-%d %H:%M')} ({fmtspan(perf_counter()-tbeg)})")
print()

# read out solution
print(" r     Q")
print("----------")
for r in range(0, 32, 3):
    print(f"{r:2d}   {Q[0][idx((0, 0, r, 0))]:5d}")
