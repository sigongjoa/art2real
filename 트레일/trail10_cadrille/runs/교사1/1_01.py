import cadquery as cq, math
prof = [(-87, -46.2), (-84, -20), (-80, -5), (-70, 6), (-60, 20), (-50, 28), (-40, 33), (-30, 39), (-20, 42), (-10, 44), (0, 45), (10, 44), (20, 43), (30, 40), (40, 38), (50, 34), (60, 31), (70, 25), (80, 20), (89, 5), (89, -20)]
def pod(sx):
    p = cq.Workplane('YZ', origin=(sx * 63 if sx < 0 else 63, 0, 0)).spline(prof[1:-1], includeCurrent=False).close()
    p = cq.Workplane('YZ', origin=(-12.5, 0, 0)).moveTo(*prof[0]).spline(prof[1:], includeCurrent=True).lineTo(89, -46.2).close().extrude(25)
    p = p.cut(cq.Workplane('YZ', origin=(-120, 0, 0)).center(95, -50).circle(45).extrude(240))
    p = p.intersect(cq.Workplane('XY').box(16, 300, 300))
    for k in range(14):   # 갈비 마디 = 짧은 원기둥
        t = math.radians(4 + k * 12.6); y, z = -74.5 * math.cos(t), -46 + 78.5 * math.sin(t)
        d = cq.Vector(74.5 * math.sin(t), 78.5 * math.cos(t), 0).normalized()
        c = cq.Vector(0, y, z) - cq.Vector(0, d.x, d.y) * 5.5
        p = p.union(cq.Workplane().add(cq.Solid.makeCylinder(12.5, 10.5, c, cq.Vector(0, d.x, d.y))))
    p = p.rotate((0, 0, 0), (0, 1, 0), -13.5).translate((-77.5, 0, 0))
    if sx > 0: p = p.mirror('YZ')
    return p.intersect(cq.Workplane('XY').box(200, 200, 92.4))
blk = cq.Workplane('XY').box(92, 51, 48.7).translate((0, -21.2, -21.9))
r = blk
for sx in (-1, 1):
    tw = cq.Workplane('XY').box(29, 56.5, 69).edges('|Y and >Z').chamfer(5).translate((sx * 40.5, -24, -11.7))
    tw = tw.cut(cq.Workplane('XY').box(40, 28, 41).translate((sx * 40.5, -24, -26)))
    r = r.union(tw).union(cq.Workplane('XY').box(12, 64, 46).translate((sx * 59, -28, -23))).union(pod(sx))
