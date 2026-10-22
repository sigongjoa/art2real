# 하네스 보고서 HTML — 보고.md 와 같은 내용 · 한 파일(그림은 같은 폴더) · GitHub Pages 로도 나감 · 10-22
# 시안 C(10-22 사용자 고름 · 왼쪽 요약 고정 · 오른쪽 본문) · 시각 기준: 프로젝트 카드 화풍(흰 · 회백 바탕 + 뜻마다 강조 하나: 초록 통과 · 빨강 실패 · 금 도구) · 읽기 화면 · 판정이 첫눈에
import html, re
E = html.escape
아이콘 = {True: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 8.5l3 3 6-7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
          False: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4.5 4.5l7 7m0-7l-7 7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'}
CSS = """
@import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css");
@import url("https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&display=swap");
:root{--paper:#f6f4ef;--sheet:#fffdf8;--ink:#1d2129;--muted:#585e68;--rule:#dcd7cc;--soft:#ece8de;--pass:#1f7a3e;--pass-bg:#e3f1e6;--fail:#b3261e;--fail-bg:#f7e2de;--tool:#8a5f00;--tool-bg:#f6ecd4;--line1:#2d5fa8;--line2:#c0661b}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.65 "Pretendard Variable",Pretendard,"Malgun Gothic",system-ui,sans-serif;font-variant-numeric:tabular-nums;word-break:keep-all}
::selection{background:#1d2129;color:#fffdf8}
a{color:var(--line1);text-underline-offset:3px}a:focus-visible{outline:2px solid var(--line1);outline-offset:2px;border-radius:2px}
main{max-width:1040px;margin:0 auto;padding:56px 32px 96px}
header{padding-bottom:28px;border-bottom:1px solid var(--rule);margin-bottom:8px}
h1{font-size:clamp(1.9rem,4vw,2.7rem);line-height:1.15;letter-spacing:-.025em;margin:0 0 10px;font-weight:800;text-wrap:balance}
.lead{font-size:1.15rem;color:var(--muted);margin:0 0 22px;max-width:62ch;text-wrap:pretty}
.판정{display:inline-flex;align-items:center;gap:8px;font-weight:700;font-size:1.05rem;padding:7px 14px 7px 11px;border-radius:999px}
.판정 svg{width:18px;height:18px}.통과{color:var(--pass);background:var(--pass-bg)}.실패{color:var(--fail);background:var(--fail-bg)}.탐색{color:var(--tool);background:var(--tool-bg)}
dl.meta{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px 28px;margin:26px 0 0}
dl.meta div{min-width:0}dl.meta dt{font-size:.82rem;color:var(--muted)}dl.meta dd{margin:2px 0 0;font-weight:600;overflow-wrap:anywhere}
h2{font-size:1.35rem;letter-spacing:-.015em;margin:56px 0 14px;font-weight:750}
h3{font-size:1.02rem;margin:30px 0 8px;font-weight:700}
p,li{max-width:72ch}
.표{overflow-x:auto;margin:6px 0 4px;border:1px solid var(--rule);border-radius:10px;background:var(--sheet)}
table{border-collapse:collapse;width:100%;font-size:.95rem}
th,td{padding:9px 14px;text-align:right;white-space:nowrap;border-bottom:1px solid var(--soft)}
th:first-child,td:first-child{text-align:left}tr:last-child td{border-bottom:0}
thead th{font-size:.8rem;font-weight:600;color:var(--muted);background:var(--paper);border-bottom:1px solid var(--rule)}
td.결과{text-align:center}td.결과 span{display:inline-flex;width:24px;height:24px;border-radius:50%;align-items:center;justify-content:center}td.결과 svg{width:15px;height:15px}
td.결과 .o{color:var(--pass);background:var(--pass-bg)}td.결과 .x{color:var(--fail);background:var(--fail-bg)}
.차{color:var(--muted);font-size:.88rem}
.주석{font-size:.88rem;color:var(--muted);margin:8px 2px 0}.주석 code{overflow-wrap:anywhere}
.줄글{display:flex;flex-wrap:wrap;gap:6px 26px;margin:4px 0}.줄글 b{font-weight:700}.줄글 span{color:var(--muted)}
figure{margin:18px 0 0}figure img{display:block;width:100%;height:auto;border:1px solid var(--rule);border-radius:10px;background:#fff}
figcaption{font-size:.86rem;color:var(--muted);margin-top:8px}
.곡선{background:var(--sheet);border:1px solid var(--rule);border-radius:10px;padding:14px 12px 6px}
.곡선 svg{display:block;width:100%;height:auto}.곡선 text{font:15px "Pretendard Variable",Pretendard,sans-serif;fill:var(--muted)}
.사람{background:var(--sheet);border:1px solid var(--rule);border-radius:10px;padding:6px 22px}
.사람 ul{padding-left:1.1em}.사람 li{margin:8px 0}.비어{color:var(--muted);font-style:italic;padding:12px 0}
code,pre{font-family:"JetBrains Mono",D2Coding,Consolas,monospace;font-size:.86rem}
pre{background:#1d2129;color:#f3efe6;padding:16px 18px;border-radius:10px;overflow-x:auto;line-height:1.55}
td.열{background:color-mix(in oklab,var(--line1) calc(var(--v)*1%),var(--sheet))}td.열.진{color:#fff}
main{max-width:1240px;display:grid;grid-template-columns:300px minmax(0,1fr);column-gap:48px;align-items:start}
main>*{grid-column:2}header{grid-column:1;grid-row:1/200;position:sticky;top:28px;border:1px solid var(--rule);border-radius:14px;background:var(--sheet);padding:24px 22px;margin:0}
header h1{font-size:1.32rem;line-height:1.4;letter-spacing:-.01em;font-weight:750;margin-bottom:16px}header .lead{font-size:1rem}dl.meta{grid-template-columns:1fr 1fr;gap:12px 16px}main>h2:first-of-type{margin-top:0}
@media (max-width:900px){main{display:block}header{position:static;margin-bottom:8px}main>h2:first-of-type{margin-top:44px}}
nav.뒤{margin:0 0 14px}nav.뒤 a{display:inline-flex;align-items:center;gap:6px;font-weight:600;font-size:.9rem;color:var(--muted);text-decoration:none}nav.뒤 a:hover{color:var(--ink)}nav.뒤 svg{width:16px;height:16px}
td.왼{text-align:left;white-space:normal}tr.깊2 td:first-child{padding-left:30px;color:var(--muted)}.흐름{max-width:72ch}ul.목표 li{max-width:72ch;margin:6px 0}ul.고리{list-style:none;padding:0;margin:0;display:grid;gap:8px}ul.고리 li{display:grid;grid-template-columns:110px minmax(0,1fr);gap:12px;align-items:baseline;padding:10px 14px;border:1px solid var(--rule);border-radius:10px;background:var(--sheet)}ul.고리 li span{font-weight:700}ul.고리 a{overflow-wrap:anywhere}ul.고리 em{color:var(--muted);font-style:normal}
.명제{margin:0 0 12px;color:var(--muted);font-size:.95rem;max-width:72ch}.명제 span{font-weight:700;color:var(--ink);margin-right:6px}.쇼츠틀{display:grid;grid-template-columns:260px minmax(0,1fr);gap:20px;align-items:start}.쇼츠{width:260px;max-width:100%;border-radius:12px;border:1px solid var(--rule);background:#000}.쇼츠글 td{white-space:normal}@media (max-width:640px){.쇼츠틀{grid-template-columns:1fr}}.구조틀{background:var(--sheet);border:1px solid var(--rule);border-radius:12px;padding:12px;overflow-x:auto}.구조도{display:block;width:100%;min-width:720px;height:auto}.구조틀{background:#fbfaf6}.구조도 text{font-family:inherit;fill:var(--ink)}.구조도 .제{font-size:15px;font-weight:700}.구조도 .작{font-size:12px;fill:var(--muted)}.구조도 .작진{font-size:13px;font-weight:600}.구조도 .묶{font-size:13px;font-weight:600;fill:var(--muted)}
@media (max-width:640px){main{padding:32px 16px 64px}th,td{padding:8px 10px}h2{margin-top:44px}}
"""
def 수(v, n=3): return "" if v is None else (f"{v:.{n}f}" if isinstance(v, float) else E(str(v)))
def 글줄(t):   # 사람 칸 · 아주 작은 마크다운(목록 · 굵게 · 코드)
    t = re.sub(r"<!--.*?-->", "", t, flags=re.S).strip()
    if not t or t == "(비어 있음)": return '<p class="비어">아직 비어 있음. 보고.md 의 이 칸을 채우면 다시 만들 때 들어온다</p>'
    def 줄(s): s = E(s); s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s); return re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    줄들 = t.split("\n"); 목 = [l[2:] for l in 줄들 if l.startswith("- ")]
    return "<ul>" + "".join(f"<li>{줄(l)}</li>" for l in 목) + "</ul>" if 목 and len(목) == len([l for l in 줄들 if l.strip()]) else "".join(f"<p>{줄(l)}</p>" for l in 줄들 if l.strip())
def 곡선svg(곡):
    if not 곡: return ""
    W, H, L, R, T, B = 620, 270, 52, 150, 14, 40; 값 = [r["학습"] for r in 곡] + [r["시험"] for r in 곡]; lo, hi = min(값), max(값); 에 = [r["에폭"] for r in 곡]
    x = lambda e: L + (e - 에[0]) / max(에[-1] - 에[0], 1) * (W - L - R); y = lambda v: T + (hi - v) / max(hi - lo, 1e-9) * (H - T - B)
    눈 = "".join(f'<line x1="{L}" x2="{W - R}" y1="{y(v):.1f}" y2="{y(v):.1f}" style="stroke:var(--soft)"/><text x="{L - 8}" y="{y(v) + 4:.1f}" text-anchor="end">{v:.1f}</text>' for v in [lo + (hi - lo) * k / 4 for k in range(5)])
    눈 += "".join(f'<text x="{x(e):.1f}" y="{H - 20}" text-anchor="middle">{e}</text>' for e in 에 if len(에) <= 12 or e % 5 == 0 or e == 1)
    선 = ""; 끝y = {k: y(곡[-1][k]) for k in ("학습", "시험")}
    if abs(끝y["학습"] - 끝y["시험"]) < 20: 가운데 = (끝y["학습"] + 끝y["시험"]) / 2; s_ = 1 if 끝y["학습"] > 끝y["시험"] else -1; 끝y = {"학습": 가운데 + 10 * s_, "시험": 가운데 - 10 * s_}   # 끝 라벨 겹침 풀기
    for 키, 색, 이름 in (("학습", "var(--line1)", "학습 loss"), ("시험", "var(--line2)", "시험 loss")):
        pts = " ".join(f"{x(r['에폭']):.1f},{y(r[키]):.1f}" for r in 곡); 끝 = 곡[-1]
        선 += f'<polyline points="{pts}" fill="none" stroke="{색}" stroke-width="2.4" stroke-linejoin="round"/>' + "".join(f'<circle cx="{x(r["에폭"]):.1f}" cy="{y(r[키]):.1f}" r="3" fill="{색}"/>' for r in 곡)
        선 += f'<text x="{x(끝["에폭"]) + 10:.1f}" y="{끝y[키] + 5:.1f}" style="fill:{색};font-weight:600">{이름} {끝[키]:.2f}</text>'
    return f'<div class="곡선"><svg viewBox="0 0 {W} {H}" role="img" aria-label="에폭별 학습 · 시험 loss">{눈}{선}<text x="{(L + W - R) / 2}" y="{H - 2}" text-anchor="middle">에폭</text></svg></div>'
모션CSS = {
 "도장": """
@media (prefers-reduced-motion:no-preference){
.기준줄{animation:줄 .5s cubic-bezier(.16,1,.3,1) both;animation-delay:calc(var(--i)*120ms + 150ms)}
@keyframes 줄{from{opacity:.15;transform:translateX(-10px)}}
td.결과 svg path{stroke-dasharray:24;stroke-dashoffset:0;animation:긋기 .45s cubic-bezier(.16,1,.3,1) both;animation-delay:calc(var(--i)*120ms + 380ms)}
@keyframes 긋기{from{stroke-dashoffset:24}}
header .판정{animation:도장 .7s cubic-bezier(.16,1,.3,1) both;animation-delay:calc(var(--n)*120ms + 520ms)}
@keyframes 도장{0%{transform:scale(1.35) rotate(-6deg);opacity:0;filter:blur(3px)}60%{transform:scale(.96) rotate(1deg);opacity:1;filter:none}100%{transform:none}}
header .판정{box-shadow:0 6px 18px -8px currentColor}}""",
 "그리기": """
@media (prefers-reduced-motion:no-preference){
.곡선 polyline{stroke-dasharray:var(--len);stroke-dashoffset:0;animation:그림 1.6s cubic-bezier(.16,1,.3,1) both .2s}
@keyframes 그림{from{stroke-dashoffset:var(--len)}}
.곡선 circle{animation:점 .4s ease-out both 1.4s}@keyframes 점{from{opacity:0;r:0}}
td.열{transition:background-color 1.1s cubic-bezier(.16,1,.3,1)}td.열.대기{background:var(--sheet)!important;color:inherit!important}}"""}
모션JS = {"도장": "", "그리기": """<script>(()=>{if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;document.querySelectorAll('.곡선 polyline').forEach(p=>p.style.setProperty('--len',p.getTotalLength()));if(/t=\d/.test(location.hash))return;
document.querySelectorAll('.곡선 polyline').forEach(p=>p.style.setProperty('--len',p.getTotalLength()));
const 셀=[...document.querySelectorAll('td.열')];셀.forEach(c=>c.classList.add('대기'));
const 수=[...document.querySelectorAll('td[data-n]')].filter(t=>t.dataset.n!=='');
const io=new IntersectionObserver(es=>es.forEach(e=>{if(!e.isIntersecting)return;const t=e.target;io.unobserve(t);
 if(t.classList.contains('열')){t.classList.remove('대기');return}
 const v=parseFloat(t.dataset.n),자=(t.dataset.n.split('.')[1]||'').length,t0=performance.now();
 const 걸음=n=>{const k=Math.min(1,(n-t0)/900),e2=1-Math.pow(2,-10*k);t.textContent=(v*e2).toFixed(자);if(k<1)requestAnimationFrame(걸음)};requestAnimationFrame(걸음)}),{threshold:.4});
[...셀,...수].forEach(x=>io.observe(x))})()</script>"""}
미리보기JS = """<script>(()=>{const m=location.hash.match(/t=(\d+)/);if(!m)return;const t=+m[1];   // 필름띠용: #t=밀리초 면 그 시점에 멈춘 모습
requestAnimationFrame(()=>requestAnimationFrame(()=>{document.querySelectorAll('td.열.대기').forEach(c=>c.classList.remove('대기'));
document.querySelectorAll('td[data-n]').forEach(c=>{if(c.dataset.n==='')return;const v=parseFloat(c.dataset.n),자=(c.dataset.n.split('.')[1]||'').length,k=Math.min(1,t/900);c.textContent=(v*(1-Math.pow(2,-10*k))).toFixed(자)});
requestAnimationFrame(()=>document.getAnimations().forEach(a=>{a.pause();a.currentTime=t}))}))})()</script>"""
def 만들기(판, d, c, j, 지, 대, 곡, 특, 해석, 다음, 모션=None, 파일="보고.html", 구=None, 쇼=None):
    말 = j["판정"]; 판정꼴 = "통과" if 말 == "통과" else ("탐색" if 말.startswith("탐색") else "실패")
    바뀐 = ", ".join(f"{k}: {a} → {b}" for k, (a, b) in j["바뀐 손잡이"].items()) or "없음 (재현)"
    meta = [("판", 판), ("가지", c.판.가지), ("종류", c.판.종류), ("바뀐 손잡이", 바뀐), ("에폭", c.학습.에폭), ("대조", c.대조.get("판", "없음") if c.대조 else "없음"), ("git", j["git"]), ("날짜", j.get("날짜", ""))]
    h = [f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>판 {E(판)} · 하네스 보고서</title><style>{CSS}{모션CSS.get(모션, "")}</style></head><body><main style="--n:{len(j["기준"])}">']
    명제 = str(c.판.get("명제") or c.판.물음); 시도 = str(c.판.get("시도") or 명제)
    뒤 = '<nav class="뒤"><a href="../../index.html"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3.5L5.5 8l4.5 4.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>판 목록</a></nav>'
    h.append(f'<header>{뒤}<h1>{E(시도)}</h1><span class="판정 {판정꼴}">{아이콘[판정꼴 != "실패"]}{E(말)}</span>')
    h.append('<dl class="meta">' + "".join(f"<div><dt>{E(k)}</dt><dd>{E(str(v))}</dd></div>" for k, v in meta) + "</dl></header>")
    h.append(f'<h2>판정 기준</h2><p class="명제"><span>명제</span> {E(명제)}</p>')
    h.append('<div class="표"><table><thead><tr><th>지표</th><th>조건</th><th>이 판</th><th>대조</th><th>결과</th></tr></thead><tbody>')
    for i_, r in enumerate(j["기준"]): h.append(f'<tr class="기준줄" style="--i:{i_}"><td>{E(r["지표"])}</td><td>{E(r["식"])} {r["값"]}</td><td><strong>{수(r["이 판"])}</strong></td><td>{수(대.get(r["지표"]))}</td><td class="결과" style="--i:{i_}"><span class="{"o" if r["통과"] else "x"}" aria-label="{"통과" if r["통과"] else "실패"}">{아이콘[r["통과"]]}</span></td></tr>')
    h.append("</tbody></table></div><p class=\"주석\">기준은 돌리기 전에 커밋됐다(하네스 관문이 확인). 대조는 같은 에폭.</p>")
    h.append('<h2>숫자: 이 판과 대조</h2><div class="표"><table><thead><tr><th>지표</th><th>이 판</th><th>대조</th><th>차</th></tr></thead><tbody>')
    for k, v in 지.items():
        b = 대.get(k); 차 = f"{v - b:+.3f}" if isinstance(v, (int, float)) and isinstance(b, (int, float)) else ""
        h.append(f'<tr><td>{E(k)}</td><td data-n="{수(v)}">{수(v)}</td><td>{수(b)}</td><td class="차">{차}</td></tr>')
    h.append("</tbody></table></div>")
    if 구:
        import 구조도
        h.append(f'<h2>모델 구조</h2><div class="구조틀">{구조도.그리기(구, "s1", 구.get("예측"), 촘촘=True)}</div><p class="주석">직육면체는 특징 맵(높이 = 해상도 · 두께 = 채널). 오른쪽은 이 판 모델이 부품 12003 에 실제로 낸 칸별 덩어리와 정답. 총 파라미터 {구["표"]["총 파라미터"]:,} 개 · 층별 수는 아래 표.</p>')
        h.append('<h3>하이퍼파라미터</h3><div class="표"><table><tbody>' + "".join(f'<tr><td>{E(k)}</td><td class="왼">{E(f"{v:,}" if isinstance(v, int) else str(v))}</td></tr>' for k, v in 구["표"].items()) + "</tbody></table></div>")
        h.append('<h3>층 <span class="차">입력 1 × 3 × 128 × 128 을 흘려 잼 · torchinfo 꼴</span></h3><div class="표"><table><thead><tr><th>층</th><th>종류</th><th>출력 모양</th><th>파라미터</th></tr></thead><tbody>' + "".join(f'<tr class="깊{r["깊이"]}"><td>{E(r["이름"])}</td><td class="왼">{E(r["종류"])}</td><td>{E(" × ".join(map(str, r["출력"])))}</td><td>{r["파라미터"]:,}</td></tr>' for r in 구["층"]) + "</tbody></table></div>")
        h.append(f'<h3>목표와 학습</h3><ul class="목표"><li>{E(구["목표"])}</li><li>{E(구["학습"])}</li></ul>')
    h.append("<h2>학습 곡선</h2>" + 곡선svg(곡) + '<figure><img src="시트.png" alt="학습 곡선 · 지표 · 12003 세 장 칸 1 주의"><figcaption>판 시트: 하네스가 판 끝에 만든 그림</figcaption></figure>')
    연 = j.get("연기", {})
    h.append("<h2>점검</h2><h3>연기 판</h3>" + f'<div class="줄글"><div><span>첫 loss</span> <b>{수(연.get("첫loss"))}</b></div><div><span>배치 하나 40 걸음 뒤</span> <b>{수(연.get("한배치40걸음"))}</b></div><div><span>VRAM</span> <b>{수(연.get("VRAM_GB"), 2)} GB</b></div></div>')
    h.append("<h3>층보기 (시험 64 부품 · 4 층)</h3>" + f'<div class="줄글"><div><span>칸끼리 닮음</span> <b>{수(지.get("칸닮음4"))}</b></div><div><span>빈 조각 주의 몫</span> <b>{수(지.get("빈조각주의4"))}</b> <span>(빈 조각 0.54)</span></div><div><span>주의 엔트로피</span> <b>{수(지.get("주의엔트로피4"))}</b></div><div><span>출력 자리 퍼짐</span> <b>{수(지.get("자리퍼짐"))}</b> <span>(정답 0.148)</span></div></div>')
    h.append("<h3>탐침 (합성 그림)</h3>" + f'<div class="줄글"><div><span>블록 4 구조 6 종</span> <b>{수(지.get("탐침_구조"))}</b></div><div><span>블록 4 곡률 R²</span> <b>{수(지.get("탐침_곡률"))}</b></div><div><span>블록 3</span> <b>{수(지.get("탐침3_구조"))} · {수(지.get("탐침3_곡률"))}</b></div></div>')
    if 특:
        이름 = list(특["조각 비율"]); h.append('<h3>특징: 실제 도면에서 곡선 · 접합 · 겹친 곳을 찾나</h3><div class="표"><table><thead><tr><th></th>' + "".join(f"<th>{E(k)}</th>" for k in 이름) + "</tr></thead><tbody>")
        h.append("<tr><td>조각 비율</td>" + "".join(f"<td>{특['조각 비율'][k]:.2f}</td>" for k in 이름) + "</tr>")
        for 층 in (1, 4):
            칸 = "".join(f'<td class="열{" 진" if 특[f"쏠림{층}"][k] > 1.3 else ""}" style="--v:{min(특[f"쏠림{층}"][k], 2) * 35:.0f}">{특[f"쏠림{층}"][k]:.2f}×</td>' for k in 이름)
            h.append(f"<tr><td>주의 쏠림 {층} 층</td>{칸}</tr>")
        for 키, 말2 in (("탐침_학습CNN", "학습 CNN"), ("탐침_무작위CNN", "무작위 CNN"), ("탐침_화소", "화소 그대로")): h.append(f'<tr><td>{말2} 재현율 <span class="차">균형 {특[키][0]:.2f}</span></td>' + "".join(f"<td>{특[키][1][k]:.2f}</td>" for k in 이름) + "</tr>")
        h.append('</tbody></table></div><p class="주석">쏠림 1× = 조각 비율만큼 고르게 봄 · 1 보다 크면 그 조각을 더 봄. 재현율 = CNN 마지막 조각 특징으로 라벨을 맞힌 몫.</p><figure><img src="특징.png" alt="조각 라벨 · 4 층 주의 · 쏠림 · 탐침"><figcaption>12003 조각 라벨(파랑 직선 · 초록 곡선 · 빨강 접합 · 금 실선×숨은선)과 4 층 칸 평균 주의</figcaption></figure>')
    if 쇼 and 쇼.get("편"):
        def 큰(r): t = r.get("큰글", ""); return f' <strong>[{E(t.split(":", 1)[-1])}]</strong>' if t else ""
        대 = "".join(f'<tr><td class="왼">{E(r["누구"])}</td><td class="왼">{E(r["말"])}{큰(r)}</td></tr>' for r in 쇼["대본"])
        영 = '<video class="쇼츠" src="쇼츠.mp4" controls preload="metadata" playsinline></video>' if 쇼.get("웹용") else '<p class="비어">웹용 영상 없음</p>'
        h.append(f'<h2>쇼츠</h2><div class="쇼츠틀">{영}<div class="쇼츠글"><p class="주석">편 {E(쇼["편"])} · {E(쇼["길이"])} · <strong>{E(쇼["상태"])}</strong> · 하네스가 판 끝에 대본(claude -p) · 대본검사 · 맥락 없는 읽기 · 굽기까지</p><div class="표"><table><thead><tr><th>누구</th><th>말</th></tr></thead><tbody>{대}</tbody></table></div></div></div>')
    h.append(f'<h2>해석</h2><div class="사람">{글줄(해석)}</div><h2>다음 가지</h2><div class="사람">{글줄(다음)}</div>')
    import json as _j, os as _o, subprocess as _s
    def 공개커밋(판):   # 공개 저장소는 이력을 걸러 해시가 다름 → 걸러진 사본(out/공개/repo)에서 「판 <판> —」 커밋을 메시지로 찾음
        r = _s.run(["git", "-C", "G:/art2real/out/공개/repo", "log", "-1", "--format=%H", f"--grep=^판 {판} —"], capture_output=True, text=True, encoding="utf-8")
        return f"https://github.com/sigongjoa/art2real/commit/{r.stdout.strip()}" if r.returncode == 0 and r.stdout.strip() else None
    끝 =_j.load(open(d + "끝.json", encoding="utf-8")) if _o.path.exists(d + "끝.json") else {}
    def 고리(제, 주, 없음): return f'<li><span>{E(제)}</span>' + (f'<a href="{E(주)}">{E(주)}</a>' if 주 else f'<em>{E(없음)}</em>') + "</li>"
    h.append(f'<h2>재현</h2><pre>python 하네스/하네스.py --config-name 판_{E(판)}</pre><p class="주석"><a href="설정.yaml">설정.yaml</a> · <a href="판정.json">판정.json</a> · <a href="보고.md">보고.md</a> · 산출 <code>{E(j.get("산출 폴더", ""))}</code></p>')
    h.append('<h2>링크</h2><ul class="고리">' + 고리("쇼츠", (쇼 or {}).get("주소"), (쇼 or {}).get("상태") or "쇼츠 없음") + 고리("GitHub 이슈", 끝.get("이슈"), "아직 없음")
             + 고리("커밋", 공개커밋(판), "아직 공개 안 됨") + 고리("판 목록", "../../index.html", "") + "</ul>")
    h.append(f'</main>{모션JS.get(모션, "")}{미리보기JS if 모션 else ""}</body></html>')
    open(d + 파일, "w", encoding="utf-8").write("".join(h)); return d + 파일
