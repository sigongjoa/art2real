b0 = place(cq.Workplane("XY").circle(20.8).extrude(15.7).faces(">Z").workplane(origin=(0, 0, 15.7)).center(-10.0, -10.4).hole(10.1, 8.0), "z", (0.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").add(cq.Solid.makeCone(26.4, 0, 14.0)), "y", (0.0, 0.0, 21.0))
result = b0.union(b1)