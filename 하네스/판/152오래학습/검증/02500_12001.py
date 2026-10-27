b0 = place(cq.Workplane("XY").box(49.4, 41.4, 20.2, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 20.2)).center(10.0, 10.0).hole(10.1, 10.0), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").box(41.2, 41.2, 20.2, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 20.2)).center(10.0, 10.0).hole(10.1, 10.0), "z", (0.0, 0.0, 29.9))
result = b0.union(b1)