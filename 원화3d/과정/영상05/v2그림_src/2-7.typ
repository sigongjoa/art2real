// 2-7 비행기: 부품을 하나씩 더해 3 → 4 → 6 → 7 → 9
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#set text(font: "Malgun Gothic", size: 12pt, fill: rgb(70, 70, 80))
#let k = 16cm / 1920
#place(top + left, image("_렌더/2-7.png", width: 16cm))
#for (n, (x, y)) in json("_렌더/2-7.json") { place(top + left, dx: x * k - 1.5cm, dy: y * k - 0.2cm, box(width: 3cm, align(center)[#n])) }
