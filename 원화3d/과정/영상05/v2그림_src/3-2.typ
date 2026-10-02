// 3-2 술잔↔얼굴: 가운데 같은 선 · 왼쪽 술잔으로 본 경계(곡률 최소) · 오른쪽 얼굴로 본 경계
#import "얼굴선.typ": *
#show: page-setup
#cetz.canvas(length: 1cm, {
  import cetz.draw: *
  let s = 1.0; let st = 2.4pt; let tk = 3.2pt
  let P = D.pts
  let top(ox) = line((ox - s * P.last().at(0), s * 10), (ox + s * P.last().at(0), s * 10), stroke: st)
  let bot(ox) = line((ox - s * P.first().at(0), 0), (ox + s * P.first().at(0), 0), stroke: st)
  // 가운데: 판 + 선
  let cx = 0
  rect((cx - s * W, -0.3), (cx + s * W, s * 10 + 0.3), stroke: st)
  line(..prof(s: s, ox: cx), stroke: st); line(..prof(s: s, sx: -1, ox: cx), stroke: st)
  top(cx); bot(cx)
  // 왼쪽: 술잔
  let lx = -11
  line(..prof(s: s, ox: lx), stroke: st); line(..prof(s: s, sx: -1, ox: lx), stroke: st); top(lx); bot(lx)
  for i in D.vase { line(..tick(i, s: s, ox: lx, len: 0.9), stroke: (paint: rgb("#d03030"), thickness: tk)); line(..tick(i, s: s, sx: -1, ox: lx, len: 0.9), stroke: (paint: rgb("#d03030"), thickness: tk)) }
  // 오른쪽: 얼굴(오른쪽 옆얼굴)
  let rx = 9
  line(..face(s: s, ox: rx), close: true, stroke: st)
  for i in D.face { line(..tick(i, s: s, ox: rx, len: 0.9), stroke: (paint: rgb("#2060c0"), thickness: tk)) }
  // 화살표
  line((-5.2, 5), (-7.0, 5), stroke: 3pt, mark: (end: "stealth", fill: black, scale: 1.6))
  line((5.2, 5), (7.0, 5), stroke: 3pt, mark: (end: "stealth", fill: black, scale: 1.6))
  content((lx, -1.1), [술잔]); content((rx + 2, -1.1), [얼굴])
})
