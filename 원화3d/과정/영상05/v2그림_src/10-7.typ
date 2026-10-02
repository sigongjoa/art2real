// 10-7 블렌더 렌더 + numpy 시점 이동(_r/10-7_*.png, 10-7.py) 배치
#import "@preview/cetz:0.4.2"
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#let T(s, c: luma(40), sz: 8pt, w: "bold") = text(font: "Malgun Gothic", size: sz, fill: c, weight: w, s)
#let I(p) = image("_r/10-7_" + p + ".png", width: 3.0cm)
#align(center + horizon, cetz.canvas(length: 1cm, {
  import cetz.draw: *
  let a = (stroke: rgb("#c0504d") + 2pt, mark: (end: ">", fill: rgb("#c0504d")))
  content((-5.6, 0), I("fg")); content((-5.6, 1.4), T("사진 한 장"))
  line((-3.85, 0), (-3.05, 0), ..a)
  content((-1.3, 1.15), I("fg")); content((1.8, 1.15), I("bg"))
  content((-1.3, -1.25), I("fgz")); content((1.8, -1.25), I("bgz"))
  content((-1.3, 2.55), T("앞 겹 · 원래 그대로")); content((1.8, 2.55), T("뒤 겹 · 물건을 지운 방"))
  content((0.25, -2.6), T("아래: 깊이 (보라 = 가까움 · 노랑 = 멂)", sz: 7pt, w: "regular"))
  line((3.55, 0), (4.35, 0), ..a)
  content((6.1, 1.15), I("warp1")); content((6.1, -1.25), I("warp2"))
  content((6.1, 2.55), T("시점 옮김 · 한 겹 → 검은 구멍"))
  content((6.1, -2.6), T("두 겹 → 뒤 겹으로 메움"))
}))
