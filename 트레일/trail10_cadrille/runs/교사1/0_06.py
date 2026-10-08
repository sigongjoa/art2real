import cadquery as cq
def yz(pts, w):
    return cq.Workplane('YZ', origin=(-w, 0, 0)).polyline(pts).close().extrude(2 * w)
def xz(pts, y0, y1):
    return cq.Workplane('XZ', origin=(0, y1, 0)).polyline(pts).close().extrude(y1 - y0)
side = [(-71.7, -50.9), (-64.7, -55.9), (72.4, -55.9), (100, -45.3), (100, 13.7), (91, 22.8), (-60, 22.8), (-71.7, 11.1)]
octa = [(-27.5, -44.2), (-12.8, -55.9), (12.8, -55.9), (27.5, -44.2), (27.5, 14.1), (18.7, 22.8), (-18.7, 22.8), (-27.5, 14.1)]
body = yz(side, 27.5).intersect(xz(octa, -80, 101))
front = xz([(-19, -50.9), (19, -50.9), (27.5, -44.2), (27.5, -7.8), (21.4, -1.8), (10, 3), (0, 5.3), (-10, 3), (-21.4, -1.8), (-27.5, -7.8), (-27.5, -44.2)], -88.8, -70)
tip = cq.Workplane("XZ", origin=(0, -88, -21.4)).circle(26.6).extrude(12)
r = body.union(front).union(tip)
r = r.cut(cq.Workplane('XZ', origin=(0, -60, -21.4)).circle(16.6).extrude(50))
r = r.union(yz([(10.3, 5), (10.3, 47.1), (19.1, 55.9), (57.8, 55.9), (98, 15), (98, 5)], 10.6))
r = r.cut(yz([(-51.1, -57), (-23.5, -8), (58.1, -8), (58.1, -57)], 12.8))
r = r.intersect(cq.Workplane('XY', origin=(0, 0, -60)).polyline([(-27.5, -101), (27.5, -101), (27.5, 76.9), (18.6, 100), (-18.6, 100), (-27.5, 76.9)]).close().extrude(120))
