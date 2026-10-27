b0 = place(cq.Workplane("XY").box(49.4, 24.8, 2.7, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 2.7)).center(10.9, -1.1).hole(10.4, 1.3).faces(">Z").workplane(origin=(0, 0, 2.7)).center(-10.4, -1.4).hole(10.4, 1.3), "y", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(22.3, 0, 14.6)), "y", (0.0, 0.0, -22.0))
result = b0.union(b1)