# 날개 둘(x=50 대칭): 날 윗면을 0.8 낮춰 등뼈만 남김 · 아랫면에 갈매기 홈 셋 + 긴 홈 하나
import math
def 홈(x0, y0, x1, y1, w, z0, z1):  # 두 점을 잇는 폭 w 의 막대 홈
    L = math.hypot(x1 - x0, y1 - y0); a = math.degrees(math.atan2(y1 - y0, x1 - x0))
    return (cq.Workplane("XY").box(L, w, z1 - z0).rotate((0, 0, 0), (0, 0, 1), a)
            .translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)))
def 왼쪽():
    날 = cq.Workplane("XY", origin=(0, 0, 51.5)).polyline([(10, 105), (41, 105), (43, 40), (23, 13), (10, 13)]).close().extrude(5)
    c = 날
    for k in range(3): c = c.union(홈(38.5, 55 - 6.5 * k, 25.5, 42 - 6.5 * k, 1.8, 40, 48.7))
    return c.union(홈(35.7, 95, 40.7, 28, 1.5, 40, 48.7))
L = 왼쪽(); Rr = L.mirror("YZ", basePointVector=(50, 0, 0))
r = 바탕.cut(L).cut(Rr)
