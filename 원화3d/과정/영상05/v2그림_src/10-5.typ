// 10-5 블렌더 렌더(_r/10-5.png, 10-5.py) + 칸 나눔 · 이름표
#import "@preview/cetz:0.4.2"
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#let T(s, c: luma(40), sz: 9pt, w: "bold") = text(font: "Malgun Gothic", size: sz, fill: c, weight: w, s)
#let W = 15.0
#align(center + horizon, cetz.canvas(length: 1cm, {
  import cetz.draw: *
  content((0, 0), image("_r/10-5.png", width: W * 1cm))
  let X(f) = (f - 0.5) * W
  let lab = (("입은 모습", 0.095), ("몸", 0.295), ("옷", 0.4025), ("머리카락", 0.5125), ("옷 단면 · 속이 빔", 0.7225), ("몸 위에 얹힌 껍질", 0.9025))
  for (s, f) in lab { content((X(f), -2.55), T(s, sz: 8pt)) }
  for f in (0.205, 0.61) { line((X(f), 3.0), (X(f), -2.9), stroke: (paint: luma(190), thickness: 0.6pt, dash: "dashed")) }
  content((X(0.095), 3.2), T("하나", c: luma(110), sz: 8pt, w: "regular"))
  content((X(0.405), 3.2), T("나눈 결과", c: luma(110), sz: 8pt, w: "regular"))
  content((X(0.81), 3.2), T("잘라 보기", c: luma(110), sz: 8pt, w: "regular"))
}))
