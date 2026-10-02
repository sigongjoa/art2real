// 반더폴 단면(10-1 · 10-2) 공통: 초타원 + 각도 혹(가우스)으로 단면 하나
#import "@preview/cetz:0.4.2"
#let pts(w, d, n, cx, cy, bumps, k: 240) = range(k).map(i => {
  let t = 360.0 * i / k
  let c = calc.cos(t * 1deg); let s = calc.sin(t * 1deg)
  let r = calc.pow(calc.pow(calc.abs(c) / w, n) + calc.pow(calc.abs(s) / d, n), -1.0 / n)
  let f = 1.0
  for (a, amp, sw) in bumps {
    let dt = calc.rem(t - a + 540.0, 360.0) - 180.0
    f += amp * calc.exp(-calc.pow(dt / sw, 2))
  }
  (cx + r * f * c, cy + r * f * s)
})
// sec: (이름, w, d, n, cx, cy, 혹들, 색, 이름표 각도, 이름표 위치)
#let draw-group(secs) = {
  import cetz.draw: *
  for (name, w, d, n, cx, cy, bumps, col, la, lp) in secs {
    let p = pts(w, d, n, cx, cy, bumps)
    line(..p, close: true, stroke: (paint: col, thickness: 1.6pt))
    let i = calc.rem(int(la / 360.0 * 240), 240)
    line(p.at(i), lp, stroke: (paint: col, thickness: 0.5pt, dash: "dotted"))
    content(lp, text(font: "Malgun Gothic", size: 9pt, fill: col, weight: "bold", name), anchor: if lp.at(0) < cx { "east" } else { "west" }, padding: 0.08)
  }
}
#let C = (rgb("#c0392b"), rgb("#d35400"), rgb("#2e86c1"), rgb("#16a085"), rgb("#8e44ad"), rgb("#2c3e50"))
