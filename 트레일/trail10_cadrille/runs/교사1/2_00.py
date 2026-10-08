import cadquery as cq
r = None
for cx, s in ((56, 1), (-51, -1)):
    ring = cq.Workplane('XZ').polyline([(0, -25.1), (76, -25.1), (81, -19), (81, 19), (76, 25.1), (0, 25.1)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).translate((cx, 0, 0))
    cone = cq.Workplane('XZ').polyline([(0, -26), (43, -26), (43, -18), (32, -5), (27.6, 0), (32, 5), (43, 18), (43, 26), (0, 26)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).translate((cx, 0, 0))
    ring = ring.cut(cone)
    wedge = cq.Workplane('XY').polyline([(cx, 0), (cx + s * 90, 97), (cx + s * 90, -97)]).close().extrude(30, both=True)
    ring = ring.cut(wedge)
    r = ring if r is None else r.union(ring)
r = r.intersect(cq.Workplane('XY').box(200, 170, 60))
