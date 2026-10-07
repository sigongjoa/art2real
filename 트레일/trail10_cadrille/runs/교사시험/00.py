import cadquery as cq
c = -3.0
b = cq.Workplane('XY').sphere(38.7).translate((61.3, 0, c)).union(cq.Workplane('XY').sphere(38.7).translate((-61.3, 0, c)))
b = b.union(cq.Workplane('YZ').circle(19.5).extrude(62, both=True).translate((0, 0, -3.5)))
r = b.intersect(cq.Workplane('XY').box(220, 100, 70.6).translate((0, 0, -0.2)))
