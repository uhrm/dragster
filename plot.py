
import base64
import jinja2

from glob import glob

from sim import parse_dump


# rom name
romname = 'Dragster (1980) (Activision)'

# run
runid = "b205071d"
# ***DEBUG***
# for s in states:
#     print(s)
# exit(0)
# ***DEBUG***

# load states
states = [s for s in parse_dump(romname, runid)]
print(f"number of states: {len(states)}")

# load frames
frames = [str(base64.b64encode(open(f, "rb").read()), 'ascii') for f in sorted(glob(f"data/{romname}_dbg_{runid}_*.png"))]
print(f"number of frames: {len(frames)}")

# create interactive svg
env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
template = env.get_template('template.svg')
template.stream(states=states, frames=frames, maxframe=len(states)).dump(f"race_{runid}.svg")
