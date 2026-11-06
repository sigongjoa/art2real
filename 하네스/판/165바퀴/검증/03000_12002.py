b0 = place(cq.Workplane("XY").add(cq.Solid.makeCone(25.2, 0, 24.6)), "z", (0.0, 0.0, 14.9))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(25.2, 0, 24.6)), "z", (0.0, 0.0, -20.0))
b2 = place(cq.Workplane("XY").add(cq.Solid.makeCone(26.2, 0, 23.1)), "z", (0.0, 0.0, 21.9))
result = b0.union(b1.union(b2))