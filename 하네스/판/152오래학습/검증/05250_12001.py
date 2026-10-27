b0 = place(cq.Workplane("XY").add(cq.Solid.makeCone(20.1, 0, 24.4)), "y", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XZ").polyline([(0.0, 0.0), (25.1, 0.0), (24.2, 6.6), (21.8, 12.9), (17.8, 18.0), (12.5, 21.9), (6.5, 24.1), (0.0, 24.1)]).close().revolve(360, (0, 0, 0), (0, 1, 0)), "y", (0.0, 0.0, 21.1))
b2 = place(cq.Workplane("XY").add(cq.Solid.makeCone(29.0, 0, 21.1)), "z", (0.0, 0.0, 21.1))
result = b0.union(b1.union(b2))