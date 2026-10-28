b0 = place(cq.Workplane("XY").add(cq.Solid.makeCone(20.4, 0, 13.4)), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(20.4, 0, 13.9)), "z", (0.0, 0.0, -21.4))
b2 = place(cq.Workplane("XY").add(cq.Solid.makeCone(20.4, 0, 13.9)), "z", (0.0, 0.0, -21.4))
result = b0.union(b1.union(b2))