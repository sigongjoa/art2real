b0 = place(cq.Workplane("XY").circle(10.0).extrude(26.6), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XZ").polyline([(0.0, 0.0), (28.9, 0.0), (28.9, 11.1), (17.8, 11.1), (17.8, 21.8), (0.0, 21.8)]).close().revolve(360, (0, 0, 0), (0, 1, 0)), "z", (0.0, 0.0, 0.0))
result = b0.union(b1)