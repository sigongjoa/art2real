b0 = place(cq.Workplane("XY").box(45.4, 31.1, 21.6, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 21.6)).center(-10.0, 1.0).hole(6.0, 10.1).faces(">Z").workplane(origin=(0, 0, 21.6)).center(10.1, 1.0).hole(6.0, 10.1), "z", (24.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").box(40.6, 40.6, 20.6, centered=(True, True, False)), "z", (-20.0, 0.0, 0.0))
result = b0.union(b1)