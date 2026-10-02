#import "@preview/cetz:0.4.2"
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#align(center + horizon, cetz.canvas(length: 1cm, {
  import cetz.draw: *
  let r = 1.4
  let pts = ((0, 2.6), (-2.25, -1.3), (2.25, -1.3))
  for (i, p) in pts.enumerate() {
    let c = pts.map(q => q).at(i)
    let d = calc.atan2(-c.at(0), -c.at(1))  // Typst atan2 는 (x, y) 순서 · 가운데를 향한 방향
    arc(c, start: d + 30deg, stop: d + 330deg, radius: r, mode: "PIE", anchor: "origin", fill: black, stroke: none)
  }
}))
