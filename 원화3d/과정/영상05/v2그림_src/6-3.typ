// 6-3 네모 뒤의 원 · 혹 달린 원: 채우기 후보 넷 (Thielen 외 2019 Fig.2 / Sekuler 1994 의 생각)
// 외곽선만 남기는 요령: 모든 조각을 굵은 선으로 먼저 긋고, 같은 조각을 흰색으로 다시 채운다(합집합 외곽선).
#import "@preview/cetz:0.4.2"
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#set text(font: "Noto Sans KR", size: 10pt)
#let W = 1.4pt + black
// kind: "circle" 온전 · "spike" 뾰족 · "chord" 깎임 · "notch" 모자이크 / bumps: 혹 각도들
#let shape(c, kind, bumps) = {
  import cetz.draw: *
  let (x, y) = c
  let R = 1.0
  let pieces(st, fl) = {
    for a in bumps { circle((x + R * calc.cos(a), y + R * calc.sin(a)), radius: 0.3, stroke: st, fill: fl) }
    if kind == "circle" { circle(c, radius: R, stroke: st, fill: fl) }
    if kind == "spike" {
      circle(c, radius: R, stroke: st, fill: fl)
      line((x - 0.55, y - 0.35), (x - 1.25, y - 1.25), (x - 0.35, y - 0.6), close: true, stroke: st, fill: fl)
    }
    if kind == "chord" { arc(c, start: -95deg, stop: 185deg, radius: R, mode: "CLOSE", anchor: "origin", stroke: st, fill: fl) }
    if kind == "notch" { arc(c, start: -90deg, stop: 180deg, radius: R, mode: "PIE", anchor: "origin", stroke: st, fill: fl) }
  }
  pieces(W, none)
  pieces(none, white)
}
#let occluded(c, bumps) = {
  import cetz.draw: *
  shape(c, "circle", bumps)
  let (x, y) = c
  rect((x - 2.0, y - 2.0), (x, y), fill: black, stroke: none)
}
#let B3 = (45deg, 135deg, -45deg)
#let B4 = (45deg, 135deg, -45deg, -135deg)
#align(center + horizon, cetz.canvas(length: 0.42cm, {
  import cetz.draw: *
  let d = (stroke: (paint: gray, dash: "dashed", thickness: 0.8pt))
  // a
  rect((-15.4, -8.2), (-0.6, 8.2), ..d)
  content((-14.6, 7.5), [a])
  occluded((-10.6, 0.4), ())
  content((-10.6, 1.9), [A0])
  let ys = (5.8, 2.0, -1.8, -5.6)
  for (i, k) in ("circle", "spike", "chord", "notch").enumerate() {
    shape((-3.6, ys.at(i)), k, ())
    content((-3.6, ys.at(i) + 1.6), [A#(i + 1)])
  }
  // b
  rect((0.6, -8.2), (15.4, 8.2), ..d)
  content((1.4, 7.5), [b])
  occluded((5.4, 0.4), B3)
  content((5.4, 2.1), [B0])
  let bs = (B3, B4, B3, B3)
  for (i, k) in ("circle", "circle", "chord", "notch").enumerate() {
    shape((12.4, ys.at(i)), k, bs.at(i))
    content((12.4, ys.at(i) + 1.75), [B#(i + 1)])
  }
}))
