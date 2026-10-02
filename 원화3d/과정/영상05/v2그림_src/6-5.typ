// 6-5 띠 넷이 꼬리를 물듯 서로 가림 → 가림 순서 고리 → 가려진 곳 채움 → 따로 떼어 냄 (Zhan 외 2020 Fig.7 의 생각)
#import "@preview/cetz:0.4.2"
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#set text(font: "Noto Sans KR", size: 10pt)
// 띠: 1 왼쪽 세로 · 2 위 가로 · 3 오른쪽 세로 · 4 아래 가로
#let C = (rgb("#3b3f8f"), rgb("#d6336c"), rgb("#7d8a80"), rgb("#f2c230"))
#let S = (((-1.5, -1.7), (-0.8, 1.2)), ((-1.9, 0.4), (1.7, 1.1)), ((0.8, -1.2), (1.5, 1.7)), ((-1.7, -1.1), (1.9, -0.4)))
#let strip(i, f, ..st) = {
  import cetz.draw: *
  rect(S.at(i).at(0), S.at(i).at(1), fill: f, ..st)
}
// 고리: 2 가 1 을, 1 이 4 를, 4 가 3 을, 3 이 2 를 가린다 → 한 번의 그리기 순서로는 안 되니, 다 그린 뒤 겹친 네 칸을 이긴 쪽 색으로 다시 칠한다
#let scene() = {
  import cetz.draw: *
  for i in range(4) { strip(i, C.at(i), stroke: none) }
  for (a, b, w) in (((-1.5, 0.4), (-0.8, 1.1), 1), ((-1.5, -1.1), (-0.8, -0.4), 0), ((0.8, -1.1), (1.5, -0.4), 3), ((0.8, 0.4), (1.5, 1.1), 2)) {
    rect(a, b, fill: C.at(w), stroke: none)
  }
}
#align(center + horizon, cetz.canvas(length: 0.5cm, {
  import cetz.draw: *
  let lab(x, t) = content((x, -3.2), t)
  // 1 장면 + 번호
  group({
    translate((-11.4, 0))
    scene()
    for (i, p) in ((-1.15, -1.45), (-0.1, 0.75), (1.15, 1.45), (0.1, -0.75)).enumerate() {
      circle(p, radius: 0.32, fill: rgb("#7ee08a"), stroke: 0.8pt + rgb("#1e7a2c"))
      content(p, text(size: 8pt)[#(i + 1)])
    }
    lab(0, [고리처럼 가림])
  })
  // 2 가림 순서 (화살 = 가린다)
  group({
    translate((-3.8, 0))
    let P = ((-1.6, 0), (0, 1.6), (1.6, 0), (0, -1.6))
    let g = rgb("#1e7a2c")
    for (a, b) in ((1, 0), (0, 3), (3, 2), (2, 1)) {
      let (pa, pb) = (P.at(a), P.at(b))
      let (dx, dy) = (pb.at(0) - pa.at(0), pb.at(1) - pa.at(1))
      let n = calc.sqrt(dx * dx + dy * dy)
      let k = 0.55 / n
      line((pa.at(0) + dx * k, pa.at(1) + dy * k), (pb.at(0) - dx * k, pb.at(1) - dy * k), mark: (end: ">", fill: g, scale: 1.4), stroke: 1.2pt + g)
    }
    for (i, p) in P.enumerate() {
      circle(p, radius: 0.45, fill: rgb("#7ee08a"), stroke: 0.8pt + g)
      content(p, [#(i + 1)])
    }
    lab(0, [누가 누구를 가리나])
  })
  // 3 채우기: 가려진 부분까지 윤곽
  group({
    translate((3.8, 0))
    scene()
    for i in range(4) { strip(i, none, stroke: (paint: C.at(i).darken(30%), thickness: 1.3pt, dash: "dashed")) }
    lab(0, [가려진 곳 채우기])
  })
  // 4 떼어 내기
  group({
    translate((11.4, 0))
    let off = ((-0.9, 0), (0, 0.9), (0.9, 0), (0, -0.9))
    for i in range(4) {
      group({ translate(off.at(i)); strip(i, C.at(i), stroke: none) })
    }
    lab(0, [따로 떼어 내기])
  })
}))
