layout = [("revolve", "z", (0.0, 0.0, 0.0)), ("revolve", "z", (0.0, 0.0, -25.7)), ("cone", "y", (0.0, 0.0, -25.7))]
b0 = at(0, cq.Workplane("XZ").polyline([(0.0, 0.0), (25.1, 0.0), (25.1, 11.1), (13.1, 11.1), (13.1, 21.0), (0.0, 21.0)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).faces(">Z").workplane(origin=(0, 0, 21.0)).center(-1.1, 1.1).hole(11.1, 11.1))
b1 = at(1, cq.Workplane("XY").box(44.1, 24.8, 14.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 14.0)).center(10.7, 10.1).hole(10.7, 10.0))
result = b0.union(b1)