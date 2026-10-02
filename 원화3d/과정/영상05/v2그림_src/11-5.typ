// 11-5 블렌더 렌더(_r/11-5.png, 11-5.py) + 이름표
#import "@preview/cetz:0.4.2"
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#let T(s, c: luma(60), sz: 8pt) = text(font: "Malgun Gothic", size: sz, fill: c, weight: "bold", s)
#align(center + horizon, cetz.canvas(length: 1cm, {
  import cetz.draw: *
  content((0, 0), image("_r/11-5.png", width: 14.6cm))
  content((-5.2, 3.6), T("원래 모양(회색) → 상자 몇 개(색)", sz: 9pt), anchor: "west")
  content((4.2, 3.6), box(fill: rgb("#e6c726").lighten(20%), inset: 3pt, T("노랑 = 좌판 · 몸통")), anchor: "west")
}))
