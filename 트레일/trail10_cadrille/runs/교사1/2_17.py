import cadquery as cq
A = [(20.2, -100), (-37.4, -26.1), (-38.9, -18.9), (-21.9, 48.7), (-6.6, 60.6), (3.6, 91.2), (26.7, 100), (34.3, 95.3), (34.2, -93.6), (25.1, -100)]
B = [(24.9, -87.7), (-26.1, -21.9), (-27.2, -16.7), (-10.9, 47.9), (2.4, 58.6), (12.4, 89.5), (31.4, 96.8), (39, 92), (38.9, -81.3), (29.8, -87.7)]
w = lambda P, z: cq.Wire.makePolygon([cq.Vector(x, y, z) for x, y in P], close=True)
plate = cq.Workplane('XY').add(cq.Solid.makeLoft([w(B, -24.1), w(A, -10)], True)).union(cq.Workplane('XY', origin=(0, 0, -10)).polyline(A).close().extrude(4.4))
lug = cq.Workplane('YZ', origin=(6.9, 0, 0)).polyline([(52.9, -6), (54.5, 14), (56.3, 18.3), (59.8, 22.5), (63.8, 22.2), (70.3, 23.1), (74.3, 21.8), (78, 18.7), (92.5, -6)]).close().extrude(15.5)
boss = cq.Workplane('YZ', origin=(3.3, 0, 0)).center(68.5, 10).circle(6.5).extrude(22)
dim = cq.Workplane('YZ', origin=(1, 0, 0)).center(68.5, 10).circle(3).extrude(4).union(cq.Workplane('YZ', origin=(23.3, 0, 0)).center(68.5, 10).circle(3).extrude(4))
r = plate.union(lug).union(boss).cut(dim)
