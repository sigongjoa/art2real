layout = [("cylinder", "z", (0.0, 0.0, 0.0)), ("cone", "y", (0.0, 0.0, -20.0)), ("cone", "y", (0.0, 0.0, -20.0))]
b0 = at(0, cq.Workplane("XY").circle(26.6).extrude(22.6).faces(">Z").workplane(origin=(0, 0, 22.6)).center(1.5, -1.1).hole(11.1, 11.1))
b1 = at(1, cq.Workplane("XY").add(cq.Workplane("XY").box(44.1, 41.3, 22.2, centered=(True, True, False)).edges("|Z").fillet(3.5))
result = b0.union(b1)