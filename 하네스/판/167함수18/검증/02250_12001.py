b0 = place(cq.Workplane("XY").add(cq.Solid.makeCone(29.5, 0, 31.0)), "z", (0.0, 0.0, 10.0))
b1 = place(cq.Workplane("XY").box(50.0, 43.0, 23.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 23.0)).center(1.9, 1.6).hole(11.5, 11.5).faces(">Z").workplane(origin=(0, 0, 23.0)).center(1.8, 1.9).hole(11.9, 12.5), "z", (0.0, 0.0, -26.0))
result = b0.union(b1)