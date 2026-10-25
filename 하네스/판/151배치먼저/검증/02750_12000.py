layout = [("revolve", "z", (0.0, 0.0, 0.0)), ("revolve", "y", (0.0, 0.0, 32.2)), ("revolve", "z", (0.0, 0.0, 32.2)), ("box", "x", (0.0, 0.0, -22.2)), ("revolve", "z", (-30.6, 0.0, 0.0))]
b0 = at(0, cq.Workplane("XZ").polyline([(0.0, 0.0), (23.6, 0.0), (23.6, 11.7), (15.1, 11.7), (15.1, 31.0), (0.0, 31.0)]).close().revolve(360, (0, 0, 0), (0, 1, 0)))
b1 = at(1, cq.Workplane("XY").box(44.1, 40.4, 21.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 21.0)).center(-1.1, -1.1).hole(1.7, 1.1).faces(">Z").workplane(origin=(0, 0, 21.0)).center(-1.1, 1.1).hole(1.1, 1.1))
b2 = at(2, cq.Workplane("XY").box(44.1, 28.0, 15.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 15.0)).center(10.0, -1.1).hole(10.0, 1.2).edges("|Z").fillet(3.5))
b3 = at(3, cq.Workplane("XY").add(cq.Workplane("XY").circle(19.0).extrude(15.0).faces(">Z").workplane(origin=(0, 0, 15.0)).center(-1.5, -1.8).hole(11.1, 11.0))
result = b0.union(b1.union(b2.union(b3.union(b4))))