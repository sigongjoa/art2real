b0 = place(cq.Workplane("XY").add(cq.Solid.makeCone(20.4, 0, 24.4)), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(20.4, 0, 14.5)), "z", (0.0, 33.3, 0.0))
b2 = place(cq.Workplane("XY").add(cq.Solid.makeCone(20.4, 0, 23.3)), "y", (0.0, 33.3, 0.0))
result = b0.union(b1.union(b2))