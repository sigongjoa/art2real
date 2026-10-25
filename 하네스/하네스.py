# 하네스 v0 — 판 하나를 코드가 끌고 감: 관문 → 연기 판 → 실행 → 점검 → 판정 → 기록 · 근거 claudedocs/research_실험하네스_20261022.md · 10-22
# 사용(cadrille venv): python 하네스/하네스.py --config-name 판_127재현   (판 설정은 하네스/conf/판_*.yaml · 바탕.yaml 에서 손잡이 하나만 바꿈)
# 산출: out/하네스/<판>/ (점검점 · tb · 그림) + 하네스/판/<판>/ (설정 · 바뀐 것 · 지표 · 판정 — git 에 남김) + 하네스/results.tsv 한 줄
import os, re, sys, json, time, subprocess, numpy as np, hydra
from omegaconf import OmegaConf
뿌리 = "G:/art2real"; 실험 = 뿌리 + "/원화3d/실험_20261013/캐드부품"; sys.path.insert(0, 실험)
import 모델124 as B, 조립124 as C, 모델127 as M7
손잡이밖 = {"판", "기준", "대조", "점검", "끝", "hydra"}
계산만 = {"학습.미세", "학습.시드", "벡터화.대조손잡이"}   # 대조손잡이: 판 안 대조로 무엇을 끌지(측정 설정 · 143)   # 시드: 판 하나는 늘 0 · 바꾸는 건 비교판의 흔들림 재기뿐(옛 판 설정엔 칸이 없어 None 대 0 이 손잡이로 세지던 것 막음) ·   # 결과가 같은 계산 방식(기울기 누적 조각 · GroupNorm 은 장마다라 같음) — 손잡이로 안 셈
def 펼친(d, 앞=""): return {f"{앞}{k}": v for k0, v0 in d.items() for k, v in (펼친(v0, f"{k0}.").items() if isinstance(v0, dict) else [(k0, v0)])} if isinstance(d, dict) else {앞: d}
class 관문거부(Exception): pass
시작시각 = time.time()   # 기록이 이번 실행이 만든 산출물만 옮기게
# ── ① 관문 ────────────────────────────────────────────────
지표출처 = {"시험loss": None, "학습loss": None, "몸수맞음": None, "칸닮음4": "층보기", "빈조각주의4": "층보기", "주의엔트로피4": "층보기", "자리퍼짐": "층보기",
         "탐침_구조": "탐침", "탐침_곡률": "탐침", "탐침3_구조": "탐침", "탐침3_곡률": "탐침", "탐침4_구조": "탐침", "탐침4_곡률": "탐침",
         "쏠림4_곡선": "특징", "쏠림4_접합": "특징", "쏠림4_빈칸": "특징", "특징탐침": "특징", "특징탐침_무작위": "특징", "시험IoU": "평가", "학습IoU": "평가"}
지표출처 |= {f"{k}{끝}": None for k in ("선_직선", "선_곡선", "선_곡면테", "선_숨음", "선_헛선", "선_자리", "선_자리헛선", "선_종류", "점_정밀", "점_재현", "점_F1") for 끝 in ("", "_화소", "_차")}
지표출처 |= {"선_곡선옆직선오류": None, "선_곡선옆직선오류_화소": None}   # 137~
지표출처 |= {f"벡_{k}{끝}": None for k in ("재현", "정밀", "F1", "종류", "조각", "한선", "끊김", "재현_보임", "종류_보임", "재현_숨", "끊김_숨", "재현_윤곽", "종류_윤곽", "윤곽수") for 끝 in ("", "_정답", "_대조", "_차")} | {"벡_끊김_숨_비": None}   # 140~ 벡터화(학습 없음)
지표출처 |= {f"코드_{k}": None for k in ("실행률", "IoU", "IoU평균", "IoU실행", "OOM", "정답실패", "학습loss", "시험loss")}   # 145~ 코드 생성(모듈이 학습까지 함) · IoU실행 = 실행된 것만 · OOM · 정답실패 = 집계에서 뺀 수(10-25 감사)
지표출처 |= {f"세뷰_{k}": None for k in ("부품", "실패", "겹침몫", "가름", "겹침당모서리")}   # 142~ 세 뷰 짝(학습 없음)
지표출처 |= {f"층{k}_{m}": None for k in (1, 2, 3, 4) for m in ("선_자리", "선_자리헛선", "선_종류", "선_직선", "선_곡선", "점_F1")}   # 선지도 탐침층   # 선지도 과제는 점검이 늘 만듦
식들 = {">=", "<=", ">", "<"}
코드경로 = ["하네스", "원화3d/실험_20261013/캐드부품"]
def 깃(*a): return subprocess.run(["git", "-C", 뿌리, "-c", "core.quotepath=off", *a], capture_output=True, text=True, encoding="utf-8").stdout.rstrip()   # 앞 공백은 남김(porcelain 첫 줄 상태 칸)
def 코드해시(): return 깃("log", "-1", "--format=%h", "--", *(f"{p}/*.py" for p in 코드경로), ":(exclude)하네스/판", ":(exclude)하네스/비교")   # 판 폴더엔 검증/*.py(생성 글)가 커밋됨 — 빼야 함   # 이어 하기 열쇠용 — HEAD 는 하네스 자체 커밋(판 · 링크)만으로 바뀌어 학습이 0 부터 다시 돌았음(134 · 137 점검_옛 · 10-25 감사)
def 관문(cfg, 설정파일, 덮어쓰기=()):
    판 = cfg.판; 대설정 = f"{뿌리}/하네스/판/{cfg.대조.get('손잡이판', cfg.대조.get('판'))}/설정.yaml" if cfg.대조 else ""   # 손잡이판 = 손잡이를 셀 판(에폭을 바꾸는 판은 같은 에폭 대조가 판 안에 있음)   # 대조 판이 하네스 판이면 그 설정과 손잡이를 셈(아니면 바탕)
    바탕 = OmegaConf.to_container(OmegaConf.load(대설정 if 대설정 and os.path.exists(대설정) else f"{뿌리}/하네스/conf/바탕.yaml")); 지금 = OmegaConf.to_container(cfg, resolve=True)
    a, b = (펼친({k: v for k, v in d.items() if k not in 손잡이밖}) for d in (바탕, 지금)); 기본 = 펼친(OmegaConf.to_container(OmegaConf.load(f"{뿌리}/하네스/conf/바탕.yaml"))); a = {**{k: v for k, v in 기본.items() if k in b}, **a}; 바뀐 = {k: (a.get(k), b.get(k)) for k in set(a) | set(b) if a.get(k) != b.get(k) and k not in 계산만}   # 대조 판 이후 생긴 손잡이는 바탕 기본값(= 옛 동작)으로 채움 — 139 가 137 에 없던 「테」를 바꿈으로 셌음
    문 = []
    if not str(cfg.판.get("명제", "") or "").strip() or str(cfg.판.get("명제")) == "???": 문.append("명제가 없다 — 이 판이 맞거나 틀릴 문장 하나를 적어라(사전 예측)")
    시 = str(cfg.판.get("시도", "") or "").strip()
    if not 시 or 시 == "???": 문.append("시도가 없다 — 이 판에서 해 보는 일을 한 문장으로 적어라")
    elif re.search(r"[()（）]|[<>≤≥±]|\d+\.\d", 시) or len(시) > 60: 문.append(f"시도는 괄호 · 숫자 문턱 없이 60 자 안의 한 문장 — 지금: {시[:70]}")
    if not cfg.기준: 문.append("기준이 없다 — 돌리기 전에 기준을 적어라")
    if cfg.대조 and 학습함(cfg) and cfg.대조.get("에폭") != cfg.학습.에폭: 문.append(f"대조 에폭 {cfg.대조.get('에폭')} ≠ 이 판 에폭 {cfg.학습.에폭} — 같은 시점끼리만 비교")
    if not cfg.대조: 문.append("대조가 없다")
    if f"| {판.가지} " not in open(f"{뿌리}/claudedocs/문제트리.md", encoding="utf-8").read(): 문.append(f"가지 {판.가지} 가 문제 트리에 없다")
    n = len(바뀐)
    if 판.종류 == "재현" and n: 문.append(f"재현 판인데 손잡이 {n} 개를 바꿈: {sorted(바뀐)}")
    if 판.종류 == "비교" and n != 1: 문.append(f"비교 판은 손잡이 하나만 — 지금 {n} 개: {sorted(바뀐)} (여럿이면 종류: 탐색)")
    for c in cfg.기준:   # 기준 식 · 지표가 이 판 점검으로 나오는가(돌린 뒤 KeyError · 조용한 실패 막기)
        if c.식 not in 식들: 문.append(f"기준 식 「{c.식}」 은 못 씀 — {sorted(식들)}")
        if c.지표 not in 지표출처: 문.append(f"기준 지표 「{c.지표}」 를 하네스가 만들지 않음")
        elif 지표출처[c.지표] and 지표출처[c.지표] not in cfg.점검: 문.append(f"기준 지표 「{c.지표}」 는 점검 「{지표출처[c.지표]}」 가 있어야 나옴")
    for 파일 in (설정파일, "하네스/conf/바탕.yaml"):
        상 = 깃("status", "--porcelain", "--", 파일)
        if 상: 문.append(f"{파일} 가 커밋 안 됨({상[:2].strip()}) — 설정 · 기준은 돌리기 전에 커밋해야 사전등록")
    if 덮어쓰기: 문.append(f"명령줄 덮어쓰기 {list(덮어쓰기)} — 판 설정 파일에 적고 커밋해야 사전등록 · 재현이 됨")
    더러 = [l for l in 깃("status", "--porcelain", "--", *코드경로).splitlines() if l[:2].strip() and (not l.startswith("??") or l[3:].startswith("하네스/")) and l.rstrip().endswith((".py", ".yaml"))]   # 하네스 안 새 .py 는 커밋 전엔 막음(import 되면 git 해시로 재현 안 됨 · 10-25 감사) · 캐드부품의 실험 낙서 .py 는 그대로 둠
    if 더러: 문.append(f"돌릴 코드가 커밋 안 됨 {len(더러)} 개(예: {더러[0][3:]}) — 기록할 git 해시가 실제 코드와 달라짐")
    import 개념그림   # 10-23 사용자: 개념 설명할 때 움직이는 그림 필수 — 그림 없는 구조는 돌리기 전에 /anatomy 로
    if 개념그림.키(cfg) and not 개념그림.찾기(cfg)[0]: 문.append(f"이 구조({개념그림.키(cfg)})의 개념 그림이 없다 — /anatomy 로 그림(mp4 · gif)을 먼저 만들어 하네스/개념그림/ 에 넣고 개념그림.구조표 에 적는다")
    if 문: raise 관문거부("\n  × ".join(["관문 거부:"] + 문))
    return 바뀐
# ── 부품 등록표 ───────────────────────────────────────────
def 망(cfg):
    if 선지도(cfg): import 과제선지도 as G; return G.망(cfg.인코더, 탐침=bool(cfg.선지도.get("탐침층", False)), 합침=str(cfg.선지도.get("합침", "없음")), 다중=bool(cfg.선지도.get("다중", False)), 시드=int(cfg.학습.get("시드", 0)))
    if cfg.인코더 == "cnn": return M7.망()
    if cfg.인코더 == "cnn4": import 모델129 as M9; return M9.망("c")
    raise KeyError(cfg.인코더)
계산과제 = {"벡터화": "과제벡터화", "세뷰": "과제세뷰", "코드생성": "과제코드"}   # 계산만 하는 과제(140~) — 자료 · 연기 · 학습 없이 점검만
def 학습함(cfg): return cfg.get("목표", "CAD") not in 계산과제
def 선지도(cfg): return cfg.get("목표", "CAD") == "선지도"   # 과제: CAD(덩어리 숫자) | 선지도(CNN 만 · 하네스/과제선지도.py)
def 모(cfg, o): return o if 선지도(cfg) else o.reshape(-1, C.K, B.W)
def 잘(cfg, Y, 쓰, ix):
    if 선지도(cfg): import 과제선지도 as G; return G.자르기(Y, ix), None
    return Y[ix], 쓰[ix]
def 손실함수(cfg):
    import 손실그림124 as L
    if 선지도(cfg): import 과제선지도 as G; return G.손실함수(cfg.선지도.빈가중, str(cfg.선지도.get("테", "구분")), bool(cfg.선지도.get("다중", False)))
    if cfg.짝 == "부피순": return lambda o, Y, 쓰: sum(L.항목(o, Y, 쓰).values())
    if cfg.짝 == "헝가리안":
        import 모델129 as M9
        def f(o, Y, 쓰): y, s = M9.바꾼과녁(o, Y, 쓰); return sum(L.항목(o, y, s).values())
        return f
    raise KeyError(cfg.짝)
def 자료(dev, cfg=None):
    import torch
    if cfg is not None and 선지도(cfg): import 과제선지도 as G; return G.자료(dev, cfg)
    z = np.load(M7.D + "그림.npz"); 이 = list(z["이름"]); 색 = {f"{r['i']:05d}": r for r in B.색인()}; 과 = [B.과녁(색[n]) for n in 이]
    X = torch.tensor(z["X"]).to(dev); Y = torch.tensor(np.stack([a for a, _ in 과])).to(dev); 쓰 = torch.tensor(np.stack([b for _, b in 과])).to(dev)
    시 = np.array([int(n) >= B.NT for n in 이]); return X, Y, 쓰, torch.tensor(np.nonzero(~시)[0]), torch.tensor(np.nonzero(시)[0]), 이, z["X"]
# ── ② 연기 판 ─────────────────────────────────────────────
def 연기(cfg, X, Y, 쓰, idx):
    import torch
    torch.cuda.reset_peak_memory_stats(); net = 망(cfg).cuda(); f = 손실함수(cfg); opt = torch.optim.AdamW(net.parameters(), 1e-3); ix = idx[:cfg.학습.미세]
    본 = (lambda o: o[:, :, :6]) if 선지도(cfg) else (lambda o: o)   # 채점은 본 머리만(134: 일부러 느린 탐침 머리 손실까지 더해 52 % 로 걸림) · 학습은 전체 손실
    y, s = 잘(cfg, Y, 쓰, ix); l0 = float(f(본(모(cfg, net(X[ix]))), y, s)); assert np.isfinite(l0), "연기: 첫 loss 가 수가 아님"
    for _ in range(40): opt.zero_grad(); l = f(모(cfg, net(X[ix])), y, s); l.backward(); opt.step()
    with torch.no_grad(): l = f(본(모(cfg, net(X[ix]))), y, s)
    값 = {"첫loss": round(l0, 3), "한배치40걸음": round(float(l), 3), "VRAM_GB": round(torch.cuda.max_memory_allocated() / 2**30, 2)}
    assert 값["한배치40걸음"] < 0.5 * l0, f"연기: 배치 하나를 못 외움 {값}"; assert 값["VRAM_GB"] < 7.0, f"연기: VRAM {값['VRAM_GB']} GB"
    del net, opt; torch.cuda.empty_cache(); return 값
# ── ③ 실행 ────────────────────────────────────────────────
def 열쇠(cfg, 해시):   # 이어 하기는 같은 설정 · 같은 코드일 때만
    import hashlib; d = {k: v for k, v in OmegaConf.to_container(cfg, resolve=True).items() if k not in 손잡이밖 or k == "판"}
    d["판"] = {"이름": cfg.판.이름}; return hashlib.sha1((json.dumps(d, sort_keys=True, ensure_ascii=False) + 해시).encode()).hexdigest()[:12]
def 실행(cfg, 폴더, X, Y, 쓰, idx, vx, 이, 해시=""):
    import torch, shutil
    from torch.utils.tensorboard import SummaryWriter
    키 = 열쇠(cfg, 해시)
    if os.path.exists(폴더 + "점검/마지막.pt") and torch.load(폴더 + "점검/마지막.pt", weights_only=False).get("열쇠") != 키:   # 다른 설정 · 코드의 옛 점검점은 쓰지 않고 치워 둠
        옛 = 폴더 + f"점검_옛_{time.strftime('%m%d_%H%M%S')}"; shutil.move(폴더 + "점검", 옛); shutil.rmtree(폴더 + "tb", ignore_errors=True); print("옛 점검점 치움 →", 옛, flush=True)
    os.makedirs(폴더 + "점검", exist_ok=True); net = 망(cfg).cuda(); opt = torch.optim.AdamW(net.parameters(), cfg.학습.학습률, weight_decay=cfg.학습.감쇠); f = 손실함수(cfg); tb = SummaryWriter(폴더 + "tb")
    기록, 시작, t0 = [], 0, time.time()
    if os.path.exists(폴더 + "점검/마지막.pt"):
        k = torch.load(폴더 + "점검/마지막.pt", weights_only=False); net.load_state_dict(k["모델"]); opt.load_state_dict(k["옵티"]); 시작, 기록 = k["에폭"], k["기록"]; torch.set_rng_state(k["rng"]); print("이어 함", 시작, flush=True)
    for ep in range(시작, cfg.학습.에폭):
        net.train(); perm = idx[torch.randperm(len(idx))]; ls = []
        for b in range(0, len(perm), cfg.학습.배치):
            ix = perm[b:b + cfg.학습.배치]; opt.zero_grad(); lt = 0.
            for c in range(0, len(ix), cfg.학습.미세): jx = ix[c:c + cfg.학습.미세]; l = f(모(cfg, net(X[jx])), *잘(cfg, Y, 쓰, jx)) * len(jx) / len(ix); l.backward(); lt += float(l)
            opt.step(); ls.append(lt)
        net.eval()
        with torch.no_grad():
            ov = 모(cfg, torch.cat([net(X[vx[i:i + 16]]) for i in range(0, len(vx), 16)])); yv, sv = 잘(cfg, Y, 쓰, vx); lv = float(f(ov, yv, sv))   # 16 개씩(137 네 층 합침은 50 개면 1.1 GB · 결과는 같음)
            if 선지도(cfg): ov = __import__("과제선지도").읽기(ov) if net.다중 else ov; 수 = {"선맞음": float((ov[:, :, :4].argmax(2)[yv["지도"] > 0] == yv["지도"][yv["지도"] > 0]).float().mean())}   # 선 화소 종류 맞음
            else: 수 = {"몸수맞음": float(((ov[..., 0] > 0).sum(1) == yv[..., 0].sum(1)).float().mean())}
        기록.append({"에폭": ep + 1, "학습": float(np.mean(ls)), "시험": lv, **수, "초": round(time.time() - t0)}); print(기록[-1], flush=True)
        for k_, v_ in 기록[-1].items(): k_ != "에폭" and tb.add_scalar(k_, v_, ep + 1)
        torch.save(net.state_dict(), 폴더 + f"점검/{ep + 1:02d}.pt"); torch.save({"모델": net.state_dict(), "옵티": opt.state_dict(), "에폭": ep + 1, "기록": 기록, "rng": torch.get_rng_state(), "열쇠": 키}, 폴더 + "점검/마지막.pt.tmp"); os.replace(폴더 + "점검/마지막.pt.tmp", 폴더 + "점검/마지막.pt")   # 쓰다 꺼져도 반쪽 파일이 안 남게
    tb.close(); json.dump(기록, open(폴더 + "학습.json", "w", encoding="utf-8"), ensure_ascii=False); return net, 기록
# ── ④ 점검 ────────────────────────────────────────────────
def 주의그림(x, w, 폴더, 폭=640):   # 쇼츠 카드용 큰 그림: 도면(흰 바탕 검은 선) 위에 모델이 보는 칸을 빨갛게 · 뷰마다 주의_<뷰>.png · 도면만 도면_<뷰>.png
    from PIL import Image
    for v in range(3):
        선 = np.kron(255 - x[v].astype(np.uint8), np.ones((폭 // 128, 폭 // 128), np.uint8)); Image.fromarray(선).save(폴더 + f"도면_{B.뷰[v]}.png")
        a = np.kron(w[v] / w.max(), np.ones((폭 // 8, 폭 // 8)))[..., None]; 바탕 = np.repeat(선[..., None], 3, 2).astype(float)
        Image.fromarray((바탕 * (1 - .6 * a) + np.array([230, 40, 40]) * .6 * a).astype(np.uint8)).save(폴더 + f"주의_{B.뷰[v]}.png")
def 점검(cfg, 폴더, net, 기록, Xnp, 이):
    import torch, 층보기127 as V, 탐침128 as P
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; plt.rcParams["font.family"] = "Malgun Gothic"
    지 = {"시험loss": round(기록[-1]["시험"], 4), "학습loss": round(기록[-1]["학습"], 4), "몸수맞음": round(기록[-1]["몸수맞음"], 4)}; net = net.cpu().eval()
    색 = {f"{r['i']:05d}": r for r in B.색인()}; 통 = [n for n in 이 if int(n) >= B.NT][:64]
    X통 = torch.tensor(Xnp[[이.index(n) for n in 통]]); Y통 = np.stack([B.과녁(색[n])[0] for n in 통]); 빈 = torch.tensor(Xnp[[이.index(n) for n in 통]].reshape(64, 3, 8, 16, 8, 16).max((3, 5)) < 40).reshape(64, 192).float()
    if "층보기" in cfg.점검:
        with torch.no_grad(): s = V.통계(V.펼침(net, X통), Y통, 빈)
        지 |= {"칸닮음4": round(s["층4 칸 닮음"], 4), "빈조각주의4": round(s["층4 빈 조각 몫"], 4), "주의엔트로피4": round(s["층4 주의 엔트로피"], 4), "자리퍼짐": round(s["출력 자리 퍼짐"], 4)}
    if "탐침" in cfg.점검:
        rng = np.random.default_rng(128); 자 = [(k, *P.한장(종, rng, 128)) for k, 종 in enumerate(P.종들) for _ in range(600)]
        y = np.array([a[0] for a in 자]); rr = np.array([a[3] for a in 자]); F = P.특징(net, [a[1] for a in 자], [a[2] for a in 자], 128)
        idx = np.random.default_rng(0).permutation(len(y)); 학, 시 = idx[:2400], idx[2400:]; 곡 = y == 1
        for b in (3, 4): 지[f"탐침{b}_구조"] = P.릿지(F[f"블록 {b}"], y, 학, 시, True); 지[f"탐침{b}_곡률"] = P.릿지(F[f"블록 {b}"], np.log(rr), 학[곡[학]], 시[곡[시]], False)
        지["탐침_구조"], 지["탐침_곡률"] = 지["탐침4_구조"], 지["탐침4_곡률"]
    import 구조 as 구, 구조도; 구s = 구.재기(net, cfg); 구s["예측"] = 구조도.재료(net, 폴더, Xnp, 이)   # 모델 구조(판마다 그 판 모델에서) · 구조도 재료(입력 · 칸별 예측 렌더 · 정답)
    json.dump(구s, open(폴더 + "구조.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if "특징" in cfg.점검:   # 실제 3면도에서 주의 · CNN 이 곡선 · 접합 · 겹친 곳을 찾나(하네스/특징.py)
        import 특징 as T; t = T.재기(net, Xnp, 이, 폴더); json.dump(t, open(폴더 + "특징.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        지 |= {"쏠림4_곡선": t["쏠림4"]["곡선"], "쏠림4_접합": t["쏠림4"]["접합·교차"], "쏠림4_빈칸": t["쏠림4"]["빈칸"], "특징탐침": t["탐침_학습CNN"][0], "특징탐침_무작위": t["탐침_무작위CNN"][0]}
    if "평가" in cfg.점검:
        import 모델125 as T5
        T5.평가(net, lambda ns: torch.tensor(Xnp[[이.index(n) for n in ns]]), 폴더); r = json.load(open(폴더 + "결과.json", encoding="utf-8")); 지 |= {"시험IoU": r["시험"]["IoU 중앙"], "학습IoU": r["학습"]["IoU 중앙"]}
    # 시트 한 장: 곡선 · 지표 대 대조 · 12003 세 장 칸 1 주의
    fig = plt.figure(figsize=(22, 10)); fig.suptitle(f"판 {cfg.판.이름} · 가지 {cfg.판.가지} · {cfg.판.종류} — {cfg.판.물음}", fontsize=17, weight="bold")
    a = fig.add_axes([.04, .55, .28, .35]); e = [r["에폭"] for r in 기록]; a.plot(e, [r["학습"] for r in 기록], "o-", label="학습 loss"); a.plot(e, [r["시험"] for r in 기록], "o-", label="시험 loss"); a.legend(); a.set_title("학습 곡선"); a.grid(alpha=.3)
    a = fig.add_axes([.38, .55, .28, .35]); a.axis("off"); 대 = dict(cfg.대조.get("값", {})) if cfg.대조 else {}
    a.text(0, 1, f"{'지표':12s} {'이 판':>9s} {'대조':>9s}", fontsize=13, family="Malgun Gothic", weight="bold", va="top")
    for k, (n, v) in enumerate(지.items()): a.text(0, .92 - k * .06, f"{n:12s} {v:9.3f} {대.get(n, float('nan')):9.3f}", fontsize=12, va="top")
    n = "12003"; x = torch.tensor(Xnp[[이.index(n)]])
    with torch.no_grad(): d = V.펼침(net, x)
    w = d["주의4"][0, 0].numpy().reshape(3, 8, 8); 주의그림(Xnp[이.index(n)], w, 폴더)
    for v in range(3):
        a = fig.add_axes([.04 + v * .21, .04, .19, .45]); a.imshow(Xnp[이.index(n), v], cmap="gray"); a.imshow(np.kron(w[v] / w.max(), np.ones((16, 16))), cmap="viridis", alpha=.6, vmin=0, vmax=1); a.axis("off"); a.set_title(f"{n} {B.뷰[v]} · 4 층 칸1 주의 {w[v].sum():.2f}", fontsize=12)
    fig.savefig(폴더 + "시트.png", dpi=60); plt.close(fig); return 지
# ── ⑤ 판정 · ⑥ 기록 ──────────────────────────────────────
여유들 = {"코드생성": 0.12}; 여유 = 0.05   # 시드 0 값이 기준 ± 이 안이면 시드 1 · 2 를 더 돎(최대 3 번 · 10-25 사용자) · 기준마다 「여유:」 로 바꿈
# 근거(시드 사이 폭): 146 시드 0 → 1 실행률 0.890 → 0.776 · IoU 0.500 → 0.441(같은 시드 재실행 ±0.02 와 다름 · 10-25 147 세션) · 선판정 비교판 시드 셋 폭 약 0.04 · ponytail: 시드 둘 · 셋에서 잰 폭 — 시드가 쌓이면 다시 잼
def 가까움(cfg, 지): return any(isinstance(v := 지.get(c.지표), (int, float)) and abs(v - c.값) <= float(c.get("여유", 여유들.get(cfg.get("목표"), 여유))) for c in cfg.기준)
def 시드돌기(cfg, 폴더, 한판):   # 한판(설정, 폴더) → 지표 · 시드 0 이 기준에 가까울 때만 시드 1 · 2(폴더/시드<n>/) · 학습 없는 계산 판은 부르지 않음
    지들 = [한판(cfg, 폴더)]
    if 가까움(cfg, 지들[0]):
        for s in (1, 2):
            print(f"시드 0 이 기준 여유 안 — 시드 {s} 도 돎", flush=True); c = OmegaConf.create(OmegaConf.to_container(cfg, resolve=True)); c.학습.시드 = s; 지들.append(한판(c, 폴더 + f"시드{s}/"))
    return 지들
def 평균(지들): return {k: (round(float(np.mean([d[k] for d in 지들])), 4) if all(isinstance(d.get(k), (int, float)) and not isinstance(d.get(k), bool) for d in 지들) else v) for k, v in 지들[0].items()}
def 판정(cfg, 지들):   # 지들 = 시드마다 지표(하나면 dict 도 됨) · 모든 시드 통과 = 통과 · 모두 못 넘음 = 실패 · 갈리면 흔들림(이김 · 짐을 말하지 않음)
    지들 = [지들] if isinstance(지들, dict) else 지들; 줄 = []
    for c in cfg.기준:
        vs = [d.get(c.지표) for d in 지들]; oks = [v is not None and {">=": v >= c.값, "<=": v <= c.값, ">": v > c.값, "<": v < c.값}[c.식] for v in vs]
        줄.append({"지표": c.지표, "식": c.식, "값": c.값, "이 판": 평균(지들).get(c.지표), "통과": all(oks), "흔들림": any(oks) and not all(oks), "목표선": bool(c.get("목표선", False)), **({"시드값": vs} if len(vs) > 1 else {})})
    명 = [r for r in 줄 if not r["목표선"]] or 줄; 목 = [r for r in 줄 if r["목표선"]]   # 판정은 명제 기준만 · 목표선(프로젝트 목표치)은 따로 셈 — 130~139 가 목표선 하나로 전부 「실패」라 가설이 틀린 건지 가를 수 없었음(10-25 감사)
    전 = all(r["통과"] for r in 명); 흔 = any(r["흔들림"] for r in 명)
    결 = "통과" if 전 else (f"흔들림 — 시드 {len(지들)} 번이 기준 양쪽" if 흔 else "실패")
    말 = (결 if cfg.판.종류 != "탐색" else ("탐색 — 이김 판정 없음 · " + ("기준 넘음" if 전 else "기준 흔들림" if 흔 else "기준 못 넘음"))) + (f" · 목표선 {sum(r['통과'] for r in 목)}/{len(목)}" if 목 else "")
    return {"판정": 말, "기준": 줄, **({"시드지표": 지들} if len(지들) > 1 else {})}
def 기록(cfg, 폴더, 바뀐, 연, 지, 판, 해시):   # 해시 = 돌리기 시작할 때의 커밋(관문이 코드 깨끗함을 확인)
    남 = f"{뿌리}/하네스/판/{cfg.판.이름}/"; os.makedirs(남, exist_ok=True)
    OmegaConf.save(cfg, 남 + "설정.yaml"); json.dump({"바뀐 손잡이": {k: list(v) for k, v in 바뀐.items()}, "git": 해시, "날짜": time.strftime("%Y-%m-%d %H:%M"), "연기": 연, "지표": 지, **판, "산출 폴더": 폴더}, open(남 + "판정.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    import shutil
    for 파 in ("시트.png", "학습.json", "특징.json", "특징.png", "구조.json", "입력_위.png", "입력_앞.png", "입력_옆.png", "칸1.png", "칸2.png", "칸3.png", "칸4.png", "칸5.png", "칸6.png", "예측전체.png", "정답.png", "검증.json", "검증.png", *(f"{종}_{뷰}.png" for 종 in ("도면", "주의") for 뷰 in B.뷰)):
        if os.path.exists(폴더 + 파) and os.path.getmtime(폴더 + 파) >= 시작시각: shutil.copy(폴더 + 파, 남 + 파)   # 이번 실행이 만든 것만 — 앞 판의 특징.json 등이 새 보고서에 섞였음(10-25 감사)
    if os.path.isdir(폴더 + "검증"): shutil.copytree(폴더 + "검증", 남 + "검증", dirs_exist_ok=True, ignore=shutil.ignore_patterns("*.err"))   # 코드생성 스텝별 검증(글 · 렌더)
    import 개념그림; 개념그림.넣기(cfg, 남)   # 개념.mp4 · 개념.gif → 판 폴더(보고서 「모델 동작」)
    try: import 보고; print("보고서", 보고.만들기(cfg.판.이름))
    except Exception as e: print("⚠ 보고서 실패 — 표 · 끝 단계는 계속(끝 단계가 다시 만듦)", repr(e)[:300], flush=True)   # 145 가 여기서 죽어 판정만 있고 표 · 커밋이 없었음
    표 = f"{뿌리}/하네스/results.tsv"; 머리 = "날짜\t판\t가지\t종류\t바뀐 손잡이\t판정\t시험loss\t탐침_구조\t탐침_곡률\t칸닮음4\tgit\t기준값\n"
    줄들 = open(표, encoding="utf-8").read().splitlines()[1:] if os.path.exists(표) else []
    줄들 = [l for l in 줄들 if l.split("\t")[1:2] != [cfg.판.이름]]   # 같은 판을 다시 돌리면 그 줄을 바꿈(옛 값은 git 이력에) — 두 줄씩 쌓여 판 수가 부풀었음
    기준값 = ",".join(f"{c.지표}={지.get(c.지표)}" for c in cfg.기준)   # 판정에 쓴 지표 — 코드 판은 시험loss 칸만으론 비교가 안 됐음
    줄들.append(f"{time.strftime('%m-%d %H:%M')}\t{cfg.판.이름}\t{cfg.판.가지}\t{cfg.판.종류}\t{','.join(f'{k}={v[1]}' for k, v in 바뀐.items()) or '-'}\t{판['판정']}\t{지.get('시험loss')}\t{지.get('탐침_구조')}\t{지.get('탐침_곡률')}\t{지.get('칸닮음4')}\t{해시}\t{기준값}")
    open(표, "w", encoding="utf-8").write(머리 + "".join(l + "\n" for l in 줄들))
    import 끝; print("끝 단계", json.dumps(끝.끝내기(cfg.판.이름, tuple(cfg.get("끝", []))), ensure_ascii=False)[:600])
@hydra.main(version_base=None, config_path="conf")
def 주(cfg):
    import torch
    hc = hydra.core.hydra_config.HydraConfig.get(); 설정파일 = f"하네스/conf/{hc.job.config_name}.yaml"
    try: 바뀐 = 관문(cfg, 설정파일, tuple(hc.overrides.task))
    except 관문거부 as e: print(e); sys.exit(2)
    if os.name == "nt" and not os.environ.get("ART_MEM_CAPPED") and os.environ.get("ART_MEM_GB") != "0": print("메모리 상한이 안 걸린 파이썬 — cadrille venv(sitecustomize)로 돌리거나 ART_MEM_GB=0 으로 일부러 끈다"); sys.exit(2)   # 10-15 PC 다운
    해시 = 깃("rev-parse", "--short", "HEAD"); 코해 = 코드해시(); print("관문 통과 · 바뀐 손잡이", {k: v[1] for k, v in 바뀐.items()}, "· git", 해시, flush=True)
    폴더 = f"{뿌리}/out/하네스/{cfg.판.이름}/"; os.makedirs(폴더, exist_ok=True)
    if not 학습함(cfg):   # 계산만 하는 판: 점검(입력 판 모델 예측 → 계산 → 정답과 맞춤 · 대조는 판 안에서) → 판정 · 기록 · 끝 단계는 같음
        V = __import__(계산과제[cfg.목표])
        def 한판(c, 폴): os.makedirs(폴, exist_ok=True); 지 = V.점검(c, 폴); torch.cuda.empty_cache(); return 지
        지들 = 시드돌기(cfg, 폴더, 한판) if cfg.목표 == "코드생성" and not cfg.get("코드", {}).get("LoRA") else [한판(cfg, 폴더)]   # 다른 판 LoRA 를 읽는 판(149~)은 학습 없음 · 탐욕이라 결정적 · 코드생성은 안에서 학습함(시드가 결과를 바꿈) · 벡터화 · 세뷰는 결정적
        판 = 판정(cfg, 지들); 기록(cfg, 폴더, 바뀐, {}, 평균(지들), 판, 해시)
        print("판정", json.dumps(판, ensure_ascii=False), flush=True); return
    X, Y, 쓰, idx, vx, 이, Xnp = 자료("cuda", cfg)
    연 = 연기(cfg, X, Y, 쓰, idx) if "연기" in cfg.점검 else {}; print("연기 판 통과", 연, flush=True)
    def 한판(c, 폴):
        os.makedirs(폴, exist_ok=True); net, 록 = 실행(c, 폴, X, Y, 쓰, idx, vx, 이, 코해)
        if 선지도(c):   # 점검 = 지표 + 같은 에폭 화소 대조(같은 머리) · 그림
            import 과제선지도 as G; 지 = G.점검(c, 폴, net, 록, X, Y, vx, 이, Xnp, lambda c2, 폴2: 실행(c2, 폴2, X, Y, 쓰, idx, vx, 이, 코해))
        else: 지 = 점검(c, 폴, net, 록, Xnp, 이)
        del net; import gc; gc.collect(); torch.cuda.empty_cache(); return 지
    지들 = 시드돌기(cfg, 폴더, 한판)
    del X, Y, 쓰; import gc; gc.collect(); torch.cuda.empty_cache()   # 끝 단계 쇼츠 TTS 가 GPU 를 씀 — 안 비우면 130 ~ 136 쇼츠 7 편이 굽기 실패(10-22)
    판 = 판정(cfg, 지들); 지 = 평균(지들); 기록(cfg, 폴더, 바뀐, 연, 지, 판, 해시)
    print("판정", json.dumps(판, ensure_ascii=False), flush=True)
if __name__ == "__main__":
    주()
