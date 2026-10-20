# 판정기준110 천장 진단 — 깎인 속 화소를 셋으로: 영역 밖(선 · 작은 영역) / 영역 안인데 어느 후보에도 정답 ±1 없음 / 후보엔 있는데 영역 하나 = 후보 하나 로 못 맞춤 · 10-20
import pickle, json, numpy as np
import 코드110 as C
R = pickle.load(open(C.D + "특징_시험.pkl", "rb")); a = np.zeros(5)
for i, rs in R:
    g6 = C.층32[i].astype(int); s6 = C.껍32[i].astype(int); 안6 = (C.입[i][:, 1] > 0) & (g6 < 32); 깎6 = 안6 & (g6 >= s6 + 2)
    for n in range(6):
        g = g6[n].ravel(); 깎 = 깎6[n].ravel(); 덮 = np.zeros(128 * 128, bool)
        for (nn, idx, vs, f, 신) in rs:
            if nn != n: continue
            덮[idx] = True; V = np.stack([v.astype(int) for v in vs]); e = np.abs(V - g[idx][None]); 화 = (e <= 1).any(0); 영 = e[신] <= 1; k = 깎[idx]
            a[1] += (k & ~화).sum(); a[2] += (k & 화 & ~영).sum(); a[3] += (k & 영).sum()
        a[0] += (깎 & ~덮).sum(); a[4] += 깎.sum()
r = {"영역 밖(선 · 30 화소 아래 영역)": a[0] / a[4], "영역 안 · 어느 후보에도 정답 ±1 없음": a[1] / a[4], "후보엔 있는데 영역 하나 = 후보 하나로 못 맞춤": a[2] / a[4], "맞음(±1)": a[3] / a[4]}
print(json.dumps({k: round(v, 3) for k, v in r.items()}, ensure_ascii=False, indent=1)); json.dump(r, open(C.D + "진단.json", "w", encoding="utf-8"), ensure_ascii=False)
