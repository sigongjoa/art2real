b0 = place(cq.Workplane("XY").add(cq.Solid.makeCone(29.5, 0, 29.9)), "z", (19.9, 13.5, 0.0))
b1 = place(cq.Workplane("XY").box(50.9, 44.4, 21.9, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 21.9)).center(-1.7, -1.6).hole(11.1, 10.5).faces(">Z").workplane(origin=(0, 0, 21.9)).center(-1.7, -1.6).hole(11.5, 10.5), "z", (19.9, 13.5, 0.0))
b2 = place(cq.Workplane("XY").box(46.9, 44.4, 20.4, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 20.4)).center(1.9, -1.6).hole(11.1, 10.5), "z", (19.9, -1.5, 0.0))
result = b0.union(b1.union(b2))