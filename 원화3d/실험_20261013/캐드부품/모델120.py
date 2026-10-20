# 판정기준120 — 얼린 EmbeddingGemma 2 그림 임베딩 위에 CAD 코드 사양을 내는 머리(MLP)를 학습 · 10-20
# 사용: (cadrille venv · ART_MEM_GB=12) 모델120.py 짓기 → (gemma venv) 모델120.py 임베딩 → (gemma) 모델120.py 학습 → (cadrille) 모델120.py 평가 → out/설명/캐드부품/모델120/
import sys, os, json, numpy as np
D = "G:/art2real/out/설명/캐드부품/모델120/"; D119 = "G:/art2real/out/설명/캐드부품/어려움119/"; os.makedirs(D + "렌더", exist_ok=True)
NT, NV = 6000, 200
종류들 = ["상자", "원기둥", "원뿔", "돔", "컵", "계단축", "그릇"]; 칸 = ["w", "d", "h", "r", "안r", "바닥", "r2", "h1", "두께"]; 쓰는칸 = {"상자": "w d h", "원기둥": "r h", "원뿔": "r h", "돔": "r h", "컵": "r h 안r 바닥", "계단축": "r h r2 h1", "그릇": "r h 두께"}
특종 = ["관통", "막힌", "홈"]; 평 = ("상자", "원기둥", "컵", "계단축"); 배 = 60.
def 저장(p, img):
    import cv2; cv2.imencode(".png", img[..., ::-1])[1].tofile(p)
def 읽(p):
    import cv2; return cv2.imdecode(np.fromfile(p, np.uint8), 1)[..., ::-1].copy()
# 사양 ↔ 과녁 벡터
def 과녁(s):
    b = s["바탕"]; k = 종류들.index(b["종류"]); 치 = np.array([b.get(c, 0.) / 배 for c in 칸], np.float32); 칸쓰 = np.array([c in 쓰는칸[b["종류"]].split() for c in 칸], np.float32)
    구 = sorted([f for f in s["특징"] if f["종류"] != "필렛"], key=lambda f: f["x"])[:2]; 특 = np.zeros((2, 8), np.float32)   # 있음 · 종류 원핫 3 · x y 크기 깊이
    for i, f in enumerate(구): 특[i] = [1, *(np.eye(3)[특종.index(f["종류"])]), f["x"], f["y"], f["크기"], f["깊이"]]
    필 = [f for f in s["특징"] if f["종류"] == "필렛"]; 기 = s["기울임"]
    return dict(k=k, 치=치, 칸쓰=칸쓰, 특=특, 필=np.array([len(필) > 0, 필[0]["크기"] / 5 if 필 else 0], np.float32), 기=np.array([기 > 0, 기 / 35], np.float32))
def 사양(k, 치, 특, 필, 기):   # 예측 → 설계116 사양(생성기 범위로 자름)
    kind = 종류들[k]; b = {"종류": kind}
    for c in 쓰는칸[kind].split(): b[c] = float(max(치[칸.index(c)] * 배, 1.))
    if kind == "컵": b["안r"] = min(b["안r"], .9 * b["r"]); b["바닥"] = min(b["바닥"], .8 * b["h"])
    if kind == "계단축": b["r2"] = min(b["r2"], .9 * b["r"]); b["h1"] = min(b["h1"], .9 * b["h"])
    if kind == "그릇": b["두께"] = float(np.clip(b["두께"], 1., .5 * b["r"]))
    s = {"바탕": b, "특징": [], "기울임": float(np.clip(기[1] * 35, 0, 40)) if 기[0] > .5 else 0.}
    if kind in 평:
        for f in 특:
            if f[0] > .5: s["특징"].append({"종류": 특종[int(np.argmax(f[1:4]))], "x": float(np.clip(f[4], -.4, .4)), "y": float(np.clip(f[5], -.4, .4)), "크기": float(np.clip(f[6], .05, .2)), "깊이": float(np.clip(f[7], .2, .8))})
    if kind == "상자" and 필[0] > .5: s["특징"].append({"종류": "필렛", "크기": float(np.clip(필[1] * 5, 1., 5.))})
    return s
def _하나(i):
    import 설계116 as S, 데이터117 as Q
    rng = np.random.default_rng(120000 + i); s = S.무작위(rng)
    try:
        w = S.짓기(s); assert w.val().isValid(); m, *_ = S.메시(w); a, e = float(rng.uniform(0, 360)), float(rng.uniform(15, 35)); 저장(D + f"렌더/{i:05d}.png", Q.렌더(m, a, e)[0]); return {"i": i, "코드": Q.코드(s)}
    except Exception: return None
def 짓기():
    from multiprocessing import Pool
    with Pool(6) as p: r = [x for x in p.map(_하나, range(NT + NV), chunksize=20) if x]
    json.dump(r, open(D + "색인.json", "w", encoding="utf-8"), ensure_ascii=False); print("짝", len(r))
def 임베딩():
    from sentence_transformers import SentenceTransformer
    import torch
    m = SentenceTransformer("google/embeddinggemma-2", device="cuda", model_kwargs={"torch_dtype": torch.bfloat16}); 색 = json.load(open(D + "색인.json", encoding="utf-8")); 입 = json.load(open(D119 + "색인.json", encoding="utf-8"))["입력"]
    e = lambda p: np.ravel(m.encode({"text": "<|image|>", "image": [p]}, normalize_embeddings=True)).astype(np.float32)
    import time; t0 = time.time(); 조 = D + "임베딩_조각.npy"; E = list(np.load(조)) if os.path.exists(조) else []   # 이어 하기: 500 개마다 저장 · 8 분 넘으면 멈춤(포그라운드 조각)
    for r in 색[len(E):]:
        E.append(e(D + f"렌더/{r['i']:05d}.png"))
        if len(E) % 500 == 0 or len(E) == len(색): np.save(조, np.stack(E)); print(len(E), flush=True)
        if time.time() - t0 > 480: np.save(조, np.stack(E)); print("멈춤", len(E)); return
    E = np.stack(E); E119 = np.stack([e(D119 + f"렌더/{r['이름']}.png") for r in 입])
    np.savez(D + "임베딩.npz", E=E, E119=E119); print(E.shape, E119.shape)
def 학습():
    import torch, torch.nn as nn
    색 = json.load(open(D + "색인.json", encoding="utf-8")); z = np.load(D + "임베딩.npz"); E = torch.tensor(z["E"]); 과 = [과녁(json.loads(r["코드"])) for r in 색]
    시험 = np.array([r["i"] >= NT for r in 색]); T = lambda key: torch.tensor(np.stack([np.array(g[key]) for g in 과]))
    K, 치, 칸쓰, 특, 필, 기 = T("k").long(), T("치"), T("칸쓰"), T("특"), T("필"), T("기")
    tr = torch.tensor(~시험); torch.manual_seed(0)
    net = nn.Sequential(nn.Linear(E.shape[1], 512), nn.GELU(), nn.Dropout(.1), nn.Linear(512, 512), nn.GELU(), nn.Linear(512, 7 + 9 + 16 + 2 + 2)); opt = torch.optim.AdamW(net.parameters(), 1e-3, weight_decay=1e-4)
    def 나눔(o): return o[:, :7], o[:, 7:16], o[:, 16:32].reshape(-1, 2, 8), o[:, 32:34], o[:, 34:36]
    def 손실(o, ix):
        k, c, f, fi, ti = 나눔(o); bce = nn.functional.binary_cross_entropy_with_logits
        L = nn.functional.cross_entropy(k, K[ix]) + ((c - 치[ix]).abs() * 칸쓰[ix]).sum(1).mean() * 4
        L = L + bce(f[..., 0], 특[ix][..., 0]) + (nn.functional.cross_entropy(f[..., 1:4].reshape(-1, 3), 특[ix][..., 1:4].argmax(-1).reshape(-1), reduction="none") * 특[ix][..., 0].reshape(-1)).mean() + ((f[..., 4:] - 특[ix][..., 4:]).abs().sum(-1) * 특[ix][..., 0]).mean() * 2
        return L + bce(fi[:, 0], 필[ix][:, 0]) + bce(ti[:, 0], 기[ix][:, 0]) + ((ti[:, 1] - 기[ix][:, 1]).abs() * 기[ix][:, 0]).mean() * 2 + ((fi[:, 1] - 필[ix][:, 1]).abs() * 필[ix][:, 0]).mean()
    def 예측(Ex):
        net.eval()
        with torch.no_grad(): k, c, f, fi, ti = 나눔(net(Ex))
        net.train(); f = f.clone(); f[..., 0] = f[..., 0].sigmoid()
        return [사양(int(k[i].argmax()), c[i].numpy(), f[i].numpy(), [float(fi[i, 0].sigmoid()), float(fi[i, 1])], [float(ti[i, 0].sigmoid()), float(ti[i, 1])]) for i in range(len(Ex))]
    idx = torch.nonzero(tr).ravel(); vx = torch.nonzero(~tr).ravel(); 기록 = []; 과정 = {}; 고정 = vx[:6]
    for ep in range(60):
        perm = idx[torch.randperm(len(idx))]
        for b in range(0, len(perm), 128): ix = perm[b:b + 128]; opt.zero_grad(); l = 손실(net(E[ix]), ix); l.backward(); opt.step()
        with torch.no_grad():
            net.eval(); lv = float(손실(net(E[vx]), vx)); ka = float((나눔(net(E[vx]))[0].argmax(1) == K[vx]).float().mean()); net.train()
        기록.append({"에폭": ep + 1, "학습": float(l), "시험": lv, "시험 종류": ka}); print(기록[-1], flush=True)
        if ep in (0, 2, 5, 10, 20, 40, 59): 과정[ep + 1] = 예측(E[고정])
    E119 = torch.tensor(z["E119"]); 종평 = {}   # 대조② 종류별 중앙값 치수
    for g, s in zip(과, [json.loads(r["코드"]) for r in 색]):
        if not 시험[len(종평) * 0]: pass
    중 = {kk: np.median(np.stack([g["치"] for g, t in zip(과, 시험) if not t and g["k"] == kk]), 0) for kk in range(7)}
    def 대조(pr): return [사양(종류들.index(p["바탕"]["종류"]), 중[종류들.index(p["바탕"]["종류"])], np.zeros((2, 8)), [0, 0], [0, 0]) for p in pr]
    pv = 예측(E[vx]); p119 = 예측(E119)
    json.dump({"기록": 기록, "과정": 과정, "고정": [색[int(i)]["i"] for i in 고정], "시험": {"예측": pv, "대조": 대조(pv), "번호": [색[int(i)]["i"] for i in vx], "정답": [색[int(i)]["코드"] for i in vx]},
               "119": {"예측": p119, "대조": 대조(p119)}}, open(D + "학습.json", "w", encoding="utf-8"), ensure_ascii=False)
    torch.save(net.state_dict(), D + "머리.pt"); print("저장")
def 평가():
    import 설계116 as S, 데이터117 as Q, 회전118 as R
    j = json.load(open(D + "학습.json", encoding="utf-8")); 입 = json.load(open(D119 + "색인.json", encoding="utf-8"))["입력"]; 결119 = json.load(open(D119 + "결과.json", encoding="utf-8"))["부품"]
    def 점(s, img, 이름=None):
        try: w = S.짓기(s); assert w.val().isValid(); m, *_ = S.메시(w)
        except Exception: return 0., None
        sc, a, e, iou = R.맞추기(m, img)
        if 이름: 저장(D + f"렌더/{이름}.png", Q.렌더(m, a, e)[0])
        return iou, (a, e)
    out = {"G1": [], "G2": [], "G3": []}
    for r, p, c, r119 in zip(입, j["119"]["예측"], j["119"]["대조"], 결119):
        img = 읽(D119 + f"렌더/{r['이름']}.png"); iou, _ = 점(p, img, r["이름"] + "_모델"); ic, _ = 점(c, img)
        out[r["무리"]].append({"이름": r["이름"], "IoU": round(iou, 3), "대조② IoU": round(ic, 3), "119 IoU": r119["찾기"]["IoU"], "종류": p["바탕"]["종류"], "정답 종류": r.get("종류"), "사양": p}); print(r["이름"], p["바탕"]["종류"], round(iou, 3), "119", r119["찾기"]["IoU"], flush=True)
    시 = []
    for n, p, c, g in list(zip(j["시험"]["번호"], j["시험"]["예측"], j["시험"]["대조"], j["시험"]["정답"]))[:60]:
        img = 읽(D + f"렌더/{n:05d}.png"); 시.append((점(p, img)[0], 점(c, img)[0], p["바탕"]["종류"] == json.loads(g)["바탕"]["종류"]))
    for ep, ps in j["과정"].items():
        for t, (n, p) in enumerate(zip(j["고정"], ps)): 점(p, 읽(D + f"렌더/{n:05d}.png"), f"과정_{int(ep):02d}_{t}")
    중 = lambda g, k: float(np.median([x[k] for x in out[g]]))
    요 = {"G1 종류": float(np.mean([x["종류"] == x["정답 종류"] for x in out["G1"]])), **{f"{g} IoU 중앙({k})": 중(g, k) for g in out for k in ("IoU", "대조② IoU", "119 IoU")},
         "생성 시험 IoU 중앙": float(np.median([a for a, _, _ in 시])), "생성 시험 IoU 중앙(대조②)": float(np.median([b for _, b, _ in 시])), "생성 시험 종류": float(np.mean([k for _, _, k in 시])), "생성 시험 짓기 실패": int(sum(a == 0 for a, _, _ in 시))}
    json.dump({"요약": 요, "부품": out}, open(D + "결과.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(요, ensure_ascii=False, indent=1))
if __name__ == "__main__": {"짓기": 짓기, "임베딩": 임베딩, "학습": 학습, "평가": 평가}[sys.argv[1]]()
