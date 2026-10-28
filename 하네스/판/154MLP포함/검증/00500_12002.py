b0 = place(cq.Workplane("XY").box(46.6, 40.4, 10.2, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 10.2)).center(-1.1, 1.0).hole(1.3, 1.9).edges("|Z").fillet(2.7), "x", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").box(46.6, 27.6, 10.2, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 10.2)).center(1.4, 0.0, 0.0))
result = b0.union(b1.union(b2))