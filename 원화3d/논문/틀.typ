// 원화3d 연구 줄기 논문 틀 — arXiv 2단 모양 · 한국어 (2026-09-15)
// 줄기마다 `논문/<줄기>/main.typ` 가 `#import "../틀.typ": *` 로 쓴다. 숫자는 같은 폴더의 json · csv 에서 읽는다.

#let serif = ("Noto Serif KR", "Batang")
#let sans = ("Noto Sans KR", "Malgun Gothic")
#let mono = ("NanumGothicCoding", "Consolas")
#let accent = rgb("#1f4e8c")

// 소수 d 자리로 — 뒤 0 을 채운다
#let 수(x, d: 3) = {
  let s = str(calc.round(float(x), digits: d))
  if not s.contains(".") { s += "." }
  s + "0" * (d - s.split(".").at(1).len())
}
#let 부호(x, d: 3) = if float(x) >= 0 { "+" + 수(x, d: d) } else { 수(x, d: d) }
#let 중앙(xs) = {
  let s = xs.map(float).sorted()
  let n = s.len()
  let q = calc.quo(n, 2)
  if calc.odd(n) { s.at(q) } else { (s.at(q - 1) + s.at(q)) / 2 }
}
#let 평균(xs) = xs.map(float).sum() / xs.len()

// 위아래 굵은 선 · 머리 아래 가는 선
#let 표(columns: auto, align: auto, header: (), ..cells) = table(
  columns: columns,
  align: align,
  stroke: none,
  table.hline(stroke: 0.8pt),
  table.header(..header.map(h => text(font: sans, weight: "bold", h))),
  table.hline(stroke: 0.4pt),
  ..cells.pos(),
  table.hline(stroke: 0.8pt),
)

#let 사례(name) = text(font: mono, size: 0.92em, name)

// 참고문헌은 영어 규칙으로 — 한국어 규칙이면 저자 사이에 「와/과」가 끼어든다
// 경로는 부르는 쪽 파일 기준이라 bibliography 는 논문에서 만들어 넘긴다: #참고문헌(bibliography("refs.bib", style: "ieee", title: none))
#let 참고문헌(bib) = {
  heading(numbering: none)[참고문헌]
  set text(lang: "en", size: 8pt)
  bib
}

#let 논문(title: "", english: none, authors: "", date: "", meta: none, abstract: [], keywords: (), body) = {
  set document(title: title, author: authors)
  set page(
    paper: "a4",
    columns: 2,
    margin: (x: 1.6cm, top: 2.1cm, bottom: 2.0cm),
    header: context {
      if here().page() > 1 {
        set text(font: sans, size: 7.5pt, fill: luma(120))
        title
        h(1fr)
        [원화3d 연구 줄기]
      }
    },
    footer: context {
      set text(font: sans, size: 7.5pt, fill: luma(120))
      h(1fr)
      counter(page).display()
      h(1fr)
    },
  )
  set columns(gutter: 0.55cm)
  set text(font: serif, size: 9.3pt, lang: "ko", cjk-latin-spacing: auto)
  set par(justify: true, leading: 0.74em, spacing: 0.95em, first-line-indent: (amount: 1em, all: false))
  set heading(numbering: "1.1")
  show heading: set text(font: sans, weight: "bold")
  show heading.where(level: 1): it => block(above: 1.35em, below: 0.7em, text(size: 10.8pt, fill: accent, it))
  show heading.where(level: 2): it => block(above: 1.05em, below: 0.55em, text(size: 9.6pt, it))
  set math.equation(numbering: "(1)", supplement: [식])
  set figure(gap: 0.55em)
  show figure.caption: set text(size: 8.3pt)
  show figure.caption: it => {
    set par(justify: true, first-line-indent: 0em)
    text(font: sans, weight: "bold", it.supplement + " " + context it.counter.display(it.numbering) + ".")
    [ ]
    it.body
  }
  show figure.where(kind: table): set figure.caption(position: top)
  set table(inset: (x: 3.6pt, y: 2.6pt))
  show table: set text(size: 8pt)
  show raw: set text(font: mono, size: 7.8pt)
  show link: set text(fill: accent)

  place(top + center, scope: "parent", float: true, clearance: 1.4em, block(width: 100%, {
    set par(first-line-indent: 0em, justify: false)
    align(center, text(font: sans, size: 16pt, weight: "bold", title))
    if english != none {
      v(0.3em)
      align(center, text(size: 9.5pt, style: "italic", fill: luma(80), english))
    }
    v(0.75em)
    align(center, text(font: sans, size: 8.6pt)[#authors #h(0.7em) · #h(0.7em) #date])
    if meta != none {
      v(0.25em)
      align(center, text(font: mono, size: 7.4pt, fill: luma(110), meta))
    }
    v(0.9em)
    block(inset: (x: 1.4cm), {
      set par(justify: true)
      text(font: sans, weight: "bold", size: 9pt)[초록 #h(0.3em)]
      text(size: 9pt, abstract)
      if keywords.len() > 0 {
        v(0.45em)
        text(font: sans, size: 8pt, fill: luma(90))[*핵심어* #h(0.4em) #keywords.join(" · ")]
      }
    })
    v(0.5em)
    line(length: 100%, stroke: 0.5pt + luma(180))
  }))
  body
}
