b0 = place(cq.Workplane("XY").box(48.8, 23.8, 2.2, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 2.2)).center(1.7, 1.0).hole(10.0, 1.2), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XZ").polyline([(0.0, 0.0), (27.0, 0.0), (26.1, 4.1), (23.4, 7.9), (19.1, 11.2), (13.5, 13.8), (7.1, 15.3), (0.0, 15.8)]).close().revolve(360, (0, 0, 0), (0, 1, 0)), "z", (0.0, 0.0, 17.0))
b2 = place(cq.Workplane("XY").circle(22.9).extrude(29.5).faces(">Z").workplane(origin=(0, 0, 29.5)).center(1.7, 1.1).hole(12.4, 12.9), "z", (0.0, 0.0, 14.0))
result = b0.union(b1.union(b2))