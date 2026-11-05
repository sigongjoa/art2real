b0 = place(cq.Workplane("XY").add(cq.Solid.makeCone(22.2, 0, 29.6)), "z", (-14.7, 0.0, 0.0))
b1 = place(cq.Workplane("XY").circle(29.5).extrude(26.5).faces(">Z").workplane(origin=(0, 0, 26.5)).center(11.1, 11.1).rect(14.6, 10.6).cutBlind(-13.4).faces(">Z").workplane(origin=(0, 0, 26.5)).center(11.9, -10.8).hole(15.1), "z", (-14.7, 0.0, 0.0))
b2 = place(cq.Workplane("XY").circle(21.9).extrude(18.7), "z", (-14.7, 0.0, 0.0))
result = b0.union(b1.union(b2))