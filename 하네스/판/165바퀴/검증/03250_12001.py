b0 = place(cq.Workplane("XY").box(50.0, 34.2, 24.2, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 24.2)).center(10.4, 1.2).hole(11.1, 10.3).faces(">Z").workplane(origin=(0, 0, 24.2)).center(10.8, 1.0).hole(11.1, 10.3), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(21.0, 0, 22.0)), "y", (0.0, 0.0, 0.0))
result = b0.union(b1)