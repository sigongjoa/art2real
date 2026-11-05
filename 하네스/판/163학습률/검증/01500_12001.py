b0 = place(cq.Workplane("XY").box(100.0, 47.4, 1.6, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 1.6)).center(1.3, 1.3).hole(1.3), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XZ").polyline([(0.0, 0.0), (29.6, 0.0), (29.6, 21.6), (20.0, 21.6), (20.0, 4.7), (0.0, 4.7)]).close().revolve(360, (0, 0, 0), (0, 1, 0)), "y", (0.0, 0.0, 0.0))
result = b0.union(b1)