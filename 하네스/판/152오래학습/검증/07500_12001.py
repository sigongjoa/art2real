b0 = place(cq.Workplane("XY").box(58.2, 24.0, 13.5, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 13.5)).center(10.4, 1.1).hole(7.1, 5.5), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(15.6, 0, 14.5)), "z", (0.0, 0.0, -22.9))
b2 = place(cq.Workplane("XZ").polyline([(0.0, 0.0), (25.1, 0.0), (25.1, 11.0), (14.8, 11.0), (14.8, 25.1), (0.0, 25.1)]).close().revolve(360, (0, 0, 0), (0, 1, 0)), "z", (0.0, 0.0, -22.9))
result = b0.union(b1.union(b2))