
from collections import namedtuple


# FrameState record
#   frame:     frame counter
#   status:    game/player status
#   countdown: game start countdown
#   time:      game race time
#   x:         distance
#   v:         speed
#   y:         gear
#   r:         motor r.p.m.
#   vr:        reference speed
#   th:        throttle
#   cl:        clutch
#   rs:        restart
FrameState = namedtuple('FrameState', ['frame', 'status', 'countdown', 'time', 'x', 'v', 'y', 'r', 'vr', 'th', 'cl', 'rs'])


def gearchr(y, cl):
    if cl == 1: return 'C'
    elif y == 0: return 'N'
    elif y == 1: return '1'
    elif y == 2: return '2'
    elif y == 3: return '3'
    elif y == 4: return '4'
    raise ValueError(f"Invalid gear: {y}.")


def printx(t, x, v, y, r, th, cl):
    if t < 0:
        print(f"{t:6d}  {t//16:5d}  {x:5d}  {v:3d}  {gearchr(y,cl)}  {r:3d}  {vref((1-cl)*y,r):3d}  {th}  {cl}")
    else:
        print(f"{t:6d}  {(t+1)//2*334//100/100:5.2f}  {x:5d}  {v:3d}  {gearchr(y,cl)}  {r:3d}  {vref((1-cl)*y,r):3d}  {th}  {cl}")


def vref(y, r):
    # compute reference speed for gear (y) and motor RPM (r)
    #   y=0: vref = 0
    #   y=1: vref = r
    #   y=2: vref = 2*r + c
    #   y=3: vref = 4*r + 2*c
    #   y=4: vref = 8*r + 4*c
    # with c=1 if r >= 20, c=0 otherwise
    return ((1 << y) >> 1)*r + ((1 << y) >> 2)*(r >= 20)


def sim(ingen, offset=0, verbose=0):
    """Simulate the game state."""

    # TODO: also support odd start frames
    if (offset & 0x01) != 0:
        ValueError(f"Odd numbered start frames are not supported: offset = {offset}.")

    # time
    t = 0
    tm = 0  # countdown
    tr = 1111000  # race time (invalid BCD value)

    # initial conditions
    x = 0  # distance
    v = 0  # speed
    y = 0  # gear
    r = 0  # motor rpm
    vr = 0 # reference speed

    busted = False

    # inputs
    th = thprev = 0
    cl = clprev = 0

    # start game (hard-coded)
    yield FrameState(frame=t, status=0x0100, countdown=tm, time=tr, x=x, v=v, y=1, r=r, vr=vr, th=0, cl=0, rs=0)
    for s in range(offset):
        t += 1
        th, cl = next(ingen)
        yield FrameState(frame=t, status=0x0100, countdown=tm, time=tr, x=x, v=v, y=1, r=r, vr=vr, th=th, cl=cl, rs=0)
    t += 1
    tm = 159
    th, cl = next(ingen)
    yield FrameState(frame=t, status=0, countdown=tm, time=tr, x=x, v=v, y=y, r=r, vr=vr, th=th, cl=cl, rs=1)
    t += 1
    tm = max(tm-1, 0)
    th, cl = next(ingen)

    # main loop
    while True:
        # check end conditions
        if tm > 0 and y > 0:
            if verbose > 0:
                print(f"{t:6d}  {t//16:5d}  EARLY")
            break  # early
        # print state
        if verbose > 0:
            printx(t, x, v, y, r, thprev, clprev)
        # yield current state
        yield FrameState(
            frame=t,
            status=0,
            countdown=tm,
            time=tr,
            x=x, v=v, y=y, r=r, vr=vr, th=th, cl=cl, rs=0)
        # update timer
        t += 1
        tm = max(tm-1, 0)
        tr = tr if tm > 0 else 334*(t & 0x01) if tr == 1111000 else tr+334 if t & 0x01 == 1 else tr
        # check for max time
        if tm == 0 and tr > 999999:
            if verbose > 0:
                print(f"{t:6d}  {99.99:5.2f}  TIME UP")
            # yield 'time up' state and quit
            yield FrameState(
                frame=t,
                status=0x0100,  # time up
                countdown=tm,
                time=999900,
                x=x, v=v, y=y, r=0, vr=0, th=th, cl=cl, rs=0)
            break  # time up
        # current inputs
        th, cl = next(ingen)
        # do state updates in odd frames only
        if t & 0x01 == 1:
            # update distance
            x += v
            # check for finish line
            if x >= 24832:  # <=> (x >> 8) > 0x60:
                if verbose > 0:
                    printx(t, x, v, y, r, thprev, clprev)
                # yield 'final' state and quit
                yield FrameState(
                    frame=t,
                    status=0x0100,  # finished
                    countdown=tm,
                    time=tr,
                    x=x, v=v, y=y, r=0, vr=0, th=th, cl=cl, rs=0)
                break
            # update motor RPM
            rpm_skip = [0x00, 0x00, 0x02, 0x06, 0x0E]
            rpm_incr = [0x03, 0x01, 0x01, 0x01, 0x01]
            yidx = (1-clprev)*y
            if t & rpm_skip[yidx] == 0:
                if th == 1:
                    r += rpm_incr[yidx]
                else:
                    r -= rpm_incr[yidx]
                r = max(r, 0)
            # check for 'busted'
            if r >= 32:  # r >= 0x20
                r = 0
                busted = True
            # update speed
            if y > 0 and clprev == 0:
                vr = vref(y, r)
                if vr < v:
                    v -= 1
                elif vr > v:
                    if vr-v >= 16:
                        r -= 1
                    v += 2
            # check for 'busted'
            if busted:
                if verbose > 0:
                    if t < 0:
                        print(f"{t:6d}  {t//16:5d}  BUSTED")
                    else:
                        print(f"{t:6d}  {t*668/10000:5.2f}  BUSTED")
                # yield 'busted' state and quit
                yield FrameState(
                    frame=t,
                    status=0x0001,  # busted
                    countdown=tm,
                    time=tr,
                    x=x, v=v, y=y, r=0, vr=vr, th=th, cl=cl, rs=0)
                break
            # update gear
            if cl == 0 and clprev == 1:
                y = min(y+1, 4)
            # save input values
            thprev = th
            clprev = cl
        # ***DEBUG***
        # if t > 10:
        #     break
        # ***ENDEBUG***


def write_script(script, ingen, offset=0, maxframe=None):
    """Write a Stella debug script for the given user inputs."""

    # previous inputs
    thprev = 0
    clprev = 0
    rsprev = 0

    for s in sim(ingen, offset):
        # inputs
        if s.th != thprev:
            script.write("joy0fire\n")
        if s.cl != clprev:
            script.write("joy0left\n")
        if s.rs != rsprev:
            script.write("joy0right\n")
        # update game logic
        script.write("stepwhile pc!=$f29a\n")
        script.write("savesnap\n")
        script.write("dump 80 ff 7\n")
        if maxframe and s.frame >= maxframe:
            break
        # save input values
        thprev = s.th
        clprev = s.cl
        rsprev = s.rs


# parse dump file
def parse_dump(romname, runid):
    """Parse a Stella dump file."""

    with open(f"data/{romname}_dbg_{runid}.dump", 'r') as f:
        fmsb = -1
        while True:
            data = [f.readline().split() for _ in range(10)]
            if len(data[0]) == 0:
                break
            # print(data)
            fidx = int(data[0][2], 16)
            if fidx == 0 or fmsb < 0:
                fmsb += 1
            yield FrameState(
                frame = (fmsb << 8) + fidx,
                status = (int(data[5][3], 16) << 8) + int(data[5][5], 16),  # $D2, $D4
                countdown = int(data[0][15], 16),
                time = 100000*(int(data[3][4], 16) >> 4)   +  \
                        10000*(int(data[3][4], 16) & 0x0F) +  \
                         1000*(int(data[3][6], 16) >> 4)   +  \
                          100*(int(data[3][6], 16) & 0x0F) +  \
                           10*(int(data[3][8], 16) >> 4)   +  \
                            1*(int(data[3][8], 16) & 0x0F),
                x = (int(data[3][12], 16) << 8) + int(data[4][3], 16),
                v = int(data[4][1], 16),
                y = int(data[4][14], 16) & 0x7F,
                r = int(data[2][10], 16),
                vr = 0, # FIXME: read out reference speed
                th = 1 - ((int(data[9][14], 16) & 0x80) >> 7),
                cl = 1 - ((int(data[9][1],  16) & 0x40) >> 6),  # 1 - ((int(data[2][15], 16) & 0x04) >> 2),
                rs = 1 - ((int(data[9][1],  16) & 0x80) >> 7)   # 1 - ((int(data[2][15], 16) & 0x08) >> 3)
            )


if __name__ == "__main__":

    import argparse
    from collections import deque
    from pathlib import Path

    # parse arguments
    parser = argparse.ArgumentParser(description="Create an interactive SVG.")
    parser.add_argument("runid", help="The identifier of the run.")
    parser.add_argument("--romname", default="Dragster (1980) (Activision)", help="The name of the ROM file.")
    parser.add_argument("--offset", type=int, default=0, help="Start frame offset (0-15).")
    parser.add_argument("--check-dump", action="store_true", help="Check simulation with Stella dump.")
    args = parser.parse_args()

    # demo input generator
    def demogen(offset):
        thtoggle = deque([148])
        cltoggle = deque([146, 164, 178, 180, 216, 218, 272, 274])
        th = 0
        cl = 0
        t = 1  # inputs start at frame 1
        while True:
            if len(thtoggle) > 0 and thtoggle[0]+offset == t:
                thtoggle.popleft()
                th = 1 - th
            if len(cltoggle) > 0 and cltoggle[0]+offset == t:
                cltoggle.popleft()
                cl = 1 - cl
            yield th, cl
            t += 1

    # write Stella debug script
    Path('scripts').mkdir(parents=True, exist_ok=True)  # create 'scripts' directory
    with open(f"scripts/{args.runid}.script", "w") as script:
        write_script(script, demogen(args.offset), args.offset)

    if args.check_dump:
        # compare dump with simulation
        ndiffs = 0
        for ss, sd in zip(sim(demogen(args.offset), args.offset), parse_dump(args.romname, args.runid)):
            if (ss.status != sd.status) or (ss.time != sd.time) or (ss.countdown != sd.countdown) or \
               (ss.x != sd.x) or (ss.v != sd.v) or (ss.y != sd.y) or (ss.r != sd.r) or (ss.th != sd.th):
                ndiffs += 1
                print(f"frame     {ss.frame:8d}  --  frame     {sd.frame:8d}")
                print(f"status    {ss.status:8d}  --  status    {sd.status:8d}")
                print(f"countdown {ss.countdown:8d}  --  countdown {sd.countdown:8d}")
                print(f"time      {ss.time:8d}  --  time      {sd.time:8d}")
                print(f"x         {ss.x:8d}  --  x         {sd.x:8d}")
                print(f"v         {ss.v:8d}  --  v         {sd.v:8d}")
                print(f"y         {ss.y:8d}  --  y         {sd.y:8d}")
                print(f"r         {ss.r:8d}  --  r         {sd.r:8d}")
                print(f"vr        {ss.vr:8d}  --  vr        {sd.vr:8d}")
                print(f"th        {ss.th:8d}  --  th        {sd.th:8d}")
                print(f"cl        {ss.cl:8d}  --  cl        {sd.cl:8d}")
                print(f"rs        {ss.rs:8d}  --  rs        {sd.rs:8d}")
                print()
        if ndiffs == 0:
            print('Frame states are equal.')