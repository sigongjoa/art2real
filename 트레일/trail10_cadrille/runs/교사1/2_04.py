import cadquery as cq, math
P = [(11.9, 100), (9.8, 99.2), (3, -49.1), (15.3, -89.5), (22.5, -96.9), (32.3, -100), (39.5, -99.1), (46, -95.9), (51.6, -89.8), (54.3, -83), (54.5, -75.8), (52.2, -68.2), (41.5, -51.6), (39.7, -49.7), (43.2, -26.9), (44.4, -1.7), (40.8, 38.5), (35.8, 57.9), (29.5, 74), (20.6, 89.3)]
w = cq.Workplane('XY', origin=(0, 0, -4.5)).polyline(P).close().extrude(9).edges().chamfer(0.8)
w = w.cut(cq.Workplane('XY', origin=(0, 0, 1.5)).polyline([(13, -22.5), (19, 105), (80, 105), (80, -89.5)]).close().extrude(10))
w = w.cut(cq.Workplane('XY').center(31.6, -70.7).circle(9.8).extrude(10, both=True))
def slot(a, b, wd, z0, z1):
    (x0, y0), (x1, y1) = a, b; L = math.hypot(x1 - x0, y1 - y0); ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    return cq.Workplane('XY').box(L, wd, z1 - z0).rotate((0, 0, 0), (0, 0, 1), ang).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
for c in (13.4, 0.5, -12.5):
    w = w.cut(slot((13, c + 2), (60, c - 46), 2.6, 0.3, 2))
for a, b in (((14, -22), (40, -48)), ((15.7, -12.8), (41.3, -38.8)), ((16.4, -0.5), (42.7, -27.3)), ((17, 11.8), (43.7, -15.3))):
    w = w.cut(slot((a[0] - 3, a[1] + 3), (b[0] + 5, b[1] - 5), 3.4, -6, -3))
w = w.cut(slot((15, -22), (19.6, 90), 3.4, -6, -3))
r = w.union(w.mirror('YZ'))
