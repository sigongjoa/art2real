b0 = place(cq.Workplane("XY").box(48.2, 31.0, 13.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 13.0)).center(10.8, 1.0).hole(7.0, 5.0), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(20.4, 0, 33.3)), "z", (0.0, 0.0, 33.3))
b2 = place(cq.Workplane("XZ").polyline([(0.0, 0.0), (25.0, 0.0), (25.0, 11.0), (15.0, 11.0), (15.0, 35.3), (0.0, 35.3)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).faces(">Z").workplane(origin=(0, 0, 35.3)).center(-1.0, -1.1).hole(11.1, 14.0), "z", (0.0, 0.0, -32.0))
result = b0.union(b1.union(b2))