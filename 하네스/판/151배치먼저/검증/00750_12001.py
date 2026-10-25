layout = [("revolve", "y", (0.0, 0.0, 0.0)), ("revolve", "z", (0.0, 0.0, -36.0))]
b0 = at(0, cq.Workplane("XZ").polyline([(0.0, 0.0), (28.6, 0.0), (28.6, 11.8), (18.8, 11.8), (18.8, 3.1), (0.0, 3.1)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).faces(">Z").workplane(origin=(0, 0, 3.1)).center(1.1, 1.1, 1.1))
b1 = at(1, cq.Workplane("XY").circle(10.0).extrude(29.5).faces(">Z").workplane(origin=(0, 0, 29.9)).center(-1.1, 1.1).hole(1.2))
b2 = at(2, cq.Workplane("XY").circle(11.0).extrude(24.5))
b1 = at(1, cq.Workplane("XY").box(36.1, 49.5, 24.5, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 24.5)).center(1.1, 1.1).rect(15.5, 4.5).cutBlind(-10.0))
b2 = at(2, cq.Workplane("XZ").polyline([(0.0, 0.0), (13.5, 0.0), (13.5, 11.7), (10.5, 11.7), (10.5, 17.3), (0.0, 17.3)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).faces(">Z").workplane(origin=(0, 0, 17.7)).center(1.5, 1.1).rect(15.5, 17.7).cutBlind(-14.1))
result = b0.union(b1.union(b2))