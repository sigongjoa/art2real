b0 = place(cq.Workplane("XY").box(52.8, 31.7, 23.2, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 23.2)).center(13.1, 10.4).hole(10.1, 10.4), "z", (-20.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(26.2, 0, 23.2)), "z", (20.0, 0.0, 0.0))
result = b0.union(b1)