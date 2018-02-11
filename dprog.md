## Solving Dragster Optimally

#### Problem formulation

From the description of the [game's physics](physics.md) one can see that it
can be modeled as a deterministic, discrete-time system of the form

$$
x_{j+1} = f_j(x_j, u_j)
$$

where the state $$x_j \in \mathcal{S}$$ and the inputs $$u_j \in
\mathcal{U}$$. The subscripts $$j$$ indicate the time step. Note that the
state-update function $$f_j(\cdot,\cdot)$$ is time-inhomogeneous because of
the frame rule for updating the motor speed. 

The state space

$$
\mathcal{S} = \mathcal{S}^{(c)} \times \mathcal{S}^{(y)} \times \mathcal{S}^{(r)} \times \mathcal{S}^{(v)} 
$$

is the cartesian product of four variables $$c \in \mathcal{S}^{(c)}$$
(clutch), $$y \in \mathcal{S}^{(y)}$$ (gear), $$r \in \mathcal{S}^{(r)}$$
(motor speed), and $$v \in \mathcal{S}^{(v)}$$ (dragster speed). With the
given domains of the state variables $$(c, y, r, v)$$, the state space has

$$
|\mathcal{S}| = 2 \times 5 \times 32 \times 254 = 81280
$$

different configurations. Similarly, the input space

$$
\mathcal{U} = \mathcal{U}^{(\mathrm{th})} \times \mathcal{U}^{(\mathrm{cl})} 
$$

is the cartesian product of two variables $$u^{(\mathrm{th})} \in
\mathcal{U}^{(\mathrm{th})}$$ (throttle) and $$u^{(\mathrm{cl})} \in
\mathcal{U}^{(\mathrm{cl})}$$ (clutch) with a cardinality of $$|\mathcal{U}| =
2 \times 2 = 4$$.

The objective is to maximize the distance in a fixed amount of time $$n$$.
Since the distance at time $$n$$ is the sum of the speeds $$v_j$$ (the fourth
component of the state vector $$x_j$$) from $$j = 1, \ldots, n-1$$, this leads
to

$$\begin{align}\tag{P}\label{eq:prob}
\max_{u_j \in \mathcal{U}} \quad \sum_{j=1}^{n-1} v_j \\
\mathrm{s.t.} \qquad x_{j+1}  &=  f_j(x_j, u_j) \\
                     x_j     &\in \mathcal{S} \qquad \forall j = 2, \ldots, n \\
                     x_1     &\in \mathcal{S}^\circ
\end{align}$$

where $$\mathcal{S}^\circ$$ is denoting the set of feasible initial
conditions. Note that the speed of the final state $$x_n$$ does not influence
the objective value.


#### Dynamic programming

Since the cardinality of the state space $$\mathcal{S}$$ and input space
$$\mathcal{U}$$ are so small, it is possible to use a dynamic programming
approach to efficiently solve problem $$\eqref{eq:prob}$$ to optimality.

To this end, one decomposes the above problem into $$n$$ nested sub-problems
$$Q_j$$ as follows

$$
Q_j(x) \;\triangleq\; \max_{u \in \mathcal{U}} \; v + Q_{j+1}(f_j(x,u))
$$

with the initial condition $$Q_n(\cdot) \equiv 0$$.

One solves the problems $$Q_j$$ backwards in time and the best value of
$$Q_1(x)$$ (among any feasible initial $$x \in \mathcal{S}^\circ$$)
corresponds to the value of the original problem.


#### Python implementation

The following Python (pseudo-)code implements the solution of the dynamic
programming problems $$Q_j$$.

```python
u = [[None]*m for j in range(n-1)]
Q = [[0]*m for j in range(n)]
for j in range(n-2, -1, -1):
    for x in product(range(2),range(5),range(32),range(254)):
        umax = max(product(range(2),range(2)), key=lambda u: Q[j+1][f(j, u, x)])
        u[j][x] = umax
        Qmax = Q[j+1][f(j, umax, x)]
        Q[j][x] = x[3] + Qmax
```

__Remarks__

  * Indexing the lists `Q[j]`/`u[j]` by a 4-tuple `x` does not work &ndash;
    one has to transform the states into a linear index.
  * To deal with infeasible inputs, it is practical to augment the state space
    by one more state denoting infeasibility, _e.g._ $$\mathcal{S} \cup \{
    \square \}$$, and defining $$Q_j(\square) = -1$$.
  * The time index `j` in the above snippet does not correspond to the global
    frame counter $$t$$. One needs an explicit mapping between the two.
  * One can choose the initial time step $$j = 1$$ to be the last frame before
    the in-game timer starts running. In this case, the set of feasible
    initial conditions $$\mathcal{S}^\circ$$ are: $$c$$ arbitrary (0 or 1),
    $$y = 0$$, $$r$$ any multiple of 3 between 0 and 31, and $$v = 0$$. 
  * For reconstructing the optimal inputs, one has to store them in a table
    (`u[][]` above). However, one only needs the optimal values for the
    current time step `j` and the previous time step `j+1`. So one could
    eliminate the table `Q[][]` and improve a little bit on the memory
    efficienty of the above code.

A working implementation can be found in
[dprog.py](https://github.com/uhrm/dragster/blob/master/dprog.py).



{% include lib/mathjax.html %}
