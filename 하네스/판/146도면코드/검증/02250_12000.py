b0 = place(cq.Workplane("XY").circle(23.2).extrude(32.2).faces(">Z").workplane(origin=(0, 0, 32.2)).center(-1.1, -1.2).hole(10.0, 10.0), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").box(46.5, 38.3, 15.4, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 15.4)).center(-1.1, 1.1).hole(10.0, 10.0), "z", (0.0, 0.0, 0.0))
result = b0.union(b1)