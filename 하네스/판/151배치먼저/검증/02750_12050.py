layout = [("revolve", "z", (0.0, 0.0, 0.0)), ("revolve", "z", (0.0, 0.0, -22.5)), ("revolve", "z", (0.0, 0.0, -22.5)), ("box", "z", (0.0, 0.0, -22.5)), ("box", "x", (0.0, 0.0, -22.5)), ("box", "z", (0.0, 0.0, -22.5))]
b0 = at(0, cq.Workplane("XY").box(40.1, 35.5, 20.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 20.0)).center(1.5, -1.1).hole(11.1, 11.1))
b1 = at(1, cq.Workplane("XY").box(40.1, 35.5, 20.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 20.0)).center(1.5, -1.1).hole(10.1, 11.1))
b2 = at(2, cq.Workplane("XY").box(40.1, 35.5, 20.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 20.0)).center(10.0, -1.1).hole(10.0, 1.1).edges("|Z").fillet(3.5))
b3 = at(3, cq.Workplane("XY").box(40.1, 35.5, 20.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 20.0)).center(10.0, -1.1).hole(10.0, 1.1).edges("|Z").fillet(2.5))
b4 = at(4, cq.Workplane("XY").box(40.1, 40.4, 20.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 20.0)).center(10.0, -1.1).hole(10.0, 1.1).edges("|Z").fillet(2.5))
b5 = at(5, cq.Workplane("XY").box(40.1, 40.4, 20.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 20.0)).center(10.0, -1.8).hole(10.0, 1.1).edges("|Z").fillet(2.5))
result = b0.union(b1.union(b2.union(b3.union(b4))))