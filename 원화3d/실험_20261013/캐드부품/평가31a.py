# 판정기준31 ① — 덩어리마다 깊이 하나로 깎기 · 시험 앞 200 · 덩어리 수 · 작은 조각 · 부피 IoU · 10-13
import json, numpy as np, cv2
from multiprocessing import Pool
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/"
def 덩어리(Y):   # 덩어리 깊이 방식에서 깎는 덩어리 = 들어감 덩어리 + 관통 덩어리
    개, 작 = 0, 0
    for m in (Y == 3, Y == 2):
        n, lab, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), connectivity=4)
        for i in range(1, n):
            if st[i, 4] >= 3: 개 += 1; 작 += st[i, 4] < 20
    return 개, 작
if __name__ == "__main__":
    d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0][:200]; del d
    p = np.load(O + "학습/시험예측.npz"); P, Dp = p["P"][:200], p["D"][:200].astype(np.float32); L = json.load(open(O + "목록.json", encoding="utf-8"))
    c = np.array([덩어리(P[j]) for j in range(200)])
    with Pool(2, maxtasksperchild=20) as pool: R = np.array(pool.map(J.부피IoU, [(L[te[j]], P[j], Dp[j], True) for j in range(200)], chunksize=4))
    결과 = {"덩어리_중앙": float(np.median(c[:, 0])), "작은조각_평균": float(c[:, 1].mean()), "부피IoU": float(R[:, 0].mean()), "바탕만": float(R[:, 1].mean())}
    결과["통과"] = 결과["덩어리_중앙"] <= 10 and 결과["작은조각_평균"] <= 7 and 결과["부피IoU"] >= .576
    json.dump(결과, open(O + "결과31a.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); np.save(O + "부피IoU_31a.npy", R); print(결과)
