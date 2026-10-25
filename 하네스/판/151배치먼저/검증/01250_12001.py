layout = [("box", "z", (0.0, 0.0, 0.0)), ("revolve", "z", (0.0, 0.0, -25.7)), ("revolve", "z", (0.0, 0.0, -25.7)), ("revolve", "z", (0.0, 0.0, -25.7)), ("box", "z", (0.0, 32.2, 0.0)), ("revolve", "z", (0.0, 18.2, 0.0))]
b0 = at(0, cq.Workplane("XY").box(36.7, 36.7, 21.3, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 21.3)).center(-1.1, 1.1).hole(1.2))
b1 = at(1, cq.Workplane("XY").circle(26.0).extrude(29.7).faces(">Z").workplane(origin=(0, 0, 29.7)).center(-1.1, 1.1).hole(11.1, 11.1))
b2 = at(2, cq.Workplane("XY").circle(26.0).extrude(29.7))
b2 = at(2, cq.Workplane("XZ").polyline([(0.0, 0.0), (28.0, 0.0), (28.0, 11.1), (17.1, 11.1), (17.1, 3.3), (0.0, 3.3)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).faces(">Z").workplane(origin=(0, 0, 11.1)).center(-1.1, 1.1).hole(10.1, 10.1))
result = b0.union(b1.union(b2))