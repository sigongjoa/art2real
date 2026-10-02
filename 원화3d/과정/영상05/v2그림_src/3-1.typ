// 3-1 꽃병/얼굴: (a) 판 안 검은 꽃병 = 흰 옆얼굴 둘 · (b) 두 해석을 떼어 놓음
#import "얼굴선.typ": *
#show: page-setup
#cetz.canvas(length: 1cm, {
  import cetz.draw: *
  let s = 1.25
  // (a)
  let ax = -9.0
  rect((ax - s * W, 0), (ax + s * W, s * 10), stroke: 1.6pt)
  line(..vase(s: s, ox: ax), close: true, fill: black, stroke: none)
  content((ax, -0.9), [a])
  // (b) 꽃병만 · 옆얼굴만 떼어 놓음
  let bx = 7.0; let g = 1.6
  line(..vase(s: s, ox: bx), close: true, fill: black, stroke: none)
  line(..face(s: s, sx: 1, ox: bx + g), close: true, fill: white, stroke: 1.6pt)
  line(..face(s: s, sx: -1, ox: bx - g), close: true, fill: white, stroke: 1.6pt)
  content((bx, -0.9), [b])
})
