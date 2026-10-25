b0 = place(cq.Workplane("XY").box(46.1, 31.1, 14.4, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 14.4)).center(-11.0, 10.0).hole(10.0), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").box(46.1, 21.1, 21.4, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 21.4)).center(-1.1, 1.1).hole(10.0, 10.0), "z", (0.0, 0.0, 0.0))
result = b0.union(b1)