// 3-13 슈뢰더 계단: 계단 한 칸(디딤판 + 챌판, 볼록 모서리로 이어짐)이 부품. 두 점은 같은 칸 위.
// 뒤집혀 보이면 볼록↔오목이 바뀌어 두 점 사이 모서리가 경계가 된다.
#import "@preview/cetz:0.4.2"
#set page(width: 33.867cm, height: 19.05cm, margin: 0cm, fill: white)
#align(center + horizon, cetz.canvas(length: 2.3cm, {
  import cetz.draw: *
  let st = 3pt
  let D = (-1.7, 1.15)
  let ad(p, s) = (p.at(0) + s * D.at(0), p.at(1) + s * D.at(1))
  let Z = ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (3, 3), (3, 4), (4, 4))
  // 앞면(계단 아래 덩어리)
  line(..Z, (4, 0), close: true, fill: white, stroke: st)
  // 뒤쪽 계단선 · 모서리를 잇는 깊이선
  line(..Z.map(p => ad(p, 1)), stroke: st)
  for p in Z { line(p, ad(p, 1), stroke: st) }
  // 두 점: 챌판(x=1) 과 그 위 디딤판(y=2) — 볼록 모서리 (1,2) 를 사이에 둠
  circle(ad((1, 1.72), 0.5), radius: 0.09, fill: black)
  circle(ad((1.28, 2), 0.5), radius: 0.09, fill: black)
}))
