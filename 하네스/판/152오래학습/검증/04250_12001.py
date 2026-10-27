b0 = place(cq.Workplane("XY").circle(27.7).extrude(27.7).faces(">Z").workplane(origin=(0, 0, 27.7)).center(10.4, -10.0).hole(11.7), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(22.2, 0, 39.4)), "y", (0.0, 0.0, 32.0))
b2 = place(cq.Workplane("XY").circle(29.7).extrude(24.7).faces(">Z").workplane(origin=(0, 0, 24.7)).center(11.9, -10.0).hole(11.7, 14.4), "z", (0.0, 0.0, 32.0))
result = b0.union(b1.union(b2))