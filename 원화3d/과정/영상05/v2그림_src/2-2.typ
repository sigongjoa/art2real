// 2-2 원기둥 하나에서 네 가지만 바꿔 지온을 만든다(단면 모서리 · 대칭 · 크기 · 축)
#import "@preview/cetz:0.4.2"
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#set text(font: "Malgun Gothic", size: 12pt, fill: rgb(60, 60, 70))
#align(center + horizon, cetz.canvas(length: 1cm, {
  import cetz.draw: *
  let g(n, w) = image("_렌더/2-2_" + n + ".png", width: w)
  let red = rgb(200, 70, 50)
  let hub = (0, -1.05)
  content(hub, g("원기둥", 3.4cm))
  content((0, -2.4), text(weight: "bold")[원기둥])
  // (자리, 렌더 이름, 이름표, 화살표 시작 · 끝)
  let items = (
    ((-4.7, 1.7), "비대칭", [대칭 없앰], (-1.5, -0.2), (-3.3, 0.75)),
    ((0.0, 1.7), "원뿔", [크기 점점 커짐], (0.0, 0.05), (0.0, 0.8)),
    ((4.7, 1.7), "통", [커졌다 작아짐], (1.5, -0.2), (3.3, 0.75)),
    ((-4.7, -2.1), "각기둥", [단면 모서리 곧게], (-1.8, -1.2), (-3.2, -1.7)),
    ((4.7, -2.1), "굽은관", [축 굽힘], (1.8, -1.2), (3.2, -1.7)),
  )
  for (p, n, lab, a, b) in items {
    content(p, g(n, 2.9cm))
    content((p.at(0), if p.at(1) > 0 { p.at(1) + 1.2 } else { p.at(1) - 1.15 }), lab)
    line(a, b, stroke: (thickness: 1.4pt, paint: red), mark: (end: ">", fill: red, scale: 1.1))
  }
}))
