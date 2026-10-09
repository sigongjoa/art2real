# 하운드 투구: 아래 목 구멍(원기둥 r12) · 아래 앞쪽 비움 · 앞면 얼굴 쐐기(눈 홈까지 비스듬히 파고 듦)
r = 바탕
r = r.cut(cq.Workplane().workplane(offset=0).center(50, 47).circle(12).extrude(36))           # 목 구멍
r = r.cut(cq.Workplane().box(50, 46, 30).translate((50, 23, 15)))                             # 아래 앞 비움 (x25~75, y<46, z<30)
r = r.cut(cq.Workplane().box(26, 17, 20).translate((50, 54.5, 5)))                           # 아래 가운데 홈
쐐기 = cq.Workplane("YZ").workplane(offset=20).polyline([(15, 36), (35, 55), (40, 62), (22, 83), (5, 83), (5, 36)]).close().extrude(60)
r = r.cut(쐐기)
