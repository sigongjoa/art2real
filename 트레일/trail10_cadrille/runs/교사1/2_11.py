import cadquery as cq
outl = cq.Workplane('XZ').polyline([(-30.8, 100), (-81.5, -21.8), (-80.4, -74.8), (62.4, -100), (65.8, -77.4), (65.3, -40.8), (27.4, 14.7), (27.4, 58.8)]).close().extrude(80, both=True)
zb = lambda x: -22 + 0.339 * (x + 81)
up = cq.Workplane('XZ').polyline([(-120, zb(-120)), (120, zb(120)), (120, 120), (-120, 120)]).close().extrude(80, both=True)
lo = cq.Workplane('XZ').polyline([(-120, zb(-120)), (120, zb(120)), (120, -120), (-120, -120)]).close().extrude(80, both=True)
fu = cq.Workplane('XY').polyline([(-100, -9), (100, -81), (100, 20.2), (-100, 20.2)]).close().extrude(120, both=True)
fl = cq.Workplane('XY').polyline([(-100, -22), (100, -62), (100, 20.2), (-100, 20.2)]).close().extrude(120, both=True)
plate = up.intersect(fu).union(lo.intersect(fl)).intersect(outl).intersect(cq.Workplane('XY').box(200, 73.3, 200).translate((0, -16.45, 0)))
H = [(-28.1, -6.8), (15.1, -14.4), (30.1, -55.7), (1.9, -89.3), (-41.3, -81.7), (-56.4, -40.4)]
hexb = cq.Workplane('XZ', origin=(0, 20.2, 0)).polyline(H).close().extrude(-32.9).faces('>Y').chamfer(3)
r = plate.union(hexb)
