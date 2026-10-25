b0 = place(cq.Workplane("XZ").polyline([(0.0, 0.0), (28.1, 0.0), (28.1, 14.0), (18.8, 14.0), (18.8, 3.9), (0.0, 3.9)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).faces(">Z").workplane(origin=(0, 0, 14.0)).center(-1.1, 1.9).hole(10.1), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").circle(26.1).extrude(27.7), "z", (0.0, 0.0, 27.7))
result = b0.union(b1)