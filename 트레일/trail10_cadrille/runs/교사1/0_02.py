import cadquery as cq
cx = 3.0
def lofted(levels, ruled):
    w = cq.Workplane('XY', origin=(cx, 0, levels[0][0])).ellipse(levels[0][1], levels[0][2])
    z0 = levels[0][0]
    for z, a, b in levels[1:]:
        w = w.workplane(offset=z - z0).ellipse(a, b); z0 = z
    return w.loft(ruled=ruled)
skirt = lofted([(-59, 71.4, 85.4), (51.5, 48.3, 56.3)], True)
dome = lofted([(51.5, 48.3, 56.3), (60, 47.2, 55), (70, 44.5, 51.5), (80, 39, 45.5), (90, 29, 34), (96, 19, 22), (99.8, 5, 6)], False)
base = cq.Workplane('XY', origin=(cx, 0, -100)).circle(61.5).extrude(42)
r = skirt.union(dome).union(base)
cav = cq.Workplane('XZ', origin=(cx, 0, 0)).polyline([(0, -101), (60.2, -101), (60.2, -95.1), (54, -95.1), (39.2, 57.7)]).threePointArc((27.7, 85.4), (8, 96.1)).lineTo(0, 96.1).close().revolve(360, (0, 0, 0), (0, 1, 0))
r = r.cut(cav)
# 돔 둘레 고리(z=70) · 두건 윗단 테(z=55~58)
path = cq.Workplane('XY', origin=(cx, 0, 70)).ellipse(45.5, 52.5).val()
ring = cq.Workplane('XZ', origin=(cx + 45.5, 0, 70)).circle(2.5).sweep(cq.Workplane('XY').add(path))
r = r.union(ring)
r = r.union(cq.Workplane('XY', origin=(cx, 0, 55)).ellipse(50, 58).extrude(2.7))
r = r.cut(cav)
