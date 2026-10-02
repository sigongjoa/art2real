// 7-4 검은 원판처럼 보여도 공의 가장자리일 수 있다: 윤곽 = 시선이 표면을 스치는 자리 · 눈은 앞뒤를 매끈하게 닫는다 (Tse 1999 Fig.9 의 생각)
#import "@preview/cetz:0.4.2"
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#set text(font: "Noto Sans KR", size: 11pt)
#let eye(p) = {
  import cetz.draw: *
  let (x, y) = p
  line((x + 0.45, y + 0.4), (x, y), (x + 0.45, y - 0.4), stroke: 1.6pt)
  circle((x + 0.2, y), radius: (0.09, 0.17), fill: black, stroke: none)
}
// 옆에서 본 납작한 렌즈 + 스치는 자리 막대
#let lens(c) = {
  import cetz.draw: *
  let (x, y) = c
  circle(c, radius: (0.32, 1.25), fill: black, stroke: none)
  circle((x + 0.08, y + 0.45), radius: 0.07, fill: white, stroke: none)
  line((x - 0.65, y + 1.38), (x + 0.65, y + 1.18), stroke: 3.5pt)
  line((x - 0.65, y - 1.38), (x + 0.65, y - 1.18), stroke: 3.5pt)
}
#align(center + horizon, cetz.canvas(length: 0.9cm, {
  import cetz.draw: *
  // a 정면: 검은 원판(공?)
  group({
    translate((-6.2, 0))
    circle((0, 0), radius: 1.3, fill: black, stroke: none)
    circle((0.5, 0.55), radius: 0.12, fill: white, stroke: none)
    content((0, -2.3), [a 앞에서 본 모습])
  })
  // b 옆에서: 시선이 스치는 곳만 정해진다
  group({
    translate((-1.4, 0))
    lens((0, 0))
    eye((4.0, 0))
    line((-1.0, 1.42), (4.0, 0.02), stroke: (thickness: 1pt, dash: "dashed"))
    line((-1.0, -1.42), (4.0, -0.02), stroke: (thickness: 1pt, dash: "dashed"))
    content((1.5, -2.3), [b 옆: 스치는 자리 = 윤곽])
  })
  // c 앞뒤를 매끈하게 닫은 덩어리
  group({
    translate((5.6, 0))
    circle((0, 0), radius: 1.33, fill: rgb("#d9d9d9"), stroke: 1pt + rgb("#777777"))
    lens((0, 0))
    eye((3.0, 0))
    content((1.0, -2.3), [c 눈이 채운 공])
  })
}))
