b0 = place(cq.Workplane("XY").box(100.0, 46.4, 25.7, centered=(True, True, False)), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").box(40.8, 46.4, 25.4, centered=(True, True, False)), "y", (0.0, 0.0, 0.0))
result = b0.union(b1)