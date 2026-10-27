b0 = place(cq.Workplane("XY").circle(20.0).extrude(16.0).faces(">Z").workplane(origin=(0, 0, 16.0)).center(10.0, -10.0).hole(10.0), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(22.0, 0, 22.0)), "y", (0.0, 0.0, -21.0))
b2 = place(cq.Workplane("XY").circle(20.0).extrude(14.0), "z", (0.0, 0.0, -21.0))
result = b0.union(b1.union(b2))