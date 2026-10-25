layout = [("box", "z", (0.0, 0.0, 0.0)), ("revolve", "y", (0.0, 32.5, 0.0)), ("revolve", "z", (0.0, 0.0, 20.0))]
b0 = at(0, cq.Workplane("XY").box(50.6, 24.0, 20.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 20.0)).center(-1.1, 1.1).hole(1.2, 11.1).faces(">Z").workplane(origin=(0, 0, 20.0)).center(-1.1, 1.1).hole(10.0, 10.0))
b1 = at(1, cq.Workplane("XY").box(40.1, 24.0, 20.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 20.0)).center(-1.1, 1.1).hole(1.1, 10.0))
b2 = at(2, cq.Workplane("XY").box(40.1, 40.0, 20.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 20.0)).center(-1.1, 1.1).hole(10.0, 10.0))
result = b0.union(b1.union(b2))