## Dragster Physics

#### States and Inputs

State of game depends on 6 variables:
  * Clutch flag: $$c \in \{ 0, 1 \}$$
  * Gear: $$y \in \{ 0, 1, 2, 3, 4 \}$$ where $$y = 0$$ indicates the
    'neutral' gear.
  * Motor speed: $$r \in \{ 0, \ldots, 31 \}$$
  * Dragster speed: $$v \in \{ 0, \ldots, 253 \}$$
  * Dragster position: $$x > 0$$. The game starts at $$x = 0$$ and ends when
    $$x \ge 24832$$.

Game (user) inputs:
  * Throttle: $$u^{\mathrm{th}} \in \{ 0, 1 \}$$.
  * Clutch: $$u^{\mathrm{cl}} \in \{ 0, 1 \}$$.


#### Effect of throttle

The throttle $$u^{\mathrm{th}}$$ affects the motor speed $$r$$. Motor speed
$$r$$ is incremented when $$u^{\mathrm{th}} = 1$$ and decremented otherwise.
To model the effect of the gear's transmission ratios, the increments are
applied only at a subset of time steps. These frame subsets depend on an
in-game global frame counter ($$t$$). 

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


#### Effect of clutch

Pressing the clutch switches gears. Whenever the clutch is _released_ the gear
increases by one. Pressing the clutch in fourth gear has no effect (the gear
stays in fourth position).

In addition to switching gears, pressing the clutch has additional side
effects on the updating rules of motor speed ($$r$$) and dragster speed
($$v$$) as explained the other subsections.


#### Effect motor speed

The motor speed $$r$$ determins whether the car accelerates or decelerates,
depending on the car's current speed $$v$$. A given gear and motor speed
determine the car's target (or reference) speed $$v^\mathrm{ref}$$. To model
the effect of a turbo charger, the target speed is boosted when $$r \ge 20$$
which is indicated by the turbo charger flag $$b$$ in the formulas below.

| Gear | Target speed |
|------|--------------|
| 0    | $$0$$        |
| 1    | $$r$$        |
| 2    | $$2r + b$$   |
| 3    | $$4r + 2b$$  |
| 4    | $$8r + 4b$$  |

If the car is slower than the target speed ($$v \lt v^\mathrm{ref}$$), it
accelerates by 2, if it is faster ($$v \gt v^\mathrm{ref}$$), it decelerates
by 1.

Additionally, if the target speed exceeds the actual speed by more than 15,
the motor speed is decremented by 1.


#### Effect of dragster speed

The speed simply affects the dragster's position. In each time step, the
position increases by the speed of the _previous_ time step.


#### Python implementation

The following Python code implements the above rules, except for the dragster
position $$x$$. The inputs are
  * `t`: global frame counter
  * `u`: current user input (2-tuple holding throttle and clutch input)
  * `x`: current game state (4-tuple holding clutch, gear, motor and car
    speed)

Output is the next game state (4-tuple). It returns `None` when the user
inputs were infeasible for the current state `x`.

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
