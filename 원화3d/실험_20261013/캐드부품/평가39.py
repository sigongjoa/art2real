# 판정기준39 — 판정37 짓기 그대로 · 모델만 학습39(회전 높이) · 10-14
import json, collections, sys, numpy as np, cv2
from multiprocessing import Pool
import 짓기 as J
sys.path.append("G:/art2real/원화3d/실험_20261013/구멍"); import 윤곽바탕 as W
O = "G:/art2real/out/설명/캐드부품/"
def 갇힌만(Y, X):   # 관통 덩어리 중 테두리에 닿는 것은 윗면으로
    m = W.바깥(X)[0]; Y = Y.copy(); n, lab = cv2.connectedComponents((Y == 2).astype(np.uint8), connectivity=4)
    for i in range(1, n):
        c = lab == i; 넓 = cv2.dilate(c.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        if (넓 & ~m).any() or c[0].any() or c[-1].any() or c[:, 0].any() or c[:, -1].any(): Y[c] = 1
    return Y
if __name__ == "__main__":
    d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0][:200]; X = d["X"][te]; Y = d["Y"][te]; D = d["D"][te].astype(np.float32); del d
    e = np.load(O + "데이터_앞옆.npz"); Fr = e["F"][te]; S = e["S"][te]; del e
    A = np.load(O + "학습/시험예측.npz"); B = np.load(O + "학습2b/시험예측.npz"); L = json.load(open(O + "목록.json", encoding="utf-8"))
    C = np.load(O + "학습39/시험예측.npz"); 판 = {"39": (C["P"][:200], C["D"][:200].astype(np.float32))}; 결과 = {}
    with Pool(2, maxtasksperchild=20) as pool:
        for k, (YY, DD) in 판.items():
            R = pool.map(J.부피IoU, [(L[te[j]], YY[j], DD[j], True, (X[j], Fr[j], S[j])) for j in range(200)], chunksize=4)
            v = np.array([r[:2] for r in R]); np.save(O + "부피IoU_39_%s.npy" % k, v)
            결과[k] = {"부피IoU": float(v[:, 0].mean()), "바탕만": float(v[:, 1].mean()), "0점": int((v[:, 0] == 0).sum()), "나아짐": int((v[:, 0] > v[:, 1] + .01).sum()), "나빠짐": int((v[:, 0] < v[:, 1] - .01).sum())}; print(k, 결과[k], flush=True)
    b = np.load(O + "부피IoU_39_39.npy"); 기 = json.load(open(O + "학습39/기록.json"))[-1]["깊이오차중앙"]
    결과["판정"] = {"A 깊이": 기 <= .077 * .7, "깊이오차": 기, "B 부피": 결과["39"]["부피IoU"] >= 결과["39"]["바탕만"] + .01, "C 나빠짐<97": 결과["39"]["나빠짐"] < 97, "D 182": float(b[182, 0]) >= .8, "182값": float(b[182, 0])}
    json.dump(결과, open(O + "결과39.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(결과["판정"])
