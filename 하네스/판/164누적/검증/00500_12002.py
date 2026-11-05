b0 = place(cq.Workplane("XY").box(100.0, 40.0, 2.6, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 2.6)).center(-10.0, -10.0).hole(10.0, 10.0), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").box(40.0, 26.6, 1.6, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 16.6)).center(-10.0, 1.1).hole(10.0, 1.6), "x", (0.0, 0.0, 0.0))
result = b0