// 6-2 가려진 모서리는 뾰족할 수도 둥글 수도 · 착시 판에서는 그 모서리가 흐릿 (Kellman & Shipley 1991 Fig.48 의 생각)
#import "@preview/cetz:0.4.2"
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#set text(font: "Noto Sans KR", size: 13pt)
#let G = rgb("#9aa3ad")
#align(center + horizon, cetz.canvas(length: 0.62cm, {
  import cetz.draw: *
  // a: 회색 사각형 위에 검은 사각형
  group({
    translate((-11.5, 1.2))
    rect((0, 0), (2.6, 2.6), fill: G, stroke: none)
    rect((1.5, -1.3), (4.1, 1.3), fill: black, stroke: none)
    content((2.05, -2.4), [a])
  })
  // b: 가려진 모서리 후보 둘
  group({
    translate((-3.8, 1.2))
    rect((0, 0), (2.6, 2.6), fill: G, stroke: none)
    rect((3.6, 0), (6.2, 2.6), fill: G, stroke: none, radius: (south-east: 1.0))
    content((1.3, -0.7), text(size: 11pt)[뾰족])
    content((4.9, -0.7), text(size: 11pt)[둥긂])
    content((3.1, -2.4), [b])
  })
  // c: 가림 없이 착시로 — 흰 사각형의 오른쪽 아래 모서리는 정해지지 않는다
  group({
    translate((6.6, 2.4))
    circle((1.2, 0.35), radius: (2.5, 1.1), fill: black, stroke: none)
    circle((0, -2.5), radius: 1.45, fill: black, stroke: none)
    rect((0, -2.5), (2.6, 0.0), fill: white, stroke: none)
    content((1.2, -5.0), [c])
  })
}))
