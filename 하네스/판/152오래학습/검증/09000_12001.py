b0 = place(cq.Workplane("XY").circle(20.5).extrude(15.0).faces(">Z").workplane(origin=(0, 0, 15.0)).center(10.9, -10.4).hole(10.9, 8.0), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(22.2, 0, 14.5)), "y", (0.0, 0.0, -22.0))
result = b0.union(b1)