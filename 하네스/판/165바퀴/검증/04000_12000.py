b0 = place(cq.Workplane("XY").add(cq.Solid.makeCone(24.4, 0, 17.0)), "z", (14.6, 0.0, 0.0))
b1 = place(cq.Workplane("XY").circle(26.5).extrude(31.2).faces(">Z").workplane(origin=(0, 0, 31.2)).center(11.1, 13.6).hole(12.1).faces(">Z").workplane(origin=(0, 0, 31.2)).center(11.8, 11.4).hole(12.1), "z", (-21.7, 0.0, 0.0))
b2 = place(cq.Workplane("XY").circle(22.9).extrude(31.3).faces(">Z").workplane(origin=(0, 0, 31.3)).center(11.4, 11.4).hole(12.1).faces(">Z").workplane(origin=(0, 0, 31.3)).center(10.8, 11.4).hole(11.8), "z", (14.6, 0.0, 0.0))
result = b0.union(b1.union(b2))