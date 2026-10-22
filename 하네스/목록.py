# Pages 쪽 — docs/판/<판>/(보고.html · 그림) 복사 + docs/index.html(판 목록 · 명제 · 판정 · 가지 · 날짜 · 최신순) · 하네스 기록 단계가 판마다 부름 · 10-22
import os, json, glob, shutil, html
from omegaconf import OmegaConf
뿌리 = "G:/art2real"; 문서 = 뿌리 + "/docs/"; E = html.escape
def 복사(판):
    s, d = f"{뿌리}/하네스/판/{판}/", f"{문서}판/{판}/"; os.makedirs(d, exist_ok=True)
    for f in ("보고.html", "시트.png", "특징.png", "보고.png", "설정.yaml", "판정.json"):
        if os.path.exists(s + f): shutil.copy(s + f, d + f)
def 목록():
    줄 = []
    for p in glob.glob(f"{뿌리}/하네스/판/*/판정.json"):
        판 = os.path.basename(os.path.dirname(p)); j = json.load(open(p, encoding="utf-8")); c = OmegaConf.load(os.path.dirname(p) + "/설정.yaml")
        줄.append((j.get("날짜", ""), 판, str(c.판.get("명제") or c.판.물음), j["판정"], c.판.가지, c.판.종류))
    줄.sort(reverse=True)
    행 = "".join(f'<li><a href="판/{E(판)}/보고.html"><span class="판정 {("통과" if 말 == "통과" else "탐색" if 말.startswith("탐색") else "실패")}">{E(말)}</span><strong>{E(명)}</strong><span class="곁">판 {E(판)} · 가지 {E(str(가))} · {E(str(종))} · {E(날)}</span></a></li>' for 날, 판, 명, 말, 가, 종 in 줄)
    글 = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>art2real 판 목록</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;600;700&display=swap"><style>
:root{{--paper:#f6f4ef;--sheet:#fffdf8;--ink:#1d2129;--muted:#585e68;--rule:#dcd7cc;--pass:#1f7a3e;--pass-bg:#e3f1e6;--fail:#b3261e;--fail-bg:#f7e2de;--tool:#8a5f00;--tool-bg:#f6ecd4}}
@media (prefers-color-scheme:dark){{:root{{--paper:#15181d;--sheet:#1c2027;--ink:#e8e4da;--muted:#a3a8b1;--rule:#343a44;--pass:#6fcf8f;--pass-bg:#1d3326;--fail:#f08a7e;--fail-bg:#3a201d;--tool:#e3b54f;--tool-bg:#3a2f15;color-scheme:dark}}}}
body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 "IBM Plex Sans KR","Malgun Gothic",sans-serif;word-break:keep-all}}
main{{max-width:880px;margin:0 auto;padding:56px max(16px,env(safe-area-inset-left,0px)) 96px}}
h1{{font-size:clamp(1.8rem,4vw,2.4rem);letter-spacing:-.02em;margin:0 0 8px}}p.lead{{color:var(--muted);margin:0 0 32px;max-width:62ch}}
ul{{list-style:none;margin:0;padding:0;display:grid;gap:10px}}a{{display:grid;grid-template-columns:auto 1fr;gap:4px 14px;align-items:baseline;padding:16px 18px;border:1px solid var(--rule);border-radius:12px;background:var(--sheet);color:inherit;text-decoration:none}}
a:hover{{border-color:var(--ink)}}a:focus-visible{{outline:2px solid var(--ink);outline-offset:2px}}strong{{font-weight:600}}.곁{{grid-column:2;color:var(--muted);font-size:.86rem}}
.판정{{grid-row:1/3;font-weight:700;font-size:.85rem;padding:4px 10px;border-radius:999px;white-space:nowrap}}.통과{{color:var(--pass);background:var(--pass-bg)}}.실패{{color:var(--fail);background:var(--fail-bg)}}.탐색{{color:var(--tool);background:var(--tool-bg)}}
</style></head><body><main><h1>art2real 판 목록</h1><p class="lead">목표: 임의의 이미지로부터 CAD 코드를 만든다. 판(실험) 하나마다 명제를 먼저 적고, 하네스가 돌려서 판정과 보고서를 남긴다.</p><ul>{행}</ul></main></body></html>"""
    os.makedirs(문서, exist_ok=True); open(문서 + "index.html", "w", encoding="utf-8").write(글); open(문서 + ".nojekyll", "w").close(); return 문서 + "index.html"
def 갱신(판): 복사(판); return 목록()
if __name__ == "__main__":
    import sys; [복사(os.path.basename(os.path.dirname(p))) for p in glob.glob(f"{뿌리}/하네스/판/*/판정.json")]; print(목록())
