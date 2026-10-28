b0 = place(cq.Workplane("XY").box(33.3, 21.0, 11.2, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 11.2)).center(10.1, 1.0).hole(6.3, 5.3).faces(">Z").workplane(origin=(0, 0, 11.2)).center(1.0, 1.0).hole(10.3, 4.9), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(21.4, 0, 29.9)), "z", (0.0, 0.0, -21.0))
result = b0.union(b1)