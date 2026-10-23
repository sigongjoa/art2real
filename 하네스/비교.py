# 비교판 실행기 — 같은 문제 · 같은 시험 · 같은 공통 자로 여러 방법을 겨룸 · 관문 → 공통 자로 재기 → 결정 규칙 → 결과 페이지(꼴 B: 상황별 틀림 표 → 방법 카드) · 10-23
# 사용(cadrille): python 하네스/비교.py 비교_선판정  → 하네스/비교/<이름>/ · docs/비교/<이름>/
# 참가자 각자는 하네스 판(보고서 · 분석 · 쇼츠)을 그대로 가짐 · 비교판은 그 위에 겹치는 한 장
import os, sys, json, html, shutil, subprocess, time
뿌리 = "G:/art2real"; sys.path.insert(0, 뿌리 + "/하네스"); sys.path.insert(0, 뿌리 + "/원화3d/실험_20261013/캐드부품")
E = html.escape
어댑터 = {"선지도": "선지도판"}   # 과제(목표) → 공통자 어댑터 함수 이름
class 비교거부(Exception): pass
def 설정(이름):
    from omegaconf import OmegaConf
    return OmegaConf.load(f"{뿌리}/하네스/conf/{이름}.yaml")
def 관문(c, 이름):
    from omegaconf import OmegaConf
    import 개념그림
    문 = []
    if not c.비교.get("물음"): 문.append("물음이 없다")
    if not c.비교.get("공통자", {}).get("주지표"): 문.append("주지표가 없다")
    if not c.비교.get("결정", {}).get("문턱"): 문.append("결정 규칙(문턱)이 없다")
    for p in c.참가자:
        d = f"{뿌리}/하네스/판/{p.판}/"
        if not os.path.exists(d + "판정.json"): 문.append(f"{p.판}: 판 기록이 없다 — 하네스로 먼저 돌린다"); continue
        pc = OmegaConf.load(d + "설정.yaml"); 목표 = pc.get("목표", "CAD")
        if 목표 not in 어댑터: 문.append(f"{p.판}: 과제 「{목표}」 의 공통 자 어댑터가 없다")
        if not 개념그림.찾기(pc)[0]: 문.append(f"{p.판}: 개념 그림이 없다(구조 {개념그림.키(pc)})")
    상 = subprocess.run(["git", "-C", 뿌리, "status", "--porcelain", "--", f"하네스/conf/{이름}.yaml"], capture_output=True, text=True).stdout.strip()
    if 상: 문.append(f"비교 설정이 커밋 안 됨 — 결정 규칙은 돌리기 전에 커밋(사전등록)")
    if 문: raise 비교거부("\n  × ".join(["비교판 관문 거부:"] + 문))
def 자해시():
    import hashlib; return hashlib.md5(open(f"{뿌리}/하네스/공통자.py", "rb").read()).hexdigest()[:10]
def 한번(c, 판, 시드):   # 참가자 하나 · 시드 하나의 공통 자 값 — 저장된 값이 같은 자(공통자.py 해시)로 잰 것이면 읽기만
    import 공통자
    from omegaconf import OmegaConf
    경로 = f"{뿌리}/하네스/판/{판}/공통자.json" if 시드 == 0 else f"{뿌리}/out/하네스/비교/{c.비교.이름}/{판}_s{시드}/공통자.json"
    if os.path.exists(경로) and json.load(open(경로, encoding="utf-8")).get("자") == 자해시(): return json.load(open(경로, encoding="utf-8"))
    net = None
    if 시드:   # 같은 판 설정에서 시드만 바꿔 다시 학습(점검 · 보고서 없이 · 이어 하기 됨)
        import 하네스 as H, 과제선지도 as G
        pc = OmegaConf.load(f"{뿌리}/하네스/판/{판}/설정.yaml"); pc.학습.시드 = 시드; X, Y, _, idx, vx, 이, _ = G.자료("cuda", pc)
        net, _ = H.실행(pc, os.path.dirname(경로) + "/", X, Y, None, idx, vx, 이, 해시="비교"); del X, Y
    r, 예, 부품들 = getattr(공통자, 어댑터["선지도"])(판, net)
    if "12050" in 부품들: r["_보기"] = 예[부품들.index("12050"), 1].tolist()
    r["자"] = 자해시(); os.makedirs(os.path.dirname(경로), exist_ok=True); json.dump(r, open(경로, "w", encoding="utf-8"), ensure_ascii=False)
    print(판, "시드", 시드, {k: v for k, v in r.items() if not k.startswith("_")}, flush=True)
    import gc, torch; del net; gc.collect(); torch.cuda.empty_cache(); return r
def 재기(c):   # 참가자마다 시드 0(판 그대로) ~ 시드 n-1 → 평균 · 시드별 주지표
    키 = c.비교.공통자.주지표; out = {}
    for p in c.참가자:
        rs = [한번(c, p.판, s) for s in range(int(c.비교.get("시드", 1)))]
        r = {k: (round(float(sum(x[k] for x in rs) / len(rs)), 4) if isinstance(v, float) else v) for k, v in rs[0].items()}
        r["_시드"] = [x.get(키) for x in rs]; 학 = f"{뿌리}/out/하네스/{p.판}/학습.json"
        r["학습_분"] = round(json.load(open(학, encoding="utf-8"))[-1]["초"] / 60) if os.path.exists(학) else None; out[p.판] = r
    return out
def 결정(c, 값):   # 사전등록 규칙: 1 위 평균 − 2 위 평균 ≥ 문턱 이고 1 위 시드 최저 > 2 위 시드 최고 → 이김 · 아니면 비김(둘 중 학습이 짧은 쪽)
    키 = c.비교.공통자.주지표; 줄 = sorted(((값[p.판].get(키) or 0, p.판) for p in c.참가자), reverse=True); 순 = [b for _, b in 줄]
    (m1, a), (m2, b) = 줄[0], 줄[1]; 차 = m1 - m2
    if min(값[a]["_시드"]) > max(값[b]["_시드"]) and 차 >= c.비교.결정.문턱: return {"판정": "이김", "까닭": f"{a} 평균이 {b} 보다 {차:+.3f} · 시드 {len(값[a]['_시드'])} 번 폭이 안 겹침", "순위": 순, "고름": a}
    싼 = min((a, b), key=lambda k: 값[k].get("학습_분") or 1e9)
    return {"판정": "비김", "까닭": f"1 · 2 위 차 {차:+.3f} · 문턱 {c.비교.결정.문턱} 또는 시드 폭 겹침 → 학습이 짧은 {싼}", "순위": 순, "고름": 싼}
def 보기그림(예지도, 경로):
    import numpy as np
    from PIL import Image
    색 = np.array([[255, 255, 255], [74, 123, 209], [40, 160, 80], [217, 160, 32]], np.uint8)
    Image.fromarray(np.kron(색[np.array(예지도)], np.ones((3, 3, 1), np.uint8))).save(경로)
def 페이지(c, 값, 판정, 폴더):
    import 공통자, 개념그림
    from omegaconf import OmegaConf
    import numpy as np
    상황 = 공통자.상황이름; 키 = c.비교.공통자.주지표
    def 칸색(v): return "" if v is None else ("h0" if v < .12 else "h1" if v < .25 else "h2")
    def 칸(v): return f'<td class="h {칸색(v)}">' + ("—" if v is None else f"{v:.2f}") + "</td>"
    줄 = []
    for p in c.참가자:
        r = 값[p.판]; 줄.append(f'<tr><td><a href="../../판/{E(p.판)}/보고.html">{E(p.이름)}</a>{" <span class=tag>대조</span>" if p.get("역할") == "대조" else ""}</td>'
            + "".join(칸(r.get("틀림_" + s)) for s in 상황)
            + f'<td><b>{r.get(키, 0):.3f}</b><br><span class=note>시드 {" · ".join(f"{v:.3f}" for v in r["_시드"])}</span></td><td>{r["모서리_종류"]:.3f}</td><td>{r["모서리_찾음"]:.3f}</td></tr>')
    수 = 값[c.참가자[0].판]; 머리 = "".join(f"<th>{E(s)}<br><span class=note>{수.get('수_' + s, 0):,} 모서리</span></th>" for s in 상황)
    카드 = []
    for p in c.참가자:
        pc = OmegaConf.load(f"{뿌리}/하네스/판/{p.판}/설정.yaml"); n, mp4 = 개념그림.찾기(pc)
        if mp4: shutil.copy(mp4, 폴더 + f"{n}.mp4")
        if "_보기" in 값[p.판]: 보기그림(값[p.판]["_보기"], 폴더 + f"보기_{p.판}.png")
        카드.append(f'<div class="card"><b>{E(p.이름)}</b>{f"<video src={n}.mp4 autoplay loop muted playsinline></video>" if mp4 else ""}'
                  + (f'<img src="보기_{E(p.판)}.png" alt="부품 12050 앞 뷰 — {E(p.이름)} 의 답">' if os.path.exists(폴더 + f"보기_{p.판}.png") else "")
                  + f'<span class="note">{E(str(pc.판.get("시도", "")))}</span><a href="../../판/{E(p.판)}/보고.html">판 보고서 →</a></div>')
    import 과제선지도 as G, 하네스 as H   # 정답 칸 = 카드들과 같은 부품(12050) 앞 뷰 · 입력 선에 맞춘 정답 지도
    z = np.load(H.M7.D + "그림.npz"); x = z["X"][list(z["이름"]).index("12050")]; d = np.load(f"{뿌리}/out/하네스/선정답/12050.npz")
    보기그림(G.맞춤(x, d["지도"])[1], 폴더 + "정답.png")
    css = """:root{--bg:#f7f6f2;--sheet:#fffefb;--ink:#1d2228;--muted:#5d6570;--rule:#dcd8ce;--good:#1f7a3e;--bad:#b3261e;--warn:#8a5f00;--chip:#eef2f6}
@media (prefers-color-scheme:dark){:root{--bg:#15181c;--sheet:#1c2026;--ink:#e7e4dc;--muted:#a1a8b2;--rule:#333a43;--good:#6fcf8f;--bad:#f08a7e;--warn:#e3b54f;--chip:#232a33;color-scheme:dark}}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 "IBM Plex Sans KR","Malgun Gothic",sans-serif;word-break:keep-all}
main{max-width:1080px;margin:0 auto;padding:40px max(16px,env(safe-area-inset-left,0px)) 80px;display:grid;gap:24px}
h1{margin:0;font-size:clamp(1.6rem,3.4vw,2.2rem)}a{color:inherit}.note{color:var(--muted);font-size:12.5px}.tag{font-size:11px;padding:2px 7px;border-radius:999px;background:var(--chip);color:var(--muted)}
.box{background:var(--sheet);border:1px solid var(--rule);border-radius:12px;padding:18px 20px;min-width:0}
.tbl{overflow-x:auto}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums;font-size:13.5px}th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--rule);white-space:nowrap}th{color:var(--muted);font-weight:600;vertical-align:bottom}
.h0{background:color-mix(in srgb,var(--good) 26%,transparent)}.h1{background:color-mix(in srgb,var(--warn) 24%,transparent)}.h2{background:color-mix(in srgb,var(--bad) 26%,transparent)}
.verdict{display:flex;gap:10px;flex-wrap:wrap;align-items:baseline;font-size:1.05rem}.pill{font-weight:700;font-size:.85rem;padding:4px 12px;border-radius:999px;background:var(--chip)}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}.card{border:1px solid var(--rule);border-radius:10px;padding:12px;background:var(--bg);display:grid;gap:8px;min-width:0}.card video,.card img{width:100%;border-radius:8px;border:1px solid var(--rule)}"""
    글 = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>비교판 {E(c.비교.이름)}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;600;700&display=swap"><style>{css}</style></head><body><main>
<nav><a href="../../index.html">← 판 목록</a></nav>
<header><span class="tag">비교판 · {time.strftime('%Y-%m-%d')}</span><h1>{E(c.비교.물음)}</h1></header>
<div class="verdict"><span class="pill">{E(판정['판정'])}</span><span>{E(판정['까닭'])}</span></div>
<section class="box"><h2 style="margin:0 0 6px;font-size:1.1rem">상황별 — 정답 모서리를 다른 종류로 읽은 비율</h2><p class="note">정답 모서리(CAD 투영)마다 모델이 그 모서리를 찾았고 종류(직선 / 곡선)를 맞혔나 · 상황 = 그 모서리에 2 화소 안으로 붙어 지나는 다른 모서리의 종류 · 초록 &lt; 0.12 · 노랑 &lt; 0.25 · 빨강 그 이상 · 시험 부품 299 · 하네스/공통자.py</p>
<div class="tbl"><table><thead><tr><th>방법</th>{머리}<th>주지표<br><span class=note>직곡 종류 맞힘</span></th><th>종류 전체</th><th>찾음</th></tr></thead><tbody>{"".join(줄)}</tbody></table></div></section>
<section><h2 style="font-size:1.1rem;margin:0 0 10px">방법들 — 개념 그림 · 부품 12050 앞 뷰 답 · 판 보고서</h2><div class="cards"><div class="card"><b>정답</b><img src="정답.png" alt="부품 12050 앞 뷰 정답 지도"><span class="note">파랑 직선 · 초록 곡선 · 노랑 곡면 테</span></div>{"".join(카드)}</div></section>
<p class="note">비교 설정: 하네스/conf/{E(c.비교.이름)} · 결정 규칙(돌리기 전에 커밋): 1 위가 2 위보다 주지표 +{c.비교.결정.문턱} 이상이고 시드 {c.비교.시드} 번의 폭이 안 겹치면 이김 · 아니면 비김 → 싼 쪽.</p>
</main></body></html>"""
    open(폴더 + "index.html", "w", encoding="utf-8").write(글)
def 주(이름):
    c = 설정(이름)
    try: 관문(c, 이름)
    except 비교거부 as e: print(e); sys.exit(2)
    폴더 = f"{뿌리}/하네스/비교/{c.비교.이름}/"; os.makedirs(폴더, exist_ok=True)
    값 = 재기(c); 판정 = 결정(c, 값)
    json.dump({"설정": 이름, "판정": 판정, "값": {k: {a: b for a, b in v.items() if not a.startswith("_") or a == "_시드"} for k, v in 값.items()}, "날짜": time.strftime("%Y-%m-%d %H:%M")}, open(폴더 + "비교.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    페이지(c, 값, 판정, 폴더)
    문서 = f"{뿌리}/docs/비교/{c.비교.이름}/"
    shutil.copytree(폴더, 문서, dirs_exist_ok=True);   # 지우지 않고 덮어씀(지우기는 열린 파일 탓에 WinError 32 로 실패한 적 있음) print("비교판", 판정, 문서 + "index.html")
if __name__ == "__main__": 주(sys.argv[1])
