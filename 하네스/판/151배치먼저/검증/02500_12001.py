layout = [("revolve", "z", (0.0, 0.0, 0.0)), ("box", "z", (0.0, 0.0, -21.2))]
b0 = at(0, cq.Workplane("XZ").polyline([(0.0, 0.0), (28.6, 0.0), (28.6, 11.1), (17.1, 11.1), (17.1, 21.0), (0.0, 21.0)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).faces(">Z").workplane(origin=(0, 0, 21.0)).center(-1.1, 1.1).hole(11.1, 11.1))
b1 = at(1, cq.Workplane("XY").box(40.1, 27.4, 14.1, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 14.1)).center(-1.1, 1.1).hole(1.1, 1.1))
b2 = at(2, cq.Workplane("XY").box(40.1, 27.4, 14.1, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 14.1)).center(10.0, 1.1).hole(10.0, 1.0).edges("|Z").fillet(3.3))
result = b0.union(b1.union(b2))