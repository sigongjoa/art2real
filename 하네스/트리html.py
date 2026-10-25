# 연구 트리 HTML 조각 — Pages 메인 · 판 보고서가 같이 씀 · 꼴 T1 가지 지도 / T2 아웃라인(시안) · 강조 = 이 판이 나온 잎 · 10-22
import html
E = html.escape; 상태꼴 = {"해결": "s-ok", "열림": "s-open", "보류": "s-hold", "안 봄": "s-none", "기각": "s-drop"}
CSS = """
.트리{--t-ok:var(--pass,#1f7a3e);--t-ok-bg:var(--pass-bg,#e3f1e6);--t-open:var(--fail,#b3261e);--t-open-bg:var(--fail-bg,#f7e2de);--t-hold:var(--tool,#8a5f00);--t-hold-bg:var(--tool-bg,#f6ecd4)}
.트리 .목표{background:var(--ink);color:var(--paper);border-radius:12px;padding:14px 18px;font-weight:700;font-size:1.05rem;text-wrap:balance}
.트리 .목표 small{display:block;font-weight:500;opacity:.75;font-size:.8rem;margin-bottom:2px}
.칩{display:inline-flex;align-items:center;font-size:.74rem;font-weight:700;padding:2px 8px;border-radius:999px;white-space:nowrap}
.s-ok{color:var(--t-ok);background:var(--t-ok-bg)}.s-open{color:var(--t-open);background:var(--t-open-bg)}.s-hold{color:var(--t-hold);background:var(--t-hold-bg)}.s-none,.s-drop{color:var(--muted);background:var(--soft)}
.판알{display:inline-flex;gap:4px;align-items:center;font-size:.74rem;padding:2px 8px;border-radius:999px;border:1px solid var(--rule);color:var(--ink);text-decoration:none;background:var(--sheet)}
.판알 i{width:7px;height:7px;border-radius:50%;background:var(--muted)}.판알.통과 i{background:var(--t-ok)}.판알.실패 i{background:var(--t-open)}
.판알:hover{border-color:var(--ink)}.판알:focus-visible{outline:2px solid var(--line1,#2d5fa8);outline-offset:2px}
.잎 details summary{cursor:pointer;color:var(--muted);font-size:.8rem;list-style:none}.잎 details summary::-webkit-details-marker{display:none}
.잎 details summary::before{content:"근거 보기";text-decoration:underline;text-underline-offset:3px}.잎 details[open] summary::before{content:"근거 접기"}
.잎 details p{font-size:.82rem;color:var(--muted);margin:6px 0 0;line-height:1.55}.잎 details p b{color:var(--ink);font-weight:600}
.잎.강조{outline:2px solid var(--ink);outline-offset:3px}.이판{font-size:.72rem;font-weight:700;color:var(--paper);background:var(--ink);padding:2px 7px;border-radius:999px}
.별{font-size:.72rem;font-weight:700;color:var(--t-hold)}
/* T1 가지 지도 */
.t1 .줄기들{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-top:22px;position:relative}
.t1 .줄기들::before{content:"";position:absolute;left:12.5%;right:12.5%;top:-11px;border-top:1px solid var(--rule)}
.t1 .줄기{display:flex;flex-direction:column;gap:10px;position:relative}.t1 .줄기::before{content:"";position:absolute;left:50%;top:-11px;height:11px;border-left:1px solid var(--rule)}
.t1 .줄기머리{font-weight:700;font-size:.95rem;text-align:center;padding:6px;border:1px solid var(--rule);border-radius:10px;background:var(--paper)}
.t1 .잎{background:var(--sheet);border:1px solid var(--rule);border-radius:10px;padding:10px 12px;display:flex;flex-direction:column;gap:6px;min-width:0}
.t1 .잎 .윗{display:flex;gap:6px;align-items:center;flex-wrap:wrap}.t1 .잎 .번{font-weight:700;font-size:.8rem;color:var(--muted)}.t1 .잎 .이름{font-weight:600;font-size:.9rem;line-height:1.4}
.t1 .판줄{display:flex;gap:4px;flex-wrap:wrap}
@media (max-width:820px){.t1 .줄기들{grid-template-columns:repeat(2,minmax(0,1fr))}.t1 .줄기들::before,.t1 .줄기::before{display:none}}
@media (max-width:480px){.t1 .줄기들{grid-template-columns:1fr}}
/* T2 아웃라인 */
.t2 .줄기{margin:18px 0 0 18px;padding-left:18px;border-left:1px solid var(--rule)}
.t2 .줄기머리{font-weight:700;font-size:1rem;position:relative;margin-left:-18px;padding-left:18px}.t2 .줄기머리::before{content:"";position:absolute;left:0;top:.75em;width:12px;border-top:1px solid var(--rule)}
.t2 .잎{position:relative;display:grid;grid-template-columns:auto 1fr;gap:4px 12px;align-items:baseline;padding:10px 12px;margin-top:6px;border-radius:10px}
.t2 .잎::before{content:"";position:absolute;left:-18px;top:1.25em;width:14px;border-top:1px solid var(--rule)}
.t2 .잎:hover{background:var(--sheet)}.t2 .잎 .번{font-weight:700;font-size:.82rem;color:var(--muted);grid-row:1}
.t2 .잎 .몸{min-width:0;display:flex;flex-direction:column;gap:5px}.t2 .잎 .윗{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.t2 .잎 .이름{font-weight:600}
.t2 .판줄{display:flex;gap:4px;flex-wrap:wrap}
"""
def 판알(판, 링크): 꼴 = "통과" if 판["판정"].startswith("통과") else ("실패" if not 판["판정"].startswith(("탐색", "흔들림")) else ""); return f'<a class="판알 {꼴}" href="{E(링크(판["판"]))}" title="{E(판["명제"])}"><i></i>판 {E(판["판"])}</a>'
def 그리기(자료, 꼴="t1", 강조=None, 링크=lambda 판: f"판/{판}/보고.html"):
    def 잎(l):
        판줄 = "".join(판알(p, 링크) for p in l["판"]); 표 = ' <span class="이판">이 판</span>' if 강조 == l["번호"] else ""
        별 = ' <span class="별">★ 지금 줄기</span>' if l["줄기"] else ""; 칩 = f'<span class="칩 {상태꼴.get(l["상태"], "s-none")}">{E(l["상태"])}</span>'
        근 = f'<details><summary></summary><p>{E(l["증거"])}</p><p><b>다음에 물을 것</b> {E(l["다음"])}</p></details>'
        cls = "잎 강조" if 강조 == l["번호"] else "잎"
        if 꼴 == "t1": return f'<div class="{cls}" id="잎-{E(l["번호"])}"><div class="윗"><span class="번">{E(l["번호"])}</span>{칩}{표}{별}</div><div class="이름">{E(l["이름"])}</div>{f"<div class=판줄>{판줄}</div>" if 판줄 else ""}{근}</div>'
        return f'<div class="{cls}" id="잎-{E(l["번호"])}"><span class="번">{E(l["번호"])}</span><div class="몸"><div class="윗">{칩}<span class="이름">{E(l["이름"])}</span>{표}{별}</div>{f"<div class=판줄>{판줄}</div>" if 판줄 else ""}{근}</div></div>'
    줄 = "".join(f'<div class="줄기"><div class="줄기머리">{E(s["글자"])} {E(s["이름"])}</div>{"".join(잎(l) for l in s["잎"])}</div>' for s in 자료["줄기"])
    return f'<section class="트리 {꼴}" aria-label="연구 트리"><div class="목표"><small>목표</small>{E(자료["목표"])}</div>' + (f'<div class="줄기들">{줄}</div>' if 꼴 == "t1" else 줄) + "</section>"
