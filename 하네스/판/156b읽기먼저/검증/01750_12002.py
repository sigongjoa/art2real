# 2 bodies: stepped disc along z, cone, box along z, at front (y, z≈-18); seen as the large circle in TOP, a rectangular pocket rectangle in TOP and a rectangle in TOP and SIDE; a rectangular pocket rectangle in TOP and a small rectangle in SIDE; a small rectangle in TOP and SIDE; a small rectangle in FRONT and a small rectangle in TOP and a rectangle in FRONT.
# b1: revolved cup along z, at back (x≈-18), at right (x≈-18), x 18); seen as the long rectangle in FRONT and the rectangle in TOP.
# b2: revolved cup along z, at front (x≈-18, z≈-18); TOP the lower circle in TOP; a rectangle in FRONT, a rectangle in FRONT and a rectangle in TOP.
# b3: revolved cup along y, at left (x about -18, y≈-18, z≈-18); seen as the lower rectangle in TOP and the rectangle in TOP.
# b3: revolved cup along x, at left (x≈-18, z≈-18, z≈-18); seen as the lower rectangle in TOP; a rectangular in FRONT and a rectangle in TOP.
# b3: revolved cup along x, at left (0, 0, z≈-18, z≈-18); seen as the lower rectangle in TOP; a rectangular pocket in TOP.
# b4: revolved cup along x, at left (0, 0, z≈-18, z≈-18, z≈-18); seen as the lower rectangle in TOP.
b0 = place(cq.Workplane("XY").box(100.0, 18.0, 18.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 18.0)).center(18.1, 18.0).rect(18.9, 18.0).cutBlind(-18.9).faces(">Z").workplane(origin=(0, 0, 18.0)).center(18.1, 18.0).rect(12.9, 18.0).cutBlind(-18.9), "x", (0.0, 0.0, 18.0))
b1 = place(cq.Workplane('XY").box(100.0, 29.9, 18.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 18.0)).center(-1.8, -1.1).rect(18.9, 18.0).cutBlind(-18.9), "z", (0.0, 0.0, -18.0))
b1 = place(cq.Workplane("XY").box(100.0, 29.9, 18.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 18.0)).center(-1.8, -1.8).rect(5.7, 1.9).cutBlind(-18.0), "y", (0.0, 0.0, -18.0))
b4 = place(cq.Workplane("XY").box(50.0, 29.9, 18.0, centered=(True, True, False)).faces(">Z").workplane(origin=(0, 0, 18.0)).center(-1.8, -1.8).rect(10.7, 18.0).cutBlind(-18.0), "y", (0.0, 0.0, -18.0))
result = b0.union(b1.union(b2.union(b3))