b0 = place(cq.Workplane("XY").circle(29.1).extrude(32.2).faces(">Z").workplane(origin=(0, 0, 32.2)).center(-10.4, -11.4).hole(11.1, 17.0), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(22.2, 0, 14.0)), "y", (0.0, 0.0, -27.0))
b2 = place(cq.Workplane("XY").add(cq.Solid.makeCone(28.0, 0, 14.0)), "z", (0.0, 0.0, -27.0))
result = b0.union(b1.union(b2))