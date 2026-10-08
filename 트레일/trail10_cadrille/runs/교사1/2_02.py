import cadquery as cq
def xz(P, y0, y1):
    return cq.Workplane('XZ').polyline(P).close().extrude(100, both=True).intersect(cq.Workplane('XY').box(300, y1 - y0, 300).translate((0, (y0 + y1) / 2, 0)))
rear = xz([(-84.6, -71.1), (84.6, -71.1), (85.1, -14.4), (97.2, -2.3), (97.2, 57.4), (-97.2, 57.4), (-97.2, -2.3), (-85.1, -14.4)], -22, 73.1)
front = xz([(-84.6, -71.1), (84.6, -71.1), (95, -20), (97.2, 57.4), (-97.2, 57.4), (-95, -20)], -77, -20)
side = cq.Workplane('YZ').polyline([(-60, -71.1), (71, -71.1), (73.1, -69), (73.1, 57.4), (-18.5, 57.4), (-18.5, 55.3), (-51.5, 55.3), (-51.5, 58.2), (-76.6, 58.2),
                                    (-76, 25), (-73, -5), (-70, -27), (-63, -33), (-58, -55)]).close().extrude(110, both=True)
b = rear.union(front).intersect(side)
for s in (1, -1):
    b = b.union(cq.Workplane('XY').box(26.5, 75, 16).translate((s * 62.75, 12.5, 63.1)).edges('|Y').fillet(1.5))
    b = b.cut(cq.Workplane('XY').box(12.7, 95, 30).translate((s * 55.05, 17, -64)))
    sock = cq.Workplane('YZ').polyline([(-4.8, 12.5), (34.3, 12.5), (34.3, 35.8), (24.3, 45.7), (5.2, 45.7), (-4.8, 35.8)]).close().extrude(60)
    b = b.cut(sock.translate((49.2, 0, 0)) if s > 0 else sock.translate((-109.2, 0, 0)))
b = b.cut(cq.Workplane('XY').box(14.6, 37, 40).translate((0, 26.5, 46.3)))
cav = cq.Workplane('XZ').circle(20).extrude(65).translate((0, 30, -45)).union(cq.Workplane('XY').sphere(20).translate((0, 30, -45)))
cav = cav.intersect(cq.Workplane('XY').box(60, 200, 60).translate((0, 0, -59.7)))
b = b.cut(cav).cut(cq.Workplane('XY').box(21.6, 100, 30).translate((0, 15, -71)))
r = b
