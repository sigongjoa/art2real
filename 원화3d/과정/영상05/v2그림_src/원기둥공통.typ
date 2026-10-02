// 원기둥 그리기(11-2 · 11-3 공통): 축 a→b, 반지름 r — 옆면 + 위 뚜껑 타원
#import "@preview/cetz:0.4.2"
#let cyl(a, b, r, col: rgb("#dfe6ee"), st: luma(60) + 0.8pt) = {
  import cetz.draw: *
  let dx = b.at(0) - a.at(0); let dy = b.at(1) - a.at(1)
  let L = calc.sqrt(dx * dx + dy * dy)
  let ang = calc.atan2(dx, dy)          // Typst atan2 는 (x, y)
  group({
    translate(a); rotate(ang - 90deg)
    let e = 0.32 * r
    // 몸통(아래 반타원 포함) 채우기
    merge-path(fill: col, stroke: none, {
      line((-r, L), (-r, 0))
      arc((-r, 0), start: 180deg, stop: 360deg, radius: (r, e))
      line((r, 0), (r, L))
    })
    line((-r, 0), (-r, L), stroke: st); line((r, 0), (r, L), stroke: st)
    arc((-r, 0), start: 180deg, stop: 360deg, radius: (r, e), stroke: st)
    circle((0, L), radius: (r, e), fill: col.lighten(40%), stroke: st)
  })
}
#let T(s, c: black, sz: 9pt, w: "bold") = text(font: "Malgun Gothic", size: sz, fill: c, weight: w, s)
