b0 = place(cq.Workplane("XY").box(62.8, 31.9, 25.2, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 25.2)).center(12.1, 10.9).hole(11.1, 11.0), "z", (-20.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").box(58.6, 47.9, 23.2, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 23.2)).center(13.1, 10.6).hole(11.1, 11.0), "z", (-20.0, 0.0, 0.0))
result = b0.union(b1)