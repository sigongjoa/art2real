import cadquery as cq
H = [(10.8, -69.9), (19.3, -69.9), (40.9, -56.6), (51.6, -56.6), (54.9, -46.6), (59.5, -46.6), (63, -56.6), (100, -56.6), (100, 56.6), (63, 56.6), (59.5, 46.6), (54.9, 46.6), (51.6, 56.6), (40.9, 56.6), (19.3, 69.9), (-52.6, 69.9), (-59.5, 67), (-66, 63.4), (-72.1, 59.1), (-77.6, 54.2), (-82.6, 48.7), (-82.6, -48.7), (-77.6, -54.2), (-72.1, -59.1), (-66, -63.4), (-59.5, -67), (-52.6, -69.9)]
B = lambda sx, sy, sz, x, y, z: cq.Workplane('XY').box(sx, sy, sz).translate((x, y, z))
r = cq.Workplane('XY', origin=(0, 0, -97.4)).polyline(H).close().extrude(194.8).faces('>Z or <Z').edges().chamfer(5)
bump = cq.Workplane('YZ', origin=(-100, 0, 0)).center(0, -45).circle(24).extrude(20).cut(cq.Workplane('YZ', origin=(-101, 0, 0)).center(0, -45).circle(16).circle(11).extrude(3))   # 왼쪽 둥근 돌기 + 고리 홈
r = r.union(bump)
r = r.cut(cq.Workplane('XY', origin=(-20.8, 0, -100)).circle(47.9).extrude(200)).cut(B(65, 95.8, 50, 12, 0, 75))   # 큰 구멍 + 위쪽 긴 구멍
for sy in (-1, 1):
    r = r.cut(cq.Workplane('XZ', origin=(0, sy * 70, 0)).center(-20, -55).polygon(6, 28).extrude(4 * sy))      # 육각 홈
    r = r.cut(cq.Workplane('XZ', origin=(0, sy * 70, 0)).center(-20, 70).slot2D(22, 9, 90).extrude(4 * sy))   # 작은 길쭉 홈
