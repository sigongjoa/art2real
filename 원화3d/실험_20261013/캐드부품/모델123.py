# 판정기준123 — 입력을 3면도 세 장(위 · 앞 · 옆)으로 · 장마다 얼린 Gemma 768 → 이어 붙여 120 과 같은 머리 · 10-21
# 사용: (cadrille · ART_MEM_GB=10) 모델123.py 짓기 [초] → (gemma) 모델123.py 임베딩 → (cadrille) 모델123.py 학습 → 모델123.py 평가 → out/설명/캐드부품/모델123/
import sys, os, json, time, numpy as np
import 모델120 as M
D = "G:/art2real/out/설명/캐드부품/모델123/"; os.makedirs(D + "도면", exist_ok=True); 뷰 = ("위", "앞", "옆"); 팔들 = ("셋", "위", "앞", "옆")
R3 = "G:/art2real/원화3d/out/레퍼런스/CAD조립/parts/"
def 그림(실, 숨, 중):   # bool 128 → 256 RGB · 실선 검정 · 숨은선 회색 점선 · 중심선 빨강
    n = 실.shape[0]; y, x = np.mgrid[:n, :n]; img = np.full((n, n, 3), 255, np.uint8)
    img[숨 & (((x + y) // 3) % 2 == 0)] = (140, 140, 140); img[중] = (220, 40, 40); img[실] = 0
    return img.repeat(2, 0).repeat(2, 1)
def 도면(s=None, m=None):   # 사양 또는 메시 → 세 장
    import 설계116 as S, 숨은선88 as H
    if s is not None:
        w = S.짓기(s); assert w.val().isValid(); m, v, c, e = S.메시(w); cl = S.중심선(s, c, e)
    else:
        c = m.bounds.mean(0); e = float(m.extents.max()); v = (m.vertices - c) / e; cl = np.zeros((3, S.N, S.N), bool)
    선 = H.그리기(v, m.faces); return [그림(선[j][0], 선[j][1], cl[j]) for j in range(3)]
def _하나(일):
    이름, s, stl = 일
    if all(os.path.exists(D + f"도면/{이름}_{nm}.png") for nm in 뷰): return
    try:
        if stl: import trimesh; ims = 도면(m=trimesh.load(stl, force="mesh"))
        else: ims = 도면(s)
        for nm, im in zip(뷰, ims): M.저장(D + f"도면/{이름}_{nm}.png", im)
    except Exception as ex: print("실패", 이름, ex, flush=True)
def 일감():
    색 = json.load(open(M.D + "색인.json", encoding="utf-8")); 입 = json.load(open(M.D119 + "색인.json", encoding="utf-8"))["입력"]
    return [(f"{r['i']:05d}", json.loads(r["코드"]), None) for r in 색] + [(r["이름"], json.loads(r["코드"]), None) if r["무리"] == "G1" else (r["이름"], None, R3 + r["출처"].replace("\\", "/")) for r in 입 if r["무리"] in ("G1", "G2")]
def 짓기(초=540):
    from multiprocessing import Pool
    일 = [x for x in 일감() if not os.path.exists(D + f"도면/{x[0]}_옆.png")]; print("남음", len(일), flush=True); t0 = time.time()
    with Pool(6) as p:
        for k, _ in enumerate(p.imap_unordered(_하나, 일, chunksize=8)):
            if time.time() - t0 > 초: p.terminate(); print("멈춤", k); return
    print("끝")
def 임베딩():   # 이어 하기 · 8 분 넘으면 멈춤
    from sentence_transformers import SentenceTransformer
    import torch
    m = SentenceTransformer("google/embeddinggemma-2", device="cuda", model_kwargs={"torch_dtype": torch.bfloat16}); 이 = [x[0] for x in 일감()]
    조 = D + "임베딩_조각.npy"; E = list(np.load(조)) if os.path.exists(조) else []; t0 = time.time(); 길 = [(n, nm) for n in 이 for nm in 뷰]
    while len(E) < len(길):
        b = 길[len(E):len(E) + 16]; e = m.encode([{"text": "<|image|>", "image": [D + f"도면/{n}_{nm}.png"]} for n, nm in b], normalize_embeddings=True, batch_size=16)
        E += list(np.asarray(e, np.float32).reshape(len(b), -1))
        if len(E) % 1600 < 16 or len(E) == len(길): np.save(조, np.stack(E)); print(len(E), flush=True)
        if time.time() - t0 > 480: np.save(조, np.stack(E)); print("멈춤", len(E)); return
    E = np.stack(E).reshape(len(이), 3, -1); np.savez(D + "임베딩.npz", E=E, 이름=np.array(이)); print(E.shape)
def 학습():
    import torch, torch.nn as nn
    색 = json.load(open(M.D + "색인.json", encoding="utf-8")); z = np.load(D + "임베딩.npz"); 번 = {n: k for k, n in enumerate(z["이름"])}; EA = torch.tensor(z["E"])
    입 = [r for r in json.load(open(M.D119 + "색인.json", encoding="utf-8"))["입력"] if r["무리"] in ("G1", "G2")]
    과 = [M.과녁(json.loads(r["코드"])) for r in 색]; 시험 = np.array([r["i"] >= M.NT for r in 색]); T = lambda key: torch.tensor(np.stack([np.array(g[key]) for g in 과]))
    K, 치, 칸쓰, 특, 필, 기 = T("k").long(), T("치"), T("칸쓰"), T("특"), T("필"), T("기")
    tr = torch.tensor(~시험); idx = torch.nonzero(tr).ravel(); vx = torch.nonzero(~tr).ravel(); 고정 = vx[:6]; out = {}
    Ei = EA[[번[f"{r['i']:05d}"] for r in 색]]; Eg = EA[[번[r["이름"]] for r in 입]]
    def 나눔(o): return o[:, :7], o[:, 7:16], o[:, 16:32].reshape(-1, 2, 8), o[:, 32:34], o[:, 34:36]
    for 팔 in 팔들:
        고 = (lambda X: X.reshape(len(X), -1)) if 팔 == "셋" else (lambda X, j=뷰.index(팔): X[:, j])
        E, EG = 고(Ei), 고(Eg); torch.manual_seed(0)
        net = nn.Sequential(nn.Linear(E.shape[1], 512), nn.GELU(), nn.Dropout(.1), nn.Linear(512, 512), nn.GELU(), nn.Linear(512, 36)); opt = torch.optim.AdamW(net.parameters(), 1e-3, weight_decay=1e-4)
        def 손실(o, ix):   # 모델120 과 같음
            k, c, f, fi, ti = 나눔(o); bce = nn.functional.binary_cross_entropy_with_logits
            L = nn.functional.cross_entropy(k, K[ix]) + ((c - 치[ix]).abs() * 칸쓰[ix]).sum(1).mean() * 4
            L = L + bce(f[..., 0], 특[ix][..., 0]) + (nn.functional.cross_entropy(f[..., 1:4].reshape(-1, 3), 특[ix][..., 1:4].argmax(-1).reshape(-1), reduction="none") * 특[ix][..., 0].reshape(-1)).mean() + ((f[..., 4:] - 특[ix][..., 4:]).abs().sum(-1) * 특[ix][..., 0]).mean() * 2
            return L + bce(fi[:, 0], 필[ix][:, 0]) + bce(ti[:, 0], 기[ix][:, 0]) + ((ti[:, 1] - 기[ix][:, 1]).abs() * 기[ix][:, 0]).mean() * 2 + ((fi[:, 1] - 필[ix][:, 1]).abs() * 필[ix][:, 0]).mean()
        def 예측(Ex):
            net.eval()
            with torch.no_grad(): k, c, f, fi, ti = 나눔(net(Ex))
            net.train(); f = f.clone(); f[..., 0] = f[..., 0].sigmoid()
            return [M.사양(int(k[i].argmax()), c[i].numpy(), f[i].numpy(), [float(fi[i, 0].sigmoid()), float(fi[i, 1])], [float(ti[i, 0].sigmoid()), float(ti[i, 1])]) for i in range(len(Ex))]
        기록 = []; 과정 = {}
        for ep in range(60):
            perm = idx[torch.randperm(len(idx))]
            for b in range(0, len(perm), 128): ix = perm[b:b + 128]; opt.zero_grad(); l = 손실(net(E[ix]), ix); l.backward(); opt.step()
            with torch.no_grad(): net.eval(); lv = float(손실(net(E[vx]), vx)); ka = float((나눔(net(E[vx]))[0].argmax(1) == K[vx]).float().mean()); net.train()
            기록.append({"에폭": ep + 1, "학습": float(l), "시험": lv, "시험 종류": ka})
            if 팔 == "셋" and ep in (0, 2, 5, 10, 20, 40, 59): 과정[ep + 1] = 예측(E[고정])
        print(팔, 기록[-1], flush=True); out[팔] = {"기록": 기록, "과정": 과정, "시험": 예측(E[vx]), "G": 예측(EG)}
    out["번호"] = [색[int(i)]["i"] for i in vx]; out["정답"] = [색[int(i)]["코드"] for i in vx]; out["고정"] = [색[int(i)]["i"] for i in 고정]; out["G 이름"] = [r["이름"] for r in 입]
    json.dump(out, open(D + "학습.json", "w", encoding="utf-8"), ensure_ascii=False); print("저장")
def 평가():
    import 설계116 as S, 데이터117 as Q, trimesh
    from 모델122 import 구멍
    j = json.load(open(D + "학습.json", encoding="utf-8")); j120 = json.load(open(M.D + "학습.json", encoding="utf-8")); 입 = {r["이름"]: r for r in json.load(open(M.D119 + "색인.json", encoding="utf-8"))["입력"]}
    def 렌(s):
        try: return Q.렌더(S.메시(S.짓기(s))[0])
        except Exception: return None
    def 잼(p, g, sg, 저=None):
        r = 렌(p); iou = 0. if r is None else float((sg & r[1]).sum() / max((sg | r[1]).sum(), 1))
        if 저 and r is not None: M.저장(D + f"렌더/{저}.png", r[0])
        if g is None: return {"IoU": round(iou, 4)}
        gh, ph = 구멍(g), 구멍(p); 자 = float(np.mean([abs(x["x"] - y["x"]) + abs(x["y"] - y["y"]) for x, y in zip(gh, ph)])) if gh and len(gh) == len(ph) else None
        return {"IoU": round(iou, 4), "특징 맞음": sorted(f["종류"] for f in g["특징"]) == sorted(f["종류"] for f in p["특징"]), "구멍 자리 오차": 자, "특징 수": len(gh), "종류 맞음": p["바탕"]["종류"] == g["바탕"]["종류"]}
    os.makedirs(D + "렌더", exist_ok=True); 결 = {"요약": {}, "부품": {}}
    정 = [json.loads(g) for g in j["정답"]]; 정렌 = [Q.렌더(S.메시(S.짓기(g))[0]) for g in 정]
    for n, (im, _) in zip(j["번호"], 정렌): M.저장(D + f"렌더/{n}_정답.png", im)
    G = [(nm, 입[nm]) for nm in j["G 이름"]]; G정 = {}
    for nm, r in G:
        m = S.메시(S.짓기(json.loads(r["코드"])))[0] if r["무리"] == "G1" else trimesh.load(R3 + r["출처"].replace("\\", "/"), force="mesh"); G정[nm] = Q.렌더(m); M.저장(D + f"렌더/{nm}_정답.png", G정[nm][0])
    G120 = dict(zip([r["이름"] for r in json.load(open(M.D119 + "색인.json", encoding="utf-8"))["입력"]], j120["119"]["예측"]))
    for 팔 in ("120",) + 팔들:
        ps = j120["시험"]["예측"] if 팔 == "120" else j[팔]["시험"]; pg = [G120[nm] for nm, _ in G] if 팔 == "120" else j[팔]["G"]
        줄 = [{"번호": n, **잼(p, g, sg, f"{n}_{팔}" if 팔 in ("120", "셋") else None)} for n, p, g, (_, sg) in zip(j["번호"], ps, 정, 정렌)]
        gg = [{"이름": nm, "무리": r["무리"], **잼(p, json.loads(r["코드"]) if r["무리"] == "G1" else None, G정[nm][1], f"{nm}_{팔}" if 팔 in ("120", "셋") else None)} for (nm, r), p in zip(G, pg)]
        자 = [x["구멍 자리 오차"] for x in 줄 if x["구멍 자리 오차"] is not None]; 중 = lambda xs: float(np.median(xs))
        결["요약"][팔] = {"3/4 IoU 중앙": 중([x["IoU"] for x in 줄]), "IoU < 0.9 몫": float(np.mean([x["IoU"] < .9 for x in 줄])), "종류": float(np.mean([x["종류 맞음"] for x in 줄])), "특징 종류 다 맞음": float(np.mean([x["특징 맞음"] for x in 줄])),
                       "특징 ≥ 2 맞음": float(np.mean([x["특징 맞음"] for x in 줄 if x["특징 수"] >= 2])), "구멍 자리 오차 중앙": 중(자), "구멍 자리 잰 수": len(자), "짓기 실패": int(sum(x["IoU"] == 0 for x in 줄)),
                       "G1 3/4 IoU 중앙": 중([x["IoU"] for x in gg if x["무리"] == "G1"]), "G1 종류": float(np.mean([x["종류 맞음"] for x in gg if x["무리"] == "G1"])), "G2 3/4 IoU 중앙": 중([x["IoU"] for x in gg if x["무리"] == "G2"])}
        결["부품"][팔] = {"시험": 줄, "G": gg}; print(팔, json.dumps(결["요약"][팔], ensure_ascii=False), flush=True)
    for ep, ps in j["셋"]["과정"].items():
        for t, p in enumerate(ps):
            r = 렌(p)
            if r is not None: M.저장(D + f"렌더/과정_{int(ep):02d}_{t}.png", r[0])
    요 = 결["요약"]; 결["통과"] = {"특징 다 맞음 ≥ 0.75": 요["셋"]["특징 종류 다 맞음"] >= .75, "구멍 자리 < 120": 요["셋"]["구멍 자리 오차 중앙"] < 요["120"]["구멍 자리 오차 중앙"], "3/4 IoU > 120": 요["셋"]["3/4 IoU 중앙"] > 요["120"]["3/4 IoU 중앙"], "G1 ≥ 0.97": 요["셋"]["G1 3/4 IoU 중앙"] >= .97}
    json.dump(결, open(D + "결과.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(결["통과"])
if __name__ == "__main__":
    f = {"짓기": 짓기, "임베딩": 임베딩, "학습": 학습, "평가": 평가}[sys.argv[1]]; f(*[int(a) for a in sys.argv[2:]])
