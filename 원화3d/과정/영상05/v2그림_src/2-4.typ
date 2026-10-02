// 2-4 같은 두 부품(상자 · 둥근 손잡이) — 붙이는 자리만 달라 a 서류 가방 · b 서랍 · c 컵 · d 양동이
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#set text(font: "Malgun Gothic", size: 15pt, fill: rgb(70, 70, 80))
#let J = json("_렌더/2-4.json")
#let k = 16cm / 1920
#place(top + left, image("_렌더/2-4.png", width: 16cm))
#for (n, (x, y)) in J { place(top + left, dx: x * k - 1cm, dy: y * k + 0.15cm, box(width: 2cm, align(center)[#n])) }
