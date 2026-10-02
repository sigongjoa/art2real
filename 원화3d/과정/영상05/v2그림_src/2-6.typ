// 2-6 부품을 덜 그린 판과 다 그린 판(펭귄 9 부품 · 와인잔 3 · 손전등 3) — 부품 몇 개면 무엇인지 읽힌다
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#set text(font: "Malgun Gothic", size: 12pt, fill: rgb(70, 70, 80))
#let k = 16cm / 1920
#place(top + left, image("_렌더/2-6.png", width: 16cm))
#for (n, (x, y)) in json("_렌더/2-6.json") {
  place(top + left, dx: x * k - 1.5cm, dy: y * k + 0.05cm, box(width: 3cm, align(center)[부품 #n.trim()]))
}
