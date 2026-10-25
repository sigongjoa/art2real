b0 = place(cq.Workplane("XY").box(38.2, 23.1, 15.1, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 15.1)).center(-1.1, 1.0).hole(10.1, 7.7), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").box(31.0, 24.1, 15.1, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 15.1)).center(-1.2, 1.0).hole(10.5, 8.7), "z", (0.0, 0.0, -21.2))
result = b0.union(b1)