// 2-3 벽돌과 원기둥을 가르는 비우연 단서: 벽돌 = 평행 모서리 셋 · 화살 꼭짓점 · 안쪽 Y 꼭짓점 / 원기둥 = 굽은 모서리 · 평행 모서리 둘
#import "@preview/cetz:0.4.2"
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#set text(font: "Malgun Gothic", size: 12pt, fill: rgb(50, 50, 60))
#align(center + horizon, cetz.canvas(length: 1cm, {
  import cetz.draw: *
  let k = (thickness: 1.8pt, paint: black, cap: "round")
  let blue = rgb(40, 110, 210); let red = rgb(215, 60, 45); let green = rgb(30, 150, 80); let orange = rgb(230, 140, 20)
  let hb = (thickness: 3.4pt, paint: blue, cap: "round")
  let add(p, q) = (p.at(0) + q.at(0), p.at(1) + q.at(1))
  // ---- 벽돌 ----
  group({
    translate((-4.2, -0.6))
    let d = (1.1, 0.8)
    let A = (-1.9, -0.9); let B = (1.3, -0.9); let C = (1.3, 0.8); let D = (-1.9, 0.8)
    let D2 = add(D, d); let C2 = add(C, d); let B2 = add(B, d)
    for (p, q) in ((A, B), (B, C), (C, D), (D, A), (D, D2), (D2, C2), (C2, B2)) { line(p, q, stroke: k) }
    for (p, q) in ((D, D2), (C, C2), (B, B2)) { line(p, q, stroke: hb) }   // 평행한 모서리 셋
    for p in (D, C2, B) { circle(p, radius: 0.13, fill: red, stroke: none) } // 바깥 화살 꼭짓점
    circle(C, radius: 0.13, fill: green, stroke: none)                      // 안쪽 Y 꼭짓점
    content((0, 2.45), text(size: 15pt, weight: "bold")[벽돌])
    let lg(y, mark, lab) = { mark(y); content((-1.1, y), anchor: "west", lab) }
    lg(-1.75, y => line((-1.75, y), (-1.35, y), stroke: hb), [평행한 모서리 셋])
    lg(-2.35, y => circle((-1.55, y), radius: 0.13, fill: red, stroke: none), [바깥 화살 꼭짓점 셋])
    lg(-2.95, y => circle((-1.55, y), radius: 0.13, fill: green, stroke: none), [안쪽 Y 꼭짓점])
  })
  // ---- 원기둥 ----
  group({
    translate((3.9, -0.6))
    let rx = 1.3; let ry = 0.42; let top = 1.4; let bot = -0.9
    let ho = (thickness: 3.4pt, paint: orange)
    circle((0, top), radius: (rx, ry), stroke: ho)                              // 굽은 모서리(윗면 테두리)
    arc((rx, bot), start: 0deg, stop: -180deg, radius: (rx, ry), stroke: ho)  // 굽은 모서리(아랫면 보이는 쪽)
    line((-rx, top), (-rx, bot), stroke: hb); line((rx, top), (rx, bot), stroke: hb)  // 평행한 모서리 둘
    for x in (-rx, rx) { circle((x, top), radius: 0.13, fill: green, stroke: none) }  // 접하는 Y 꼭짓점
    content((0, 2.45), text(size: 15pt, weight: "bold")[원기둥])
    let lg(y, mark, lab) = { mark(y); content((-1.1, y), anchor: "west", lab) }
    lg(-1.75, y => line((-1.75, y), (-1.35, y), stroke: ho), [굽은 모서리])
    lg(-2.35, y => line((-1.75, y), (-1.35, y), stroke: hb), [평행한 모서리 둘])
    lg(-2.95, y => circle((-1.55, y), radius: 0.13, fill: green, stroke: none), [접하는 Y 꼭짓점 둘])
  })
}))
