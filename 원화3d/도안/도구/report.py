"""`art3d.py` 결과를 **PDF 한 장짜리 산출물**로 묶는다.

    py -3.11 report.py <art3d 출력폴더> [--title "..."] [--pdf 나갈경로.pdf]

왜 PDF 인가: 맵과 숫자가 폴더에 흩어져 있으면 **판정이 사람 눈에 도달하지 못한다.**
지표·맵·판 표를 한 장에 놓고 **판정란은 비워둔다** — 이 저장소 LIMS 규약대로 사람이 적는다.

typst 가 있어야 한다 (`winget install Typst.Typst`).
"""
import argparse
import datetime
import json
import pathlib
import shutil
import subprocess
import sys

TYPST = shutil.which("typst") or (
    r"C:\Users\zesky\AppData\Local\Microsoft\WinGet\Packages"
    r"\Typst.Typst_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\typst-x86_64-pc-windows-msvc\typst.exe")

HEAD = """#set page(paper: "a4", margin: 1.6cm)
#set text(font: ("Malgun Gothic", "Segoe UI"), size: 9pt)
#show heading: set text(weight: "bold")
"""


def okt(good, txt):
    """typst 색칠 텍스트. (파이썬에서 typst 함수를 부를 수는 없으니 문자열로 낸다)"""
    c = "#1a7f37" if good else "#c4322d"
    return f'text(fill: rgb("{c}"), weight: "bold")[{txt}]'


def cell(p, cap):
    # `grid(...)` 인자 자리는 이미 코드 모드다 — 여기에 `#` 를 붙이면 컴파일이 깨진다
    return f'figure(image("{p}", width: 100%), caption: [{cap}])'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--title", default=None)
    ap.add_argument("--pdf", default=None)
    a = ap.parse_args()
    d = pathlib.Path(a.dir).resolve()
    js = json.loads((d / "art3d.json").read_text(encoding="utf-8"))
    m = js["metrics"]
    title = a.title or f'원화 3D 정보 추출 — {js["src"]}'
    pdf = pathlib.Path(a.pdf) if a.pdf else d / "report.pdf"
    today = datetime.date.today().isoformat()

    rec_ok = m["recon_error"] <= 5
    ord_ok = m["junctions_used"] >= 5
    rows = js["regions"][:22]

    def tone(rgb):
        r, g, b = rgb
        if sum(rgb) / 3 < 110: return "검정"
        if r - b > 40: return "금색"
        if b - r > 12: return "청회"
        return "흰색"

    tbl = "".join(
        f'[{r["id"]}], [{r["area"]:,}], [{tone(r["rgb"])}], '
        f'[{r["rgb"][0]},{r["rgb"][1]},{r["rgb"][2]}], [{r["color_std"]}], '
        f'[{r["depth_score"]:+d}], [{len(r["necks"])}],\n'
        for r in rows)

    src = f"""{HEAD}
#align(center)[#text(size: 15pt, weight: "bold")[{title}]]
#align(center)[#text(size: 8pt, fill: gray)[{today} · {js["src"]} · {js["size"][0]}×{js["size"][1]}px · art-to-3d-maps]]
#v(4pt)

== 지표

#table(columns: (auto, auto, 1fr), stroke: 0.4pt, inset: 5pt,
  [*항목*], [*값*], [*뜻*],
  [판 수], [{m["regions"]}], [누수방지 분할 + 톤 클래스 연결성분],
  [재구성 오차], [#{okt(rec_ok, f'{m["recon_error"]} / 255')}],
    [판별 평균색으로 원본을 되만든 오차. 5 이하면 분할이 음영 경계와 일치],
  [T-접합], [#{okt(ord_ok, str(m["junctions_used"]))}],
    [가림 순서 투표에 쓰인 접합 수. 적으면 순서를 못 믿는다],
  [목 후보], [{m["neck_candidates"]}], [판 안에서 폭이 잘록해지는 자리 = 하위부품 경계],
)

== 맵

#grid(columns: (1fr, 1fr), gutter: 8pt,
  {cell("regions.png", "① 판 분할 — 선 + 톤 계단 둘 다 경계")},
  {cell("recon.png", "② 판별 평균색 재구성 — 원본과 같아야 분할이 맞다")},
  {cell("order.png", "③ 가림 순서 — 밝을수록 앞 (T-접합 투표)")},
  {cell("necks.png", "④ 목 — 빨간 테두리 판에 하위부품 경계 후보")},
)

#pagebreak()

== 판 (면적 상위 {len(rows)})

#table(columns: 7, stroke: 0.4pt, inset: 4pt, align: (right, right, center, right, right, right, right),
  [*id*], [*면적*], [*색*], [*평균RGB*], [*색 표준편차*], [*깊이점수*], [*목*],
  {tbl}
)

#text(size: 8pt, fill: gray)[
색 표준편차가 22 를 넘으면 그 판은 음영 경계를 가로지른 것 —
톤 단계(`--tones`)를 올리거나 목 후보로 더 갈라야 한다.
깊이점수는 T-접합 투표의 합(+ 가 앞). 절댓값이 아니라 *판 사이 순서*로만 읽는다.
]

== 판정

#table(columns: (auto, 1fr), stroke: 0.4pt, inset: 6pt,
  [분할이 맞나], [],
  [가림 순서가 맞나], [],
  [모델에 쓸 것], [],
)
#text(size: 8pt, fill: gray)[판정란은 사람이 적는다 (LIMS 규약).]

== 방법 근거

#text(size: 8pt)[
① 누수방지 분할 — trapped-ball segmentation. 반지름 r 인 공은 폭 2r 보다 좁은 틈을
못 지나므로 선이 끊겨도 옆 판으로 안 샌다. ·
② T-접합 가림순서 — Entem et al., *Structuring and layering contour drawings of organic
shapes*, Expressive/SBIM 2018. T 자 접합의 가로대가 가리는 쪽이다. ·
③ 반경 변화 — 같은 논문의 radial variation metric. 판 주축을 따라 반경이 잘록해지는
자리를 하위부품 경계로 본다. ·
음영에서 법선을 역산하는 길은 닫혀 있다 — 셀 채색에 단일 광원을 최소제곱으로 맞추면
R² = 0.12 다.
]
"""
    typ = d / "report.typ"
    typ.write_text(src, encoding="utf-8")
    r = subprocess.run([TYPST, "compile", str(typ), str(pdf), "--root", str(d)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        print(r.stdout, r.stderr, file=sys.stderr)
        sys.exit(1)
    print(pdf)


if __name__ == "__main__":
    main()
