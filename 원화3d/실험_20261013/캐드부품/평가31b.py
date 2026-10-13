# 판정기준31 ② 평가 — 2b(위 · 앞 · 옆) 예측 · 같은 시험 앞 200 · 덩어리 깊이로 깎기 · 들어감 깊이 오차(2a 0.095 대비) · 부피 IoU(① 0.593 대비) · 10-13
import json, numpy as np
from multiprocessing import Pool
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/"
if __name__ == "__main__":
    d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0][:200]; Yg = d["Y"][te]; Dg = d["D"][te].astype(np.float32); del d
    p = np.load(O + "학습2b/시험예측.npz"); P, Dp = p["P"][:200], p["D"][:200].astype(np.float32); L = json.load(open(O + "목록.json", encoding="utf-8"))
    m = Yg == 3; 오차 = float(np.median(np.abs(Dp[m] - Dg[m]))); mi = float(np.mean([((P == c) & (Yg == c)).sum() / max(((P == c) | (Yg == c)).sum(), 1) for c in (1, 2, 3)]))
    with Pool(2, maxtasksperchild=20) as pool: R = np.array(pool.map(J.부피IoU, [(L[te[j]], P[j], Dp[j], True) for j in range(200)], chunksize=4))
    a = json.load(open(O + "결과31a.json", encoding="utf-8"))
    결과 = {"깊이오차중앙": 오차, "깊이오차_2a": .095, "부피IoU": float(R[:, 0].mean()), "부피IoU_①": a["부피IoU"], "바탕만": float(R[:, 1].mean()), "화소mIoU": mi}
    결과["통과"] = 오차 <= .066 and 결과["부피IoU"] >= a["부피IoU"] + .02 and mi >= .6
    json.dump(결과, open(O + "결과31b.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); np.save(O + "부피IoU_31b.npy", R); print(결과)
