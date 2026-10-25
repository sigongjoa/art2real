layout = [("revolve", "z", (0.0, 0.0, 0.0)), ("box", "z", (0.0, 0.0, 29.2)), ("revolve", "z", (0.0, 0.0, 29.2))]
b0 = at(0, cq.Workplane("XY").box(33.6, 34.0, 13.5, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 13.5)).center(-1.1, -1.1).hole(1.1, 1.1).edges("|Z").fillet(2.0))
b1 = at(1, cq.Workplane("XY").box(36.1, 36.5, 10.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 10.0)).center(-1.1, -1.1).hole(1.1, 1.1))
b2 = at(2, cq.Workplane("XY").box(41.1, 24.0, 2.3, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 2.3)).center(-1.1, 1.1).hole(1.1, 1.1).faces(">Z").workplane(origin=(0, 0, 2.3)).center(1.1, 1.1).hole(1.1, 1.1))
b3 = at(3, cq.Workplane("XY").box(46.1, 24.1, 15.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 15.0)).center(-1.1, -1.1).hole(1.1, 1.1).edges("|Z").fillet(3.1))
result = b0.union(b1.union(b2.union(b3)))