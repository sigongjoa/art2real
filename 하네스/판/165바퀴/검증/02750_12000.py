b0 = place(cq.Workplane("XY").circle(20.9).extrude(29.6).faces(">Z").workplane(origin=(0, 0, 29.6)).center(1.2, 1.0).hole(10.9, 15.5).faces(">Z").workplane(origin=(0, 0, 29.6)).center(1.9, 1.2).hole(11.9, 17.4), "z", (0.0, 0.0, 15.9))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(21.9, 0, 29.9)), "y", (0.0, 0.0, -19.9))
b2 = place(cq.Workplane("XY").add(cq.Solid.makeCone(21.9, 0, 29.9)), "y", (0.0, 0.0, 15.9))
result = b0.union(b1.union(b2))