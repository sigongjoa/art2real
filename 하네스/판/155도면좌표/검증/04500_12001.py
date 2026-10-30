b0 = place(cq.Workplane("XY").circle(29.0).extrude(31.2).faces(">Z").workplane(origin=(0, 0, 31.2)).center(1.2, 1.0).rect(11.1, 7.9).cutBlind(-13.0), "z", (0.0, 0.0, 1.9))
b1 = place(cq.Workplane("XY").box(58.8, 47.7, 2.8, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 2.8)).center(-1.7, 1.0).hole(1.7, 0.8), "z", (0.0, 0.0, 1.9))
result = b0.union(b1)