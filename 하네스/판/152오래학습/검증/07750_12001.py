b0 = place(cq.Workplane("XY").add(cq.Solid.makeCone(20.4, 0, 24.4)), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(21.4, 0, 15.0)), "z", (0.0, 0.0, -22.0))
b2 = place(cq.Workplane("XZ").polyline([(0.0, 0.0), (28.9, 0.0), (28.9, 13.6), (19.4, 13.6), (19.4, 3.7), (0.0, 3.7)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).faces(">Z").workplane(origin=(0, 0, 13.6)).center(-10.7, 10.4).hole(11.4, 7.4), "z", (0.0, 0.0, -22.0))
result = b0.union(b1.union(b2))