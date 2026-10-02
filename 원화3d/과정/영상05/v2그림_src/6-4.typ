// 6-4 저절로 갈라지는 도형: 색이 고른 검은 덩어리 하나가 막대 둘로 보이고 앞뒤가 번갈아 바뀐다 (Kellman & Shipley 1991 Fig.12 의 생각)
#import "@preview/cetz:0.4.2"
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#align(center + horizon, cetz.canvas(length: 1.6cm, {
  import cetz.draw: *
  let s = (fill: black, stroke: none)
  // 가로 막대 (기울어진 사다리꼴)
  line((-2.35, 0.95), (1.05, 1.0), (1.5, 0.6), (-1.55, -0.2), close: true, ..s)
  // 세로 막대 (휜 칼날 모양)
  merge-path({
    bezier((-0.1, 2.35), (0.3, -1.75), (-0.32, 1.0), (-0.3, -0.6))
    line((0.3, -1.75), (1.32, -0.95))
    bezier((1.32, -0.95), (-0.1, 2.35), (0.9, 0.0), (0.5, 1.3))
  }, ..s)
}))
