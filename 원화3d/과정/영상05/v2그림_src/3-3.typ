// 3-3 (a) 회색 얼굴 · 흰 꽃병 (b) 같은 선 · 왼쪽은 술잔 부품, 오른쪽은 얼굴 부품 경계
#import "얼굴선.typ": *
#show: page-setup
#cetz.canvas(length: 1cm, {
  import cetz.draw: *
  let s = 1.25; let st = 2.2pt
  let P = D.pts; let yy(i) = s * P.at(i).at(1); let xx(i) = s * P.at(i).at(0)
  let ax = -7.5
  rect((ax - s * W, 0), (ax + s * W, s * 10), fill: rgb("#b4b5b8"), stroke: 1.6pt)
  line(..vase(s: s, ox: ax), close: true, fill: white, stroke: none)
  content((ax, -1.0), [a])
  let bx = 7.5
  rect((bx - s * W, 0), (bx + s * W, s * 10), stroke: 1.6pt)
  line(..prof(s: s, ox: bx), stroke: st); line(..prof(s: s, sx: -1, ox: bx), stroke: st)
  line((bx - xx(800), s * 10), (bx + xx(800), s * 10), stroke: st)
  line((bx - xx(0), 0), (bx + xx(0), 0), stroke: st)
  for i in D.vase { line(..tick(i, s: s, sx: -1, ox: bx, len: 0.6), stroke: 2pt) }
  for i in D.face { line(..tick(i, s: s, ox: bx, len: 0.6), stroke: 2pt) }
  // 이름표: 구간 가운데 옆
  let lab(i, sx, t, dx) = content((bx + sx * (xx(i) + dx), yy(i)), text(size: 20pt, t))
  let V = D.vase; let F = D.face
  lab(int((V.at(5) + 800) / 2), -1, [입술], 1.0)
  lab(int((V.at(4) + V.at(5)) / 2), -1, [그릇], 1.0)
  lab(int((V.at(1) + V.at(3)) / 2), -1, [줄기], 1.0)
  lab(int(V.at(0) / 2), -1, [받침], 1.0)
  lab(int((F.at(4) + 800) / 2), 1, [이마], 1.4)
  lab(int((F.at(3) + F.at(4)) / 2), 1, [코], 1.0)
  lab(int((F.at(1) + F.at(3)) / 2), 1, [입술], 1.5)
  lab(int((F.at(0) + F.at(1)) / 2), 1, [턱], 1.0)
  content((bx, -1.0), [b])
})
