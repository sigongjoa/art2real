b0 = place(cq.Workplane("XZ").polyline([(0.0, 0.0), (24.9, 0.0), (24.9, 11.1), (15.8, 11.1), (15.8, 31.1), (0.0, 31.1)]).close().revolve(360, (0, 0, 0), (0, 1, 0)), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").circle(10.0).extrude(28.6).faces(">Z").workplane(origin=(0, 0, 28.6)).center(10.9, -1.1).hole(10.8), "z", (0.0, 0.0, 0.0))
b2 = place(cq.Workplane("XY").box(44.4, 41.2, 28.4, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 28.4)).center(1.8, -1.1).hole(11.1), "z", (0.0, 0.0, 0.0))
result = b0.union(b1.union(b2))