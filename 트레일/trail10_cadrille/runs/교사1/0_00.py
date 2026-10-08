import cadquery as cq
def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane('XY').box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
def yz(pts, x0, x1):
    return cq.Workplane('YZ', origin=(x0, 0, 0)).polyline(pts).close().extrude(x1 - x0)
base = yz([(-75.2, -78.9), (59.3, -78.9), (59.3, -19.7), (51.6, -18.3), (-36.6, -18.3), (-36.6, -8.5), (-40.4, -5.3), (-75.2, -54.4)], 6.8, 99.5)
fin = cq.Workplane('YZ', origin=(86.4, 0, 0)).moveTo(-75.2, -60).lineTo(-75.2, -54.4).spline([(-50.9, -18.6), (-24.9, 12.5), (0, 38), (24, 58.8), (49.6, 78.3)], includeCurrent=True) \
    .spline([(62, 45.4), (69, 20.4), (73.1, -1)], includeCurrent=True).lineTo(65.8, -10.3).lineTo(60, -17.5).lineTo(59.3, -17.5).lineTo(59.3, -60).close().extrude(13.1)
heel = yz([(59, -78.9), (67, -78.9), (72.5, -55.6), (74.9, -37), (75.2, -27), (75.1, -22.4), (59, -19.5)], 6.8, 19.9)
r = base.union(fin).union(heel)
# 바깥 아래 모따기: z = -58.7 + 0.37y + 1.07(x-70.5) 아래 제거
import math
n = cq.Vector(1.07, 0.37, -1).normalized()
pl = cq.Plane(origin=(70.5, 0, -58.7), xDir=cq.Vector(0, 1, 0).cross(n).normalized() if False else cq.Vector(-0.37, 1.07, 0).normalized(), normal=n)
r = r.cut(cq.Workplane(pl).rect(600, 600).extrude(300).intersect(box(70.5, 200, -200, 200, -200, 200)))
# 바깥 D 홈
D = cq.Workplane('YZ', origin=(91.7, 0, 0)).moveTo(-28.5, -70).lineTo(-28.5, -45).spline([(-27, -26), (-20, -12.4), (-10, -3.4), (0, 1.5), (13, 3.3), (25, 1), (35, -4), (44, -12), (47.8, -17)], includeCurrent=True).lineTo(47.8, -70).close().extrude(20)
r = r.cut(D)
# 볼 소켓
r = r.cut(cq.Workplane('XY', origin=(43.5, 21, -33)).circle(16).extrude(20)).cut(box(30.8, 56, 21, 45.7, -40.2, 0))
r = r.cut(cq.Workplane("XY").sphere(16).translate((43.5, 21, -31)).intersect(box(20, 70, 0, 45, -46, -20)))
# 안쪽 V 홈 · 바닥 홈
r = r.cut(yz([(42.8, -18.3), (-24.3, -43.2), (-49.3, -16.6), (-49.3, 10), (45, 10), (45, -18.3)], 6.0, 20.2))
r = r.cut(box(22, 38.3, -80, -54.7, -80, -60)).cut(box(19.9, 36.2, 39.1, 60, -80, -52.9))
r = r.union(r.mirror('YZ'))
