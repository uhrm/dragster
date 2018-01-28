
import argparse
import gurobipy as grb
from gurobipy import GRB


# parse arguments
parser = argparse.ArgumentParser(description="Compute optimal Dragster inputs.")
# parser.add_argument("--romname", default="Dragster (1980) (Activision)", help="The name of the ROM file.")
parser.add_argument("--offset", type=int, default=0, help="Global frame counter offset for starting game.")
parser.add_argument("--nsteps", type=int, default=177, help="Number of time steps to optimize.")
args = parser.parse_args()


# basic model
#
#  * model only odd frames where physics of player 0 is evaluated
#  * time starts 10 time steps (i.e. 20 frames) before race start (enough to
#    max out -- but not bust -- the engine in gear N)
#

# parameters

offset = args.offset  # offset (in time steps) of game start relative to global frame counter [0-7]
# n = 66  # number of time steps
n = args.nsteps  # number of time steps (default 177 corresponds to a 5.57 finish time)

def frame(j, offset):
    """Convert time step j to in-game frame number."""
    return 161+2*(j+offset-10)

def step(frame, offset):
    """Convert in-game frame number to time step j."""
    return (frame-161)//2 - offset + 10


# model

mod = grb.Model("dragster")

# objective sense
mod.modelSense = GRB.MAXIMIZE

# inputs (throttle, clutch)
u = [[mod.addVar(vtype=GRB.BINARY, name=f"u(th,{j})") for j in range(n)],
     [mod.addVar(vtype=GRB.BINARY, name=f"u(cl,{j})") for j in range(n)]]

# gear variables (N, 1, 2, 3, 4)
y = [[1]*10 + [mod.addVar(vtype=GRB.BINARY, name=f"y(0,{j})") for j in range(10,n)],
     [0]*10 + [mod.addVar(vtype=GRB.BINARY, name=f"y(1,{j})") for j in range(10,n)],
     [0]*10 + [mod.addVar(vtype=GRB.BINARY, name=f"y(2,{j})") for j in range(10,n)],
     [0]*10 + [mod.addVar(vtype=GRB.BINARY, name=f"y(3,{j})") for j in range(10,n)],
     [0]*10 + [mod.addVar(vtype=GRB.BINARY, name=f"y(4,{j})") for j in range(10,n)]]
# gear switch flag
yc = [None] + [mod.addVar(vtype=GRB.BINARY, name=f"yc({j})") for j in range(1,n)]
# gear/motor speed coupling
yr = [[1] + [mod.addVar(vtype=GRB.BINARY, name=f"yr0({j})") for j in range(1,n)],
      [0] + [mod.addVar(vtype=GRB.BINARY, name=f"yr1({j})") for j in range(1,n)],
      [0] + [mod.addVar(vtype=GRB.BINARY, name=f"yr2({j})") for j in range(1,n)],
      [0] + [mod.addVar(vtype=GRB.BINARY, name=f"yr3({j})") for j in range(1,n)],
      [0] + [mod.addVar(vtype=GRB.BINARY, name=f"yr4({j})") for j in range(1,n)]]

# motor speed
r = [mod.addVar(vtype=GRB.INTEGER, lb=0, ub=31, name=f"r({j})") for j in range(n)]
# motor speed increment (throttle)
rd = [[mod.addVar(vtype=GRB.INTEGER, lb=-1, ub=1, name=f"rd(0,{j})") for j in range(n)],
      [mod.addVar(vtype=GRB.INTEGER, lb=-1, ub=1, name=f"rd(1,{j})") for j in range(n)]]

# turbocharger flag (c == r >= 20)
c = [0] + [mod.addVar(vtype=GRB.BINARY, name=f"c({j})") for j in range(1,n)]

# ref speed (per gear)
vr = [[0]*n,
      [0] + [mod.addVar(vtype=GRB.INTEGER, name=f"vr(1,{j})") for j in range(1,n)],
      [0] + [mod.addVar(vtype=GRB.INTEGER, name=f"vr(2,{j})") for j in range(1,n)],
      [0] + [mod.addVar(vtype=GRB.INTEGER, name=f"vr(3,{j})") for j in range(1,n)],
      [0] + [mod.addVar(vtype=GRB.INTEGER, name=f"vr(4,{j})") for j in range(1,n)]]

# dragster speed
v = [0]*10 + [mod.addVar(vtype=GRB.INTEGER, obj=1.0 if j<n-1 else 0.0, name=f"v({j})") for j in range(10,n)]
# dragster speed increment
vd = [[None] + [mod.addVar(vtype=GRB.BINARY, name=f"vd(0,{j})") for j in range(1,n)],
      [None] + [mod.addVar(vtype=GRB.BINARY, name=f"vd(1,{j})") for j in range(1,n)]]
# motor speed increment (speed difference)
rv = [0] + [mod.addVar(vtype=GRB.BINARY, name=f"rv({j})") for j in range(1,n)]

mod.update()

# gear switching
#
#   yc[j] = u[cl][j-1]==1 and u[cl][j]==0
#
#   y[i][j] = y[i-1][j-1]    if yc[j]==1
#   y[i][j] = y[i][j-1]      otherwise
#
for j in range(1, n):
    mod.addConstr(yc[j], GRB.LESS_EQUAL, u[1][j-1], f"Sc1({j}")
    mod.addConstr(yc[j], GRB.LESS_EQUAL, 1-u[1][j], f"Sc2({j}")
    mod.addConstr(yc[j], GRB.GREATER_EQUAL, u[1][j-1]-u[1][j], f"Sc3({j}")
    # y[0]
    mod.addConstr(y[0][j], GRB.GREATER_EQUAL, y[0][j-1]-yc[j], f"S1(0,{j})")
    mod.addConstr(y[0][j], GRB.LESS_EQUAL, y[0][j-1]+yc[j], f"S3(0,{j})")
    mod.addConstr(y[0][j], GRB.LESS_EQUAL, 1-yc[j], f"S4(0,{j})")
    # y[1] - y[3]
    for i in range(1, 4):
        mod.addConstr(y[i][j], GRB.GREATER_EQUAL, y[i][j-1]-yc[j], f"S1({i},{j})")
        mod.addConstr(y[i][j], GRB.GREATER_EQUAL, y[i-1][j-1]-1+yc[j], f"S2({i},{j})")
        mod.addConstr(y[i][j], GRB.LESS_EQUAL, y[i][j-1]+yc[j], f"S3({i},{j})")
        mod.addConstr(y[i][j], GRB.LESS_EQUAL, y[i-1][j-1]+1-yc[j], f"S4({i},{j})")
    # y[4]
    mod.addConstr(y[4][j], GRB.GREATER_EQUAL, y[4][j-1]-yc[j], f"S1(4,{j})")
    mod.addConstr(y[4][j], GRB.GREATER_EQUAL, y[3][j-1]+y[4][j-1]-1+yc[j], f"S2(4,{j})")
    mod.addConstr(y[4][j], GRB.LESS_EQUAL, y[4][j-1]+yc[j], f"S3(4,{j})")
    mod.addConstr(y[4][j], GRB.LESS_EQUAL, y[3][j-1]+y[4][j-1]+1-yc[j], f"S4(4,{j})")

# gear/motor speed coupling
#
#   yr[0][j] = y[0][j]==1 or u[cl][j-1]==1
#   yr[i][j] = y[i][j]==1 and u[cl][j-1]==0
#
for j in range(1, n):
    mod.addConstr(yr[0][j], GRB.GREATER_EQUAL, y[0][j], f"YR1(0,{j}")
    mod.addConstr(yr[0][j], GRB.GREATER_EQUAL, u[1][j-1], f"YR2(0,{j}")
    mod.addConstr(yr[0][j], GRB.LESS_EQUAL, y[0][j] + u[1][j-1], f"YR3(0,{j}")
    for i in range(1, 5):
        mod.addConstr(yr[i][j], GRB.LESS_EQUAL, y[i][j], f"YR1({i},{j}")
        mod.addConstr(yr[i][j], GRB.LESS_EQUAL, 1-u[1][j-1], f"YR2(0,{j}")
        mod.addConstr(yr[i][j], GRB.GREATER_EQUAL, y[i][j] - u[1][j-1], f"YR3({i},{j}")

# motor speed
#
#   rd[0][j] =  1    if yr[0][j]==1 and u[th][j]==1
#   rd[0][j] = -1    if yr[0][j]==1 and u[th][j]==0
#   rd[0][j] =  0    otherwise
#
#   rd[1][j] =  1    if sum(yr[i][j]*(j&mask[i]==0),i=1,..,4)==1 and u[th][j]==1
#   rd[1][j] = -1    if sum(yr[i][j]*(j&mask[i]==0),i=1,..,4)==1 and u[th][j]==0
#   rd[1][j] =  0    otherwise
#
#   r[j] = r[j-1] + 3*rd[0] + rd[1] - rv[j-1]
#
rpm_skip = [0x00, 0x00, 0x02, 0x06, 0x0E]
for j in range(n):
    mod.addConstr(rd[0][j], GRB.LESS_EQUAL, -yr[0][j] + 2*u[0][j], f"Rd1(0,{j})")
    mod.addConstr(rd[0][j], GRB.GREATER_EQUAL, yr[0][j] + 2*u[0][j] - 2, f"Rd2(0,{j})")
    mod.addConstr(rd[0][j], GRB.LESS_EQUAL, yr[0][j], f"Rd3(0,{j})")
    mod.addConstr(rd[0][j], GRB.GREATER_EQUAL, -yr[0][j], f"Rd3(0,{j})")
    Rdrhs = (2*u[0][j], 2*u[0][j]-2, 0, 0)
    for i in range(1, 5):
        if frame(j, offset) & rpm_skip[i] == 0:
            Rdrhs = (-yr[i][j]+Rdrhs[0], yr[i][j]+Rdrhs[1], yr[i][j]+Rdrhs[2], -yr[i][j]+Rdrhs[3])
    mod.addConstr(rd[1][j], GRB.LESS_EQUAL, Rdrhs[0], f"Rd1(1,{j})")
    mod.addConstr(rd[1][j], GRB.GREATER_EQUAL, Rdrhs[1], f"Rd2(1,{j})")
    mod.addConstr(rd[1][j], GRB.LESS_EQUAL, Rdrhs[2], f"Rd3(1,{j})")
    mod.addConstr(rd[1][j], GRB.GREATER_EQUAL, Rdrhs[3], f"Rd3(1,{j})")
    # mod.addConstr(r[j], GRB.EQUAL, (r[j-1] if j > 0 else 0) + 3*rd[0][j] + rd[1][j], f"R({j})")
    mod.addConstr(r[j], GRB.EQUAL, (r[j-1] if j > 0 else 0) + 3*rd[0][j] + rd[1][j] - rv[j-1], f"R({j})")

# turbocharger flag
#
#   (r[j]-19)/12 <= c[j] <= r[j]/20
#
for j in range(1, n):
    mod.addConstr(c[j], GRB.LESS_EQUAL, r[j]/20, f"Cub({j})")
    mod.addConstr(c[j], GRB.GREATER_EQUAL, (r[j]-19)/12, f"Clb({j})")

# ref speed
#
#   vr[0][j] = 0                  if yr[0][j] = 1
#   vr[1][j] = r[j]               if yr[1][j] = 1
#   vr[2][j] = 2*r[j] + c[j]      if yr[2][j] = 1
#   vr[3][j] = 4*r[j] + 2*c[j]    if yr[3][j] = 1
#   vr[4][j] = 8*r[j] + 4*c[j]    if yr[4][j] = 1
#
for j in range(1, n):
    # y = 1
    mod.addConstr(vr[1][j], GRB.LESS_EQUAL, 31*yr[1][j], "")
    mod.addConstr(vr[1][j], GRB.LESS_EQUAL, r[j], "")
    mod.addConstr(vr[1][j], GRB.GREATER_EQUAL, r[j]-31*(1-yr[1][j]))
    # y = 2
    mod.addConstr(vr[2][j], GRB.LESS_EQUAL, 63*yr[2][j], "")
    mod.addConstr(vr[2][j], GRB.LESS_EQUAL, 2*r[j]+c[j], "")
    mod.addConstr(vr[2][j], GRB.GREATER_EQUAL, 2*r[j]+c[j]-63*(1-yr[2][j]))
    # y = 3
    mod.addConstr(vr[3][j], GRB.LESS_EQUAL, 126*yr[3][j], "")
    mod.addConstr(vr[3][j], GRB.LESS_EQUAL, 4*r[j]+2*c[j], "")
    mod.addConstr(vr[3][j], GRB.GREATER_EQUAL, 4*r[j]+2*c[j]-126*(1-yr[3][j]))
    # y = 4
    mod.addConstr(vr[4][j], GRB.LESS_EQUAL, 252*yr[4][j], "")
    mod.addConstr(vr[4][j], GRB.LESS_EQUAL, 8*r[j]+4*c[j], "")
    mod.addConstr(vr[4][j], GRB.GREATER_EQUAL, 8*r[j]+4*c[j]-252*(1-yr[4][j]))

# dragster speed
#
#   vd[0][j] = 1    if yr[0][j]==0 and v[j-1] < vr[j]
#   vd[1][j] = 1    if yr[0][j]==0 and v[j-1] > vr[j]
#
#   v[j] = v[j-1] + 2*vd[0][j] - vd[1][j]
#
#   rv[j] = 1       if yr[0][j]==0 and v[j-1] < vr[j]-15
#
for j in range(1, n):
    # vd[0] (increment)
    mod.addConstr(vd[0][j], GRB.LESS_EQUAL, 1-yr[0][j], "")
    mod.addConstr(v[j-1] + 252*(yr[0][j]+vd[0][j]), GRB.GREATER_EQUAL, vr[1][j]+vr[2][j]+vr[3][j]+vr[4][j], "")
    mod.addConstr(v[j-1] - 252*(1-vd[0][j]), GRB.LESS_EQUAL, vr[1][j]+vr[2][j]+vr[3][j]+vr[4][j]-1, "")
    # vd[1] (decrement)
    mod.addConstr(vd[1][j], GRB.LESS_EQUAL, 1-yr[0][j], "")
    mod.addConstr(v[j-1] - 252*(yr[0][j]+vd[1][j]), GRB.LESS_EQUAL, vr[1][j]+vr[2][j]+vr[3][j]+vr[4][j], "")
    mod.addConstr(v[j-1] + 252*(1-vd[1][j]), GRB.GREATER_EQUAL, vr[1][j]+vr[2][j]+vr[3][j]+vr[4][j]+1, "")
    # v (speed)
    mod.addConstr(v[j], GRB.EQUAL, v[j-1] + 2*vd[0][j] - vd[1][j], "")
    # rv (motor speed increment)
    mod.addConstr(rv[j], GRB.LESS_EQUAL, 1-yr[0][j], "")
    mod.addConstr(v[j-1] + 252*(yr[0][j]+rv[j]), GRB.GREATER_EQUAL, vr[1][j]+vr[2][j]+vr[3][j]+vr[4][j]-15, "")
    mod.addConstr(v[j-1] - 252*(1-rv[j]), GRB.LESS_EQUAL, vr[1][j]+vr[2][j]+vr[3][j]+vr[4][j]-16, "")

# symmetry breaking
#
#   u[th][j] = 1    if sum(yr[i][j]*(j&mask[i]=1),i=1,..,4)==1
#
for j in range(1, n):
    Srhs = 0
    for i in range(1, 5):
        if (frame(j, offset) & rpm_skip[i]) != 0:
            Srhs = Srhs + yr[i][j]
    mod.addConstr(u[0][j], GRB.GREATER_EQUAL, Srhs, f"S{j}")


status = mod.optimize()

if (mod.status == GRB.OPTIMAL) or (mod.status == GRB.INTERRUPTED) or (mod.status == GRB.SUBOPTIMAL):
    print("j    frame  th  cl  y  yc  yr  rd  r   c  vr   vd  v    rv")
    for j in range(n):
        print(f"{j:<3d}  "
              f"{frame(j, offset):<5d}  "
              f"{int(u[0][j].x):<2d}  "
              f"{int(u[1][j].x):<2d}  "
              f"{sum(i*(int(y[i][j].x) if j >= 10 else y[i][j]) for i in range(5)):d}  "
              f"{int(yc[j].x) if j >= 1 else 0:<2d}  "
              f"{sum(i*(int(yr[i][j].x) if j >= 1 else yr[i][j]) for i in range(5)):<2d}  "
              f"{3*int(rd[0][j].x)+int(rd[1][j].x):2d}  "
              f"{int(r[j].x):<2d}  "
              f"{int(c[j].x) if j >= 1 else c[j]:d}  "
              f"{sum(int(vr[i][j].x) if j >= 1 else vr[i][j] for i in range(1, 5)):<3d}  "
              f"{2*(int(vd[0][j].x) if j >= 1 else 0)-(int(vd[1][j].x) if j >= 1 else 0):2d}  "
              f"{int(v[j].x) if j >= 10 else v[j]:<3d}  "
              f"{int(rv[j].x) if j >= 1 else rv[j]:d}")
elif (mod.status == GRB.INF_OR_UNBD) or (mod.status == GRB.INFEASIBLE):
    # mod.computeIIS()
    # mod.write("%s.ilp" % "tmp")
    pass


from pathlib import Path
from sim import write_script

# input generator from optimal solution
def optgen(offset):
    th = 0
    cl = 0
    t = 1  # inputs start at frame 1
    while True:
        j = step(t, offset)
        if j >= 0:
            th = int(u[0][j].x)
            cl = int(u[1][j].x)
        yield th, cl
        t += 1


# write Stella debug script
Path('scripts').mkdir(parents=True, exist_ok=True)  # create 'scripts' directory
with open(f"scripts/opt{n:03d}_ofs{2*offset:x}.script", "w") as script:
    write_script(script, optgen(offset), offset, frame(n, offset)-1)

