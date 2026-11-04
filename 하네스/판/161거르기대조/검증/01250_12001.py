b0 = place(cq.Workplane("XY").box(100.0, 47.2, 26.6, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 26.6)).center(10.1, 10.0).hole(10.0), "z", (0.0, 0.0, 0.0))
result = b0