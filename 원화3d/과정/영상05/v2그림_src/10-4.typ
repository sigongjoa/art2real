// 10-4 브리지먼 손가락: 마디 사이 세 곳을 잘라 본 단면 1 · 2 · 3 (모서리 있는 납작한 모양 · 끝으로 갈수록 작아짐)
#import "단면공통.typ": *
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#let T(s, c: black, sz: 11pt) = text(font: "Malgun Gothic", size: sz, fill: c, weight: "bold", s)
#align(center + horizon, cetz.canvas(length: 1.25cm, {
  import cetz.draw: *
  let g = luma(70); let cs = (rgb("#c0392b"), rgb("#2e86c1"), rgb("#16a085"))
  let top = ((-5.6, 0.7), (-4.6, 0.82), (-4.0, 0.62), (-2.7, 0.55), (-2.3, 0.62), (-1.9, 0.5), (-0.9, 0.42), (-0.35, 0.28), (-0.15, 0.0))
  let bot = ((-5.6, -0.72), (-4.0, -0.6), (-2.3, -0.52), (-0.9, -0.42), (-0.35, -0.3), (-0.15, 0.0))
  catmull(..top, stroke: g + 1.6pt); catmull(..bot, stroke: g + 1.6pt)
  // 손톱 · 마디 주름
  catmull((-1.25, 0.47), (-0.85, 0.55), (-0.4, 0.42), (-0.28, 0.3), stroke: g + 1.0pt)
  line((-1.25, 0.47), (-1.18, 0.3), stroke: g + 0.8pt)
  for x in (-1.25, -2.35, -4.1) { line((x - 0.1, -0.52), (x + 0.1, -0.35), stroke: g + 0.8pt) }
  content((-5.9, 0), text(font: "Malgun Gothic", size: 8pt, fill: luma(120), "손등 마디"), anchor: "east")
  // 자르는 자리
  for (i, x) in ((-3.3, -1.55, -0.6)).enumerate() {
    line((x, 1.15), (x, -1.15), stroke: (paint: cs.at(i), thickness: 1.2pt, dash: "dashed"))
    content((x, 1.45), T(str(i + 1), c: cs.at(i)))
  }
  // 단면 (위 = 손등 · 손톱 쪽)
  let hex = ((-0.42, 0.5), (0.42, 0.5), (0.68, 0.12), (0.58, -0.42), (-0.58, -0.42), (-0.68, 0.12))
  let S = (
    (hex, (2.5, 1.6)),
    (pts(0.58, 0.42, 4.5, 0, 0, ((90, 0.04, 30),)), (2.0, -0.4)),
    (pts(0.46, 0.3, 5, 0, 0, ((35, 0.1, 8), (145, 0.1, 8), (270, -0.04, 25))), (2.9, -2.2)),
  )
  for (i, (p, c)) in S.enumerate() {
    group({
      translate(c)
      line(..p, close: true, stroke: (paint: cs.at(i), thickness: 1.8pt, join: "round"), fill: cs.at(i).lighten(88%))
      content((-1.1, 0), T(str(i + 1), c: cs.at(i)))
    })
  }
  content((4.6, 2.3), text(font: "Malgun Gothic", size: 8pt, fill: luma(120), "↑ 손등"))
}))
