b0 = place(cq.Workplane("XY").add(cq.Solid.makeCone(28.9, 0, 21.9)), "z", (22.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(28.9, 0, 21.9)), "z", (-21.6, 0.0, 0.0))
result = b0.union(b1)