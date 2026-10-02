// 11-7 블렌더 렌더(_r/11-7.png, 11-7.py) + 화살표 · 이름표
#import "@preview/cetz:0.4.2"
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#let T(s, c: luma(40), sz: 10pt) = text(font: "Malgun Gothic", size: sz, fill: c, weight: "bold", s)
#align(center + horizon, cetz.canvas(length: 1cm, {
  import cetz.draw: *
  content((0, 0), image("_r/11-7.png", width: 14.4cm))
  let labs = ("찰흙 개 스캔", "상자 틀 씌우기", "부위 찾기", "자세 바꾸기")
  for (i, s) in labs.enumerate() { content(((i - 1.5) * 3.72, -1.6), T(s)) }
  for i in range(3) { let x = (i - 1) * 3.72; line((x - 0.3, 0.0), (x + 0.3, 0.0), mark: (end: ">", fill: luma(120)), stroke: luma(120) + 1.5pt) }
}))
