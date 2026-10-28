b0 = place(cq.Workplane("XY").box(45.2, 31.0, 10.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 10.0)).center(-1.0, -1.0).hole(10.0, 5.6).edges("|Z").fillet(4.1), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(20.4, 0, 24.6)), "z", (0.0, 0.0, -22.5))
b2 = place(cq.Workplane("XY").box(32.1, 43.0, 15.6, centered=(True, True, False)).edges("|Z").fillet(4.1), "z", (0.0, 0.0, -13.5))
result = b0.union(b1.union(b2))