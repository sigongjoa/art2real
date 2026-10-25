b0 = place(cq.Workplane("XY").box(36.8, 4.0, 36.8, centered=(True, True, True, False)).faces(">Z").workplane(origin=(0, 0, 36.8)).center(14.0, 0.0, 0.0))
b1 = place(cq.Workplane("XY").box(4.2, 4.4, 36.8, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 36.8)).center(1.3, 0.0, 0.0))
result = b0