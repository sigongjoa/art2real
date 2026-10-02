// 3-1~3-4 공통: 얼굴선.json(얼굴선.py) 의 옆선을 그리는 도우미
#import "@preview/cetz:0.4.2"
#let D = json("얼굴선.json")
#let W = 4.2  // 판 반폭
// 오른쪽 옆선(아래→위). sx=-1 이면 왼쪽 거울
#let prof(s: 1, sx: 1, ox: 0, oy: 0) = D.pts.map(p => (ox + s * sx * p.at(0), oy + s * p.at(1)))
#let vase(s: 1, ox: 0, oy: 0) = prof(s: s, ox: ox, oy: oy) + prof(s: s, sx: -1, ox: ox, oy: oy).rev()
// 얼굴 영역: 옆선 + 판 바깥 모서리
#let face(s: 1, sx: 1, ox: 0, oy: 0) = prof(s: s, sx: sx, ox: ox, oy: oy) + ((ox + s * sx * W, oy + s * 10), (ox + s * sx * W, oy))
// 옆선 i 번 점의 바깥(sx 쪽) 짧은 눈금
#let tick(i, s: 1, sx: 1, ox: 0, oy: 0, len: 0.45, dir: 1) = {
  let p = D.pts.at(i); let q = D.pts.at(i + 1); let r = D.pts.at(i - 1)
  let tx = q.at(0) - r.at(0); let ty = q.at(1) - r.at(1); let n = calc.sqrt(tx * tx + ty * ty)
  let nx = ty / n * dir; let ny = -tx / n * dir   // 오른쪽 선의 바깥 법선 (dir=-1 이면 안쪽)
  let a = (ox + s * sx * p.at(0), oy + s * p.at(1))
  ((a.at(0) - s * sx * nx * len * 0.5, a.at(1) - s * ny * len * 0.5), (a.at(0) + s * sx * nx * len * 0.5, a.at(1) + s * ny * len * 0.5))
}
#let page-setup(body) = {
  set page(width: 33.867cm, height: 19.05cm, margin: 0cm, fill: white)
  set text(font: ("Malgun Gothic",), size: 22pt)
  align(center + horizon, body)
}
