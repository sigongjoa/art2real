import cadquery as cq
cyl = cq.Workplane('XZ').circle(100).extrude(14, both=True).translate((0, -50, 0)).union(cq.Workplane('XZ').circle(100).extrude(36, both=True).translate((0, -50, 0)))
dome = cq.Workplane('XY').sphere(100).rotate((0, 0, 0), (1, 0, 0), 90).translate((0, -14, 0))
b = cyl.union(dome).intersect(cq.Workplane('XY').box(220, 171.2, 220).translate((0, -0.2, 0)))
for s in (1, -1):
    pk = cq.Workplane('XZ').circle(45).extrude(-130).translate((s * 62, -18, 70))
    sp = cq.Workplane('XY').sphere(45).rotate((0, 0, 0), (1, 0, 0), 45).translate((s * 62, -18, 70))
    b = b.cut(pk.union(sp))
r = b
