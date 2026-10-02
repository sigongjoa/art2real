// 10-6 See-through: 머리카락 · 치마 한 층을 앞 겹 / 뒤 겹으로 가르고, 앞 겹에 가려졌던 뒤쪽을 새로 채운다
#import "@preview/cetz:0.4.2"
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#let T(s, c: black, sz: 9pt, w: "bold") = text(font: "Malgun Gothic", size: sz, fill: c, weight: w, s)
#let FR = rgb("#e67e22"); #let BK = rgb("#7d5ba6")
#let hatch(c) = tiling(size: (5pt, 5pt), place(line(start: (0pt, 5pt), end: (5pt, 0pt), stroke: c + 0.7pt)))
#align(center + horizon, cetz.canvas(length: 0.56cm, {
  import cetz.draw: *
  let mir(ps) = ps + ps.rev().map(p => (-p.at(0), p.at(1)))
  // 머리카락
  let hair-back = mir(((0, 3.1), (1.15, 2.75), (1.55, 1.9), (1.6, 0.6), (1.85, -0.6), (1.7, -1.5), (2.0, -2.3), (1.6, -3.0), (1.25, -2.6), (1.0, -3.1), (0.5, -2.8), (0.15, -3.2)))
  let face = ((0, 1.1), (0.68, 0.95))
  let bangs = mir(((0, 3.15), (1.2, 2.8), (1.4, 1.9), (1.25, 0.6), (1.35, -0.3), (1.0, -0.4), (0.95, 0.5), (0.85, 1.4), (0.6, 1.55), (0.45, 1.85), (0.25, 1.5), (0.05, 1.8)))
  // 치마
  let sk-back = mir(((0, 2.0), (0.75, 2.0), (1.3, 0.9), (1.8, -0.4), (2.05, -1.6), (1.75, -1.85), (1.4, -1.6), (1.05, -1.9), (0.7, -1.65), (0.35, -1.95), (0.0, -1.7)))
  let sk-front = mir(((0, 2.0), (0.75, 2.0), (1.05, 1.3), (1.5, 0.6), (1.85, -0.1), (1.65, -0.25), (1.45, -0.05), (1.25, -0.3), (1.0, -0.05), (0.75, -0.3), (0.5, -0.05), (0.25, -0.3), (0.0, -0.05)))
  let hem1 = ((-1.3, 0.75), (-0.95, 0.6), (-0.65, 0.75), (-0.32, 0.6), (0, 0.75), (0.32, 0.6), (0.65, 0.75), (0.95, 0.6), (1.3, 0.75))
  let st(c) = (paint: c.darken(25%), thickness: 1.0pt)
  let in-hair(x) = group({ translate((x, 0))
    catmull(..hair-back, close: true, fill: BK.lighten(70%), stroke: st(BK))
    circle(face.at(0), radius: face.at(1), fill: white, stroke: (paint: luma(170), thickness: 0.6pt, dash: "dotted"))
    catmull(..bangs, close: true, fill: FR.lighten(55%), stroke: st(FR)) })
  let in-skirt(x) = group({ translate((x, 0)); scale(0.9)
    catmull(..sk-back, close: true, fill: BK.lighten(70%), stroke: st(BK))
    catmull(..sk-front, close: true, fill: FR.lighten(55%), stroke: st(FR))
    catmull(..hem1, stroke: st(FR)) })
  let xs = (-11.4, -7.2, -3.0, 3.0, 7.2, 11.4)
  in-hair(xs.at(0))
  group({ translate((xs.at(1), 0)); catmull(..bangs, close: true, fill: FR.lighten(55%), stroke: st(FR)) })
  group({ translate((xs.at(2), 0))
    catmull(..hair-back, close: true, fill: BK.lighten(70%), stroke: st(BK))
    catmull(..bangs, close: true, fill: hatch(BK.lighten(20%)), stroke: (paint: BK, thickness: 0.7pt, dash: "dashed"))
    circle(face.at(0), radius: face.at(1), fill: hatch(BK.lighten(20%)), stroke: (paint: BK, thickness: 0.7pt, dash: "dashed")) })
  in-skirt(xs.at(3))
  group({ translate((xs.at(4), 0)); scale(0.9); catmull(..sk-front, close: true, fill: FR.lighten(55%), stroke: st(FR)); catmull(..hem1, stroke: st(FR)) })
  group({ translate((xs.at(5), 0)); scale(0.9)
    catmull(..sk-back, close: true, fill: BK.lighten(70%), stroke: st(BK))
    catmull(..sk-front, close: true, fill: hatch(BK.lighten(20%)), stroke: (paint: BK, thickness: 0.7pt, dash: "dashed")) })
  // 화살표 · 이름표
  for x in (-9.3, -5.1, 5.1, 9.3) { line((x - 0.35, 0), (x + 0.35, 0), mark: (end: ">", fill: luma(120)), stroke: luma(120) + 1.2pt) }
  let labs = (("한 층", black), ("앞 겹", FR.darken(20%)), ("뒤 겹", BK.darken(10%)))
  for (i, x) in xs.enumerate() {
    let (s, c) = labs.at(calc.rem(i, 3))
    content((x, -4.0), T(s, c: c, sz: 10pt))
  }
  content((xs.at(2), -4.9), T("빗금 = 새로 채운 곳", c: BK.darken(10%), sz: 7pt, w: "regular"))
  content((xs.at(5), -4.9), T("빗금 = 새로 채운 곳", c: BK.darken(10%), sz: 7pt, w: "regular"))
  content((-7.2, 4.6), T("머리카락", sz: 11pt)); content((7.2, 4.6), T("치마", sz: 11pt))
  line((0, 4.2), (0, -4.6), stroke: (paint: luma(200), thickness: 0.6pt, dash: "dashed"))
}))
