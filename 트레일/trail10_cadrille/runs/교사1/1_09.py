import cadquery as cq
XZ = [(39, -100), (45, -100), (47, -83), (55, -57.6), (55, -50.6), (48, -25), (43.5, -19.7), (34.4, -19), (-38.6, 71.7), (-40, 84), (-40, 94), (-55, 98.6), (-56.6, 92), (-47, 89), (-47, 72), (30, -26), (39, -26)]
YZ = [(44.9, -100.0), (-6.1, -100.0), (-44.9, 86.9), (-44.9, 100.0), (44.9, 91.4)]
XY = [(-56.1, -44.9), (-56.6, 44.9), (51.0, 44.9), (56.6, -15.2), (51.5, -21.2), (36.9, -23.7), (-39.9, -44.9)]
w = lambda y: cq.Wire.makePolygon([cq.Vector(x - 0.0 * y, y, z) for x, z in XZ], close=True)   # y 따라 x 가 밀린 판(층밀림)
r = cq.Workplane().add(cq.Solid.makeLoft([w(-50), w(50)], True))
r = r.intersect(cq.Workplane('YZ').polyline(YZ).close().extrude(80, both=True)).intersect(cq.Workplane('XY').polyline(XY).close().extrude(120, both=True))
