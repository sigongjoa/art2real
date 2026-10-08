import cadquery as cq
T = 30.3
def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane('XY').box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
# 팔: 둥근 끝(중심 y=-70) 납작 막대 · 모서리 모따기 · 끝 모래시계 홈 · 위아래 원뿔 오목
arm = cq.Workplane('XY', origin=(0, 0, -T)).center(0, -70).circle(T).extrude(2 * T).union(box(-T, T, -70, 20, -T, T)).faces('>Z or <Z').edges().chamfer(6)
cone = cq.Workplane('XZ').polyline([(18.2, 0), (80, 61.8), (80, -61.8)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).translate((0, -70, 0)).intersect(box(-90, 90, -110, -39.4, -60, 60))
dim = cq.Workplane('XZ').polyline([(0, 24.2), (6, 24.2), (12.1, T), (12.1, 40), (0, 40)]).close().revolve(360, (0, 0, 0), (0, 1, 0))
arm = arm.cut(cone).cut(dim.translate((0, -70, 0))).cut(dim.mirror('XY').translate((0, -70, 0))).cut(box(-40, 40, -39.4, -9.1, -18.2, 19.4))
up = cq.Workplane('XY', origin=(0, 0, -T)).polyline([(-T, 9.1), (T, 9.1), (48.5, 27.3), (48.5, 100), (-48.5, 100), (-48.5, 27.3)]).close().extrude(2 * T).edges('|Y').chamfer(6)
# 가운데 구멍(렌즈) · 가로대 위 홈
hole = [(0, 22.8), (12, 24.8), (29.6, 31), (30.4, 32.1), (29.6, 33.3), (16.7, 33.3), (12, 34.5), (8, 36.9), (0, 38.8)]
hole = hole + [(-x, y) for x, y in hole[-2:0:-1]]
up = up.cut(cq.Workplane('XY', origin=(0, 0, -40)).polyline(hole).close().extrude(80))
fork = box(-33.9, 33.9, 39.4, 70.9, -40, 40).cut(cq.Workplane('XY').circle(24.4).extrude(80, both=True).translate((0, 20.4, 0)))
up = up.cut(fork.intersect(box(-33.9, 33.9, 39.4, 70.9, 16, 40).union(box(-T, T, 39.4, 70.9, -40, 40)).union(cq.Workplane('XZ', origin=(0, 71, 0)).circle(37.6).extrude(40)).union(box(-33.9, 33.9, 39.4, 70.9, -16, 40))))
up = up.cut(cq.Workplane('XZ', origin=(0, 101, 0)).circle(19.4).extrude(30.1)).cut(box(-18.2, 18.2, 70.9, 101, 0, 40))
r = arm.union(up)
