b0 = place(cq.Workplane("XY").add(cq.Solid.makeCone(25.1, 0, 24.4)), "y", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(22.2, 0, 15.0)), "z", (33.5, 0.0, 0.0))
b2 = place(cq.Workplane("XZ").polyline([(0.0, 0.0), (28.2, 0.0), (27.2, 7.3), (24.2, 14.3), (19.5, 20.0), (13.9, 24.7), (7.2, 27.7), (0.0, 28.7)]).close().revolve(360, (0, 0, 0), (0, 1, 0)), "z", (33.5, 0.0, 0.0))
result = b0.union(b1.union(b2))