import cadquery as cq
side = cq.Workplane('YZ', origin=(-70, 0, 0)).polyline([(-48, -100), (-6.1, -100), (-6.1, -66.2), (-23.2, -54.4), (-23.2, 19), (0.2, 79.7), (-30.4, 100), (-48, 56.1)]).close().extrude(140)
front = cq.Workplane('XZ', origin=(0, 60, 0)).polyline([(-43.5, -100), (43.5, -100), (57.6, -54.5), (57.6, 40), (47.4, 64.9), (41.1, 100), (-41.1, 100), (-47.4, 64.9), (-57.6, 40), (-57.6, -54.5)]).close().extrude(120)
r = side.intersect(front).intersect(cq.Workplane('XY', origin=(0, 0, -110)).polyline([(-59, -48), (59, -48), (40, 2), (-40, 2)]).close().extrude(220))
r = r.union(cq.Workplane('XZ', origin=(0, -10, -25)).circle(19).extrude(15))   # 목: y -23..-10
ball = cq.Workplane('XY').sphere(32.4).translate((0, 15.7, -25)).intersect(cq.Workplane('XY').box(80, 80, 62).translate((0, 15.7, -25)))
r = r.union(ball)
