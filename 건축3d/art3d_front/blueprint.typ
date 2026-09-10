#set page(paper: "a4", margin: 1.5cm)
#set text(font: ("Malgun Gothic", "Segoe UI"), size: 9pt)

#align(center)[#text(size: 16pt, weight: "bold")[설계도 — gate_front]]
#align(center)[#text(size: 8pt, fill: gray)[2026-09-10 · schema art-to-3d/buildspec/2 · art-to-3d-maps]]
#v(2pt)
#rect(width: 100%, inset: 6pt, fill: rgb("#fff6e5"))[
  *규칙* — 조립 스크립트는 `buildspec.json` **만** 읽는다. 상수를 스크립트에 적지 않는다.
  스크립트에 숫자를 손으로 넣는 순간 추출값과 갈라지고, 눈으로 고치기 시작한다.
]

== 기준 (datum)

#table(columns: (auto, 1fr), stroke: 0.4pt, inset: 5pt,
  [단위], [총높이 = 1.0],
  [원점], [발바닥 z=0 · 몸 중심선 x=0],
  [축], [+x 화면 오른쪽(캐릭터의 왼쪽) · -y 앞 · +z 위],
  [주의], [미러는 원점 (0,0,0) 기준. rotation_euler 는 쓰지 않는다(회전은 정점에 굽는다).],
)

== 외형

#figure(image("blueprint_dims.png", width: 100%), caption: [외형 치수 — 정면 반폭과 측면 깊이. 붉은 숫자가 실측값])

== 참조 원화

#text(fill: gray)[원화 없음 — `--refdir` 를 주면 실린다]

== 삼면도

#figure(image("blueprint_views.png", width: 100%), caption: [삼면도 — 같은 z 축. 미러로 대체된 쪽은 그리지 않는다])

#table(columns: 5, stroke: 0.4pt, inset: 5pt,
  [*뷰*], [*출처*], [*판 수*], [*T-접합*], [*재구성 오차*],
  [front], [r6_gate_front.png], [77], [35], [4.22],

)

== 좌우 대칭

#table(columns: (auto, auto, 1fr), stroke: 0.4pt, inset: 5pt,
  [미러 쌍], [0], [한쪽만 만들고 Mirror 로 넘긴다],
  [중심 걸침], [2], [좌우 대칭 부품. 중심선을 지난다],
  [*비대칭(unique)*], [*24*], [짝이 없다 — **따로 만들어야 한다**],
)
#text(size: 8pt, fill: gray)[
비대칭 부품을 미러로 처리하면 원작에 없는 대칭이 생긴다 — 오메가몬의 어깨 방패가 그런 것.
반대로 **대칭인 캐릭터인데 unique 가 많다면** 짝짓기 허용오차가 빡빡하거나 **참조 그림 자체가
좌우 비대칭**이라는 뜻이다(생성 이미지는 완전 대칭이 아니다). 숫자를 그대로 믿지 말고
삼면도에서 눈으로 확인해라 — LESSON 47.
]

== 맵 (정면)

#grid(columns: (1fr, 1fr, 1fr), gutter: 6pt,
  figure(image("regions.png", width: 100%), caption: [판 분할]),
  figure(image("order.png", width: 100%), caption: [가림 순서 (T-접합)]),
  figure(image("necks.png", width: 100%), caption: [목]),
  figure(image("depth.png", width: 100%), caption: [깊이 (crease 팽창)]),
  figure(image("normal.png", width: 100%), caption: [법선]),
  figure(image("shade.png", width: 100%), caption: [그 법선으로 셰이딩]),
)

#table(columns: (auto, auto, 1fr), stroke: 0.4pt, inset: 5pt,
  [깊이/폭], [1.0], [측면 참조 실측. 지어내면 1.4배 깊어진다],
  [판 안쪽 평평도], [#text(fill: rgb("#1a7f37"), weight: "bold")[11.8도]], [10도 이하 평면 / 30도 이상 물집. bevel 3px],
  [평면 맞춘 판], [175], [나머지는 전체 팽창 그대로],
)

== 뷰별 맵

#text(fill: gray)[추가 뷰 없음]

== 뷰별 부품표

#text(fill: gray)[추가 뷰 없음]

#pagebreak()

== 공정표 (build ops)

#rect(width: 100%, inset: 5pt, fill: rgb("#eef5ff"))[
  *규약* — 사각면 100% · 미러 원점 (0,0,0) · #raw("rotation_euler") 금지(회전은 정점에 굽는다) ·
  하드서피스는 flat 셰이딩
]

#table(columns: 6, stroke: 0.4pt, inset: 4pt,
  align: (left, center, right, left, center, center),
  [*id*], [*make*], [*protrusion*], [*modifier 스택*], [*셰이딩*], [*미러*],
  [gate_front_r530], [plate], [0.014], [SUBSURF(0)], [flat], [-],
[gate_front_r563], [plate], [0.0104], [SUBSURF(0)], [flat], [-],
[gate_front_r2828], [plate], [0.0097], [SUBSURF(0)], [flat], [-],
[gate_front_r1311], [blade], [0.0076], [SUBSURF(0)], [flat], [-],
[gate_front_r876], [plate], [0.0083], [SUBSURF(0)], [flat], [-],
[gate_front_r1291], [blade], [0.009], [SUBSURF(0)], [flat], [-],
[gate_front_r322], [plate], [0.0083], [SUBSURF(0)], [flat], [-],
[gate_front_r355], [plate], [0.0083], [SUBSURF(0)], [flat], [-],
[gate_front_r688], [plate], [0.004], [SUBSURF(0)], [flat], [-],
[gate_front_r588], [plate], [0.0083], [SUBSURF(0)], [flat], [-],
[gate_front_r574], [plate], [0.009], [SUBSURF(0)], [flat], [-],
[gate_front_r223], [plate], [0.0047], [SUBSURF(0)], [flat], [-],
[gate_front_r119], [plate], [0.0083], [SUBSURF(0)], [flat], [-],
[gate_front_r36], [plate], [0.0076], [SUBSURF(0)], [flat], [-],
[gate_front_r25], [blade], [0.0083], [SUBSURF(0)], [flat], [-],
[gate_front_r85], [blade], [0.0083], [SUBSURF(0)], [flat], [-],
[gate_front_r28], [blade], [0.0083], [SUBSURF(0)], [flat], [-],
[gate_front_r150], [blade], [0.0083], [SUBSURF(0)], [flat], [-],
[gate_front_r141], [blade], [0.0083], [SUBSURF(0)], [flat], [-],
[gate_front_r90], [plate], [0.0083], [SUBSURF(0)], [flat], [-],

)

#text(size: 8pt, fill: gray)[
모디파이어 값은 규칙에서 **파생**된다 — Solidify = protrusion x 0.9, Subsurf = 1,
Mirror 는 좌우 짝이 있는 부품에만. 규칙은 `recipes` 에 한 번만 적혀 있고
부품마다 손으로 타이핑하지 않는다. `skip` 인 부품은 미러로 대체되므로 만들지 않는다.
]

== 조립 후 점검

#table(columns: (auto, 1fr), stroke: 0.4pt, inset: 5pt,
  [사각면 100%], [ngon-count == 0],
[정수리 높이], [abs(bbox-z-max - 1.0) < 0.01],
[미러 원점], [all mirrored objects at (0,0,0)],

)

== 부품 상세 (정면)

#figure(image("blueprint_parts.png", width: 88%), caption: [부품 윤곽 — 월드 좌표. 회색이 외형])

== 부품표 (면적 상위 24 / 전체 77)

#table(columns: 7, stroke: 0.4pt, inset: 4pt,
  align: (left, center, right, center, center, right, right),
  [*id*], [*재질*], [*면적px*], [*z 범위(월드)*], [*돌출*], [*깊이순위*], [*목*],
  [gate_front_r530], [steel], [6,147], [-1.551-0.989], [0.014], [+8], [0],
[gate_front_r563], [steel], [5,990], [-1.551-0.946], [0.0104], [+3], [0],
[gate_front_r2828], [dark], [5,197], [-6.222-0.989], [0.0097], [+2], [3],
[gate_front_r1311], [dark], [3,037], [-2.369-0.989], [0.0076], [-1], [0],
[gate_front_r876], [dark], [2,961], [-1.572-0.989], [0.0083], [+0], [0],
[gate_front_r1291], [dark], [2,827], [-2.283-0.989], [0.009], [+1], [1],
[gate_front_r322], [dark], [1,007], [-1.788-0.107], [0.0083], [+0], [0],
[gate_front_r355], [dark], [941], [-1.788-0.085], [0.0083], [+0], [0],
[gate_front_r688], [gold], [671], [-1.120-0.709], [0.004], [-6], [4],
[gate_front_r588], [gold], [406], [-0.625-0.731], [0.0083], [+0], [0],
[gate_front_r574], [gold], [402], [-0.754-0.752], [0.009], [+1], [0],
[gate_front_r223], [gold], [363], [-0.044-0.989], [0.0047], [-5], [0],
[gate_front_r119], [dark], [355], [-0.152-0.989], [0.0083], [+0], [0],
[gate_front_r36], [dark], [327], [0.042-0.989], [0.0076], [-1], [0],
[gate_front_r25], [dark], [163], [0.193-0.989], [0.0083], [+0], [0],
[gate_front_r85], [dark], [159], [0.430-0.989], [0.0083], [+0], [0],
[gate_front_r28], [dark], [149], [-0.216-0.989], [0.0083], [+0], [0],
[gate_front_r150], [dark], [125], [0.322-0.989], [0.0083], [+0], [0],
[gate_front_r141], [dark], [115], [0.516-0.989], [0.0083], [+0], [0],
[gate_front_r90], [dark], [110], [0.430-0.989], [0.0083], [+0], [0],
[gate_front_r203], [gold], [92], [-0.022-0.839], [0.0083], [+0], [0],
[gate_front_r278], [gold], [77], [-0.130-0.387], [0.0083], [+0], [0],
[gate_front_r97], [dark], [70], [0.236-0.795], [0.0083], [+0], [0],
[gate_front_r7], [dark], [68], [0.408-0.989], [0.0083], [+0], [0],

)

== px → 월드 매핑

#table(columns: (auto, 1fr), stroke: 0.4pt, inset: 5pt,
  [앵커], [y 0 → z 1.0 · y 511 → z 0.0],
  [월드/px], [0.021526],
  [출처], [given(외형과 같은 이미지에서 나옴 — 맞춤 없음)],
  [맞춤 오차], [#text(fill: rgb("#1a7f37"), weight: "bold")[중앙값 상대오차 0%]],
)

== 신뢰도

#table(columns: (auto, 1fr), stroke: 0.4pt, inset: 5pt,
  [값 출처], [derived(T-junction) 77, given(외형과 같은 이미지에서 나옴 — 맞춤 없음) 77, guessed(진폭). 순위는 derived 77, measured 154],
  [분할 재구성 오차], [4.22 / 255],
  [T-접합], [35],
)
#text(size: 8pt, fill: gray)[
`guessed` 로 표시된 값은 **하류가 다시 재야 한다.** 지금 돌출(protrusion)이 전부 guessed 다 —
측면/3-4 참조에서 부품별 앞뒤를 재면 derived 로 바뀐다.
]

#pagebreak()

= 부품 검증 — **붙이기 전에 하나씩 확인한다**

한 부품만 만들어 **자기 bbox 에 맞춘 창**으로 렌더하고, 그 부품이 나온 원화의 같은 창과
실루엣을 겹쳐 IoU 를 낸다. 전체 창으로 보면 작은 부품은 몇 픽셀이라 판정이 안 된다.

#table(columns: (auto, auto, auto, auto), stroke: 0.4pt, inset: 5pt, align: left,
  [*부품*], [*종류*], [*IoU*], [*판정*],
  
)

#table(columns: (auto, 1fr), stroke: 0.4pt, inset: 5pt,
  [검사한 부품], [0],
  [통과 (IoU >= 0.7)], [0],
  [중앙값 IoU], [0.000],
  [조립 대상], [77],
)

#text(size: 8pt, fill: gray)[
**실패한 부품은 조립에서 뺀다.** 49개를 한꺼번에 붙여놓고 전체 IoU 를 보면 숫자가
안 움직여도 어느 부품이 틀렸는지 알 수 없다 — 실제로 0.537\~0.615 에서 다섯 번
안 움직였다. 부품별로 재기 시작하자 원인이 한 번에 나왔다 (윤곽 단순화 허용오차가
크기에 비례하지 않아 작은 부품이 2.4배 부풀었고, 라벨 번짐이 버려진 판까지 흡수했다).
]

#pagebreak()

== 판정

#table(columns: (auto, 1fr), stroke: 0.4pt, inset: 6pt,
  [기준이 맞나], [],
  [부품 검증을 통과했나], [],
  [외형 치수가 맞나], [],
  [부품표에서 뺄 것 / 합칠 것], [],
  [이 설계도로 조립해도 되나], [],
)
#text(size: 8pt, fill: gray)[판정란은 사람이 적는다 (LIMS 규약).]
