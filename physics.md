---
title: Dragster Physics
---

## Dragster Physics

#### States and Inputs

The evolution of the game can be modeled as a discrete-time dynamical system
of the form

$$
x_{t+1} = f_t(x_t, u_t)
$$

where $$t$$ is a global in-game frame counter, $$x_t$$ is the state in frame
$$t$$ and $$u_t$$ are the user inputs in frame $$t$$.

The state $$x = (c, y, r, v, z)$$ of the game is completely characterized by
five variables:

| Symbol | State             | Domain                                       | Comments                                                    |
|--------|-------------------|----------------------------------------------|-------------------------------------------------------------|
| $$c$$  | Clutch flag       | $$\mathcal{S}^{(c)} = \{ 0, 1 \}$$           |                                                             |
| $$y$$  | Gear              | $$\mathcal{S}^{(y)} = \{ 0, 1, 2, 3, 4 \}$$  | Gear $$y = 0$$ indicates the 'neutral' gear.                |
| $$r$$  | Motor speed       | $$\mathcal{S}^{(r)} = \{ 0, \ldots, 31 \}$$  |                                                             |
| $$v$$  | Dragster speed    | $$\mathcal{S}^{(v)} = \{ 0, \ldots, 253 \}$$ |                                                             |
| $$z$$  | Dragster position | $$\mathcal{S}^{(z)} = \{ 0, 1, \ldots \}$$   | The game starts at $$z = 0$$ and ends when $$z \ge 24832$$. |

The user input $$u = \left( u^{(\mathrm{th})}, u^{(\mathrm{cl})} \right)$$
consist of two variables:

| Symbol                 | Input    | Domain                                       |
|------------------------|----------|----------------------------------------------|
| $$u^{(\mathrm{th})}$$  | Throttle | $$\mathcal{U}^{(\mathrm{th})} = \{ 0, 1 \}$$ |
| $$u^{(\mathrm{cl})}$$  | Clutch   | $$\mathcal{U}^{(\mathrm{cl})} = \{ 0, 1 \}$$ |

Note that the clutch flag $$c$$ and the clutch user input
$$u^{(\mathrm{cl})}$$ are not redundant. The clutch flag $$c$$ denotes the
clutch input from the previous frame, _i.e._ $$c_t =
u^{(\mathrm{cl})}_{t-1}$$.


#### Effect of throttle

The throttle $$u^{(\mathrm{th})}$$ affects the motor speed $$r$$. Motor speed
$$r$$ is incremented when $$u^{(\mathrm{th})} = 1$$ and decremented otherwise.
To model the effect of the gear's transmission ratios, the increments are
applied only at a subset of time steps.

| Gear | Increment | Frame rule  |
|------|-----------|-------------|
| 0    | &plusmn;3 | every frame |
| 1    | &plusmn;1 | every frame |
| 2    | &plusmn;1 | every second frame (when $$t \mathrel{\&} 2_\mathrm{hex} = 0$$) |
| 3    | &plusmn;1 | every fourth frame (when $$t \mathrel{\&} 6_\mathrm{hex} = 0$$) |
| 4    | &plusmn;1 | every eighth frame (when $$t \mathrel{\&} \mathrm{E}_\mathrm{hex} = 0$$) |

The frame rule is not applied when the clutch was pressed in the previous time
step (indicated by state variable $$c = 1$$). In this case, the increment of
$$y = 0$$ is applied regardless.

Note that this frame rule makes the function $$f_t(\cdot,\cdot)$$
time-inhomogenous, _i.e._ the function itself depends on the frame counter
$$t$$.


#### Effect of clutch

Pressing the clutch switches gears. Whenever the clutch is _released_ the gear
increases by one. Releasing the clutch in fourth gear has no effect (the gear
stays in fourth position).

In addition to switching gears, pressing the clutch modulates the rules for
updating the motor speed $$r$$ (see [Effect of
throttle](#effect-of-throttle)).


#### Effect of motor speed

The motor speed $$r$$ determines whether the car accelerates or decelerates,
depending on the car's current speed $$v$$. A given gear and motor speed
determine the car's target (or reference) speed $$v^\mathrm{ref}$$. To model
the effect of a turbo charger, the target speed is boosted when $$r \ge 20$$
which is indicated by the turbo charger flag $$b$$ in the formulas below.

| Gear | Target speed  |
|------|---------------|
| 0    | $$0$$         |
| 1    | $$r$$         |
| 2    | $$2r + b$$    |
| 3    | $$4r + 2b$$   |
| 4    | $$8r + 4b$$   |

If the car is slower than the target speed ($$v \lt v^\mathrm{ref}$$), it
accelerates by 2, if it is faster ($$v \gt v^\mathrm{ref}$$), it decelerates
by 1.

Additionally, if the target speed exceeds the actual speed by 16 or more, the
motor speed is decremented by 1.

Motor speeds $$r \gt 31$$ are illegal. In the game, such states result in a
busted engine and the game is over.


#### Effect of dragster speed

The speed simply affects the dragster's position. In each time step, the
position increases by the speed of the _previous_ time step.


#### Python implementation

Since writing down the above rules in a mathematical formula for
$$f(\cdot,\cdot)$$ is tedious, we give a description in the form of Python
code which is more concise. The code snippet below implements the function
$$f(\cdot,\cdot)$$. The inputs are
  * `t`: global frame counter
  * `u`: current user input (2-tuple holding throttle and clutch input)
  * `x`: current game state (4-tuple holding clutch, gear, motor and car
    speed)

The output is the next game state (4-tuple). It returns `None` when the user
inputs were infeasible for the current state `x`.

Note that the function does not calculate the dragster position $$z$$, since
it is straightforward to get the position $$z_t$$ as the sum of speeds $$v_s$$
for $$s = 1, \ldots, t-1$$.

```python
mask = (0x00, 0x00, 0x02, 0x06, 0x0E)
rd = (3, 1, 1, 1, 1)

def f(t, u, x):
    # unpack variables
    c, y, r, v = x
    th, cl = u
    # motor speed (r)
    k = (1-c)*y
    if t & mask[k] == 0:
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
```


#### References

* Omnigamer's analysis of Dragster: <http://tasvideos.org/5517S.html>.


{% include lib/mathjax.html %}
