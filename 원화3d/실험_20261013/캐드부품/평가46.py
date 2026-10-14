# 판정기준46 — 새 채점기 · 중복 뺀 시험 712 개 · 틀 · 39 · 42 · 10-14
import json, hashlib, numpy as np
from multiprocessing import Pool
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/"
if __name__ == "__main__":
    d = np.load(O + "데이터.npz"); 시 = d["시험"]; te = np.nonzero(시)[0]; Xa, Ya, Da = d["X"], d["Y"], d["D"]; del d
    h = lambda i: hashlib.md5(Xa[i].tobytes() + Ya[i].tobytes() + Da[i].tobytes()).hexdigest(); 학 = {h(i) for i in np.nonzero(~시)[0]}
    범위 = [j for j in range(200, len(te)) if h(te[j]) not in 학]; print("부품", len(범위), flush=True); X = Xa[te]
    e = np.load(O + "데이터_앞옆.npz"); Fr = e["F"][te]; S = e["S"][te]; del e; L = json.load(open(O + "목록.json", encoding="utf-8")); 결과 = {"부품": len(범위)}
    with Pool(2, maxtasksperchild=20) as pool:
        for k in ("42", "39"):
            M = np.load(O + "학습%s/시험예측.npz" % k); P, PD = M["P"], M["D"].astype(np.float32)
            v = np.array([r[:2] for r in pool.map(J.부피IoU, [(L[te[j]], P[j], PD[j], True, (X[j], Fr[j], S[j])) for j in 범위], chunksize=4)]); np.save(O + "부피IoU_46_%s.npy" % k, v)
            결과[k] = {"평균": float(v[:, 0].mean()), "틀": float(v[:, 1].mean()), "0점": int((v[:, 0] == 0).sum()), "나아짐": int((v[:, 0] > v[:, 1] + .01).sum()), "망침": int((v[:, 0] < v[:, 1] - .01).sum()), "크게망침": int((v[:, 0] < v[:, 1] - .1).sum())}; print(k, 결과[k], flush=True)
    a, n = 결과["42"], len(범위); json.dump(범위, open(O + "범위46.json", "w"))
    결과["판정"] = {"A": a["평균"] >= a["틀"] + .01, "B": a["망침"] / n < 354 / 803, "C": a["크게망침"] / n < 98 / 803, "39 기준": 결과["39"]["평균"] >= 결과["39"]["틀"] + .01}
    json.dump(결과, open(O + "결과46.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(결과["판정"])
