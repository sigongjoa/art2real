import cadquery as cq
side = cq.Workplane('XZ').polyline([(56.8, -16.9), (100, -16.9), (100, 12), (94, 9.9), (73.2, 6.7), (72.2, 13), (56.8, 16.9)]).close().extrude(40, both=True)
top = cq.Workplane('XY').polyline([(56.8, -36.1), (72.1, -32), (73.2, -28.5), (92.4, -34.1), (100, -36), (100, 35.8), (92.4, 33.9), (73.2, 28.2), (72.1, 31.8), (56.8, 35.9)]).close().extrude(20, both=True)
front = cq.Workplane('YZ').polyline([(-34.4, -16.9), (34.3, -16.9), (25.8, 10), (19.7, 15), (-22.1, 15), (-27.9, 10), (-34.4, -16.9)]).close().extrude(110)
body = side.intersect(top).intersect(front)
body = body.cut(cq.Workplane('XY').box(40, 40.7, 10).translate((87.2, -2.85, -18.6)))
for P in ([(60, 13.8), (43.6, 13.8), (34.7, 19.6), (28.5, 15.2), (31.3, 11.2), (34.7, 13.6), (43.6, 7.4), (60, 7.4)],
          [(60, 1.6), (43.6, 1.6), (34.8, -4.7), (31.3, -2.3), (28.5, -6.3), (34.8, -10.6), (43.6, -4.8), (60, -4.7)]):
    body = body.union(cq.Workplane('XY', origin=(0, 0, -12.5)).polyline(P).close().extrude(15.4))
r = body.union(body.mirror('YZ'))
