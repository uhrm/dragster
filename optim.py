
import gurobipy as grb
from gurobipy import GRB


# basic model
#
#  * model only odd frames where physics of player 0 is evaluated
#  * time starts 10 frames before race start (enough to max out -- but not bust -- the engine in gear N)
#

# parameters

n = 60  # number of frames


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
v = [0]*10 + [mod.addVar(vtype=GRB.INTEGER, obj=1.0, name=f"v({j})") for j in range(10,n)]
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
    for i in range(5):
        mod.addConstr(y[i][j], GRB.GREATER_EQUAL, y[i][j-1]-yc[j], f"S1({i},{j})")
        mod.addConstr(y[i][j], GRB.GREATER_EQUAL, y[i-1][j-1]-1+yc[j], f"S2({i},{j})")
        mod.addConstr(y[i][j], GRB.LESS_EQUAL, y[i][j-1]+yc[j], f"S3({i},{j})")
        mod.addConstr(y[i][j], GRB.LESS_EQUAL, y[i-1][j-1]+1-yc[j], f"S4({i},{j})")

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
    mod.addConstr(rd[0][j], GRB.LESS_EQUAL, -yr[0][j] + 2*u[0][j], f"Rd1(0,{j}")
    mod.addConstr(rd[0][j], GRB.GREATER_EQUAL, yr[0][j] + 2*u[0][j] - 2, f"Rd2(0,{j}")
    mod.addConstr(rd[0][j], GRB.LESS_EQUAL, yr[0][j], f"Rd3(0,{j}")
    mod.addConstr(rd[0][j], GRB.GREATER_EQUAL, -yr[0][j], f"Rd3(0,{j}")
    Rdrhs = (2*u[0][j], 2*u[0][j]-2, 0, 0)
    for i in range(1, 5):
        if (j-10) & rpm_skip[i] == 0:
            Rdrhs = (-yr[i][j]+Rdrhs[0], yr[i][j]+Rdrhs[1], yr[i][j]+Rdrhs[2], -yr[i][j]+Rdrhs[3])
    mod.addConstr(rd[1][j], GRB.LESS_EQUAL, Rdrhs[0], f"Rd1(1,{j}")
    mod.addConstr(rd[1][j], GRB.GREATER_EQUAL, Rdrhs[1], f"Rd2(1,{j}")
    mod.addConstr(rd[1][j], GRB.LESS_EQUAL, Rdrhs[2], f"Rd3(1,{j}")
    mod.addConstr(rd[1][j], GRB.GREATER_EQUAL, Rdrhs[3], f"Rd3(1,{j}")
    # mod.addConstr(r[j], GRB.EQUAL, (r[j-1] if j > 0 else 0) + 3*rd[0][j] + rd[1][j], f"R({j})")
    mod.addConstr(r[j], GRB.EQUAL, (r[j-1] if j > 0 else 0) + 3*rd[0][j] + rd[1][j] - rv[j], f"R({j})")

# turbocharger flag
#
#   (r[j]-19)/12 <= c[j] <= r[j]/20
#
for j in range(1, n):
    mod.addConstr(c[j], GRB.LESS_EQUAL, r[j]/20, f"Cub({j})")
    mod.addConstr(c[j], GRB.GREATER_EQUAL, (r[j]-19)/12, f"Clb({j})")

# ref speed
#
#   yr[0]=1:  vr[0] = 0
#   yr[1]=1:  vr[1] = r
#   yr[2]=1:  vr[2] = 2*r + c
#   yr[3]=1:  vr[3] = 4*r + 2*c
#   yr[4]=1:  vr[4] = 8*r + 4*c
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
#   vd[0][j] = 1    if yr[0][j-1]==0 and v[j-1] < vr[j]
#   vd[1][j] = 1    if yr[0][j-1]==0 and v[j-1] > vr[j]
#
#   v[j] = v[j-1] + 2*vd[0][j] - vd[1][j]
#
#   rv[j] = 1       if yr[0][j-1]==0 and v[j-1] < vr[j]-15
#
for j in range(1, n):
    # vd[0] (increment)
    mod.addConstr(vd[0][j], GRB.LESS_EQUAL, 1-yr[0][j-1], "")
    mod.addConstr(v[j-1] + 252*(yr[0][j-1]+vd[0][j]), GRB.GREATER_EQUAL, vr[1][j]+vr[2][j]+vr[3][j]+vr[4][j], "")
    mod.addConstr(v[j-1] - 252*(1-vd[0][j]), GRB.LESS_EQUAL, vr[1][j]+vr[2][j]+vr[3][j]+vr[4][j]-1, "")
    # vd[1] (decrement)
    mod.addConstr(vd[1][j], GRB.LESS_EQUAL, 1-yr[0][j-1], "")
    mod.addConstr(v[j-1] - 252*(yr[0][j-1]+vd[1][j]), GRB.LESS_EQUAL, vr[1][j]+vr[2][j]+vr[3][j]+vr[4][j], "")
    mod.addConstr(v[j-1] + 252*(1-vd[1][j]), GRB.GREATER_EQUAL, vr[1][j]+vr[2][j]+vr[3][j]+vr[4][j]+1, "")
    # v (speed)
    mod.addConstr(v[j], GRB.EQUAL, v[j-1] + 2*vd[0][j] - vd[1][j], "")
    # rv (motor speed increment)
    mod.addConstr(rv[j], GRB.LESS_EQUAL, 1-yr[0][j-1], "")
    mod.addConstr(v[j-1] + 252*(yr[0][j-1]+rv[j]), GRB.GREATER_EQUAL, vr[1][j]+vr[2][j]+vr[3][j]+vr[4][j]-15, "")
    mod.addConstr(v[j-1] - 252*(1-rv[j]), GRB.LESS_EQUAL, vr[1][j]+vr[2][j]+vr[3][j]+vr[4][j]-16, "")

status = mod.optimize()

if mod.status == GRB.OPTIMAL:
    print("j:       ", str.join(" ", (f"{j:4d}" for j in range(n))))
    print("u(th):   ", str.join(" ", (f"{int(uj.x):4d}" for uj in u[0])))
    print("u(cl):   ", str.join(" ", (f"{int(uj.x):4d}" for uj in u[1])))
    print("y(0):    ", str.join(" ", (f"{int(yj.x) if j >= 10 else yj:4d}" for j, yj in enumerate(y[0]))))
    print("y(1):    ", str.join(" ", (f"{int(yj.x) if j >= 10 else yj:4d}" for j, yj in enumerate(y[1]))))
    print("y(2):    ", str.join(" ", (f"{int(yj.x) if j >= 10 else yj:4d}" for j, yj in enumerate(y[2]))))
    print("y(3):    ", str.join(" ", (f"{int(yj.x) if j >= 10 else yj:4d}" for j, yj in enumerate(y[3]))))
    print("y(4):    ", str.join(" ", (f"{int(yj.x) if j >= 10 else yj:4d}" for j, yj in enumerate(y[4]))))
    print("yc:      ", str.join(" ", (f"{int(ycj.x) if j >= 1 else 0:4d}" for j, ycj in enumerate(yc))))
    print("yr(0):   ", str.join(" ", (f"{int(yrj.x) if j >= 1 else yrj:4d}" for j, yrj in enumerate(yr[0]))))
    print("yr(1):   ", str.join(" ", (f"{int(yrj.x) if j >= 1 else yrj:4d}" for j, yrj in enumerate(yr[1]))))
    print("yr(2):   ", str.join(" ", (f"{int(yrj.x) if j >= 1 else yrj:4d}" for j, yrj in enumerate(yr[2]))))
    print("yr(3):   ", str.join(" ", (f"{int(yrj.x) if j >= 1 else yrj:4d}" for j, yrj in enumerate(yr[3]))))
    print("yr(4):   ", str.join(" ", (f"{int(yrj.x) if j >= 1 else yrj:4d}" for j, yrj in enumerate(yr[4]))))
    print("rd(N):   ", str.join(" ", (f"{int(rdj.x):4d}" for rdj in rd[0])))
    print("rd(G):   ", str.join(" ", (f"{int(rdj.x):4d}" for rdj in rd[1])))
    print("r:       ", str.join(" ", (f"{int(rj.x):4d}" for rj in r)))
    print("c:       ", str.join(" ", (f"{int(cj.x) if j >= 1 else cj:4d}" for j, cj in enumerate(c))))
    print("vr(0):   ", str.join(" ", (f"{int(vrj):4d}" for vrj in [0]*n)))
    print("vr(1):   ", str.join(" ", (f"{int(vrj.x) if j >= 1 else vrj:4d}" for j, vrj in enumerate(vr[1]))))
    print("vr(2):   ", str.join(" ", (f"{int(vrj.x) if j >= 1 else vrj:4d}" for j, vrj in enumerate(vr[2]))))
    print("vr(3):   ", str.join(" ", (f"{int(vrj.x) if j >= 1 else vrj:4d}" for j, vrj in enumerate(vr[3]))))
    print("vr(4):   ", str.join(" ", (f"{int(vrj.x) if j >= 1 else vrj:4d}" for j, vrj in enumerate(vr[4]))))
    print("vd(inc): ", str.join(" ", (f"{int(vdj.x) if j >= 1 else 0:4d}" for j, vdj in enumerate(vd[0]))))
    print("vd(dec): ", str.join(" ", (f"{int(vdj.x) if j >= 1 else 0:4d}" for j, vdj in enumerate(vd[1]))))
    print("v:       ", str.join(" ", (f"{int(vj.x) if j >= 10 else vj:4d}" for j, vj in enumerate(v))))
    print("rv:      ", str.join(" ", (f"{int(rvj.x) if j >= 1 else rvj:4d}" for j, rvj in enumerate(rv))))
elif (mod.status == GRB.INF_OR_UNBD) or (mod.status == GRB.INFEASIBLE):
    # mod.computeIIS()
    # mod.write("%s.ilp" % "tmp")
    pass
