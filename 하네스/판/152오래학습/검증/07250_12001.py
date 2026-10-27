b0 = place(cq.Workplane("XY").circle(29.2).extrude(31.2).faces(">Z").workplane(origin=(0, 0, 31.2)).center(-1.1, 11.4).hole(11.1, 17.4), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(22.1, 0, 14.5)), "y", (0.0, 0.0, -27.0))
b2 = place(cq.Workplane("XY").add(cq.Solid.makeCone(22.1, 0, 14.5)), "z", (0.0, 0.0, -27.0))
result = b0.union(b1.union(b2))