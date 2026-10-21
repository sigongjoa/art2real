# 판정기준122 — 모델120 머리에 시점(방위 · 고도)을 입력으로 붙여 다시 학습 · 대조 없음 · 섞음 · 10-21
# 사용(cadrille venv · ART_MEM_GB=10): 모델122.py 학습 → 모델122.py 평가 → 모델122.py 그림 → out/설명/캐드부품/모델122/
import sys, os, json, numpy as np
import 모델120 as M
D = "G:/art2real/out/설명/캐드부품/모델122/"; os.makedirs(D + "렌더", exist_ok=True); 팔들 = ("없음", "시점", "섞음")
def 시점(i):   # 모델120._하나 와 같은 순서로 시드를 소비해 렌더할 때 쓴 방위 · 고도를 다시 뽑음
    import 설계116 as S
    rng = np.random.default_rng(120000 + i); S.무작위(rng); return float(rng.uniform(0, 360)), float(rng.uniform(15, 35))
def 칸(a, e): return [np.sin(np.radians(a)), np.cos(np.radians(a)), (e - 25) / 10]
def 학습():
    import torch, torch.nn as nn
    색 = json.load(open(M.D + "색인.json", encoding="utf-8")); z = np.load(M.D + "임베딩.npz"); E0 = torch.tensor(z["E"]); 과 = [M.과녁(json.loads(r["코드"])) for r in 색]
    시험 = np.array([r["i"] >= M.NT for r in 색]); T = lambda key: torch.tensor(np.stack([np.array(g[key]) for g in 과]))
    K, 치, 칸쓰, 특, 필, 기 = T("k").long(), T("치"), T("칸쓰"), T("특"), T("필"), T("기")
    V = torch.tensor([칸(*시점(r["i"])) for r in 색], dtype=torch.float32); V119 = torch.tensor([칸(155, 25)] * len(z["E119"]), dtype=torch.float32)
    tr = torch.tensor(~시험); idx = torch.nonzero(tr).ravel(); vx = torch.nonzero(~tr).ravel(); 고정 = vx[:6]; out = {}
    def 나눔(o): return o[:, :7], o[:, 7:16], o[:, 16:32].reshape(-1, 2, 8), o[:, 32:34], o[:, 34:36]
    for 팔 in 팔들:
        if 팔 == "없음": E, E119 = E0, torch.tensor(z["E119"])
        else:
            Vp = V.clone()
            if 팔 == "섞음": g = torch.Generator().manual_seed(1); Vp[idx] = V[idx[torch.randperm(len(idx), generator=g)]]; Vp[vx] = V[vx[torch.randperm(len(vx), generator=g)]]
            E, E119 = torch.cat([E0, Vp], 1), torch.cat([torch.tensor(z["E119"]), V119], 1)
        torch.manual_seed(0)
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
            with torch.no_grad(): net.eval(); lv = float(손실(net(E[vx]), vx)); net.train()
            기록.append({"에폭": ep + 1, "학습": float(l), "시험": lv})
            if 팔 == "시점" and ep in (0, 2, 5, 10, 20, 40, 59): 과정[ep + 1] = 예측(E[고정])
        print(팔, 기록[-1], flush=True); out[팔] = {"기록": 기록, "과정": 과정, "시험": 예측(E[vx]), "G": 예측(E119)}
    out["번호"] = [색[int(i)]["i"] for i in vx]; out["정답"] = [색[int(i)]["코드"] for i in vx]; out["고정"] = [색[int(i)]["i"] for i in 고정]
    json.dump(out, open(D + "학습.json", "w", encoding="utf-8"), ensure_ascii=False); print("저장")
def 구멍(s): return sorted([f for f in s["특징"] if f["종류"] != "필렛"], key=lambda f: f["x"])
def 평가():
    import 설계116 as S, 데이터117 as Q, 회전118 as R
    j = json.load(open(D + "학습.json", encoding="utf-8")); 입 = json.load(open(M.D119 + "색인.json", encoding="utf-8"))["입력"]; 결 = {"요약": {}, "부품": {}}
    def 그림(s, a, e):
        try: return Q.렌더(S.메시(S.짓기(s))[0], a, e)
        except Exception: return None
    for 팔 in 팔들:
        줄 = []
        for n, p, g in zip(j["번호"], j[팔]["시험"], j["정답"]):
            g = json.loads(g); a, e = 시점(n); _, sg = 그림(g, a, e); r = 그림(p, a, e); iou = 0. if r is None else float((sg & r[1]).sum() / max((sg | r[1]).sum(), 1))
            if 팔 == "시점" and r is not None: M.저장(D + f"렌더/{n}_시점.png", r[0])
            if 팔 == "없음" and r is not None: M.저장(D + f"렌더/{n}_없음.png", r[0])
            gh, ph = 구멍(g), 구멍(p); 맞 = sorted(f["종류"] for f in g["특징"]) == sorted(f["종류"] for f in p["특징"])
            자 = float(np.mean([abs(x["x"] - y["x"]) + abs(x["y"] - y["y"]) for x, y in zip(gh, ph)])) if gh and len(gh) == len(ph) else None
            줄.append({"번호": n, "IoU": round(iou, 4), "특징 맞음": 맞, "구멍 자리 오차": 자, "특징 수": len(gh), "기울임": g["기울임"] > 0})
        G1 = []
        for r, p in zip(입, j[팔]["G"]):
            if r["무리"] != "G1": continue
            try: m = S.메시(S.짓기(p))[0]; _, a, e, iou = R.맞추기(m, M.읽(M.D119 + f"렌더/{r['이름']}.png"))
            except Exception: iou = 0.
            G1.append({"이름": r["이름"], "IoU": round(float(iou), 4), "종류 맞음": p["바탕"]["종류"] == r["종류"]})
        자 = [x["구멍 자리 오차"] for x in 줄 if x["구멍 자리 오차"] is not None]
        결["요약"][팔] = {"같은 시점 IoU 중앙": float(np.median([x["IoU"] for x in 줄])), "IoU < 0.9 몫": float(np.mean([x["IoU"] < .9 for x in 줄])), "특징 종류 다 맞음": float(np.mean([x["특징 맞음"] for x in 줄])),
                       "특징 ≥ 2 맞음": float(np.mean([x["특징 맞음"] for x in 줄 if x["특징 수"] >= 2])), "구멍 자리 오차 중앙": float(np.median(자)), "구멍 자리 잰 수": len(자),
                       "기울임 IoU 중앙": float(np.median([x["IoU"] for x in 줄 if x["기울임"]])), "짓기 실패": int(sum(x["IoU"] == 0 for x in 줄)), "G1 IoU 중앙": float(np.median([x["IoU"] for x in G1])), "G1 종류": float(np.mean([x["종류 맞음"] for x in G1]))}
        결["부품"][팔] = {"시험": 줄, "G1": G1}; print(팔, json.dumps(결["요약"][팔], ensure_ascii=False), flush=True)
    요 = 결["요약"]; 결["통과"] = {"특징 다 맞음 ≥ 0.75": 요["시점"]["특징 종류 다 맞음"] >= .75, "IoU > 없음": 요["시점"]["같은 시점 IoU 중앙"] > 요["없음"]["같은 시점 IoU 중앙"], "자리 오차 < 없음": 요["시점"]["구멍 자리 오차 중앙"] < 요["없음"]["구멍 자리 오차 중앙"],
                  "섞음 셋 다 나쁨": 요["섞음"]["특징 종류 다 맞음"] < 요["시점"]["특징 종류 다 맞음"] and 요["섞음"]["같은 시점 IoU 중앙"] < 요["시점"]["같은 시점 IoU 중앙"] and 요["섞음"]["구멍 자리 오차 중앙"] > 요["시점"]["구멍 자리 오차 중앙"]}
    # 과정 렌더(시점 팔 · 고정 6 · 에폭별)
    for ep, ps in j["시점"]["과정"].items():
        for t, (n, p) in enumerate(zip(j["고정"], ps)):
            r = 그림(p, *시점(n))
            if r is not None: M.저장(D + f"렌더/과정_{int(ep):02d}_{t}.png", r[0])
    json.dump(결, open(D + "결과.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(결["통과"])
if __name__ == "__main__": {"학습": 학습, "평가": 평가}[sys.argv[1]]()
