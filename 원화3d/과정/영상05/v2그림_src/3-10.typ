// 3-10 a = 오목점끼리 이은 선(자연스러운 부품 경계) · b = 오목점이 아닌 곳을 가로지름(부자연)
#import "@preview/cetz:0.4.2"
#set page(width: 33.867cm, height: 19.05cm, margin: 0cm, fill: white)
#set text(font: ("Malgun Gothic",), size: 26pt)
#align(center + horizon, cetz.canvas(length: 1.7cm, {
  import cetz.draw: *
  let st = 2.6pt
  let N1 = (5.4, 0.95); let N2 = (5.6, -0.55); let T1 = (6.4, 2.6); let T2 = (7.4, -2.0)
  let W1 = (0.9, 0.35); let W2 = (1.05, -0.45)
  hobby(N2, (4.4, -1.65), (2.4, -0.9), W2, (0.0, -1.3), (-1.2, -0.6), (-1.1, 0.6), (0.0, 1.0), W1, (2.4, 2.0), (4.2, 1.85), N1, stroke: st)
  line(N1, T1, T2, N2, stroke: st)
  let ext(p, q, a, b) = { let d = (q.at(0) - p.at(0), q.at(1) - p.at(1)); ((p.at(0) + a * d.at(0), p.at(1) + a * d.at(1)), (p.at(0) + b * d.at(0), p.at(1) + b * d.at(1))) }
  let ds = (paint: rgb("#2060c0"), thickness: 2.6pt, dash: "dashed")
  let la = ext(W1, W2, -3.2, 4.0); let lb = ext(N1, N2, -2.2, 3.0)
  line(..la, stroke: ds); line(..lb, stroke: ds)
  content((la.at(1).at(0), la.at(1).at(1) - 0.4), text(fill: rgb("#2060c0"))[a])
  content((lb.at(1).at(0), lb.at(1).at(1) - 0.4), text(fill: rgb("#2060c0"))[a])
  let b0 = (2.6, -2.1); let b1 = (8.6, 1.7)
  line(b0, b1, stroke: (paint: rgb("#d03030"), thickness: 2.6pt, dash: "dashed"))
  content((b1.at(0) + 0.35, b1.at(1) + 0.15), text(fill: rgb("#d03030"))[b])
  for p in (W1, W2, N1, N2) { circle(p, radius: 0.09, fill: black) }
}))
