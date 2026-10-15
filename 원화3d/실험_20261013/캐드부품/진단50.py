# 진단50 — 덩어리 수(26 이웃 연결 성분) · 정답 · 틀 · 42 · 96 칸 · 48³ 틀 < 0.3 인 134 개 · 사용자 「연결구조가 없네?」 10-15
import json, numpy as np
from multiprocessing import Pool
from scipy.ndimage import label
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/"; N = 96; K = np.ones((3, 3, 3))
def 셈(job):
    p, Y, D, 그림 = job
    try:
        v, f, H = J.정규메시(p); 몸, _ = J.몸통37(그림, H); s = J.깎기(몸, Y, D, H, True)
        return [int(label(q, K)[1]) for q in (J.점유_메시(v, f, N), J.점유_캐드(몸, N), J.점유_캐드(s, N))] + [""]
    except Exception as ex: return [-1, -1, -1, type(ex).__name__]
if __name__ == "__main__":
    d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; del d; e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te]; S = e["S"][te]; del e; L = json.load(open(O + "목록.json", encoding="utf-8"))
    v48 = np.load(O + "부피IoU_46_42.npy"); 범 = json.load(open(O + "범위46.json")); M = np.load(O + "학습42/시험예측.npz"); P, PD = M["P"], M["D"].astype(np.float32)
    ks = [k for k in range(len(v48)) if v48[k, 1] < .3]; js = [범[k] for k in ks]
    with Pool(2, maxtasksperchild=20) as pool: r = pool.map(셈, [(L[te[j]], P[j], PD[j], (X[j], F[j], S[j])) for j in js], chunksize=2)
    a = np.array([x[:3] for x in r]); ok = a[:, 0] >= 0; print("실패", (~ok).sum())
    a = a[ok]; 
    for i, t in enumerate(("정답", "틀", "42")): print(t, "덩어리 1 개: %d · 2~5: %d · 6+: %d · 중앙값 %d" % ((a[:, i] == 1).sum(), ((a[:, i] > 1) & (a[:, i] <= 5)).sum(), (a[:, i] > 5).sum(), np.median(a[:, i])))
    print("정답은 1 개인데 틀이 여럿:", ((a[:, 0] == 1) & (a[:, 1] > 1)).sum(), " 42 가 여럿:", ((a[:, 0] == 1) & (a[:, 2] > 1)).sum(), " 정답이 0(빈 칸):", (a[:, 0] == 0).sum())
    json.dump({"부품": [j for j, o in zip(js, ok) if o], "덩어리": a.tolist()}, open(O + "진단50.json", "w"))
