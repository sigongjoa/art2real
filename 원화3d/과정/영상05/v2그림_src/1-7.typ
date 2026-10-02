// 1-7 브레그만의 B: 같은 조각 — 왼쪽은 의미 없는 조각, 오른쪽은 잉크 얼룩을 얹자 B 다섯 개
#import "@preview/cetz:0.4.2"
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#set text(font: "Malgun Gothic", size: 13pt)
#align(center + horizon, cetz.canvas(length: 1cm, {
  import cetz.draw: *
  let Bs = ((-2.25, 1.15, -8deg), (0.0, 1.3, 6deg), (2.25, 1.05, -4deg), (-1.15, -1.2, 5deg), (1.2, -1.25, -7deg))
  let letters() = for (x, y, r) in Bs {
    content((x, y), std.rotate(r, text(font: "Arial", weight: "bold", size: 60pt, fill: rgb(175, 178, 188), stroke: 1.3pt + rgb(40, 40, 45))[B]))
  }
  // 얼룩: 글자마다 세로 기둥 · 가운데 이음매 · 두 고리의 바깥을 덮는 붓질 — 서로 이어져 한 덩어리
  let th = (thickness: 0.48cm, cap: "round", join: "round")
  let blob(col) = {
    let st = th + (paint: col)
    // 줄마다 글자 가운데 이음매를 지나는 가로 붓질 하나
    catmull((-3.3, 1.35), (-2.25, 1.1), (-1.1, 1.45), (0.0, 1.25), (1.1, 0.9), (2.25, 1.05), (3.2, 0.75), stroke: st)
    catmull((-2.2, -1.0), (-1.15, -1.25), (0.0, -1.05), (1.2, -1.3), (2.1, -1.05), stroke: st)
    // 글자마다 위에서 아래로 고리를 끊는 비스듬한 붓질
    for (x, y, r) in Bs {
      catmull((x - 0.3, y + 1.0), (x + 0.05, y + 0.45), (x - 0.05, y - 0.4), (x + 0.35, y - 1.0), stroke: st)
    }
    // 고리 위 · 아래를 더 끊는 붓질 — 조각만 남을 때 B 로 안 읽히게(10-02)
    for (x, y, r) in Bs {
      catmull((x - 0.55, y + 0.62), (x, y + 0.72), (x + 0.5, y + 0.52), stroke: st + (thickness: 0.22cm))
      catmull((x - 0.5, y - 0.62), (x + 0.1, y - 0.72), (x + 0.55, y - 0.55), stroke: st + (thickness: 0.22cm))
    }
    // 두 줄을 잇는 붓질
    catmull((-2.25, 0.4), (-1.6, -0.2), (-1.2, -1.0), stroke: st)
    catmull((0.1, 0.5), (0.6, 0.0), (1.1, -1.0), stroke: st)
    catmull((2.3, 0.3), (2.0, -0.4), (1.5, -1.0), stroke: st)
  }
  group({ translate((-3.9, 0)); letters(); blob(white); content((0, -3.1), text(fill: rgb(90, 90, 100))[조각만]) })
  group({ translate((3.9, 0)); letters(); blob(black); content((0, -3.1), text(fill: rgb(90, 90, 100))[같은 조각 + 얼룩]) })
}))
