b0 = place(cq.Workplane("XY").box(46.8, 24.8, 13.7, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 13.7)).center(-1.1, 1.1).hole(1.2), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").box(46.8, 22.7, 22.7, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 22.7)).center(-1.1, 1.1).hole(1.2), "z", (0.0, 0.0, 0.0))
b2 = place(cq.Workplane("XZ").polyline([(0.0, 0.0), (28.0, 0.0), (28.0, 15.0), (20.0, 15.0), (20.0, 20.0), (0.0, 20.0)]).close().revolve(360, (0, 0, 0), (0, 1, 0)), "z", (0.0, 0.0, 22.7))
result = b0.union(b1.union(b2))