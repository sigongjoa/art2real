b0 = place(cq.Workplane("XZ").polyline([(0.0, 0.0), (28.9, 0.0), (28.9, 21.7), (18.8, 21.7), (18.8, 41.3), (0.0, 41.3)]).close().revolve(360, (0, 0, 0), (0, 1, 0)), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").circle(10.0).extrude(27.6), "z", (0.0, 0.0, 0.0))
b2 = place(cq.Workplane("XZ").polyline([(0.0, 0.0), (23.7, 0.0), (23.7, 11.1), (17.4, 11.1), (17.4, 29.1), (0.0, 29.1)]).close().revolve(360, (0, 0, 0), (0, 1, 0)), "z", (0.0, 0.0, 0.0))
result = b0.union(b1.union(b2))