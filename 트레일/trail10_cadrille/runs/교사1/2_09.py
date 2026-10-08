import cadquery as cq
S = [(-77.6, -6, -4, 27, 37), (-60, -4.5, -4, 30.5, 40), (-40, -0.5, -3.8, 36.5, 42.8), (-20, 1, -3.6, 43, 44.6),
     (0, 0, -2, 46, 44), (20, 0, 0, 46.5, 42.5), (40, 0, 0, 45, 42), (60, 0, 0, 41.6, 41), (80, 0, 0, 34, 39), (98, 0, 0, 22, 34)]
W = [cq.Workplane('YZ', origin=(x, 0, 0)).center(cy, cz).ellipse(ry, rz).wires().val() for x, cy, cz, ry, rz in S]
b = cq.Workplane('XY').add(cq.Solid.makeLoft(W)).intersect(cq.Workplane('XY').box(178, 100, 100).translate((11, 0, 0)))
b = b.cut(cq.Workplane('XZ').polyline([(0, -60), (0, -46), (20, -30), (40, -15), (45, 3), (60, 11), (80, 21), (100, 26), (110, 26), (110, -60)]).close().extrude(60, both=True))
b = b.cut(cq.Workplane('XY', origin=(0, 0, -60)).center(40, 0).ellipse(48, 34).extrude(64.5))
b = b.cut(cq.Workplane('XY').box(32, 30, 21).translate((-18, 0, -6.5)))
D = cq.Workplane('XZ').center(-56.5, -4.5).rect(43, 47).extrude(-60).union(cq.Workplane('XZ').center(-35, -4.5).circle(23.5).extrude(-60))
b = b.cut(D.translate((0, 12, 0)))
b = b.cut(D.translate((0, -60, 0)).translate((0, 0, 0)).intersect(cq.Workplane('XY').box(200, 100, 200).translate((0, -84, 0))))
C = [(-3.3, -32.5), (-21.5, -25.3), (-29.3, -14.8), (-29.3, 6.1), (-19.3, 18), (-3.3, 23.8), (-3.9, 9.1), (-17.7, 8.1), (-17.7, -22.4), (-4.3, -23.1)]
r = b.union(cq.Workplane('YZ', origin=(-97, 0, 0)).polyline(C).close().extrude(20))
