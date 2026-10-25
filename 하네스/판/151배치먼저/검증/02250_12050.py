layout = [("revolve", "z", (0.0, 0.0, 0.0)), ("revolve", "x", (0.0, 0.0, -22.7)), ("revolve", "z", (0.0, 0.0, -22.7)), ("revolve", "z", (-32.6, 0.0, -22.7))]
b0 = at(0, cq.Workplane("XZ").polyline([(0.0, 0.0), (26.6, 0.0), (26.6, 11.1), (17.1, 11.1), (17.1, 31.0), (0.0, 31.0)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).faces(">Z").workplane(origin=(0, 0, 31.0)).center(-1.1, 1.1).hole(11.1, 11.1))
b1 = at(1, cq.Workplane("XZ").polyline([(0.0, 0.0), (26.6, 0.0), (26.6, 11.1), (15.1, 11.1), (15.1, 28.1), (0.0, 28.1)]).close().revolve(360, (0, 0, 0), (0, 1, 0)))
b2 = at(2, cq.Workplane("XY").box(44.1, 40.1, 21.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 21.0)).center(-1.1, -1.1).hole(11.1, 11.1))
b3 = at(3, cq.Workplane("XY").box(54.7, 47.5, 21.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 21.0)).center(-1.1, 1.1).hole(1.7, 10.1))
b4 = at(4, cq.Workplane("XY").box(40.1, 44.8, 21.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 21.0)).center(-1.1, 1.1).hole(1.1, 10.1))
b5 = at(5, cq.Workplane("XY").add(cq.Workplane("XY").box(56.7, 28.8, 21.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 21.0)).center(-1.1, -1.1).hole(1.1, 1.1).faces(">Z").workplane(origin=(0, 0, 21.0)).center(1.1, 1.1).hole(1.1, 1.1))
result = b0.union(b1.union(b2.union(b3)))