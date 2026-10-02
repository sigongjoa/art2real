// 10-3 반더폴 여백 스케치: 어깨 높이 단면(불규칙한 타원 + 가운데 목) · 가슴 높이 단면(거의 네모)
#import "단면공통.typ": *
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#let T(s, c: black, sz: 9pt, w: "bold") = text(font: "Malgun Gothic", size: sz, fill: c, weight: w, s)
#align(center + horizon, cetz.canvas(length: 1cm, {
  import cetz.draw: *
  let blue = rgb("#2e86c1"); let green = rgb("#16a085"); let g = luma(90)
  // 왼쪽: 앞에서 본 몸통 + 자르는 높이 두 줄
  group({
    translate((-4.6, 0))
    circle((0, 2.95), radius: (0.42, 0.52), stroke: g + 1.2pt)
    for sx in (-1, 1) {
      catmull((sx*0.3, 2.45), (sx*0.38, 2.1), (sx*1.2, 1.85), (sx*1.62, 1.55), (sx*1.45, 0.9), (sx*1.3, 0.2), (sx*1.05, -0.7), (sx*1.2, -1.4), (sx*1.15, -2.0), stroke: g + 1.2pt)
      catmull((sx*1.62, 1.55), (sx*1.85, 0.6), (sx*1.95, -0.6), stroke: g + 1.2pt)
    }
    line((-2.3, 1.85), (2.3, 1.85), stroke: (paint: blue, thickness: 1.2pt, dash: "dashed"))
    line((-2.3, 0.75), (2.3, 0.75), stroke: (paint: green, thickness: 1.2pt, dash: "dashed"))
    content((2.4, 1.85), T("어깨 높이", c: blue), anchor: "west")
    content((2.4, 0.75), T("가슴 높이", c: green), anchor: "west")
  })
  // 오른쪽: 위에서 내려다본 단면 둘 (위 = 등)
  group({
    translate((3.0, 1.5))
    let p = pts(2.7, 1.0, 2.2, 0, 0, ((90, -0.04, 25), (20, 0.08, 18), (160, 0.06, 22), (200, 0.1, 15), (330, -0.05, 20), (270, 0.05, 30)))
    line(..p, close: true, stroke: blue + 1.8pt, fill: blue.lighten(88%))
    line((-1.9, 0.75), (-1.75, -0.75), stroke: (paint: blue, thickness: 0.8pt, dash: "dashed"))
    line((1.9, 0.75), (1.75, -0.75), stroke: (paint: blue, thickness: 0.8pt, dash: "dashed"))
    circle((0, 0.05), radius: 0.5, stroke: black + 1.6pt, fill: white)
    content((0, 0.05), T("목", sz: 8pt))
    content((0, -1.35), T("어깨 높이 · 불규칙한 타원", c: blue, sz: 8pt))
  })
  group({
    translate((3.0, -1.95))
    let o = pts(1.85, 1.15, 4.2, 0, 0, ((90, -0.07, 8),))
    line(..o, close: true, stroke: green + 1.8pt, fill: green.lighten(88%))
    let r = pts(1.45, 0.85, 2.6, 0, 0.0, ((90, -0.12, 8),))
    line(..r, close: true, stroke: (paint: green.darken(30%), thickness: 0.9pt, dash: "dashed"))
    circle((0, 0.82), radius: 0.16, stroke: green.darken(30%) + 0.9pt, fill: white)
    content((2.0, 0.5), T("갈비뼈", c: green.darken(30%), sz: 7pt, w: "regular"), anchor: "west")
    line((1.45, 0.3), (1.98, 0.5), stroke: (paint: green.darken(30%), thickness: 0.4pt))
    content((0, -1.5), T("가슴 높이 · 거의 네모", c: green, sz: 8pt))
  })
  content((6.6, 2.6), T("↑ 등", c: g, sz: 7pt, w: "regular"))
  content((6.6, -2.8), T("↓ 배", c: g, sz: 7pt, w: "regular"))
}))
