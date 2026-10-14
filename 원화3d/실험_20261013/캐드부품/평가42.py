# 판정기준42 — 부피 벌점 모델을 새 803 개에서 · 10-14
import json, numpy as np
from multiprocessing import Pool
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/"
if __name__ == "__main__":
    d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; del d
    e = np.load(O + "데이터_앞옆.npz"); Fr = e["F"][te]; S = e["S"][te]; del e; L = json.load(open(O + "목록.json", encoding="utf-8")); 범위 = range(200, len(te))
    결과 = {}
    with Pool(2, maxtasksperchild=20) as pool:
        for k, 폴더 in (("42", "학습42"),):
            P = np.load(O + 폴더 + "/시험예측.npz"); PP, DD = P["P"], P["D"].astype(np.float32)
            R = pool.map(J.부피IoU, [(L[te[j]], PP[j], DD[j], True, (X[j], Fr[j], S[j])) for j in 범위], chunksize=4)
            v = np.array([r[:2] for r in R]); np.save(O + "부피IoU_42_%s.npy" % k, v)
            결과[k] = {"부품": len(v), "부피IoU": float(v[:, 0].mean()), "틀만": float(v[:, 1].mean()), "0점": int((v[:, 0] == 0).sum()), "나아짐": int((v[:, 0] > v[:, 1] + .01).sum()), "망침": int((v[:, 0] < v[:, 1] - .01).sum())}; print(k, 결과[k], flush=True)
    a = 결과["42"]; d = np.load(O + "데이터.npz"); Yt = d["Y"][te]; Pt = np.load(O + "학습42/시험예측.npz")["P"]
    비 = float((Pt == 2).sum() / (Yt == 2).sum()); 재 = float(((Pt == 2) & (Yt == 2)).sum() / (Yt == 2).sum())
    v = np.load(O + "부피IoU_42_42.npy"); 큰 = int((v[:, 0] < v[:, 1] - .1).sum())
    결과["판정"] = {"A 부피": a["부피IoU"] >= a["틀만"] + .01, "B 망침": a["망침"] < 354, "C 크게 망침": 큰 < 98, "크게망침": 큰, "D 구멍 재현": 재 >= .89, "재현": 재, "뚫음비율": 비}
    json.dump(결과, open(O + "결과42.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(결과["판정"])
