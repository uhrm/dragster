
import argparse
import base64
import jinja2

from glob import glob
from pathlib import Path

from sim import parse_dump


# parse arguments
parser = argparse.ArgumentParser(description='Create an interactive SVG.')
parser.add_argument("runid", help="The identifier of the run.")
parser.add_argument("--romname", help="The name of the ROM file.", default='Dragster (1980) (Activision)')
args = parser.parse_args()

# create output directory
Path('pages/plots').mkdir(parents=True, exist_ok=True)

# load states
states = [s for s in parse_dump(args.romname, args.runid)]
print(f"number of states: {len(states)}")

# load frames
frames = [str(base64.b64encode(open(f, "rb").read()), 'ascii') for f in sorted(glob(f"data/{args.romname}_dbg_{args.runid}_*.png"))]
print(f"number of frames: {len(frames)}")

# create interactive svg
env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
template = env.get_template('race.svg.j2')
template.stream(states=states, frames=frames, maxframe=len(states)).dump(f"pages/plots/race_{args.runid}.svg")
