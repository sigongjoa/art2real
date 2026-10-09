# -*- coding: utf-8 -*-
"""조각0 판정 — 시험 400: 디코더 칸 → CadQuery → 모서리 F1 · IoU (모양자.재기) · 빼기 개수 · 대조 = 특징 최근접 학습 부품
python runs/조각0/평가.py  →  평가.json · 판정.json · 시험그림.png"""
import os, sys, json, glob, numpy as np, torch, tempfile
from multiprocessing import Pool
H = os.path.dirname(os.path.abspath(__file__)); T = os.path.dirname(os.path.dirname(H)); sys.path[:0] = [H, os.path.join(T, "s0")]
NTR = 3600

def 메시(P):
    import cadquery as cq, trimesh
    from 합성 import 짓기
    if not any(q[0] in ("상자", "원통z", "원통x", "원통y", "공") for q in P) or P[0][0].startswith(("구멍", "사각")): 
        P = sorted(P, key=lambda q: q[0].startswith(("구멍", "사각")))   # 더하기를 앞으로
    p = os.path.join(tempfile.gettempdir(), "조각0평가_%d.stl" % os.getpid())
    cq.exporters.export(짓기([(q[0], [v * 100 for v in q[1]], [max(v, .01) * 100 for v in q[2]]) + tuple(q[3:4]) for q in P]), p, tolerance=0.05, angularTolerance=0.2)   # 4 번째 = 회전(v2)
    m = trimesh.load(p); m.apply_translation([-50] * 3); m.apply_scale(1 / 50.0); return m   # 단위 상자 → [-1,1]

def 채점(a):
    P, Q = a
    from 모양자 import 재기
    try:
        if not any(q[0] in ("상자", "원통z", "원통x", "원통y", "공") for q in P): raise ValueError("더하는 칸 없음")
        pm = 메시(P)
        if os.environ.get("NORM") == "1":   # 입력 규약(긴 변 1 · 가운데)을 예측에도 — 정답은 이미 그 규약
            lo, hi = pm.bounds; pm.apply_translation(-(lo + hi) / 2); pm.apply_scale(2.0 / (hi - lo).max())
        r = 재기(pm, 메시(Q))
    except Exception as e: r = {"edge_f1": 0.0, "iou": 0.0, "오류": str(e)[:80]}
    빼기 = lambda L: sum(q[0].startswith(("구멍", "사각")) for q in L)
    return {"edge_f1": r["edge_f1"], "iou": r["iou"], "빼기수": [빼기(Q), 빼기(P)], "오류": r.get("오류")}

if __name__ == "__main__":
    from 조각 import 이름
    from 학습 import 디코더  # N3 와 무관(평가는 CadQuery)
    O = os.environ.get("OUT", H); X = torch.from_numpy(np.load(os.path.join(H, "특징.npy"))); Qs = [json.load(open(p, encoding="utf-8")) for p in sorted(glob.glob(os.path.join(H, "정답", "*.json")))]
    m = 디코더().cuda(); m.load_state_dict(torch.load(os.path.join(O, "디코더.pt"))); m.eval(); 예측 = []
    with torch.no_grad():
        for i in range(NTR, len(X), 50):
            lg, c, s = m(X[i:i + 50].cuda().float()); t = lg.argmax(-1)
            for b in range(len(t)): 예측.append([(이름[int(t[b, k])], c[b, k].tolist(), s[b, k].tolist()) for k in range(len(t[b])) if int(t[b, k]) != 0])
    f = X.float().mean(1); f = f / f.norm(dim=1, keepdim=True); nn_ = (f[NTR:] @ f[:NTR].T).argmax(1)   # 대조: 최근접 학습 부품 그대로
    대조 = [Qs[int(j)] for j in nn_]
    with Pool(12) as pool:
        R = pool.map(채점, [(p, Qs[NTR + i]) for i, p in enumerate(예측)]); RC = pool.map(채점, [(p, Qs[NTR + i]) for i, p in enumerate(대조)])
    json.dump({"디코더": R, "대조": RC, "예측": 예측}, open(os.path.join(O, "평가_정규화.json" if os.environ.get("NORM") == "1" else "평가.json"), "w", encoding="utf-8"), ensure_ascii=False)
    맞 = lambda L: float(np.mean([r["edge_f1"] >= 0.42 for r in L]))
    판 = {"디코더 맞힘": 맞(R), "대조 맞힘": 맞(RC), "기준": "≥ 0.80 그리고 대조 + 0.10", "통과": 맞(R) >= .8 and 맞(R) >= 맞(RC) + .1,
         "모서리 중앙": [float(np.median([r["edge_f1"] for r in L])) for L in (R, RC)], "IoU 중앙": [float(np.median([r["iou"] for r in L])) for L in (R, RC)],
         "빼기 수 맞힘": [float(np.mean([r["빼기수"][0] == r["빼기수"][1] for r in L])) for L in (R, RC)], "오류": sum(bool(r["오류"]) for r in R)}
    json.dump(판, open(os.path.join(O, "판정_정규화.json" if os.environ.get("NORM") == "1" else "판정.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(판)
