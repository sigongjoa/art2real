# 판정기준33 — 몸통 = 53 편 그림 윤곽 · 모델 지도는 관통 · 들어감에만 · 덩어리 깊이 · 같은 시험 앞 200 · 천장 · 2a · 2b · 몸통 경로 세기 · 10-13
import json, collections, numpy as np
from multiprocessing import Pool
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/"
if __name__ == "__main__":
    d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0][:200]; X = d["X"][te]; Y = d["Y"][te]; D = d["D"][te].astype(np.float32); del d
    A = np.load(O + "학습/시험예측.npz"); B = np.load(O + "학습2b/시험예측.npz"); L = json.load(open(O + "목록.json", encoding="utf-8"))
    판 = {"천장": (Y, D), "2a": (A["P"][:200], A["D"][:200].astype(np.float32)), "2b": (B["P"][:200], B["D"][:200].astype(np.float32))}; 결과 = {}
    with Pool(2, maxtasksperchild=20) as pool:
        for k, (YY, DD) in 판.items():
            R = pool.map(J.부피IoU, [(L[te[j]], YY[j], DD[j], True, X[j]) for j in range(200)], chunksize=4)
            v = np.array([r[:2] for r in R]); np.save(O + "부피IoU_33_%s.npy" % k, v); 길 = collections.Counter(r[2] for r in R)
            결과[k] = {"부피IoU": float(v[:, 0].mean()), "바탕만": float(v[:, 1].mean()), "0점": int((v[:, 0] == 0).sum()), "몸통경로": dict(길)}; print(k, 결과[k], flush=True)
    실패 = sum(n for k in 판 for g, n in 결과[k]["몸통경로"].items() if g.startswith("실패"))
    결과["판정"] = {"2a": 결과["2a"]["부피IoU"] >= 결과["2a"]["바탕만"] + .04, "2b": 결과["2b"]["부피IoU"] >= 결과["2a"]["부피IoU"] + .02, "몸통실패0": 실패 == 0}
    json.dump(결과, open(O + "결과33.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(결과["판정"])
