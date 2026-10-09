# 고관절 조인트: 아래 축은 y 축 원통으로 둥글게 · 집게 안쪽은 진짜 원통 + 구 소켓
def Y원통(R, y0, y1): return cq.Workplane("XZ", origin=(50, y0, 50)).circle(R).extrude(-(y1 - y0))
틀 = Y원통(23, -5, 45).union(Y원통(25, 45, 58)).union(cq.Workplane("XY").box(120, 60, 120).translate((50, 88, 50)))
r = 바탕.intersect(틀)
r = r.cut(cq.Workplane("XY", origin=(50, 75, 0)).circle(15.5).extrude(100))   # 집게 구멍(z 축 원통)
r = r.cut(cq.Workplane("XY").sphere(17.5).translate((50, 75, 50)))            # 안쪽 구면
