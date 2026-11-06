b0 = place(cq.Workplane("XY").circle(29.6).extrude(28.3).faces(">Z").workplane(origin=(0, 0, 28.3)).center(-1.2, -13.6).hole(15.0).faces(">Z").workplane(origin=(0, 0, 28.3)).center(13.5, 11.9).hole(15.1), "z", (0.0, 0.0, 19.6))
b1 = place(cq.Workplane("XY").circle(29.6).extrude(26.1).faces(">Z").workplane(origin=(0, 0, 26.1)).center(-10.6, 11.9).hole(14.1), "z", (0.0, 0.0, -19.6))
b2 = place(cq.Workplane("XY").circle(29.6).extrude(26.1).faces(">Z").workplane(origin=(0, 0, 26.1)).center(-14.0, 13.9).hole(14.1), "z", (0.0, 0.0, 19.6))
result = b0.union(b1.union(b2))