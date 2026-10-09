# 팔꿈치 이음 판: 바깥 = 두 원(r40) 합 · 양 끝 축 구멍(가운데 r13, 면 쪽 r19.5 로 벌어지는 V 벽) + 바깥 쪽 쐐기 열림 = C 클립
원 = lambda x, rr: cq.Workplane().workplane(offset=37.4).center(x, 50).circle(rr).extrude(25.2)
판 = 원(25, 40).union(원(75, 40)).intersect(바탕.union(cq.Workplane().box(100, 40, 25.2).translate((50, 50, 50))))
def 구멍(x):
    p = cq.Workplane("XZ").polyline([(0, 30), (19.5, 30), (19.5, 37.4), (13.5, 50), (19.5, 62.6), (19.5, 70), (0, 70)]).close().revolve(360, (0, 0, 0), (0, 1, 0))
    return p.translate((x, 50, 0))
def 쐐기(s):  # s=+1 왼쪽, -1 오른쪽
    pts = [(50 - s * 50, 80), (50 - s * 40, 62), (50 - s * 30, 50), (50 - s * 40, 38), (50 - s * 50, 20)]
    return cq.Workplane().workplane(offset=30).polyline([(50 - s * 55, 80)] + pts + [(50 - s * 55, 20)]).close().extrude(40)
r = 판.cut(구멍(20)).cut(구멍(80)).cut(쐐기(1)).cut(쐐기(-1))
