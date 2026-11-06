b0 = place(cq.Workplane("XY").box(52.0, 31.1, 1.1, centered=(True, True, False)).edges("|Z").fillet(2.2), "z", (0.0, 0.0, 21.1))
b1 = place(cq.Workplane("XY").box(52.2, 40.2, 2.2, centered=(True, True, False)).edges("|Z").fillet(2.2), "z", (0.0, 0.0, -17.6))
b2 = place(cq.Workplane("XY").box(48.4, 40.2, 2.0, centered=(True, True, False)).edges("|Z").fillet(2.2), "z", (0.0, 0.0, 21.1))
result = b0.union(b1.union(b2))