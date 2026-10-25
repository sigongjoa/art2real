layout = [("revolve", "z", (0.0, 0.0, 0.0)), ("revolve", "z", (36.0, 0.0, 0.0)), ("revolve", "z", (36.0, 0.0, 0.0)), ("revolve", "z", (36.0, 0.0, 0.0)), ("revolve", "z", (36.0, 0.0, 36.0))]
b0 = at(0, cq.Workplane("XZ").polyline([(0.0, 0.0), (18.8, 0.0), (18.8, 11.1), (10.1, 11.1), (10.1, 21.1), (0.0, 21.1)]).close().revolve(360, (0, 0, 0), (0, 1, 0)))
b1 = at(1, cq.Workplane("XZ").polyline([(0.0, 0.0), (28.8, 0.0), (28.8, 11.1), (18.8, 11.1), (18.8, 27.1), (0.0, 27.1)]).close().revolve(360, (0, 0, 0), (0, 1, 0)))
b2 = at(2, cq.Workplane("XZ").polyline([(0.0, 0.0), (28.8, 0.0), (28.8, 18.1), (13.8, 18.1), (13.8, 3.2), (0.0, 3.2)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).faces(">Z").workplane(origin=(0, 0, 18.1)).center(-1.1, 1.1).hole(11.1, 17.1))
b2 = at(2, cq.Workplane("XY").box(34.1, 34.1, 10.1, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 10.1)).center(-1.1, 1.1).hole(11.1, 11.1))
b3 = at(3, cq.Workplane("XY").box(40.1, 47.8, 24.1, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 24.1)).center(-1.1, 1.1).hole(11.1, 11.1))
b4 = at(4, cq.Workplane("XY").box(34.1, 34.8, 24.1, centered=(10.7, 24.1, centered=(10.7, 10.1), (10.7, 6.0), (0.0, 6.0)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).faces(">Z").workplane(origin=(0, 0, 24.1)).center(-1.1, 1.1).hole(11.1, 10.5))
result = b0.union(b1.union(b2.union(b3)))