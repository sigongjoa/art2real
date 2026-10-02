// 1-3 같이 움직이는 두 토막: 검은 판 위 · 아래 막대 토막이 함께 좌우로 → 판 뒤 막대 하나
#import "@preview/cetz:0.4.2"
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#set text(font: "Malgun Gothic", size: 13pt)
#align(center + horizon, cetz.canvas(length: 1cm, {
  import cetz.draw: *
  let rod(dx, col) = {
    // 기울어진 막대 하나(판 뒤를 지나간다)
    line((-0.85 + dx, 2.9), (0.85 + dx, -2.9), stroke: (thickness: 0.42cm, paint: col, cap: "butt"))
  }
  // 움직임 잔상(옅게 좌우)
  rod(-0.9, rgb(225, 225, 230)); rod(0.9, rgb(225, 225, 230))
  rod(0, rgb(110, 110, 120))
  // 판(가림)
  rect((-4.2, -1.2), (4.2, 1.2), fill: rgb(30, 30, 34), stroke: none)
  // 공통 좌우 이동 화살표(위 · 아래)
  let ar = (thickness: 1.6pt, paint: rgb(200, 70, 50))
  for y in (2.2, -2.2) {
    line((-2.6, y), (-1.6, y), stroke: ar, mark: (start: ">", fill: rgb(200, 70, 50), scale: 1.4))
    line((1.6, y), (2.6, y), stroke: ar, mark: (end: ">", fill: rgb(200, 70, 50), scale: 1.4))
  }
  content((0, 3.4), text(fill: rgb(200, 70, 50))[위 · 아래 토막이 같이 움직인다])
}))
