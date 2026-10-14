# 판정기준40 — 회전 모델을 시험 부품 803 개(200 ~ 1002)에서 · 2b 와 같은 부품 · 10-14
import json, numpy as np
from multiprocessing import Pool
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/"
if __name__ == "__main__":
    d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; del d
    e = np.load(O + "데이터_앞옆.npz"); Fr = e["F"][te]; S = e["S"][te]; del e; L = json.load(open(O + "목록.json", encoding="utf-8")); 범위 = range(200, len(te))
    결과 = {}
    with Pool(2, maxtasksperchild=20) as pool:
        for k, 폴더 in (("39", "학습39"), ("2b", "학습2b")):
            P = np.load(O + 폴더 + "/시험예측.npz"); PP, DD = P["P"], P["D"].astype(np.float32)
            R = pool.map(J.부피IoU, [(L[te[j]], PP[j], DD[j], True, (X[j], Fr[j], S[j])) for j in 범위], chunksize=4)
            v = np.array([r[:2] for r in R]); np.save(O + "부피IoU_40_%s.npy" % k, v)
            결과[k] = {"부품": len(v), "부피IoU": float(v[:, 0].mean()), "틀만": float(v[:, 1].mean()), "0점": int((v[:, 0] == 0).sum()), "나아짐": int((v[:, 0] > v[:, 1] + .01).sum()), "망침": int((v[:, 0] < v[:, 1] - .01).sum())}; print(k, 결과[k], flush=True)
    a, b = 결과["39"], 결과["2b"]
    결과["판정"] = {"A": a["부피IoU"] >= a["틀만"] + .01, "B": a["부피IoU"] >= b["부피IoU"] + .02, "C": a["망침"] / a["부품"] < b["망침"] / b["부품"], "D": a["0점"] <= b["0점"]}
    json.dump(결과, open(O + "결과40.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(결과["판정"])
