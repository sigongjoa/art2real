import cadquery as cq
z0, h = -33.9, 61.6
fork = cq.Workplane('XY', origin=(0, 0, z0)).center(0, -72.5).circle(55.5).extrude(h).union(cq.Workplane('XY', origin=(0, 0, z0)).center(0, -51.6).rect(88.6, 41.8).extrude(h))
fork = fork.edges('not |Z').chamfer(5)
fork = fork.intersect(cq.Workplane('XY').box(200, 100, 200).translate((0, -50, 0)))
fork = fork.cut(cq.Workplane('XY').sphere(35.2).translate((0, -72.5, -3))).cut(cq.Workplane("XY").circle(26.6).extrude(50, both=True).translate((0, -72.5, 0)))
fork = fork.cut(cq.Workplane('XY').polyline([(29.1, -92), (45, -103), (-45, -103), (-29.1, -92)]).close().extrude(50, both=True))
fork = fork.cut(cq.Workplane("XY").box(53.2, 40, 100).translate((0, -100, 0)))
stem = cq.Workplane('XY', origin=(0, 0, z0)).polyline([(-30.8, -35), (30.8, -35), (30.8, 7.5), (24.7, 13.7), (-24.7, 13.7), (-30.8, 7.5)]).close().extrude(h)
neck = cq.Workplane('XY').box(36.4, 22, 34.5).translate((0, 22, -1.85))
ball = cq.Workplane('XY').sphere(36.8).translate((0, 63.2, -3)).intersect(cq.Workplane('XY').box(100, 100, 67.2).translate((0, 63.2, -0.3)))
r = fork.union(stem).union(neck).union(ball)
