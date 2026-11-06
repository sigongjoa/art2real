b0 = place(cq.Workplane("XZ").polyline([(0.0, 0.0), (24.4, 0.0), (24.4, 18.0), (15.0, 18.0), (15.0, 3.9), (0.0, 3.9)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).faces(">Z").workplane(origin=(0, 0, 18.0)).center(1.2, -1.0).hole(13.7, 10.0), "z", (0.0, 0.0, 22.2))
b1 = place(cq.Workplane("XY").box(44.6, 40.4, 20.0, centered=(True, True, False)).edges("|Z").fillet(2.7), "z", (0.0, 0.0, -17.0))
b2 = place(cq.Workplane("XY").box(43.7, 40.7, 20.0, centered=(True, True, False)).edges("|Z").fillet(2.7), "z", (0.0, 0.0, 22.2))
result = b0.union(b1.union(b2))