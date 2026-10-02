// 11-2 마 · 니시하라: 윤곽 → 부위 → 부위마다 축(빨강) → 축마다 원기둥
#import "원기둥공통.typ": *
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#align(center + horizon, cetz.canvas(length: 0.62cm, {
  import cetz.draw: *
  // 부위: (a, b, r) — 앞에서 본 사람(얼굴 없음)
  let P = (
    ((0, 0.45), (0, 2.3), 0.62),                 // 몸통
    ((0, 2.55), (0, 3.25), 0.33),                // 머리
    ((-0.82, 2.15), (-1.08, -0.25), 0.18), ((0.82, 2.15), (1.08, -0.25), 0.18),   // 팔
    ((-0.32, 0.4), (-0.38, -2.95), 0.24), ((0.32, 0.4), (0.38, -2.95), 0.24),     // 다리
  )
  let L = 0.62
  let caps(dark, inner) = for (a, b, r) in P {
    line(a, b, stroke: (paint: dark, thickness: 2 * r * L * 1cm, cap: "round"))
    if inner != none { line(a, b, stroke: (paint: inner, thickness: (2 * r * L - 0.07) * 1cm, cap: "round")) }
  }
  let xs = (-9.6, -3.2, 3.2, 9.6)
  group({ translate((xs.at(0), 0)); caps(luma(90), none) })
  let tint = (rgb("#f6d7a7"), rgb("#f3b9b0"), rgb("#bcd9f2"), rgb("#bcd9f2"), rgb("#c6e8c8"), rgb("#c6e8c8"))
  group({ translate((xs.at(1), 0))
    for i in (2, 3, 4, 5, 1, 0) { let (a, b, r) = P.at(i)
      line(a, b, stroke: (paint: luma(60), thickness: 2 * r * L * 1cm, cap: "round"))
      line(a, b, stroke: (paint: tint.at(i), thickness: (2 * r * L - 0.06) * 1cm, cap: "round")) } })
  group({ translate((xs.at(2), 0))
    for (a, b, r) in P { line(a, b, stroke: (paint: luma(170), thickness: 2 * r * L * 1cm, cap: "round")) }
    for (a, b, r) in P { line(a, b, stroke: (paint: white, thickness: (2 * r * L - 0.05) * 1cm, cap: "round")) }
    for (a, b, r) in P {
      let d = (b.at(0) - a.at(0), b.at(1) - a.at(1)); let k = 0.18
      line((a.at(0) - k * d.at(0), a.at(1) - k * d.at(1)), (b.at(0) + k * d.at(0), b.at(1) + k * d.at(1)), stroke: rgb("#e0281e") + 1.8pt)
    } })
  group({ translate((xs.at(3), 0))
    for (a, b, r) in P.rev() { cyl(a, b, r) } })
  for x in (-6.4, 0, 6.4) { line((x - 0.7, 0.2), (x + 0.7, 0.2), mark: (end: ">", fill: rgb("#20a387")), stroke: rgb("#20a387") + 2.5pt) }
  let labs = ("윤곽", "부위 나누기", "축 긋기", "원기둥 씌우기")
  for (i, x) in xs.enumerate() { content((x, -4.0), T(labs.at(i), sz: 10pt, c: if i == 2 { rgb("#c0392b") } else { black })) }
}))
