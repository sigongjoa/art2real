import cadquery as cq
def yz(pts, x0, x1):
    return cq.Workplane('YZ', origin=(x0, 0, 0)).polyline(pts).close().extrude(x1 - x0)
def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane('XY').box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
top = [(-38, -45), (97, -45), (100, 8), (95, 22), (68, 31), (64, 28), (50, 22), (42, 21), (4, 29.5), (-38, 37)]
half = yz(top, 9, 71)
ch = yz([(-39, -46), (101, -46), (101, -4), (70, -4), (64, -20), (58, -20), (58, -46), (17, -46), (17, -15), (5, -15), (2, -46), (-39, -46)], 28, 51)
half = half.cut(box(28, 51, -39, 101, -46, 4)).union(box(28, 51, 58, 70, -20, 5)).union(box(28, 51, 2, 17, -15, 5)).union(box(28, 51, 70, 97, -5, 5))
pr = [(-100, -45), (-36, -45), (-36, 36.5), (-90, 43.5), (-100, 44)]
half = half.union(yz(pr, 6, 15)).union(yz(pr, 65, 74))
r = half.union(half.mirror('YZ'))
