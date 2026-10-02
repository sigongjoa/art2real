// 3-8 코사인 회전면 z = cos r: 동심 고리로 보이고, 고리 경계(점선)는 골(오목) 자리.
// b 는 a 를 180° 돌린 것 — 골과 마루가 바뀌어 경계가 r = 2π 로 옮겨 간다.
#import "@preview/cetz:0.4.2"
#set page(width: 33.867cm, height: 19.05cm, margin: 0cm, fill: white)
#set text(font: ("Malgun Gothic",), size: 22pt)
#align(center + horizon, cetz.canvas(length: 1cm, {
  import cetz.draw: *
  let e = 32deg; let k = 0.62; let amp = 1.1; let R = 3 * calc.pi
  let pr(r, t) = (k * r * calc.cos(t), k * r * calc.sin(t) * calc.sin(e) + amp * calc.cos(r * 1rad) * calc.cos(e))
  let panel(ox, flip, dashes) = {
    let tf(p) = if flip { (ox - p.at(0), -p.at(1)) } else { (ox + p.at(0), p.at(1)) }
    for j in range(44) {
      let t = j * 360deg / 44
      line(..range(0, 121).map(i => tf(pr(R * i / 120, t))), stroke: 1.5pt)
    }
    for rr in dashes {
      line(..range(0, 121).map(i => tf(pr(rr, i * 360deg / 120))), stroke: (paint: rgb("#d03030"), thickness: 3.2pt, dash: "dashed"))
    }
  }
  panel(-8.0, false, (calc.pi, 3 * calc.pi))
  panel(8.0, true, (2 * calc.pi,))
  content((-8.0, -5.6), [a]); content((8.0, -5.6), [b 뒤집으면])
}))
