b0 = place(cq.Workplane("XY").box(67.9, 49.0, 23.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 23.0)).center(11.0, 10.9).hole(11.0), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").box(58.9, 49.0, 21.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 21.0)).center(-10.5, 10.4).hole(11.0, 10.0), "z", (0.0, 0.0, 0.0))
result = b0.union(b1)