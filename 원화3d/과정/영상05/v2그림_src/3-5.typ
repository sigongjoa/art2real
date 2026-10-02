// 3-5 횡단성: 따로 있던 두 덩어리를 파고들게 합치면 만나는 자리는 오목한 이음매(점선)
#import "@preview/cetz:0.4.2"
#set page(width: 33.867cm, height: 19.05cm, margin: 0cm, fill: white)
#align(center + horizon, cetz.canvas(length: 1.1cm, {
  import cetz.draw: *
  let st = 3.2pt
  let sh(p, d) = p.map(q => (q.at(0) + d.at(0), q.at(1) + d.at(1)))
  // 가로 덩어리(울퉁불퉁) — 오른쪽 끝을 뺀 위·아래 선
  let topA = ((4.4, 0.62), (3.4, 0.68), (2.2, 0.95), (1.3, 0.6), (0.6, 1.0), (-0.1, 0.3))
  let botA = ((-0.1, 0.3), (0.3, -0.55), (1.1, -0.45), (1.9, -0.9), (3.1, -0.62), (4.4, -0.62))
  let endA = ((4.4, -0.62), (5.3, -0.4), (5.5, 0), (5.3, 0.4), (4.4, 0.62))
  // 세로 덩어리
  let B = ((6.3, 3.5), (7.4, 3.3), (7.7, 1.0), (7.3, -2.0), (6.5, -3.7), (5.7, -2.6), (5.2, -0.6), (5.7, 1.4))
  // 왼쪽: 따로
  let o1 = (-15.0, 0); let o2 = (-12.5, 0)
  hobby(..sh(topA + botA.slice(1) + endA.slice(1, 4), o1), close: true, stroke: st, fill: white)
  hobby(..sh(B, o2), close: true, stroke: st, fill: white)
  // 화살표
  line((-2.6, 0), (-0.8, 0), stroke: 8pt, mark: (end: "stealth", fill: black, scale: 0.8))
  // 오른쪽: 파고듦
  let o3 = (3.0, 0); let o4 = (2.0, 0)
  hobby(..sh(B, o4), close: true, stroke: st, fill: white)
  hobby(..sh(topA + botA.slice(1), o3), close: true, stroke: none, fill: white)
  hobby(..sh(topA + botA.slice(1), o3), stroke: st)
  // 만나는 자리: 오목한 이음매
  let c = (4.4 + o3.at(0) + 0.05, 0)
  circle(c, radius: (0.42, 0.66), stroke: (thickness: 3.6pt, dash: (array: (7pt, 7pt))))
}))
