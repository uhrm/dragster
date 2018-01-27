
from base64 import b64encode
from collections import namedtuple
from flask import Flask, session, render_template, jsonify, redirect, url_for, escape, request
from http import HTTPStatus
from os import urandom

from sim import sim

# FrameState record
#   offset:     offset w.r.t global frame counter
#   maxframes:  number of frames to simulate
#   uth:        throttle user inputs
#   ucl:        clutch user inputs
#   states:     simulated frame states
Model = namedtuple('Model', ['offset', 'maxframes', 'uth', 'ucl', 'states'])

# input generator from lists
def listgen(uth, ucl):
    t = 1  # inputs start at frame 1
    while t < len(uth) and t < len(ucl):
        yield uth[t], ucl[t]
        t += 1

def compute_model(offset, maxframes, uth, ucl):
    return Model(
        offset=offset,
        maxframes=maxframes,
        uth=uth,
        ucl=ucl,
        states=list(sim(listgen(uth, ucl), offset))
    )

# global model dict (holding session data)
model = {}

app = Flask(__name__)
app.secret_key = urandom(16)

@app.route('/')
def index():
    if 'key' not in session:
        # create unique session key
        key = urandom(16)
        print(f"init session with key {b64encode(key).decode('utf-8')}")
        session['key'] = key
        offset = 0
        maxframes = 493
        uth = [0 if j-offset < 149 else 1 for j in range(maxframes)]
        ucl = [1 if j-offset in (159, 160, 193, 194, 225, 226, 265, 266) else 0 for j in range(maxframes)]
        model[key] = compute_model(offset, maxframes, uth, ucl)
    key = session['key']
    # print(model[key])
    return render_template('race.html.j2', maxframes=model[key].maxframes, states=model[key].states)

@app.route('/u', methods=['POST'])
def toggle():
    r = 'none'
    if 'key' in session:
        m = model[session['key']]
        u = None
        content = request.get_json(silent=True)
        if content.get('type', None) == 'th':
            u = m.uth
        elif content.get('type', None) == 'cl':
            u = m.ucl
        try:
            i = int(content.get('frame', -1))
        except ValueError:
            i = -1
        if u is not None and 0 <= i < len(u):
            u[i] = 1 - u[i]
            model[session['key']] = compute_model(m.offset, m.maxframes, m.uth, m.ucl)
            r = f"({content.get('type')},{content.get('frame')})"
            print(f"toggled {r}")
    return ('', HTTPStatus.NO_CONTENT)
    # return render_template('race.html.j2', maxframes=m.maxframes, states=m.states)
