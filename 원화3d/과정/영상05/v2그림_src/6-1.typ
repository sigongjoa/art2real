// 6-1 가려진 몸통은 홀쭉할 수도 뚱뚱할 수도 (Tse 1999 Fig.10 의 생각)
#import "@preview/cetz:0.4.2"
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#set text(font: "Noto Sans KR", size: 13pt)
#let K = 1.3   // 가림 상자 반폭
// 바깥으로 보이는 네 덩어리 (가림 상자 가장자리에서 나와 다시 들어간다)
#let lobes(draw) = {
  import cetz.draw: *
  let s = (stroke: 1.6pt + black)
  bezier((-K, 0.45), (-K, -0.45), (-3.3, 1.5), (-3.4, -1.4), ..s)           // 왼쪽 머리
  bezier((-0.25, K), (0.65, K), (-1.2, 3.4), (1.9, 2.6), ..s)               // 위 지느러미
  bezier((K, 0.7), (K, -0.15), (3.4, 2.0), (3.0, -1.5), ..s)                // 오른쪽 꼬리
  bezier((0.25, -K), (-0.65, -K), (1.4, -3.3), (-0.9, -2.9), ..s)           // 아래 지느러미
}
// 가려진 이음: f = 0 홀쭉 (가운데로 오목) · 1 뚱뚱 (모서리로 볼록)
#let joins(f) = {
  import cetz.draw: *
  let s = (stroke: 1.6pt + black)
  let m(p, q) = (p.at(0) * (1 - f) + q.at(0) * f, p.at(1) * (1 - f) + q.at(1) * f)
  bezier((-K, 0.45), (-0.25, K), m((-0.5, 0.25), (-1.25, 1.0)), m((-0.25, 0.5), (-1.0, 1.25)), ..s)
  bezier((0.65, K), (K, 0.7), m((0.35, 0.45), (1.0, 1.25)), m((0.45, 0.35), (1.25, 1.0)), ..s)
  bezier((K, -0.15), (0.25, -K), m((0.45, -0.3), (1.25, -1.0)), m((0.3, -0.45), (1.0, -1.25)), ..s)
  bezier((-0.65, -K), (-K, -0.45), m((-0.3, -0.45), (-1.0, -1.25)), m((-0.45, -0.3), (-1.25, -1.0)), ..s)
}
#align(center + horizon, cetz.canvas(length: 0.62cm, {
  import cetz.draw: *
  // 가림
  group({
    translate((-7.6, 0))
    lobes(none)
    joins(0.5)
    rect((-K - 0.08, -K - 0.08), (K + 0.08, K + 0.08), fill: rgb("#9aa3ad"), stroke: none, radius: 0.15)
    content((0, -4.2), [가림])
  })
  group({
    lobes(none)
    joins(0)
    content((0, -4.2), [a 홀쭉])
  })
  group({
    translate((7.6, 0))
    lobes(none)
    joins(1)
    content((0, -4.2), [b 뚱뚱])
  })
}))
