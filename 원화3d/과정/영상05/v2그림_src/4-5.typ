// 4-5: 정육면체 — 중간 지움(복원 가능) vs 꼭짓점 지움(복원 불가) · b) 지운 자리에 가짜 꼭짓점이 생기는 판
#import "@preview/cetz:0.4.2"
#set page(width: 33.867cm, height: 19.05cm, margin: 0cm, fill: white)
#set text(font: "Malgun Gothic", size: 22pt, weight: "bold", fill: rgb("#282828"))
#align(center + horizon, cetz.canvas(length: 0.88cm, {
  import cetz.draw: *
  let st = (paint: black, thickness: 2.6pt, cap: "round", join: "round")
  let s = 1.9
  let P = ((0, s), (0.866 * s, 0.5 * s), (0.866 * s, -0.5 * s), (0, -s), (-0.866 * s, -0.5 * s), (-0.866 * s, 0.5 * s))
  let C = (0, 0)
  // 보이는 모서리 9: 바깥 육각 6 + 가운데 Y 3
  let E = range(6).map(i => (P.at(i), P.at(calc.rem(i + 1, 6)))) + ((C, P.at(1)), (C, P.at(3)), (C, P.at(5)))
  let lerp(a, b, t) = (a.at(0) + (b.at(0) - a.at(0)) * t, a.at(1) + (b.at(1) - a.at(1)) * t)
  let add(p, o) = (p.at(0) + o.at(0), p.at(1) + o.at(1))
  // pieces: 모서리마다 남길 구간 [(t0, t1), …]
  let cube(o, pieces) = {
    for (i, e) in E.enumerate() {
      for (t0, t1) in pieces(i) { line(add(o, lerp(e.at(0), e.at(1), t0)), add(o, lerp(e.at(0), e.at(1), t1)), stroke: st) }
    }
  }
  let full(i) = ((0, 1),)
  let mid-a(i) = ((0, 0.3), (0.7, 1))                       // 가운데만 지움 → 꼭짓점 그대로
  let mid-b(i) = if calc.rem(i, 2) == 0 { ((0, 0.38), (0.62, 1)) } else { ((0, 0.25), (0.75, 1)) }
  let vtx-a(i) = ((0.3, 0.7),)                               // 꼭짓점 둘레를 지움
  let vtx-b(i) = if calc.rem(i, 3) == 0 { ((0.2, 0.55),) } else { ((0.4, 0.8),) }
  // 패널 a
  rect((-15.2, 0.4), (15.2, 8.6), stroke: 1.2pt + gray)
  content((-14.4, 1.1), [a)])
  let ya = 4.6
  cube((-11.2, ya), full); cube((-6.6, ya), mid-a); cube((-2.0, ya), mid-b)
  cube((4.6, ya), vtx-a); cube((10.4, ya), vtx-b)
  content((-6.6, 1.3), [복원 가능]); content((7.5, 1.3), [복원 불가])
  line((1.3, 1.2), (1.3, 8.0), stroke: (paint: gray, thickness: 1pt, dash: "dashed"))
  // 패널 b: 중간 지움 vs 지운 끝에 꺾임(가짜 꼭짓점)
  rect((-15.2, -8.6), (15.2, -0.4), stroke: 1.2pt + gray)
  content((-14.4, -7.9), [b)])
  let yb = -4.4
  cube((-6.6, yb), ((i) => ((0, 0.42), (0.6, 1))))
  // 복원 불가: 남긴 토막 끝에 짧은 꺾임 → 원래 없던 L 꼭짓점
  let o = (7.5, yb)
  for (i, e) in E.enumerate() {
    let a = lerp(e.at(0), e.at(1), 0.22); let b = lerp(e.at(0), e.at(1), 0.66)
    line(add(o, a), add(o, b), stroke: st)
    let d = (e.at(1).at(0) - e.at(0).at(0), e.at(1).at(1) - e.at(0).at(1))
    let k = if calc.rem(i, 2) == 0 { 0.22 } else { -0.22 }
    line(add(o, b), add(o, (b.at(0) - d.at(1) * k, b.at(1) + d.at(0) * k)), stroke: st)
  }
  content((-6.6, -7.7), [복원 가능]); content((7.5, -7.7), [복원 불가])
  line((1.3, -7.8), (1.3, -1.0), stroke: (paint: gray, thickness: 1pt, dash: "dashed"))
}))
