import cadquery as cq
def yz(P): return cq.Workplane('YZ').polyline(P).close().extrude(120, both=True)
def xz(P): return cq.Workplane('XZ').polyline(P).close().extrude(80, both=True)
outl = xz([(-90.4, 100), (-94.8, 90.6), (-95, -100), (95, -100), (88.4, -32.8), (73.7, 90.6), (68.2, 100)])
plate = yz([(-25, 100), (-44.5, 33.4), (-56.9, -28.4), (-51, -37.3), (-9.8, -37.3), (-9.8, -100), (-1.1, -100), (5.7, -18), (9, 23.8), (0.3, 100)])
hexa = yz([(36.2, -100), (56.9, 23.8), (0.3, 100), (-23.7, 100), (-33.6, 73.6), (-47.8, 19.6), (-56.9, -28.4), (-9.8, -100)])
walls = xz([(-95, -100), (-84.2, -100), (-77.6, 23.8), (-77.6, 100), (-95, 100)]).union(xz([(84.2, -100), (95, -100), (75, 100), (66.6, 100), (66.6, 60), (75.3, -12.3)]))
b = plate.union(walls.intersect(hexa)).intersect(outl)
for x0, x1 in ((-46.1, -25.3), (28.7, 49.5)):
    b = b.cut(cq.Workplane('XY').box(x1 - x0, 100, 32.2).translate(((x0 + x1) / 2, 0, -53.4)))
for x0, x1 in ((-55.5, -34.7), (28, 48.9)):
    b = b.cut(cq.Workplane('XY').box(x1 - x0, 40, 45.8).translate(((x0 + x1) / 2, -1.4, 0.9)))
r = b
