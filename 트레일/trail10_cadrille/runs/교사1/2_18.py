import cadquery as cq
inner = [(5.2, 87.8), (11, 78.4), (14.7, 68.9), (17.1, 59.5), (21.1, 35.8), (23.6, 2.7), (22.5, -21.6), (19.1, -50), (14.7, -68.9), (11, -78.4), (5.2, -87.8)]
outer = [(14.1, -87.8), (19.9, -76.4), (21, -66.5), (25.4, -48.3), (28.8, -20.9), (29.9, 0), (28.8, 20.9), (25.4, 48.3), (21, 66.5), (19.9, 76.4), (14.1, 87.8)]
plate = cq.Workplane('XZ').polyline(inner + outer).close().extrude(110, both=True)
plate = plate.intersect(cq.Workplane('YZ').polyline([(-100, 0), (-92, 30), (-87.8, 50), (-72, 87.8), (46, 87.8), (71.7, 50), (88, 25), (100, 0), (88, -25), (71.7, -50), (46, -87.8), (-72, -87.8), (-87.8, -50), (-92, -30)]).close().extrude(100, both=True))
bar = cq.Workplane('XY').box(15.9, 76.3, 25.1).translate((-24.55, -3.95, -47.85)).union(cq.Workplane('XY').box(54, 20, 25.1).translate((-5.5, -32, -47.85)))
hexb = cq.Workplane('XZ').polyline([(-1.8, -10), (-1.8, 10), (8, 30), (24, 30), (24, -30), (8, -30)]).close().extrude(-22).translate((0, -87, 0)).cut(cq.Workplane('XY').box(13.6, 50, 30).translate((13.2, -76, 0)))
r = plate.union(bar).union(hexb)
