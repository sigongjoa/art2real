// 3-14 L 자 블록: 오목한 곳은 안쪽 세로 모서리(점선) 하나뿐 → 규칙만으로는 닫힌 경계가 안 나옴.
// 아래 셋: 그 모서리에서 출발해 가로 · 대각 · 세로로 잇는 세 가지 자르기(빨간 점선)
#import "@preview/cetz:0.4.2"
#set page(width: 33.867cm, height: 19.05cm, margin: 0cm, fill: white)
#align(center + horizon, cetz.canvas(length: 2.0cm, {
  import cetz.draw: *
  let st = 3pt; let D = (0.38, -0.32)
  let block(o, cut) = {
    let p(x, y) = (o.at(0) + x, o.at(1) + y)
    let q(x, y) = (o.at(0) + x + D.at(0), o.at(1) + y + D.at(1))
    line(p(0, 0), p(1, 0), p(1, 1.2), p(2.2, 1.2), p(2.2, 2.2), p(0, 2.2), close: true, stroke: st)
    line(q(0, 0), q(1, 0), q(1, 1.2), q(2.2, 1.2), q(2.2, 2.2), stroke: st)
    for (x, y) in ((0, 0), (1, 0), (2.2, 1.2), (2.2, 2.2)) { line(p(x, y), q(x, y), stroke: st) }
    line(p(1, 1.2), q(1, 1.2), stroke: (thickness: 3pt, dash: "dotted"))   // 오목한 모서리
    let red = (paint: rgb("#d03030"), thickness: 3.4pt, dash: "dashed")
    if cut == 1 { line(p(1, 1.2), p(0, 1.2), stroke: red) }
    if cut == 2 { line(p(1, 1.2), p(0, 2.2), stroke: red) }
    if cut == 3 { line(p(1, 1.2), p(1, 2.2), stroke: red) }
  }
  block((-1.3, 0.6), 0)
  block((-5.3, -2.6), 1); block((-1.3, -2.6), 2); block((2.7, -2.6), 3)
}))
