// 3-11 부품 두드러짐: (a) 한 선 (b) 오른쪽 영역은 뾰족한 조각, 왼쪽 영역은 둥근 조각으로 나뉨
// (c) 둥근 조각 쪽이 앞(회색) (d) 한 선 위에서 앞뒤가 바뀜 — 둥근 조각이 있는 쪽을 칠함
#import "@preview/cetz:0.4.2"
#set page(width: 33.867cm, height: 19.05cm, margin: 0cm, fill: white)
#set text(font: ("Malgun Gothic",), size: 26pt)
#let A = 1.5    // 혹 높이
#let Pd = 2.0   // 한 주기 길이
#let N = 3
#let f(t) = 1 - calc.pow(calc.abs(2 * t - 1), 3)   // 가운데 둥글고 양 끝은 뾰족
// 주기 k 의 t 구간 [a, b] 를 따라가는 점 (세로: y 는 위에서 아래로)
#let seg(ox, oy, k, a, b) = range(0, 41).map(i => { let t = a + (b - a) * i / 40; (ox + A * f(t), oy - (k + t) * Pd) })
#let curve(ox, oy) = range(N).map(k => seg(ox, oy, k, 0, 1)).flatten().chunks(2)
#let GR = rgb("#a0a0a0")
#align(center + horizon, cetz.canvas(length: 1cm, {
  import cetz.draw: *
  let st = 2.4pt; let oy = 3.0
  // (a)
  let ax = -14.0
  line(..curve(ax, oy), stroke: st)
  // (b) 오른쪽 영역 조각(뾰족, 꼭짓점 사이) → 왼쪽에 · 왼쪽 영역 조각(둥근 혹) → 오른쪽에
  let bx = -9.0
  for k in range(N + 1) {
    let pts = ()
    if k > 0 { pts += seg(bx, oy - 0.25 * k, k - 1, 0.5, 1) }
    if k < N { pts += seg(bx, oy - 0.25 * k, k, 0, 0.5) }
    line(..pts, (bx + A, pts.last().at(1)), (bx + A, pts.first().at(1)), close: true, fill: GR, stroke: 1.6pt)
  }
  let bx2 = -5.6
  for k in range(N) {
    let pts = seg(bx2, oy - 0.25 * k, k, 0, 1)
    line(..pts, close: true, fill: GR, stroke: 1.6pt)
  }
  // (c) 왼쪽 영역을 칠함 — 둥근 혹이 두드러져 앞으로 보임
  let cx = -0.5
  line(..curve(cx, oy), (cx - 1.6, oy - N * Pd), (cx - 1.6, oy), close: true, fill: GR, stroke: none)
  line(..curve(cx, oy), stroke: st)
  // (d) 가로로 누운 같은 선: 왼쪽 반은 혹이 위로(아래가 앞), 오른쪽 반은 혹이 아래로(위가 앞)
  let dx = 4.5; let dy = 0.6
  let h(k, s, x0, y0) = range(0, 41).map(i => { let t = i / 40; (x0 + (k + t) * Pd * 0.75, y0 + s * A * 0.7 * f(t)) })
  let L = range(3).map(k => h(k, 1, dx, dy - 1.0)).flatten().chunks(2)
  let R = range(3).map(k => h(k, -1, dx + 5.0, dy + 1.0)).flatten().chunks(2)
  line(..L, (L.last().at(0), dy - 2.4), (dx, dy - 2.4), close: true, fill: GR, stroke: none)
  line(..R, (R.last().at(0), dy + 2.4), (R.first().at(0), dy + 2.4), close: true, fill: GR, stroke: none)
  line(..L, (L.last().at(0), R.first().at(1)), ..R, stroke: st)
  line((dx, dy - 1.0), (dx, dy - 2.6), stroke: st); line(R.last(), (R.last().at(0), dy + 2.6), stroke: st)
  for (x, t) in ((ax + 0.7, [a]), (-7.6, [b]), (cx - 0.1, [c]), (dx + 4.6, [d])) { content((x, oy - N * Pd - 1.6), t) }
}))
