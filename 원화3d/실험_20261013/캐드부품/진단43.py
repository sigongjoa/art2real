# 판정기준43 — 깎기 CAD 깨짐 세기 · 깎은 칸 ∩ 틀 로 고친 점수 · 새 803 개 · 39 · 42 · 10-14
import json, numpy as np
from multiprocessing import Pool
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/"
def 하나(job):
    p, Y, D, 그림 = job
    try:
        v, f, H = J.정규메시(p); 정 = J.점유_메시(v, f); 몸, _ = J.몸통37(그림, H); s = J.깎기(몸, Y, D, H, True); 틀, q = J.점유_캐드(몸), J.점유_캐드(s)
        r = lambda a: float((a & 정).sum() / max((a | 정).sum(), 1))
        return (r(q), r(q & 틀), r(틀), int((q & ~틀).sum()), int(몸.val().isValid()), int(s.val().isValid()))
    except Exception: return (0., 0., 0., -1, 0, 0)
if __name__ == "__main__":
    d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; del d
    e = np.load(O + "데이터_앞옆.npz"); Fr = e["F"][te]; S = e["S"][te]; del e; L = json.load(open(O + "목록.json", encoding="utf-8")); 결과 = {}
    with Pool(2, maxtasksperchild=20) as pool:
        for k in ("42", "39"):
            M = np.load(O + "학습%s/시험예측.npz" % k); P, PD = M["P"], M["D"].astype(np.float32)
            v = np.array(pool.map(하나, [(L[te[j]], P[j], PD[j], (X[j], Fr[j], S[j])) for j in range(200, len(te))], chunksize=4)); np.save(O + "진단43_%s.npy" % k, v)
            원, 고, 틀 = v[:, 0], v[:, 1], v[:, 2]
            결과[k] = {"틀 밖 칸 있는 부품": int((v[:, 3] > 0).sum()), "깎은 모양 무효": int((v[:, 5] == 0).sum()), "틀 무효": int((v[:, 4] == 0).sum()), "원래 평균": float(원.mean()), "고친 평균": float(고.mean()), "틀 평균": float(틀.mean()),
                     "고친 망침": int((고 < 틀 - .01).sum()), "고친 크게 망침": int((고 < 틀 - .1).sum()), "고친 나아짐": int((고 > 틀 + .01).sum())}; print(k, 결과[k], flush=True)
    a = 결과["42"]; 결과["판정42 유지"] = a["고친 평균"] >= a["틀 평균"] + .01 and a["고친 망침"] < 354 and a["고친 크게 망침"] < 98
    json.dump(결과, open(O + "결과43.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(결과["판정42 유지"])
