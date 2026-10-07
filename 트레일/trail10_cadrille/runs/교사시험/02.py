import cadquery as cq
def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane('XY').box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
def plate(x0, x1, yf):   # 앞 치마 판: 옆 윤곽(아래가 앞으로 올라감 · 위가 앞으로 내려감)
    return cq.Workplane('YZ', origin=(x0, 0, 0)).polyline([(-19, -51), (-55, -51), (-94, -35), (-94, 8), (-19, 16)]).close().extrude(x1 - x0).intersect(box(x0, x1, yf, 0, -70, 30))
r = cq.Workplane('XY', origin=(0, 0, -61)).polyline([(-90, 47), (-90, -20), (-25, -42), (25, -42), (90, -20), (90, 47)]).close().extrude(87)
r = r.union(box(-100, -90, -20, 50, -51, 17)).union(box(90, 100, -20, 50, -51, 17))
r = r.union(cq.Workplane('YZ', origin=(-20, 0, 0)).polyline([(-45, -61), (-45, 35), (-35, 52), (-20, 57), (0, 60), (10, 51), (15, 38), (47, 36), (47, -61)]).close().extrude(40))
for s in (-1, 1):
    r = r.cut(box(44, 61, -2, 38, -20, 30).mirror('YZ') if s < 0 else box(44, 61, -2, 38, -20, 30))
    for a, b, yf in ((75, 85, -94), (65, 75, -64), (35, 45, -64), (25, 35, -94)):
        r = r.union(plate(a, b, yf) if s > 0 else plate(-b, -a, yf))
r = r.union(cq.Workplane('XZ', origin=(0, 40, -20)).circle(13).extrude(-25))
r = r.union(cq.Workplane('XY').sphere(22).translate((0, 72, -20)).intersect(box(-25, 25, 40, 100, -41, 1)))
