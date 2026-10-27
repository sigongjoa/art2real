b0 = place(cq.Workplane("XY").circle(20.0).extrude(21.2).faces(">Z").workplane(origin=(0, 0, 21.2)).center(1.1, 1.1).hole(11.1), "x", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(22.0, 0, 21.0)), "z", (0.0, 0.0, 21.0))
b2 = place(cq.Workplane("XY").circle(20.0).extrude(22.2), "z", (0.0, 0.0, 21.0))
result = b0.union(b1.union(b2))