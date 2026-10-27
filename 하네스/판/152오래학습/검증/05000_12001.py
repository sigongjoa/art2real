b0 = place(cq.Workplane("XY").add(cq.Solid.makeCone(20.4, 0, 23.4)), "y", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(22.2, 0, 15.0)), "z", (0.0, 0.0, -22.0))
b2 = place(cq.Workplane("XY").box(39.0, 31.0, 24.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 24.0)).center(-1.1, 1.0).hole(11.1, 11.0).faces(">Z").workplane(origin=(0, 0, 24.0)).center(-1.2, 1.1).hole(11.1, 11.0), "z", (0.0, 0.0, -22.0))
result = b0.union(b1.union(b2))