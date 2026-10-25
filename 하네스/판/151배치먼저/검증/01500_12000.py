layout = [("revolve", "y", (0.0, 0.0, 0.0)), ("revolve", "x", (0.0, 0.0, 29.2))]
b0 = at(0, cq.Workplane("XZ").polyline([(0.0, 0.0), (23.0, 0.0), (22.0, 10.0), (20.0, 21.0), (17.0, 29.9), (12.9, 36.9), (7.0, 39.9), (0.0, 39.9)]).close().revolve(360, (0, 0, 0), (0, 1, 0)))
b1 = at(1, cq.Workplane("XZ").polyline([(0.0, 0.0), (28.6, 0.0), (28.6, 11.1), (18.8, 11.1), (18.8, 21.1), (0.0, 21.1)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).faces(">Z").workplane(origin=(0, 0, 21.1)).center(-1.1, -1.1).hole(11.1, 11.1))
b2 = at(2, cq.Workplane("XZ").polyline([(0.0, 0.0), (23.1, 0.0), (22.1, 10.8), (19.0, 21.3), (14.1, 29.9), (8.8, 36.0), (0.0, 37.6)]).close().revolve(360, (0, 0, 0), (0, 1, 0)))
b4 = at(4, cq.Workplane("XY").circle(26.0).extrude(22.0).faces(">Z").workplane(origin=(0, 0, 22.0)).center(1.5, -1.8).hole(11.1, 11.1))
result = b0.union(b1.union(b2.union(b3)))