b0 = place(cq.Workplane("XY").add(cq.Solid.makeCone(24.8, 0, 25.6)), "z", (0.0, 0.0, 15.6))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(25.2, 0, 26.2)), "x", (0.0, 0.0, -20.0))
b2 = place(cq.Workplane("XY").add(cq.Solid.makeCone(26.1, 0, 26.2)), "x", (0.0, 0.0, 20.0))
result = b0.union(b1.union(b2))