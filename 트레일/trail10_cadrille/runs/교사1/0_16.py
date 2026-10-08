import cadquery as cq
def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane('XY').box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
def mx(w, s): return w.mirror('YZ') if s < 0 else w
F = [(-100, -57), (-95, -63), (-74, -67), (-34, -75), (34, -75), (74, -67), (95, -63), (100, -57), (100, 60), (94, 67), (27, 80), (-27, 80), (-94, 67), (-100, 60)]
hull = cq.Workplane('XY', origin=(0, 0, -57.3)).polyline(F).close().extrude(70.3)
hull = hull.intersect(cq.Workplane('XZ').polyline([(-94, -57.3), (94, -57.3), (100, -51), (100, -10), (72, 13), (-72, 13), (-100, -10), (-100, -51)]).close().extrude(100, both=True))
rear = cq.Workplane('XY', origin=(0, 0, -57.3)).polyline(F).close().extrude(114).intersect(box(-100, 100, 55, 90, -60, 60))
rear = rear.intersect(cq.Workplane('XZ').polyline([(-94, -57.3), (94, -57.3), (100, -51), (100, 25), (85, 50), (50, 57), (-50, 57), (-85, 50), (-100, 25), (-100, -51)]).close().extrude(100, both=True))
bar = cq.Workplane('YZ', origin=(-25, 0, 0)).polyline([(-86, -36), (-86, 10), (-80, 44), (-74, 50), (62, 50), (62, -36)]).close().extrude(50)
r = hull.union(rear).union(bar)
for s in (-1, 1):
    pocket = cq.Workplane('XY', origin=(0, 0, -36)).center(s * 54.5, 0).circle(30).extrude(60).union(mx(box(25, 54.5, -30, 30, -36, 24), s))
    bowl = cq.Workplane('XY').add(cq.Solid.makeSphere(45, cq.Vector(s * 55, 0, 15), cq.Vector(1, 0, 0), -90, 90)).intersect(mx(box(11, 99, -60, 60, -40, 59), s))
    r = r.cut(pocket).cut(bowl).cut(mx(box(57, 87, -42, 44, -60, -48), s))
    r = r.cut(cq.Workplane('XY', origin=(s * 45, 0, -60)).circle(20).extrude(80))
r = r.cut(box(-57, 57, -45, 43, -60, -36))
