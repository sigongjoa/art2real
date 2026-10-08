import cadquery as cq
def yz(pts, x0, x1):
    return cq.Workplane('YZ', origin=(x0, 0, 0)).polyline(pts).close().extrude(x1 - x0)
def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane('XY').box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
r = box(-62, 17, -100, 12, -42, -15)
r = r.union(cq.Workplane('XY', origin=(-20, -68, -42)).circle(36).extrude(45)).intersect(box(-62, 30, -100, 12, -50, 10))
r = r.cut(cq.Workplane('XY', origin=(-20, -68, -50)).circle(22).extrude(70))
r = r.cut(box(-34, -6, -101, -80, -50, 10))   # C 입구
r = r.union(box(0, 13, 0, 92, -42, -19))
r = r.union(yz([(10, -42), (50, -42), (95, -14), (95, 5), (40, -19), (10, -16)], -25, -7))
r = r.union(yz([(10, -42), (40, -42), (82, -5), (82, 8), (40, -24), (10, -16)], -50, -32))
r = r.union(yz([(5, -42), (25, -30), (65, 7), (62, 22), (45, 21), (5, -16)], -72, -58))
r = r.union(cq.Workplane("XZ", origin=(0, -12, 0)).polyline([(10, -42), (25, -35), (72, 22), (68, 42), (55, 40), (10, -10)]).close().extrude(26))
