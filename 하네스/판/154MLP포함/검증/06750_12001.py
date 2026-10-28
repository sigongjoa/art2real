b0 = place(cq.Workplane("XY").box(48.8, 23.8, 20.8, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 20.8)).center(-1.7, -1.0).hole(10.0, 12.1).edges("|Z").fillet(4.1), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").circle(26.9).extrude(23.7), "z", (0.0, 0.0, -17.5))
b2 = place(cq.Workplane("XY").add(cq.Solid.makeCone(27.1, 0, 24.6)), "z", (0.0, 0.0, -17.5))
result = b0.union(b1.union(b2))