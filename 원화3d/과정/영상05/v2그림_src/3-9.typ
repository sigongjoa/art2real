// 3-9 회전체: 옆선이 오목하게 가장 세게 휘는 곳마다 고리 경계(빨간 점선). 회색 점 = 가장 가는 곳(어긋날 수 있음).
#import "@preview/cetz:0.4.2"
#set page(width: 33.867cm, height: 19.05cm, margin: 0cm, fill: white)
#set text(font: ("Malgun Gothic",), size: 20pt)
#let J = json("3-9.json")
#align(center + horizon, cetz.canvas(length: 1cm, {
  import cetz.draw: *
  let s = 1.45; let ox = -6.5; let oy = -7.2; let st = 2.6pt
  let P = J.pts
  let R = P.map(p => (ox + s * p.at(0), oy + s * p.at(1))); let L = P.map(p => (ox - s * p.at(0), oy + s * p.at(1)))
  line(..R, stroke: st); line(..L, stroke: st)
  line(R.first(), L.first(), stroke: st); line(R.last(), L.last(), stroke: st)
  let red = (paint: rgb("#d03030"), thickness: 3pt, dash: "dashed")
  for i in J.cut { line(L.at(i), R.at(i), stroke: red) }
  for i in J.neck { circle(R.at(i), radius: 0.13, fill: rgb("#888"), stroke: none) }
  // 메모: 경계(점선)와 가장 가는 곳(회색 점)이 어긋남
  let i = J.cut.at(1); let n = J.neck.at(1)
  content((R.at(i).at(0) + 1.0, R.at(i).at(1) + 0.15), anchor: "west", text(fill: rgb("#d03030"))[경계])
  content((R.at(n).at(0) + 1.0, R.at(n).at(1) - 0.45), anchor: "west", text(fill: rgb("#777"))[가장 가는 곳])
  // 종 모양 회전면
  let bx = 7.5; let by = -4.5; let k = 1.35; let h = 5.2; let e = 0.28
  let prof(r) = h * calc.exp(-r * r / 2)
  let rr = range(0, 101).map(j => -3.6 + 7.2 * j / 100)
  let rim(a0, a1) = range(0, 61).map(j => { let t = a0 + (a1 - a0) * j / 60; (bx + k * 3.6 * calc.cos(t), by + k * 3.6 * e * calc.sin(t)) })
  line(..rim(0deg, 180deg), stroke: st)  // 뒤 테두리 — 종이 가림
  line(..rr.map(r => (bx + k * r, by + prof(r))), ..rim(180deg, 360deg).rev(), close: true, fill: white, stroke: none)
  line(..rr.map(r => (bx + k * r, by + prof(r))), stroke: st)
  line(..rim(180deg, 360deg), stroke: st)
  for t in (250deg, 290deg) {  // 앞쪽 자오선 둘
    line(..range(0, 61).map(j => { let r = 3.6 * j / 60; (bx + k * r * calc.cos(t), by + k * r * calc.sin(t) * e + prof(r)) }), stroke: 1.8pt)
  }
  let rb = J.rb
  circle((bx, by + prof(rb)), radius: (k * rb, k * rb * e), stroke: red)
}))
