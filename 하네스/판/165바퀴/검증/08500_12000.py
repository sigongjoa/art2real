b0 = place(cq.Workplane("XZ").polyline([(0.0, 0.0), (25.2, 0.0), (25.2, 13.9), (16.0, 13.9), (16.0, 2.9), (0.0, 2.9)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).faces(">Z").workplane(origin=(0, 0, 13.9)).center(-1.2, 11.0).hole(11.2, 6.0).faces(">Z").workplane(origin=(0, 0, 13.9)).center(1.2, 1.0).hole(11.7, 7.0), "z", (18.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(26.4, 0, 21.1)), "x", (-21.6, 0.0, 0.0))
b2 = place(cq.Workplane("XY").add(cq.Solid.makeCone(21.4, 0, 21.4)), "z", (21.0, 0.0, 0.0))
result = b0.union(b1.union(b2))