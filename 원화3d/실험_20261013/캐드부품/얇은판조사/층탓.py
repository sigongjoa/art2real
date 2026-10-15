# 89 개: 칸 깎기의 낮은 점수가 격자(48³) 탓인지 · 층 16 내림 탓인지 · 안 보이는 곳 탓인지 — 정확 깊이(내림 없음)로 48 · 192
import json, numpy as np, 채점후보 as K
from multiprocessing import Pool
S6 = K.S6
def 하나(job):
    p, 반 = job; v, f, H = K.J.정규메시(p); 지 = S6.깊이지도(v, f); 상자 = (v.min(0) - 1e-4, v.max(0) + 1e-4)
    표 = [(S6.R(*S6.방향[k]), float(반[n]), np.where(np.isnan(지[k]), 2 * float(반[n]) + .1, float(반[n]) - 지[k])) for n, k in enumerate(S6.방향)]
    out = {}
    for m in (48, 192):
        g = K.점유(v, f, m); c = K.깎기칸(표, 상자, m); out[m] = K.IoU(c, g)
    out["부분"] = K.부분IoU(K.깎기칸(표, 상자, 192), K.점유(v, f, 192)); out["단_칸"] = float(np.median([2 * float(b) / 16 for b in 반]) / K.칸48); return out
if __name__ == "__main__":
    O = K.O; d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; del d
    L = json.load(open(O + "목록.json", encoding="utf-8")); 범 = json.load(open(O + "범위46.json")); R = json.load(open("결과.json", encoding="utf-8"))
    z = np.load(O + "데이터51.npz"); 반 = z["반"]; ks = [r["k"] for r in R if r["무리"] == "89"]
    with Pool(2) as pool: Q = pool.map(하나, [(L[te[범[k]]], 반[te[범[k]]]) for k in ks])
    json.dump(Q, open("층탓.json", "w"), indent=0)
    for key in (48, 192, "부분", "단_칸"): print(key, np.mean([q[key] for q in Q]).round(3))
    print("정확 깊이 192 ≥ .5:", sum(q[192] >= .5 for q in Q), "/", len(Q))
