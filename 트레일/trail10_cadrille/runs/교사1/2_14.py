import cadquery as cq
r = None
for s in (1, -1):
    oct_ = cq.Workplane('XZ').polyline([(s * x, z) for x, z in [(45.5, 63.6), (54.5, 63.6), (65.4, 54.7), (72.7, 18.2), (72.7, -18.2), (65.4, -54.7), (54.5, -63.6), (45.5, -63.6)]]).close().extrude(110, both=True)
    xy = cq.Workplane('XY').polyline([(s * x, y) for x, y in [(45.5, -100), (54.5, -100), (64.4, -90.9), (72.7, 9.1), (72.7, 100), (45.5, 100)]]).close().extrude(80, both=True)
    p = oct_.intersect(xy)
    r = p if r is None else r.union(p)
r = r.intersect(cq.Workplane('YZ').polyline([(-100, -14), (-100, 14), (-65.5, 49.1), (-52.6, 63.6), (100, 63.6), (100, -63.6), (-52.6, -63.6), (-65.5, -49.1)]).close().extrude(80, both=True))
for s in (1, -1):
    r = r.union(cq.Workplane('YZ').polyline([(y, s * z) for y, z in [(-18.2, 63.6), (-54.5, 63.6), (-63.6, 54.5), (-63.6, 48.2), (-33.6, 48.2)]]).close().extrude(60, both=True))
r = r.cut(cq.Workplane('XZ').circle(56.4).extrude(-96).translate((0, 5.5, 0)))
