// 11-6 블렌더 렌더 넷(_r/11-6_k.png, 11-6.py)을 시계 방향으로 · 위치 명령 없이 붙이기만
#import "@preview/cetz:0.4.2"
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#let T(s, c: luma(40), sz: 9pt) = text(font: "Malgun Gothic", size: sz, fill: c, weight: "bold", s)
#align(center + horizon, cetz.canvas(length: 1cm, {
  import cetz.draw: *
  let P = ((-2.6, 1.85), (2.6, 1.85), (2.6, -1.95), (-2.6, -1.95))
  let labs = ("재료 상자 · 처음엔 한가운데", "붙이기 ① ② ③", "붙이기 ④ ⑤", "거울 ⑥ (반대편에 하나 더)")
  for (k, p) in P.enumerate() {
    content(p, image("_r/11-6_" + str(k) + ".png", height: 3.3cm))
    content((p.at(0), p.at(1) - 1.75), T(labs.at(k)))
  }
  let a = (stroke: luma(30) + 2pt, mark: (end: ">", fill: luma(30)))
  line((-0.6, 1.9), (0.6, 1.9), ..a); line((4.2, 0.6), (4.2, -0.6), ..a); line((0.6, -1.9), (-0.6, -1.9), ..a)
}))
