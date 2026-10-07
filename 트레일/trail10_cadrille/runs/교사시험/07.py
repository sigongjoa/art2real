import cadquery as cq
def P(X, Yn, Yp):   # 팔각 윤곽 (모서리 비율은 z=0 단면에서)
    return [(-0.427 * X, -Yn), (0.427 * X, -Yn), (0.908 * X, -0.769 * Yn), (X, -0.59 * Yn), (X, 0.59 * Yp), (0.908 * X, 0.769 * Yp), (0.427 * X, Yp), (-0.427 * X, Yp), (-0.908 * X, 0.769 * Yp), (-X, 0.59 * Yp), (-X, -0.59 * Yn), (-0.908 * X, -0.769 * Yn)]
A, B, C = P(97.5, 68.2, 73.6), P(89.5, 61.2, 66.8), P(100, 73.8, 71.8)
low = cq.Workplane('XY', origin=(0, 0, -83.7)).polyline(A).close().workplane(offset=43.3).polyline(B).close().loft(ruled=True)
mid = cq.Workplane('XY', origin=(0, 0, -40.4)).polyline(B).close().workplane(offset=52.4).polyline(C).close().loft(ruled=True)
top = cq.Workplane('XY', origin=(0, 0, 12)).polyline(C).close().extrude(71.7)
arch = cq.Workplane('YZ').center(-1, 12).circle(71.7).extrude(110, both=True).union(cq.Workplane('XY').box(220, 200, 100).translate((0, 0, -38)))
r = low.union(mid).union(top).intersect(arch)
hole = cq.Workplane('XY', origin=(0, 2.8, -39.5)).circle(38.4).extrude(130).union(cq.Workplane('XY', origin=(0, 2.8, -84)).circle(49.3).workplane(offset=44.5).circle(38.4).loft())
r = r.cut(hole).cut(cq.Workplane('XY').box(38.4, 200, 60).translate((0, 0, 58.1)))
