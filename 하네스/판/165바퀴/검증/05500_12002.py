b0 = place(cq.Workplane("XY").box(45.1, 31.9, 21.9, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 21.9)).center(10.1, 1.1).rect(10.9, 7.7).cutBlind(-11.1), "z", (0.0, 0.0, -17.9))
b1 = place(cq.Workplane("XY").circle(21.9).extrude(21.9).faces(">Z").workplane(origin=(0, 0, 21.9)).center(10.6, -1.1).rect(11.1, 7.9).cutBlind(-13.3), "z", (0.0, 0.0, 13.9))
b2 = place(cq.Workplane("XY").add(cq.Solid.makeCone(21.9, 0, 15.9)), "z", (0.0, 0.0, 24.9))
result = b0.union(b1.union(b2))