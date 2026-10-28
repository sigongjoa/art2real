b0 = place(cq.Workplane("XZ").polyline([(0.0, 0.0), (27.1, 0.0), (26.2, 6.4), (23.4, 12.3), (19.0, 17.4), (13.5, 20.5), (7.1, 22.6), (0.0, 23.4)]).close().revolve(360, (0, 0, 0), (0, 1, 0)), "y", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(27.1, 0, 38.1)), "z", (0.0, 0.0, 31.1))
b2 = place(cq.Workplane("XY").circle(22.1).extrude(23.2).faces(">Z").workplane(origin=(0, 0, 23.2)).center(1.2, 1.0).hole(11.4, 12.4).faces(">Z").workplane(origin=(0, 0, 23.2)).center(1.2, 1.2).hole(12.1, 11.4), "z", (0.0, 0.0, 39.1))
result = b0.union(b1.union(b2))