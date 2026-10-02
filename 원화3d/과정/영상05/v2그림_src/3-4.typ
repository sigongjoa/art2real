// 3-4 데이터 만들 때의 규칙: (a) 앞뒤 순서 — 빨강은 거꾸로 · 초록이 맞음
// (b) 맞닿은 두 영역 — 빨강은 경계를 어느 한쪽 다각형으로 그려 겹치고 빔 · 초록은 공유 경계 하나
#import "얼굴선.typ": *
#show: page-setup
#let RED = rgb("#e03030")
#let GRN = rgb("#20c040")
#cetz.canvas(length: 1cm, {
  import cetz.draw: *
  let s = 0.75; let pw = 2 * W * s; let ph = 10 * s; let gap = 0.4
  let frame(cx, c) = rect((cx - pw / 2, -ph / 2), (cx + pw / 2, ph / 2), stroke: (paint: c, thickness: 5pt))
  // (a) 두 덩어리: 뒤(파랑) 일부가 앞(주황)에 가림
  let pairA(cx, wrong) = {
    rect((cx - pw / 2, -ph / 2), (cx + pw / 2, ph / 2), fill: rgb("#d9c7b0"), stroke: none)
    let back = (cx - 0.9, -1.1); let front = (cx + 0.8, -0.6)
    circle(back, radius: (1.7, 2.1), fill: rgb("#7f9fd6"), stroke: (paint: rgb("#3050a0"), thickness: 1.5pt))
    circle((back.at(0), back.at(1) + 2.6), radius: 0.7, fill: rgb("#7f9fd6"), stroke: (paint: rgb("#3050a0"), thickness: 1.5pt))
    circle(front, radius: (1.5, 2.2), fill: rgb("#f2c48a"), stroke: (paint: rgb("#3050a0"), thickness: 1.5pt))
    circle((front.at(0), front.at(1) + 2.75), radius: 0.65, fill: rgb("#f2c48a"), stroke: (paint: rgb("#3050a0"), thickness: 1.5pt))
    let n1 = if wrong { "2" } else { "1" }; let n2 = if wrong { "1" } else { "2" }
    content(front, text(size: 30pt, weight: "bold", n1)); content((back.at(0) - 0.8, back.at(1) - 0.4), text(size: 30pt, weight: "bold", n2))
    frame(cx, if wrong { RED } else { GRN })
  }
  // (b) 얼굴 둘 + 가운데 회색
  let oy = -ph / 2
  let pairB(cx, wrong) = {
    rect((cx - pw / 2, -ph / 2), (cx + pw / 2, ph / 2), fill: rgb("#8a8580"), stroke: none)
    if wrong {
      // 경계를 성글게 따서 각자 다각형으로: 회색 쪽으로 삐져나오고 틈이 남
      let coarse(sx, d) = D.pts.enumerate().filter(((i, p)) => calc.rem(i, 32) == 0 or i == 800).map(((i, p)) => (cx + s * sx * (p.at(0) + d * calc.sin(i * 0.37)), oy + s * p.at(1))) + ((cx + s * sx * W, oy + s * 10), (cx + s * sx * W, oy))
      line(..coarse(-1, 0.16), close: true, fill: rgb("#a39a3a"), stroke: (paint: black, thickness: 0.8pt))
      line(..coarse(1, -0.16), close: true, fill: rgb("#6e5a30"), stroke: (paint: black, thickness: 0.8pt))
    } else {
      line(..face(s: s, sx: -1, ox: cx, oy: oy), close: true, fill: rgb("#a39a3a"), stroke: none)
      line(..face(s: s, sx: 1, ox: cx, oy: oy), close: true, fill: rgb("#6e5a30"), stroke: none)
      line(..prof(s: s, sx: -1, ox: cx, oy: oy), stroke: (paint: white, thickness: 2pt))
      line(..prof(s: s, sx: 1, ox: cx, oy: oy), stroke: (paint: white, thickness: 2pt))
    }
    frame(cx, if wrong { RED } else { GRN })
  }
  let x0 = -11.0
  pairA(x0, true); pairA(x0 + pw + gap, false)
  pairB(x0 + 2 * pw + 3 * gap + 1.0, true); pairB(x0 + 3 * pw + 4 * gap + 1.0, false)
  content((x0 + (pw + gap) / 2, -ph / 2 - 0.9), [a 앞뒤 순서])
  content((x0 + 2.5 * pw + 3.5 * gap + 1.0, -ph / 2 - 0.9), [b 공유 경계])
})
