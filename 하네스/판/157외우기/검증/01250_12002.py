b0 = place(cq.Workplane("XY").add(cq.Workplane("XY").Z").workplane(origin=(0,0,0)).box(83, 42,0))..union(b1 = 4.4)).fil(1=4.4), "z",(-30.8, 16.4, -14.8))
b1 = x.box(48.4, 33.4, 24.5, " True, True, False)).fil(35.4, 0, 24.5))
b2 = place(cq.Workplane("XZ").polyline([(0.0, 0.0), (27.7, 0.0), (27.7, 35.2), (20.2, 35.2), (20.2, 65.6), (0.0, 65.6)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).faces(">Z").workplane(origin=(0, 0, 65.6)).center(1.5, -2.7).hole(24.6), "z", (0.0, 16.4, -14.5))
result = b0.union(b1.union(b2))