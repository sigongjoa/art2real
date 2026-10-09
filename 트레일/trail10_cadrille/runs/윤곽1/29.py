# 골반: 양옆 볼 소켓(구 대신 x·z 원기둥 교차 r13.5 — 구는 메시가 새서) + 소켓 위 열림 · 밑면 사각 포켓(깊이 ~12)
r = 바탕
for x in (20, 80):
    cx = cq.Workplane("YZ").workplane(offset=x - 13.5).center(50, 50).circle(13.5).extrude(27)
    cz = cq.Workplane().workplane(offset=36.5).center(x, 50).circle(13.5).extrude(27)
    r = r.cut(cx.intersect(cz))
    r = r.cut(cq.Workplane().box(37, 70, 30).translate((x - 1.5 if x < 50 else x + 1.5, 40, 72)))
r = r.cut(cq.Workplane().box(56, 50, 24).translate((50, 50, 21)))
