import cadquery as cq
o = cq.Workplane('XY').center(0, -1.65).rect(6.6, 196.7).extrude(1.8, both=True).union(cq.Workplane('XY').center(0, 96.7).circle(3.3).extrude(1.8, both=True))
i = cq.Workplane('XY').center(0, -1.7).rect(4, 196.8).extrude(2, both=True).union(cq.Workplane('XY').center(0, 96.7).circle(2).extrude(2, both=True))
r = o.cut(i).intersect(cq.Workplane('XY').box(10, 200, 10).translate((0, 0, 0)))
