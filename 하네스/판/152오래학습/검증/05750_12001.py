b0 = place(cq.Workplane("XY").add(cq.Solid.makeCone(29.4, 0, 39.4)), "y", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(20.4, 0, 39.4)), "y", (0.0, 0.0, -27.0))
b2 = place(cq.Workplane("XY").circle(29.0).extrude(29.2).faces(">Z").workplane(origin=(0, 0, 29.2)).center(-10.4, -10.4).hole(11.8, 13.4).faces(">Z").workplane(origin=(0, 0, 29.2)).center(-10.4, -10.4).hole(11.9, 11.9), "z", (0.0, 0.0, -27.0))
result = b0.union(b1.union(b2))