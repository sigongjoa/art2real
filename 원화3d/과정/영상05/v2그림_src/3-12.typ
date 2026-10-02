// 3-12 애트니브 원반: 검은 원반에 구불한 선 하나 → 떼어 놓으면 양쪽 테두리가 다른 모양.
// 왼쪽 조각 = 넓고 매끈한 셋(경계는 뾰족한 꺾임 2 곳) · 오른쪽 조각 = 좁고 뾰족한 넷(경계는 둥근 마루 3 곳)
#import "@preview/cetz:0.4.2"
#set page(width: 33.867cm, height: 19.05cm, margin: 0cm, fill: white)
#let Rr = 3.6
#let x0 = -1.2
#let yt = calc.sqrt(Rr * Rr - x0 * x0)
#let N = 3
#let Pd = 2 * yt / N
#let A = 1.35
#let f(t) = 1 - calc.pow(calc.abs(2 * t - 1), 3)
#let crv = range(0, N * 60 + 1).map(i => { let u = i / 60; let k = calc.min(int(u), N - 1); let t = u - k; (x0 + A * f(t), yt - u * Pd) })
#let a0 = calc.atan2(x0, yt)   // 위 끝 각 (Typst atan2 는 (x, y))
#let rim(s, e) = range(0, 81).map(i => { let a = s + (e - s) * i / 80; (Rr * calc.cos(a), Rr * calc.sin(a)) })
#let sh(P, d) = P.map(p => (p.at(0) + d.at(0), p.at(1) + d.at(1)))
#align(center + horizon, cetz.canvas(length: 1cm, {
  import cetz.draw: *
  // 온 원반
  let o = (-9.5, 0)
  circle(o, radius: Rr, fill: black, stroke: none)
  line(..sh(crv, o), stroke: (paint: white, thickness: 2.6pt))
  // 왼쪽 조각: 선 + 왼쪽 호(아래 끝 → 위 끝, 왼쪽으로 돌아)
  let dl = (2.2, 1.6)
  line(..sh(crv + rim(-a0, a0 - 360deg), dl), close: true, fill: black, stroke: none)
  // 오른쪽 조각: 선 + 오른쪽 호
  let dr = (6.2, -1.6)
  line(..sh(crv + rim(-a0, a0), dr), close: true, fill: black, stroke: none)
  let ds = (paint: rgb("#888"), thickness: 2.8pt, dash: "dashed")
  for k in range(1, N) { let y = yt - k * Pd; line((dl.at(0) + x0 - 0.9, dl.at(1) + y), (dl.at(0) + x0 + 1.0, dl.at(1) + y), stroke: ds) }
  for k in range(N) { let y = yt - (k + 0.5) * Pd; line((dr.at(0) + x0 + A - 1.0, dr.at(1) + y), (dr.at(0) + x0 + A + 0.9, dr.at(1) + y), stroke: ds) }
}))
