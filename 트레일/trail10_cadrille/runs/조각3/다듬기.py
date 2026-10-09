# -*- coding: utf-8 -*-
"""조각3 — 디코더가 고른 조각을 부품마다 컨투어로 다듬기(학습 없음) → 평가.json · 판정.json
python runs/조각3/다듬기.py [걸음=200]"""
import os, sys, json, glob, time, numpy as np, torch
H = os.path.dirname(os.path.abspath(__file__)); Z0 = os.path.join(os.path.dirname(H), "조각0"); sys.path[:0] = [Z0, os.path.join(os.path.dirname(os.path.dirname(H)), "s0")]
os.environ.setdefault("N3", "48")
from 조각 import 이름, 점유, 격자, 보기, 모서리, 정답칸
from 학습 import 디코더, 손실, K, N3
from 평가 import 채점
if __name__ == "__main__":
    STEPS = int(sys.argv[1]) if len(sys.argv) > 1 else 200; NTR = 3600; dev = "cuda"
    X = torch.from_numpy(np.load(os.path.join(Z0, "특징.npy"))); Qs = [json.load(open(p, encoding="utf-8")) for p in sorted(glob.glob(os.path.join(Z0, "정답", "*.json")))]
    INIT = os.environ.get("INIT", ""); OUTD = os.path.join(H, "대조_최근접") if INIT == "nn" else H; os.makedirs(OUTD, exist_ok=True)
    f_ = X.float().mean(1); f_ = f_ / f_.norm(dim=1, keepdim=True); NN = (f_[NTR:] @ f_[:NTR].T).argmax(1)
    m = 디코더().to(dev); m.load_state_dict(torch.load(os.path.join(os.path.dirname(H), "조각2", "디코더.pt"))); m.eval(); g = 격자(N3, dev)[None]
    예측, t0, B = [], time.time(), 8
    for i in range(NTR, len(X), B):
        j = list(range(i, min(i + B, len(X))))
        with torch.no_grad():
            lg, c, s = m(X[j].to(dev).float()); P = torch.nn.functional.one_hot(lg.argmax(-1), len(이름)).float()
            if INIT == "nn":   # 대조: 디코더 대신 특징 최근접 학습 부품의 정답 조각을 출발점으로(같은 다듬기)
                P, c, s = map(lambda t: torch.stack(t).to(dev), zip(*[정답칸(Qs[int(NN[q - NTR])], K) for q in j]))
            Pg, Cg, Sg = map(lambda t: torch.stack(t).to(dev), zip(*[정답칸(Qs[q], K) for q in j])); Y = [y.detach() for y in (lambda S, D: (S, D, 모서리(D)))(*보기(점유(g, Pg, Cg, Sg, .005), N3))]
        c, s = c.clone().requires_grad_(True), s.clone().requires_grad_(True); opt = torch.optim.Adam([c, s], 3e-3)
        for k in range(STEPS):
            tau = .03 + (.005 - .03) * k / (STEPS - 1); Sil, D = 보기(점유(g, P, c, s, tau), N3)
            add = P[..., 1:6].sum(-1); out = (torch.relu(c + s / 2 - 1.05) + torch.relu(-0.05 - (c - s / 2))).sum(-1)
            loss = 손실((Sil, D, 모서리(D)), Y) + 2 * (add * out).mean()
            opt.zero_grad(); loss.backward(); opt.step()
            with torch.no_grad(): s.clamp_(min=0.005)
        t_ = P.argmax(-1)
        for b in range(len(j)): 예측.append([(이름[int(t_[b, q])], c[b, q].tolist(), s[b, q].tolist()) for q in range(K) if int(t_[b, q]) != 0])
        if i % 80 == 0: print(i, "%.0f 초" % (time.time() - t0), flush=True)
    print("다듬기 부품당 %.2f 초" % ((time.time() - t0) / len(예측)))
    from multiprocessing import Pool
    with Pool(12) as pool: R = pool.map(채점, [(p, Qs[NTR + i]) for i, p in enumerate(예측)])
    RC = json.load(open(os.path.join(os.path.dirname(H), "조각2", "평가.json"), encoding="utf-8"))["대조"]
    json.dump({"디코더": R, "대조": RC, "예측": 예측}, open(os.path.join(OUTD, "평가.json"), "w", encoding="utf-8"), ensure_ascii=False)
    맞 = lambda L: float(np.mean([r["edge_f1"] >= 0.42 for r in L]))
    판 = {"디코더 맞힘": 맞(R), "대조 맞힘": 맞(RC), "기준": "≥ 0.80 그리고 대조 + 0.10", "통과": 맞(R) >= .8 and 맞(R) >= 맞(RC) + .1,
         "모서리 중앙": float(np.median([r["edge_f1"] for r in R])), "IoU 중앙": float(np.median([r["iou"] for r in R])),
         "빼기 수 맞힘": float(np.mean([r["빼기수"][0] == r["빼기수"][1] for r in R])), "오류": sum(bool(r["오류"]) for r in R)}
    json.dump(판, open(os.path.join(OUTD, "판정.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(판)
