# 판정기준124 — 복잡한 부품(조립124: 몸 1~6) 12000 으로 학습 · 입력 3면도 셋(123b 와 같은 그림 · 얼린 Gemma) · 머리는 몸 칸 6 개를 냄 · 10-21
# 사용: (cadrille · ART_MEM_GB=10) 모델124.py 짓기 [초] → (gemma) 모델124.py 임베딩 → (cadrille) 모델124.py 학습 → 모델124.py 평가 → out/설명/캐드부품/모델124/
import sys, os, json, time, glob, numpy as np
os.environ.setdefault("ART_CL", "0")
import 모델120 as M, 조립124 as C
D = "G:/art2real/out/설명/캐드부품/모델124/"; NT, NV = 12000, 300; 뷰 = ("위", "앞", "옆"); 배 = 60.
for d in ("도면", "사양", "렌더"): os.makedirs(D + d, exist_ok=True)
D123 = "G:/art2real/out/설명/캐드부품/모델123b/"
def _하나(i):
    import 모델123 as T
    p = D + f"사양/{i:05d}.json"
    if os.path.exists(p): return
    try:
        c = C.무작위(np.random.default_rng(124000 + i)); w = C.짓기(c); assert w.val().isValid(); m = C.메시(w)[0]
        for nm, im in zip(뷰, T.도면(m=m)): M.저장(D + f"도면/{i:05d}_{nm}.png", im)
        json.dump({"i": i, "코드": c, "가운데": [float(x) for x in m.bounds.mean(0)], "크기": float(m.extents.max())}, open(p, "w", encoding="utf-8"), ensure_ascii=False)
    except Exception as ex: json.dump({"i": i, "실패": str(ex)[:80]}, open(p, "w", encoding="utf-8"), ensure_ascii=False)
def 짓기(초=540):
    from multiprocessing import Pool
    일 = [i for i in range(NT + NV) if not os.path.exists(D + f"사양/{i:05d}.json")]; print("남음", len(일), flush=True); t0 = time.time()
    with Pool(6) as p:
        for k, _ in enumerate(p.imap_unordered(_하나, 일, chunksize=4)):
            if time.time() - t0 > 초: p.terminate(); print("멈춤", k, flush=True); return
    print("끝")
def 색인():
    rs = [json.load(open(p, encoding="utf-8")) for p in sorted(glob.glob(D + "사양/*.json"))]; return [r for r in rs if "코드" in r]
def 임베딩():   # 이어 하기 · 8 분 넘으면 멈춤 · 이름도 같이 저장(123 의 조각 이름 없음 위험 막기)
    from sentence_transformers import SentenceTransformer
    import torch
    m = SentenceTransformer("google/embeddinggemma-2", device="cuda", model_kwargs={"torch_dtype": torch.bfloat16}); 이 = [f"{r['i']:05d}" for r in 색인()]
    조 = D + "임베딩_조각.npz"; E, 길이름 = (list(np.load(조)["E"]), list(np.load(조)["길"])) if os.path.exists(조) else ([], []); t0 = time.time(); 길 = [f"{n}_{nm}" for n in 이 for nm in 뷰]
    한 = set(길이름); 할 = [x for x in 길 if x not in 한]   # 이름으로 이어 함(재시도로 살린 부품이 중간에 끼어도 됨)
    while 할:
        b, 할 = 할[:16], 할[16:]; e = m.encode([{"text": "<|image|>", "image": [D + f"도면/{x}.png"]} for x in b], normalize_embeddings=True, batch_size=16)
        E += list(np.asarray(e, np.float32).reshape(len(b), -1)); 길이름 += b
        if len(E) % 1600 < 16: np.savez(조, E=np.stack(E), 길=np.array(길이름)); print(len(E), flush=True)
        if 할 and time.time() - t0 > 480: np.savez(조, E=np.stack(E), 길=np.array(길이름)); print("멈춤", len(E)); return
    np.savez(조, E=np.stack(E), 길=np.array(길이름)); 자 = {x: k for k, x in enumerate(길이름)}
    np.savez(D + "임베딩.npz", E=np.stack([E[자[x]] for x in 길]).reshape(len(이), 3, -1), 이름=np.array(이)); print("끝", len(이))
# ── 과녁 ↔ 사양 · 몸 칸 = 있음 1 · 종류 7 · 치수 9 · 축 3 · 자리 3 · 특징 2×8 · 필렛 2 = 41 ──
W = 41
def 부피(s):
    b = s["바탕"]; return b["w"] * b["d"] * b["h"] if b["종류"] == "상자" else 4 * b["r"] ** 2 * b["h"]
def 과녁(r):
    c = r["코드"]; cen = np.array(r["가운데"]); E = r["크기"]; 칸들 = np.zeros((C.K, W), np.float32); 쓰 = np.zeros((C.K, 9), np.float32)
    for t, s in enumerate(sorted(c["몸"], key=lambda s: -부피(s))):
        g = M.과녁({**s, "기울임": 0.}); 칸들[t, 0] = 1; 칸들[t, 1 + g["k"]] = 1; 칸들[t, 8:17] = g["치"] * 배 / E; 쓰[t] = g["칸쓰"]
        칸들[t, 17 + C.축들.index(s["축"])] = 1; 칸들[t, 20:23] = (np.array(s["자리"]) - cen) / E; 칸들[t, 23:39] = g["특"].ravel(); 칸들[t, 39:41] = g["필"]
    return 칸들, 쓰
def 사양(o):   # 머리 출력(K×W) → 조립 사양(부품 크기 60 기준 · 자리 그대로)
    몸들 = []
    for v in o:
        if 1 / (1 + np.exp(-v[0])) < .5: continue
        f = v[23:39].reshape(2, 8).copy(); f[:, 0] = 1 / (1 + np.exp(-f[:, 0]))
        s = M.사양(int(np.argmax(v[1:8])), v[8:17], f, [1 / (1 + np.exp(-v[39])), float(v[40])], [0, 0])
        s["축"] = C.축들[int(np.argmax(v[17:20]))]; s["자리"] = [float(x) * 60 for x in v[20:23]]; 몸들.append(s)
    if not 몸들: o = np.array(o).copy(); o[int(np.argmax(o[:, 0])), 0] = 9.; return 사양(o)   # 하나도 없으면 가장 있을 법한 칸 하나
    return {"몸": 몸들}
def 망():
    import torch, torch.nn as nn
    torch.manual_seed(0); return nn.Sequential(nn.Linear(2304, 1024), nn.GELU(), nn.Dropout(.1), nn.Linear(1024, 1024), nn.GELU(), nn.Linear(1024, C.K * W))
def 학습():
    import torch, torch.nn as nn
    z = np.load(D + "임베딩.npz"); 색 = {f"{r['i']:05d}": r for r in 색인()}; 이 = list(z["이름"]); E = torch.tensor(z["E"]).reshape(len(이), -1)
    과 = [과녁(색[n]) for n in 이]; Y = torch.tensor(np.stack([a for a, _ in 과])); 쓰 = torch.tensor(np.stack([b for _, b in 과]))
    시험 = np.array([int(n) >= NT for n in 이]); idx = torch.tensor(np.nonzero(~시험)[0]); vx = torch.tensor(np.nonzero(시험)[0]); 고정 = vx[:6]
    net = 망(); opt = torch.optim.AdamW(net.parameters(), 1e-3, weight_decay=1e-4); bce = nn.functional.binary_cross_entropy_with_logits; ce = nn.functional.cross_entropy
    def 손실(o, ix):
        o = o.reshape(-1, C.K, W); y = Y[ix]; 있 = y[..., 0]; n = 있.sum().clamp(min=1); 있f = 있.reshape(-1)
        L = bce(o[..., 0], 있)
        L = L + (ce(o[..., 1:8].reshape(-1, 7), y[..., 1:8].argmax(-1).reshape(-1), reduction="none") * 있f).sum() / n
        L = L + ((o[..., 8:17] - y[..., 8:17]).abs() * 쓰[ix]).sum() / n * 4
        L = L + (ce(o[..., 17:20].reshape(-1, 3), y[..., 17:20].argmax(-1).reshape(-1), reduction="none") * 있f).sum() / n
        L = L + ((o[..., 20:23] - y[..., 20:23]).abs().sum(-1) * 있).sum() / n * 4
        f, g = o[..., 23:39].reshape(-1, C.K, 2, 8), y[..., 23:39].reshape(-1, C.K, 2, 8); g있 = g[..., 0] * 있[..., None]
        L = L + (bce(f[..., 0], g[..., 0], reduction="none") * 있[..., None]).sum() / n
        L = L + (ce(f[..., 1:4].reshape(-1, 3), g[..., 1:4].argmax(-1).reshape(-1), reduction="none") * g있.reshape(-1)).sum() / n + ((f[..., 4:] - g[..., 4:]).abs().sum(-1) * g있).sum() / n * 2
        return L + (bce(o[..., 39], y[..., 39], reduction="none") * 있).sum() / n + ((o[..., 40] - y[..., 40]).abs() * y[..., 39] * 있).sum() / n
    기록 = []; 과정 = {}
    for ep in range(60):
        perm = idx[torch.randperm(len(idx))]; ls = []
        for b in range(0, len(perm), 128): ix = perm[b:b + 128]; opt.zero_grad(); l = 손실(net(E[ix]), ix); l.backward(); opt.step(); ls.append(float(l))
        net.eval()
        with torch.no_grad(): ov = net(E[vx]); lv = float(손실(ov, vx)); 수 = float(((ov.reshape(-1, C.K, W)[..., 0] > 0).sum(1) == Y[vx][..., 0].sum(1)).float().mean())
        net.train(); 기록.append({"에폭": ep + 1, "학습": float(np.mean(ls)), "시험": lv, "몸 수 맞음": 수}); print(기록[-1], flush=True)
        if ep in (0, 2, 5, 10, 20, 40, 59):
            net.eval()
            with torch.no_grad(): 과정[ep + 1] = net(E[고정]).reshape(-1, C.K, W).numpy().tolist()
            net.train()
    torch.save(net.state_dict(), D + "머리.pt")
    json.dump({"기록": 기록, "과정": 과정, "고정": [이[int(i)] for i in 고정]}, open(D + "학습.json", "w", encoding="utf-8"), ensure_ascii=False); print("저장")
def _렌더잡(a):   # (짓기 종류, 사양) → (그림, 실루엣) · 일꾼에서 돎(OCC 가 걸려도 본 프로세스는 안 멈춤)
    import 설계116 as S, 데이터117 as Q
    k, s = a
    try: return Q.렌더(C.메시({"조립": C.짓기, "자리": C.짓기_자리, "단일": S.짓기}[k](s))[0])
    except Exception: return None
def _묶음(잡파일, ks, 칸):   # 일꾼 프로세스 하나 = 잡 여러 개 · 결과를 하나씩 파일로(죽어도 끝낸 것은 남음)
    import pickle
    잡 = pickle.load(open(잡파일, "rb"))
    for k in ks:
        with open(칸 + f"{k}.tmp", "wb") as f: pickle.dump(_렌더잡(잡[k]), f)
        os.replace(칸 + f"{k}.tmp", 칸 + f"{k}.pkl")
def 병렬렌더(잡, 초=60, 묶=8):   # 10-21 Pool 은 OCC 로 일꾼이 죽으면 일이 사라져 47 분 멈춤 → 프로세스 6 개씩 · 묶음 마감 = 초 × 묶 · 못 끝낸 잡은 하나씩 한 번 더 · 그래도 안 되면 None(0 점)
    import pickle, shutil, tempfile
    from multiprocessing import Process
    칸 = tempfile.mkdtemp() + "/"; 잡파일 = 칸 + "잡.pkl"; pickle.dump(잡, open(잡파일, "wb")); 있 = lambda k: os.path.exists(칸 + f"{k}.pkl")
    for 크 in (묶, 1):
        남 = [k for k in range(len(잡)) if not 있(k)]; 묶음들 = [남[b:b + 크] for b in range(0, len(남), 크)]
        for g in range(0, len(묶음들), 6):
            ps = [Process(target=_묶음, args=(잡파일, ks, 칸)) for ks in 묶음들[g:g + 6]]; [q.start() for q in ps]; t0 = time.time()
            for q in ps: q.join(max(1, 초 * 크 - (time.time() - t0))); q.is_alive() and q.terminate()
    out = [pickle.load(open(칸 + f"{k}.pkl", "rb")) if 있(k) else None for k in range(len(잡))]; shutil.rmtree(칸, ignore_errors=True)
    print("걸림·실패", sum(o is None for o in out), "/", len(out), flush=True); return out
def 평가():
    import torch, torch.nn as nn, trimesh, 설계116 as S, 데이터117 as Q, 모델123 as T, 복잡123b as X
    net = 망(); net.load_state_dict(torch.load(D + "머리.pt")); net.eval()
    old = nn.Sequential(nn.Linear(2304, 512), nn.GELU(), nn.Dropout(.1), nn.Linear(512, 512), nn.GELU(), nn.Linear(512, 36)); old.load_state_dict(torch.load(D123 + "머리_셋.pt")); old.eval()
    def 예(Ex):
        x = torch.tensor(np.asarray(Ex, np.float32)).reshape(len(Ex), -1)
        with torch.no_grad(): return net(x).reshape(-1, C.K, W).numpy(), old(x).numpy()
    def 옛사양(oo):
        f = oo[16:32].reshape(2, 8).copy(); f[:, 0] = 1 / (1 + np.exp(-f[:, 0])); 시 = lambda v: float(1 / (1 + np.exp(-v)))
        return M.사양(int(np.argmax(oo[:7])), oo[7:16], f, [시(oo[32]), float(oo[33])], [시(oo[34]), float(oo[35])])
    def 겹(sg, r): return 0. if r is None else round(float((sg & r[1]).sum() / max((sg | r[1]).sum(), 1)), 4)
    def 판(이름들, 정답들, o, oo, 저=True):   # 정답 = (그림, 실루엣) · 예측 124 · 123b 를 한꺼번에 병렬로 지음 → 줄
        새 = [사양(a) for a in o]; 렌 = 병렬렌더([("자리", s) for s in 새] + [("단일", 옛사양(b)) for b in oo]); k = len(새); 줄 = []
        for t, (n, g) in enumerate(zip(이름들, 정답들)):
            if 저 and g is not None: M.저장(D + f"렌더/{n}_정답.png", g[0])
            if 저 and 렌[t] is not None: M.저장(D + f"렌더/{n}_124.png", 렌[t][0])
            줄.append({"이름": n, "예측 몸 수": len(새[t]["몸"]), "124": 0. if g is None else 겹(g[1], 렌[t]), "123b": 0. if g is None else 겹(g[1], 렌[k + t])})
        return 줄
    결 = {}
    z = np.load(D + "임베딩.npz"); 색 = {f"{r['i']:05d}": r for r in 색인()}; 이 = [n for n in z["이름"] if int(n) >= NT]; 전 = list(z["이름"]); o, oo = 예(z["E"][[전.index(n) for n in 이]])
    줄 = 판(이, 병렬렌더([("조립", 색[n]["코드"]) for n in 이]), o, oo)
    for x in 줄: x["몸 수"] = len(색[x["이름"]]["코드"]["몸"])
    결["조립 시험"] = 줄; print("조립", np.median([x["124"] for x in 줄]), np.median([x["123b"] for x in 줄]), flush=True)
    z3 = np.load(D123 + "임베딩.npz"); 이3 = list(z3["이름"]); j3 = json.load(open(D123 + "학습.json", encoding="utf-8")); 입 = {r["이름"]: r for r in json.load(open(M.D119 + "색인.json", encoding="utf-8"))["입력"]}
    단 = [(f"{n:05d}", json.loads(g)) for n, g in zip(j3["번호"], j3["정답"])]; o, oo = 예(z3["E"][[이3.index(n) for n, _ in 단]])
    결["단순 시험"] = 판([n for n, _ in 단], 병렬렌더([("단일", g) for _, g in 단]), o, oo, 저=False); print("단순", np.median([x["124"] for x in 결["단순 시험"]]), flush=True)
    G = list(j3["G 이름"]); o, oo = 예(z3["E"][[이3.index(n) for n in G]])
    정 = [Q.렌더(S.메시(S.짓기(json.loads(입[n]["코드"])))[0] if 입[n]["무리"] == "G1" else trimesh.load(T.R3 + 입[n]["출처"].replace(chr(92), "/"), force="mesh")) for n in G]
    결["G"] = 판(G, 정, o, oo)
    for x in 결["G"]: x["무리"] = 입[x["이름"]]["무리"]
    print("G2", np.median([x["124"] for x in 결["G"] if x["무리"] == "G2"]), flush=True)
    이x = list(X.일); o, oo = 예(np.load(X.D + "임베딩.npy"))
    결["실물"] = 판(["실물_" + n for n in 이x], [Q.렌더(X.메시(n)) for n in 이x], o, oo)
    j = json.load(open(D + "학습.json", encoding="utf-8"))
    키 = [(int(ep), t) for ep, os_ in j["과정"].items() for t in range(len(os_))]
    for (ep, t), r in zip(키, 병렬렌더([("자리", 사양(np.array(j["과정"][str(ep)][t]))) for ep, t in 키])):
        if r is not None: M.저장(D + f"렌더/과정_{ep:02d}_{t}.png", r[0])
    중 = lambda xs: round(float(np.median(xs)), 4)
    요 = {f"{k} {팔}": 중([x[팔] for x in 결[k]]) for k in ("조립 시험", "단순 시험", "실물") for 팔 in ("124", "123b")}
    for 팔 in ("124", "123b"): 요[f"G2 {팔}"] = 중([x[팔] for x in 결["G"] if x["무리"] == "G2"]); 요[f"G1 {팔}"] = 중([x[팔] for x in 결["G"] if x["무리"] == "G1"])
    요["조립 몸 수 맞음"] = float(np.mean([x["몸 수"] == x["예측 몸 수"] for x in 결["조립 시험"]]))
    통 = {"1 조립 ≥ 0.85": 요["조립 시험 124"] >= .85, "2 실물 ≥ 0.60": 요["실물 124"] >= .60, "3 G2 ≥ 0.55": 요["G2 124"] >= .55, "4 단순 ≥ 0.93": 요["단순 시험 124"] >= .93}
    json.dump({"요약": 요, "통과": 통, "부품": 결}, open(D + "결과.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(요, ensure_ascii=False, indent=1), 통)
if __name__ == "__main__":
    f = {"짓기": 짓기, "임베딩": 임베딩, "학습": 학습, "평가": 평가}[sys.argv[1]]; f(*[int(a) for a in sys.argv[2:]])
