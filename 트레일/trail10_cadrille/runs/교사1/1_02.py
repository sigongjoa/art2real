import cadquery as cq
def el(z, cx, a, b): return cq.Wire.makeEllipse(a, b, cq.Vector(cx, 0, z), cq.Vector(0, 0, 1), cq.Vector(1, 0, 0)) if a >= b else cq.Wire.makeEllipse(b, a, cq.Vector(cx, 0, z), cq.Vector(0, 0, 1), cq.Vector(0, 1, 0))
def loft(S, ruled=False): return cq.Workplane().add(cq.Solid.makeLoft([el(*s) for s in S], ruled))
neck = cq.Workplane().add(cq.Solid.makeCylinder(61.6, 45, cq.Vector(3, 0, -100)))
cone = loft([(-57, 3, 69, 83), (52, 3, 45.5, 52)], True)
dome = loft([(52, 3, 45.5, 52), (58, 3, 45, 50.5), (68, 3, 41, 47), (79, 3, 35, 39), (87, 3, 28, 31), (94, 3, 20, 21), (98, 3, 12, 12), (99.7, 3, 4, 4)])
cav = loft([(-95, 3, 54, 54), (57.7, 3, 39.5, 39.5)], True).union(loft([(57.7, 3, 39.5, 39.5), (64, 3, 39, 39), (72, 3, 36.8, 36.8), (79, 3, 33, 33), (85.5, 3, 28, 28), (90.7, 3, 21.5, 21.5), (94.5, 3, 14, 14), (96.8, 3, 4, 4)]))
r = neck.union(cone).union(dome).cut(cav).cut(cq.Workplane().add(cq.Solid.makeCylinder(60.4, 6, cq.Vector(3, 0, -101))))
for z in (65, 30, -10):
    for y in (-12.5, 12.5):
        r = r.cut(cq.Workplane().add(cq.Solid.makeCylinder(6.5, 50, cq.Vector(-80, y, z), cq.Vector(1, 0, 0))))
r = r.union(loft([(52, 3, 49, 59), (57, 3, 48, 58)], True).cut(cq.Workplane().add(cq.Solid.makeCylinder(39, 10, cq.Vector(3, 0, 50)))))
