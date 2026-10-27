b0 = place(cq.Workplane("XY").add(cq.Solid.makeCone(21.1, 0, 24.8)), "y", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XZ").polyline([(0.0, 0.0), (21.2, 0.0), (20.4, 4.3), (18.1, 8.0), (14.7, 11.5), (10.3, 14.3), (5.3, 16.0), (0.0, 16.9)]).close().revolve(360, (0, 0, 0), (0, 1, 0)), "z", (0.0, 0.0, 21.0))
result = b0.union(b1)