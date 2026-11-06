b0 = place(cq.Workplane("XY").circle(26.0).extrude(27.6), "y", (0.0, 27.6, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(26.0, 0, 27.6)), "y", (0.0, -26.6, 0.0))
b2 = place(cq.Workplane("XY").add(cq.Solid.makeCone(26.0, 0, 27.6)), "y", (0.0, 27.6, 0.0))
result = b0.union(b1.union(b2))