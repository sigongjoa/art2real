// 4-6: 가림 판이 곧은 모서리를 가리면 판 테두리에 「짝을 이룬 홀로 끝난 선」 두 개가 한 직선 위에서 마주 본다 · b) 각도 조건
#import "@preview/cetz:0.4.2"
#set page(width: 33.867cm, height: 19.05cm, margin: 0cm, fill: white)
#set text(font: "Malgun Gothic", size: 20pt, weight: "bold", fill: rgb("#282828"))
#align(center + horizon, cetz.canvas(length: 0.88cm, {
  import cetz.draw: *
  let thick = (paint: black, thickness: 4.5pt, join: "miter")
  // ----- a) 물체 윤곽(굵은 선) + 가림 판(가는 선) -----
  rect((-15, 0.2), (15, 9.6), stroke: 1.2pt + gray)
  content((-14.2, 0.9), [a)])
  // 물체: 아래 상자 + 기울어진 윗변(판 뒤로 지나감)
  let L0 = (-6.5, 4.4); let R0 = (5.5, 6.6)
  let y(x) = L0.at(1) + (R0.at(1) - L0.at(1)) * (x - L0.at(0)) / (R0.at(0) - L0.at(0))
  let bx0 = -4.0; let bx1 = 3.4   // 판 왼 · 오 테두리
  line((bx0, y(bx0)), L0, (-6.5, 1.4), (5.5, 1.4), R0, (bx1, y(bx1)), stroke: thick)
  rect((bx0, 2.6), (bx1, 8.4), stroke: 1.4pt + black, fill: white)
  content(((bx0 + bx1) / 2, 7.7), [가림 판])
  for p in ((bx0, y(bx0)), (bx1, y(bx1))) { circle(p, radius: 0.2, fill: rgb("#d03a2a"), stroke: none) }
  content((10.4, 8.3), [홀로 끝난 선])
  line((9.4, 7.8), (bx1 + 0.3, y(bx1) + 0.25), stroke: 1.6pt + rgb("#d03a2a"), mark: (end: ">", fill: rgb("#d03a2a")))
  content((-10.2, 8.3), [홀로 끝난 선])
  line((-9.4, 7.8), (bx0 - 0.25, y(bx0) + 0.25), stroke: 1.6pt + rgb("#d03a2a"), mark: (end: ">", fill: rgb("#d03a2a")))
  // ----- b) 각도 조건 -----
  rect((-15, -9.6), (15, -0.2), stroke: 1.2pt + gray)
  content((-14.2, -8.9), [b)])
  let ang = 22deg
  let T1 = (-7.5, -6.2); let d = (calc.cos(ang), calc.sin(ang))
  let T2 = (T1.at(0) + 5.2 * d.at(0), T1.at(1) + 5.2 * d.at(1))
  line(T1, (T1.at(0) - 4.5 * d.at(0), T1.at(1) - 4.5 * d.at(1)), stroke: thick, mark: (end: ">", fill: black, scale: 1.4))
  line(T2, (T2.at(0) + 4.5 * d.at(0), T2.at(1) + 4.5 * d.at(1)), stroke: thick, mark: (end: ">", fill: black, scale: 1.4))
  line(T1, T2, stroke: (paint: gray, thickness: 2pt, dash: "dotted"))
  circle(T1, radius: 0.2, fill: black); circle(T2, radius: 0.2, fill: black)
  content((T1.at(0) + 0.3, T1.at(1) - 0.7), [T1]); content((T2.at(0) + 0.2, T2.at(1) - 0.7), [T2])
  // 각 표시: 수평선 기준
  let hz(p) = line(p, (p.at(0) + 1.6, p.at(1)), stroke: 1pt + black)
  hz(T1); hz(T2)
  arc(T1, start: 0deg, stop: 180deg + ang, radius: 1.1, anchor: "origin", stroke: 1.2pt + black, mark: (end: ">", fill: black))
  content((T1.at(0) - 0.6, T1.at(1) + 1.6), [$alpha_1$])
  arc(T1, start: 0deg, stop: ang, radius: 1.6, anchor: "origin", stroke: 1.2pt + black)
  content((T1.at(0) + 2.4, T1.at(1) + 0.45), [$alpha_12$])
  arc(T2, start: 0deg, stop: ang, radius: 1.1, anchor: "origin", stroke: 1.2pt + black)
  content((T2.at(0) + 2.2, T2.at(1) + 0.3), [$alpha_2$])
  content((7.6, -3.6), [두 끝이 반대 방향 · 한 직선 위])
  content((7.6, -5.4), text(size: 24pt)[$|alpha_1 - alpha_2| approx 180 degree$])
  content((7.6, -7.0), text(size: 24pt)[$|alpha_1 - alpha_12| approx 180 degree$])
}))
