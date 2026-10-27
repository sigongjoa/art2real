b0 = place(cq.Workplane("XY").add(cq.Solid.makeCone(21.1, 0, 22.0)), "y", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XZ").polyline([(0.0, 0.0), (20.9, 0.0), (20.9, 11.0), (11.9, 11.0), (11.9, 25.0), (0.0, 25.0)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).faces(">Z").workplane(origin=(0, 0, 25.0)).center(-1.9, -1.1).hole(11.1, 10.9), "z", (0.0, 0.0, 21.0))
result = b0.union(b1)