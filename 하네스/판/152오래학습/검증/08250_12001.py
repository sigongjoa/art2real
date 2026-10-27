b0 = place(cq.Workplane("XY").circle(29.1).extrude(29.7).faces(">Z").workplane(origin=(0, 0, 29.7)).center(11.4, -11.4).hole(11.1, 14.4), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(22.2, 0, 14.4)), "y", (0.0, 0.0, -22.2))
result = b0.union(b1)