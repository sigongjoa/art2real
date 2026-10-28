b0 = place(cq.Workplane("XY").box(40.0, 23.0, 10.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 10.0)).center(10.0, 1.0).hole(10.0, 4.7), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").box(40.0, 39.0, 10.0, centered=(True, True, False)).edges("|Z").fillet(4.1), "z", (0.0, 0.0, -20.0))
b2 = place(cq.Workplane("XY").add(cq.Solid.makeCone(27.1, 0, 13.0)), "y", (0.0, 0.0, -20.0))
result = b0.union(b1.union(b2))