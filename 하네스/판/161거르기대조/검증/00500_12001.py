b0 = place(cq.Workplane("XZ").polyline([(0.0, 0.0), (16.0, 0.0), (16.0, 10.0), (14.0, 10.0), (14.0, 16.0), (0.0, 16.0)]).close().revolve(360, (0, 0, 0), (0, 1, 0)), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").box(100.0, 50.0, 100.0, " False", (5.0, 0.0, 0.0))
result = b0.union(b1.union(b2.union(b2.union(b2.union(b2.union(b2))