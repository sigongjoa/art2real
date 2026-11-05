b0 = place(cq.Workplane("XY").box(100.0, 40.0, 40.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 40.0)).center(-10.0, 10.0).hole(10.0, 10.0), "z", (0.0, 0.0, 0.0))
result = b0