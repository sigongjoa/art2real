import cadquery as cq
def yz(pts, x0, x1):
    return cq.Workplane('YZ', origin=(x0, 0, 0)).polyline(pts).close().extrude(x1 - x0)
def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane('XY').box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
side = [(-19, -100), (40, -100), (40, -84), (36.5, -83), (36, -50), (40.5, 0), (44.7, 76), (-44, 76), (-40, 0), (-36, -50), (-32, -80), (-30, -90)]
tab = [(-40, 22), (40.7, 22), (44.7, 76), (35.8, 76), (13.9, 100), (-44.7, 100), (-43.8, 76)]
front = cq.Workplane('XZ', origin=(0, 60, 0)).polyline([(12, 76), (86.5, 76), (85.4, 0), (82, -70), (82, -100), (15.4, -100), (14, -70), (12, 0)]).close().extrude(120)
half = yz(side, 10, 90).intersect(front).union(yz(tab, 9, 16.7))
half = half.cut(cq.Workplane('XY', origin=(0, 0, 47)).polyline([(34, -7), (54, -7), (54, 13), (44, 23), (34, 13)]).close().extrude(40))
half = half.cut(box(38, 59.2, -50, 19.8, -101, -54.6))
half = half.cut(cq.Workplane('XZ', origin=(48.6, 4, -73.5)).circle(16).extrude(60))
r = half.union(half.mirror('YZ'))
