// 1-6 미쇼트의 삼각형: 가운데만 다른 네 이등변삼각형 — 가운데를 가리면 넷 다 같은 삼각형
#import "@preview/cetz:0.4.2"
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#set text(font: "Malgun Gothic", size: 14pt)
#align(center + horizon, cetz.canvas(length: 1cm, {
  import cetz.draw: *
  let s = (thickness: 2.2pt, paint: black, join: "round", cap: "round")
  let H = 6.2; let W = 1.15   // 높이 · 밑변 반폭
  let m = 0.42                // 가운데 띠(y 비율) 아래 · 위 경계
  let n = 0.62
  let ex(y) = W * (1 - y / H) // 높이 y 에서 오른쪽 변의 x
  let xs = (-4.5, -1.5, 1.5, 4.5)
  for (i, x0) in xs.enumerate() {
    group({
      translate((x0, -H / 2))
      // 아래(밑변 + 두 변 아래쪽)와 위(꼭짓점 부분)는 넷 다 같다
      line((-ex(m * H), m * H), (-W, 0), (W, 0), (ex(m * H), m * H), stroke: s)
      line((-ex(n * H), n * H), (0, H), (ex(n * H), n * H), stroke: s)
      let y0 = m * H; let y1 = n * H
      if i == 0 {        // 가운데에서 꼬임: 두 변이 엇갈린다
        line((-ex(y0), y0), (ex(y1), y1), stroke: s)
        line((ex(y0), y0), (-ex(y1), y1), stroke: s)
      } else if i == 1 { // 끊김
      } else if i == 2 { // 울퉁불퉁
        for sg in (-1, 1) {
          let pts = range(0, 13).map(k => {
            let t = k / 12; let y = y0 + (y1 - y0) * t
            (sg * (ex(y) + 0.13 * calc.sin(t * 3 * calc.pi)), y)
          })
          line(..pts, stroke: s)
        }
      } else {           // 반듯함
        line((-ex(y0), y0), (-ex(y1), y1), stroke: s)
        line((ex(y0), y0), (ex(y1), y1), stroke: s)
      }
    })
  }
  // 가운데 띠를 가리는 연필 자리(옅은 띠) — 「여기를 가려 보세요」
  rect((-5.9, -H / 2 + m * H - 0.12), (5.9, -H / 2 + n * H + 0.12), fill: rgb(120, 150, 220, 40), stroke: (paint: rgb(90, 120, 200), dash: "dashed", thickness: 1pt))
  content((5.9, -H / 2 + n * H + 0.2), anchor: "south-east", text(fill: rgb(60, 90, 180), size: 12pt)[가림])
}))
