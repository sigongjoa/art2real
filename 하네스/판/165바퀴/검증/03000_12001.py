b0 = place(cq.Workplane("XY").add(cq.Solid.makeCone(24.8, 0, 25.6)), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(24.2, 0, 26.2)), "z", (0.0, 0.0, 0.0))
result = b0.union(b1)