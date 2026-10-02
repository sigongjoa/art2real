// 2-5 번호 붙인 지온 다섯과, 그 번호들로만 지은 물건들 — 몇 개의 덩어리를 다르게 붙여 여러 물건
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#set text(font: "Malgun Gothic", size: 11pt, fill: rgb(50, 50, 60))
#let k = 16cm / 1920
#place(top + left, image("_렌더/2-5.png", width: 16cm))
#for (n, x, y) in json("_렌더/2-5.json") {
  place(top + left, dx: x * k - 0.22cm, dy: y * k - 0.22cm,
    circle(radius: 0.22cm, fill: rgb(200, 70, 50), stroke: none, align(center + horizon, text(fill: white, weight: "bold", size: 10.5pt)[#n])))
}
#place(top + left, dx: 640 * k, dy: 230 * k, line(length: 600 * k, angle: 90deg, stroke: (thickness: 1pt, paint: rgb(190, 190, 198), dash: "dashed")))
#place(top + left, dx: 330 * k - 2cm, dy: 170 * k, box(width: 4cm, align(center, text(size: 14pt, weight: "bold")[지온])))
#place(top + left, dx: 1290 * k - 2cm, dy: 170 * k, box(width: 4cm, align(center, text(size: 14pt, weight: "bold")[물건])))
