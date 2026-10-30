b0 = place(cq.Workplane("XZ").polyline([(0.0, 0.0), (25.1, 0.0), (25.1, 15.0), (15.5, 15.0), (15.5, 34.9), (0.0, 34.9)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).faces(">Z").workplane(origin=(0, 0, 34.9)).center(10.1, 10.6).hole(10.0, 12.2).faces(">Z").workplane(origin=(0, 0, 34.9)).center(10.7, 10.4).hole(10.9, 15.1), "z", (-20.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(26.2, 0, 26.2)), "z", (-20.0, 0.0, 0.0))
b2 = place(cq.Workplane("XY").add(cq.Solid.makeCone(22.2, 0, 26.2)), "z", (-20.0, 0.0, 0.0))
result = b0.union(b1.union(b2))