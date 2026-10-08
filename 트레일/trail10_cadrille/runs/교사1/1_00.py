import cadquery as cq
def el(z, cx, cy, a, b): return cq.Wire.makeEllipse(a, b, cq.Vector(cx, cy, z), cq.Vector(0, 0, 1), cq.Vector(1, 0, 0)) if a >= b else cq.Wire.makeEllipse(b, a, cq.Vector(cx, cy, z), cq.Vector(0, 0, 1), cq.Vector(0, 1, 0))
def loft(S): return cq.Workplane().add(cq.Solid.makeLoft([el(*s) for s in S], True))
body = loft([(-100, -1, 24, 36, 38), (-60, 0, 12, 38.5, 40.5), (-20, 2.5, -1.5, 36.5, 35.5), (0, 2, -9, 33, 32), (40, -1, -23, 30, 30), (52, -1, -23, 31, 27)])
cav = loft([(-68, -1, 2, 29, 22), (-60, -0.5, 10, 29.5, 29), (-20, -1, -2, 25, 27), (0, -1, -9.5, 23, 24.5), (15, -1, -14, 18, 14)])
dome = cq.Workplane().sphere(30).translate((-1, -20, 45)).intersect(cq.Workplane().box(100, 100, 25).translate((0, 0, 62)))
collar = cq.Workplane().add(cq.Solid.makeTorus(30, 4, pnt=cq.Vector(-1, -23, 52)))
r = body.cut(cav).union(dome).union(collar)
for sx in (-1, 1):
    r = r.union(cq.Workplane().add(cq.Solid.makeCylinder(6, 48, cq.Vector(sx * 24, -40, 44), cq.Vector(sx * 4, -21, 44))))
r = r.union(cq.Workplane().add(cq.Solid.makeCylinder(6, 50, cq.Vector(-1, -6, 50), cq.Vector(0, 0, 1))))

ann = cq.Workplane().add(cq.Solid.makeCylinder(31, 10, cq.Vector(-1, 25, -101))).cut(cq.Workplane().add(cq.Solid.makeCylinder(18, 12, cq.Vector(-1, 25, -102))))
r = r.cut(ann).cut(cq.Workplane().add(cq.Solid.makeCylinder(12, 23, cq.Vector(-1, 25, -101))))
r = r.union(cq.Workplane().box(24, 5, 10).translate((-1, 25, -82)))
