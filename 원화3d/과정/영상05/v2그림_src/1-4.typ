// 1-4 홈 파인 판이 가만히 있는 삼각형 앞을 지나간다: 순간마다 조각만, 시간이 지나면 삼각형 하나
#import "@preview/cetz:0.4.2"
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#set text(font: "Malgun Gothic", size: 13pt)
#align(center + horizon, cetz.canvas(length: 1cm, {
  import cetz.draw: *
  let tri = ((-1.0, -0.5), (1.0, -0.5), (0, 0.8))   // 가만히 있는 삼각형(칸마다 같은 자리)
  let gray = rgb(150, 152, 165)
  // 판: 윗변에 홈(폭 0.9) 하나 · 칸마다 x 로 밀린다
  let cl(x) = calc.max(-1.6, calc.min(1.6, x))   // 판은 칸(±1.6) 안에서만
  let plate(dx) = line(
    (-1.6, -1.3), (1.6, -1.3), (1.6, 1.1), (cl(0.45 + dx), 1.1), (cl(0.45 + dx), -0.75),
    (cl(-0.45 + dx), -0.75), (cl(-0.45 + dx), 1.1), (-1.6, 1.1), close: true, fill: gray, stroke: none)
  let cx = (-5.4, -1.8, 1.8)
  let shift = (-0.9, 0.0, 0.9)
  for i in range(3) {
    group({
      translate((cx.at(i), 0))
      // 칸 틀
      rect((-1.6, -1.6), (1.6, 1.6), stroke: (thickness: 0.8pt, paint: rgb(200, 200, 205)))
      line(..tri, close: true, fill: black, stroke: none)
            plate(shift.at(i))
      rect((-1.6, -1.6), (1.6, 1.6), stroke: (thickness: 0.8pt, paint: rgb(170, 170, 178)))
      content((0, -2.05), text(fill: rgb(90, 90, 100))[#("순간 1", "순간 2", "순간 3").at(i)])
    })
  }
  // 판이 지나가는 방향
  line((-6.6, 2.1), (2.8, 2.1), stroke: (thickness: 1.4pt, paint: rgb(90, 90, 100)), mark: (end: ">", fill: rgb(90, 90, 100), scale: 1.3))
  content((-1.9, 2.5), text(fill: rgb(90, 90, 100))[판이 지나간다 · 삼각형은 그대로])
  // 시간이 지나면 보이는 것
  line((3.75, 0), (4.45, 0), stroke: (thickness: 1.6pt, paint: rgb(200, 70, 50)), mark: (end: ">", fill: rgb(200, 70, 50), scale: 1.3))
  group({
    translate((5.6, 0))
    line(..tri, close: true, fill: none, stroke: (thickness: 2.4pt, paint: black, join: "miter"))
    content((0, -2.05), text(fill: rgb(200, 70, 50))[보이는 것])
  })
}))
