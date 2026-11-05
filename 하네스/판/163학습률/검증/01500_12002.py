b0 = place(cq.Workplane("XZ").polyline([(0.0, 0.0), (17.6, 0.0), (17.6, 11.1), (10.0, 11.1), (10.0, 3.4), (0.0, 3.4)]).close().revolve(360, (0, 0, 0), (0, 1, 0)), "y", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").box(50.0, 35.1, 21.6, centered=(True, True, False)), "y", (0.0, 0.0, 0.0))
result = b0.union(b1)