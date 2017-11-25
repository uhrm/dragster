
"""
Computing a (slightly nontrivial) lower bound.
"""

y = 0
v = 0
x = 0

j = 0
while x < 24832:
    j += 1
    x += v
    a = 2
    if v+a > ((1 << y) >> 1)*31 + ((1 << y) >> 2):
        a = 0
        y = min(y+1, 4)
    v += a
    print(f"j = {j:3d}   t = {j*334//100/100:4.2f}   v = {v:3d}   x = {x:5d} {'  (*)' if a == 0 and v < 252 else '  (-)' if a == 0 else ''}")
