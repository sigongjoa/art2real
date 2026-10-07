import cadquery as cq
r = cq.Workplane('YZ').circle(13.2).extrude(73, both=True).translate((0, 0, -1.35))
for x in (-72.8, 0, 72.8):
    r = r.union(cq.Workplane('XY').sphere(27.3).translate((x, 0, 0)))
r = r.intersect(cq.Workplane('XY').box(220, 80, 50))
