b0 = place(cq.Workplane("XY").circle(10.0).extrude(100.0), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XZ").polyline([(0.0, 0.0), (26.0, 0.0), (26.0, 10.0), (18.0, 10.0), (18.0, 25.0), (0.0, 25.0)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).faces(">Z").workplane(origin=(0, 0, 25.0)).center(10.0, -1.0).hole(10.0), "z", (0.0, 0.0, 0.0))
result = b0.union(b1)