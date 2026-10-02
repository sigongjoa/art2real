// 11-4 블렌더 렌더 둘(_r/11-4_pot.png · _r/11-4_gc.png, 11-4.py) + 이름표. 연구자 사진(원본 a)은 뺐다.
#import "@preview/cetz:0.4.2"
#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)
#let T(s, c: luma(40), sz: 9pt, w: "bold") = text(font: "Malgun Gothic", size: sz, fill: c, weight: w, s)
#align(center + horizon, cetz.canvas(length: 1cm, {
  import cetz.draw: *
  content((-3.6, 0.1), image("_r/11-4_pot.png", height: 6.2cm))
  content((3.4, 0.1), image("_r/11-4_gc.png", height: 6.6cm))
  line((-0.6, 0.1), (0.4, 0.1), mark: (end: ">", fill: luma(110)), stroke: luma(110) + 2pt)
  content((-3.6, -3.4), T("커피포트"))
  content((3.4, -3.4), T("일반화 원기둥 부품"))
  let r = rgb("#c0392b")
  content((5.6, 1.1), T("주둥이 · 휜 가는 관", c: r, sz: 7pt, w: "regular"), anchor: "west")
  content((3.4, -2.75), T("몸통 · 굵은 통", c: r, sz: 7pt, w: "regular"))
  content((3.4, 3.55), T("빨강 = 축 · 고리 = 축 따라 쓴 단면", c: r, sz: 7pt, w: "regular"))
}))
