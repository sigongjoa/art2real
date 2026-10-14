# 판정기준37 — 몸통 = 위 · 앞 · 옆 윤곽 교차 · 나머지는 평가33 과 같음 · 10-14
import json, collections, numpy as np
from multiprocessing import Pool
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/"
if __name__ == "__main__":
    d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0][:200]; X = d["X"][te]; Y = d["Y"][te]; D = d["D"][te].astype(np.float32); del d
    e = np.load(O + "데이터_앞옆.npz"); Fr = e["F"][te]; S = e["S"][te]; del e
    A = np.load(O + "학습/시험예측.npz"); B = np.load(O + "학습2b/시험예측.npz"); L = json.load(open(O + "목록.json", encoding="utf-8"))
    판 = {"천장": (Y, D), "2a": (A["P"][:200], A["D"][:200].astype(np.float32)), "2b": (B["P"][:200], B["D"][:200].astype(np.float32))}; 결과 = {}
    with Pool(2, maxtasksperchild=20) as pool:
        for k, (YY, DD) in 판.items():
            R = pool.map(J.부피IoU, [(L[te[j]], YY[j], DD[j], True, (X[j], Fr[j], S[j])) for j in range(200)], chunksize=4)
            v = np.array([r[:2] for r in R]); np.save(O + "부피IoU_37_%s.npy" % k, v); 길 = collections.Counter(r[2] for r in R)
            결과[k] = {"부피IoU": float(v[:, 0].mean()), "바탕만": float(v[:, 1].mean()), "0점": int((v[:, 0] == 0).sum()), "몸통경로": dict(길.most_common(8))}; print(k, 결과[k], flush=True)
    실패 = sum(n for g, n in collections.Counter(r[2] for r in R).items() if g.startswith("실패"))
    결과["판정"] = {"바탕": 결과["2a"]["바탕만"] >= .676 + .02, "몸통실패0": 실패 == 0, "0점≤5": 결과["2a"]["0점"] <= 5, "깎기": 결과["2a"]["부피IoU"] >= 결과["2a"]["바탕만"], "판정36": {"바탕만": .676, "천장": .706, "2a": .659, "2b": .661}, "판정33": {"바탕만": .565, "천장": .647, "2a": .584, "2b": .599}}
    json.dump(결과, open(O + "결과37.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(결과["판정"])
