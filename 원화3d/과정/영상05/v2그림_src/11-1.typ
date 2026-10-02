// 11-1 블렌더 렌더(_r/11-1.png, 11-1.py) 위에 지수 방향 이름표
#import "@preview/cetz:0.4.2"
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#let T(s, c: luma(50), sz: 9pt) = text(font: "Malgun Gothic", size: sz, fill: c, weight: "bold", s)
#align(center + horizon, scale(88%, cetz.canvas(length: 1cm, {
  import cetz.draw: *
  content((0, 0), image("_r/11-1.png", height: 7.2cm))
  let c = rgb("#c0392b"); let b = rgb("#2e86c1")
  line((-4.3, 3.3), (-4.3, -3.3), mark: (end: ">", fill: c), stroke: c + 1.5pt)
  content((-4.6, 0), T([남북 지수 ε#sub[1] 커짐], c: c), anchor: "east")
  line((3.6, 3.85), (-3.6, 3.85), mark: (end: ">", fill: b), stroke: b + 1.5pt)
  content((0, 4.15), T([동서 지수 ε#sub[2] 커짐], c: b))
  for (i, v) in ("0.3", "1", "2", "3").enumerate() {
    content((-3.95, 2.7 - i * 1.8), T(v, c: c, sz: 7pt))
    content((2.7 - i * 1.8, -3.85), T(v, c: b, sz: 7pt))
  }
  content((5.6, -0.0), T("식 하나 ·\n숫자 둘", sz: 10pt), anchor: "west")
})))
