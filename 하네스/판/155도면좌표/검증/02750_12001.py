b0 = place(cq.Workplane("XY").box(100.0, 69.8, 2.9, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 2.9)).center(-1.9, 1.0).hole(1.2, 1.3).edges("|Z").fillet(3.5), "z", (0.0, 0.0, 13.6))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(29.4, 0, 34.9)), "y", (0.0, 0.0, -19.6))
result = b0.union(b1)