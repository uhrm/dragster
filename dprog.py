
import argparse
import sys
from datetime import datetime
from itertools import product
from pathlib import Path
from sim import write_script
from time import perf_counter


# parse arguments
parser = argparse.ArgumentParser(description="Compute optimal Dragster inputs.")
# parser.add_argument("--romname", default="Dragster (1980) (Activision)", help="The name of the ROM file.")
parser.add_argument("--offset", type=int, default=0, help="Global frame counter offset for starting game.")
parser.add_argument("--nsteps", type=int, default=168, help="Number of time steps to optimize.")
parser.add_argument("--save", action="store_true", help="Save best solution to Stella script file.")
args = parser.parse_args()

# global parameters
ofs = args.offset  # offset (in time steps) of game start relative to global frame counter [0-7]
m = 2*5*32*254+1  # size of state space
n = args.nsteps  # number of time steps (default 168 corresponds to a 5.57 finish time)

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

# read out solution
print()
print("c  r     Q")
print("------------")
for c, r in product(range(2), range(0,32,3)):
    print(f"{c} {r:2d}   {Q[0][idx((c, 0, r, 0))]:5d}")

# find best starting condition
x0 = max(product(range(2), range(0,32,3)), key=lambda x: Q[0][idx((x[0], 0, x[1], 0))])
x0 = (x0[0], 0, x0[1], 0)

print()
print("j    frame  th  cl  c   y   r    v     Q")
print("------------------------------------------")
print(f"{j:<3d}  {frm(j, ofs):<5d}  -    -  {x0[0]:<2d}  {x0[1]:<2d}  {x0[2]:2d}  {x0[3]:3d}  {Q[0][idx(x0)]:5d}")
xj = x0
for j in range(1, n):
    uj = u[j-1][idx(xj)]
    xj = nxt(j, ofs, uj, xj)
    Qj = Q[j][idx(xj)]
    print(f"{j:<3d}  "
          f"{frm(j, ofs):<5d}  "
          f"{uj[0]:<2d}  "
          f"{uj[1]:<2d}  "
          f"{xj[0]:<2d}  "
          f"{xj[1]:<2d}  "
          f"{xj[2]:2d}  "
          f"{xj[3]:3d}  "
          f"{Qj:5d}  ")


# input generator from optimal solution
def dproggen(ofs, x0):
    t = 1  # inputs start at frame 1
    while stp(t, ofs) <= -x0[2]//3:
        yield 0, 0
        t += 1
    while stp(t, ofs) < 0:
        yield 1, 0
        t += 1
    j = 0
    yield 1, x0[0]
    t += 1
    yield 1, x0[0]
    t += 1
    j += 1
    xj = x0
    while j < n:
        uj = u[j-1][idx(xj)]
        xj = nxt(j, ofs, uj, xj)
        yield uj[0], uj[1]
        t += 1
        yield uj[0], uj[1]
        t += 1
        j += 1


if args.save:
    # write Stella debug script
    print(f"Writing script file 'dprog{n:03d}_ofs{2*ofs:X}'.")
    Path('scripts').mkdir(parents=True, exist_ok=True)  # create 'scripts' directory
    with open(f"scripts/dprog{n:03d}_ofs{2*ofs:X}.script", "w") as script:
        write_script(script, dproggen(ofs, x0), 2*ofs, frm(n, ofs)-1)
