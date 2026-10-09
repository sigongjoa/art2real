# 손잡이: 안쪽 손잡이 면에 가로 홈(폭 1.7 · 깊이 0.4 · 간격 5.5) · 안쪽 구석 둥글림 시도
r = 바탕
try: r = r.edges("|Y").edges(cq.selectors.BoxSelector((12, 0, 26), (88, 100, 34))).fillet(3)
except Exception: pass
홈 = cq.Workplane()
x = 19.0
while x < 81.5:
    r = r.cut(cq.Workplane().box(1.7, 30, 2).translate((x + 0.85, 50, 29.4))); x += 5.5
