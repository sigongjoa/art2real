b0 = place(cq.Workplane("XY").Z").add(cq.Workplane("XY").Z").Z").polyline([(0.0, 0.0), (4.0, 0.0), (4.0, 21.9), (2.5, 21.9), (2.5, 20.4), (2.0, 17.5), (0.0, 17.9, 17.9), (0.0,0),(-1,0)).faces(">Z").workplane(origin=(0, 0, 21.9)).center(3.2, -0.0).hole(12.0, 26.0), "z", (26.7, -10.0, 0.0))
b1 = place(cq.Workplane("XY").box(43.3, 43.7, 0.0))
result = b0.union(b1)