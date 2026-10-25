b0 = place(cq.Workplane("XY").box(42.9, 33.1, 15.1, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 15.1)).center(-1.1, 1.0).hole(10.1, 7.1), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").circle(21.1).extrude(21.6).faces(">Z").workplane(origin=(0, 0, 21.6)).center(-1.2, -1.1).hole(10.1, 11.1), "z", (0.0, 0.0, -23.2))
result = b0.union(b1)