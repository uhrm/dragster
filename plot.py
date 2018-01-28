
import argparse
import jinja2

from base64 import b64encode
from glob import glob
from itertools import islice
from pathlib import Path

from sim import parse_dump


# parse arguments
parser = argparse.ArgumentParser(description="Create an interactive SVG.")
parser.add_argument("runid", help="The identifier of the run.")
parser.add_argument("--romname", default="Dragster (1980) (Activision)", help="The name of the ROM file.")
parser.add_argument("--offset", type=int, default=0, help="Skip the first <n> frames.")
args = parser.parse_args()

# create output directory
Path('pages/plots').mkdir(parents=True, exist_ok=True)

# load states
states = [s for s in islice(parse_dump(args.romname, args.runid), args.offset, None)]
print(f"number of states: {len(states)}")

# load frames
frames = [str(b64encode(open(f, "rb").read()), 'ascii') for f in islice(sorted(glob(f"data/{args.romname}_dbg_{args.runid}_*.png")), args.offset, None)]
print(f"number of frames: {len(frames)}")

# create interactive svg
env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
template = env.get_template('race.svg.j2')
template.stream(states=states, frames=frames).dump(f"pages/plots/race_{args.runid}.svg")
