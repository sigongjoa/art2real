layout = [("box", "x", (0.0, 0.0, 0.0)), ("revolve", "z", (0.0, 0.0, 29.2))]
b0 = at(0, cq.Workplane("XY").box(33.2, 34.0, 13.1, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 13.1)).center(-1.1, 1.1).hole(1.1, 1.1).edges("|Z").fillet(2.0))
b1 = at(1, cq.Workplane("XY").box(40.1, 27.0, 13.1, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 13.1)).center(-1.1, 1.1).hole(1.1, 3.1))
b2 = at(2, cq.Workplane("XY").circle(21.0).extrude(19.0).faces(">Z").workplane(origin=(0, 0, 19.0)).center(-1.1, 1.1).hole(1.1, 1.0).faces(">Z").workplane(origin=(0, 0, 19.0)).center(1.1, 1.1).hole(1.1, 1.0))
result = b0.union(b1.union(b2))