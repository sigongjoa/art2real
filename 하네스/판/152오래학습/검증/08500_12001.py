b0 = place(cq.Workplane("XY").circle(20.6).extrude(19.1).faces(">Z").workplane(origin=(0, 0, 19.1)).center(10.9, -10.4).hole(10.1), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(22.1, 0, 14.4)), "y", (0.0, 0.0, -22.0))
result = b0.union(b1)