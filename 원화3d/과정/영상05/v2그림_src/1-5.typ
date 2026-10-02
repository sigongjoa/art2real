// 1-5 판 뒤 고양이?: 머리 · 꼬리만 보이면 고양이 한 마리 — 판을 걷으면 머리는 꽃병 위, 꼬리는 구불한 선 끝일 수도
#import "@preview/cetz:0.4.2"
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#set text(font: "Malgun Gothic", size: 13pt)
#align(center + horizon, cetz.canvas(length: 1cm, {
  import cetz.draw: *
  let fur = rgb(214, 170, 120); let ink = rgb(60, 45, 35)
  let st = (thickness: 1.2pt, paint: ink)
  let head(c) = group({
    translate(c)
    line((-0.62, 0.2), (-0.5, 0.95), (-0.12, 0.5), close: true, fill: fur, stroke: st)   // 귀
    line((0.62, 0.2), (0.5, 0.95), (0.12, 0.5), close: true, fill: fur, stroke: st)
    circle((0, 0), radius: (0.68, 0.6), fill: fur, stroke: st)
    circle((-0.25, 0.08), radius: (0.11, 0.08), fill: rgb(70, 110, 60), stroke: (thickness: 0.8pt, paint: ink))
    circle((0.25, 0.08), radius: (0.11, 0.08), fill: rgb(70, 110, 60), stroke: (thickness: 0.8pt, paint: ink))
    line((-0.07, -0.12), (0.07, -0.12), (0, -0.2), close: true, fill: rgb(200, 110, 110), stroke: none)
  })
  let tailst = (thickness: 0.2cm, paint: fur, cap: "round")
  let tailtip = ((1.4, 0.8), (1.55, 1.7), (2.2, 2.15), (2.85, 1.95))
  let plate(dashed) = if dashed {
    rect((-2.3, -0.8), (2.3, 0.8), fill: none, stroke: (thickness: 1.2pt, paint: rgb(90, 90, 100), dash: "dashed"))
  } else { rect((-2.3, -0.8), (2.3, 0.8), fill: rgb(48, 48, 52), stroke: none) }
  // ---- 왼쪽: 판 있음 ----
  group({
    translate((-3.9, 0.2))
    head((-1.0, 1.35))
    catmull(..tailtip, stroke: tailst)
    plate(false)
    content((0, -2.75), text(fill: rgb(90, 90, 100))[판 있음])
  })
  line((-0.6, 0.2), (0.4, 0.2), stroke: (thickness: 1.6pt, paint: rgb(200, 70, 50)), mark: (end: ">", fill: rgb(200, 70, 50), scale: 1.3))
  // ---- 오른쪽: 판을 걷으면 ----
  group({
    translate((3.9, 0.2))
    // 꽃병: 머리 밑 목 → 불룩한 몸 → 받침
    let vase = rgb(150, 175, 200)
    hobby((-1.25, 0.85), (-1.3, -0.3), (-1.85, -1.3), (-1.45, -2.2), (-0.55, -2.2), (-0.15, -1.3), (-0.7, -0.3), (-0.75, 0.85), close: true, fill: vase, stroke: (thickness: 1.2pt, paint: rgb(60, 80, 100)))
    head((-1.0, 1.35))
    // 꼬리 = 구불한 선의 끝
    catmull((1.25, -2.2), (1.7, -1.6), (1.0, -0.9), (1.6, -0.2), ..tailtip, stroke: (thickness: 0.2cm, paint: ink, cap: "round"))
    catmull(..tailtip, stroke: tailst)
    plate(true)
    content((0, -2.75), text(fill: rgb(90, 90, 100))[판을 걷으면])
  })
}))
