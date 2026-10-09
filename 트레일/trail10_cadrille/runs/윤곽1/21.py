# 머리 아래 껍질: 위로 벌어지는 속을 로프트로 파내고(벽 ~3) 바닥에 큰 창
속 = (cq.Workplane().workplane(offset=38).center(50, 44).rect(38, 70)
      .workplane(offset=34).center(0, 6).rect(42, 90).loft())
r = 바탕.cut(속).cut(cq.Workplane().box(36, 62, 20).translate((49, 44, 30)).edges("|Z").fillet(3))
