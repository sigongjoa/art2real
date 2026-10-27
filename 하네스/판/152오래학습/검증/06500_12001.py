b0 = place(cq.Workplane("XY").circle(20.7).extrude(15.7), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").circle(19.7).extrude(15.3).faces(">Z").workplane(origin=(0, 0, 15.3)).center(1.1, 11.4).hole(10.9, 8.0), "z", (-36.7, 0.0, 0.0))
b2 = place(cq.Workplane("XY").circle(20.7).extrude(22.7), "z", (-36.7, 0.0, 0.0))
result = b0.union(b1.union(b2))