# 판정기준42 실제 결과 — 정답 · 틀만 · 39(칠 + 깊이 벌점) · 42(+ 부피 벌점) · 같은 부품 · 채점 칸 48³ · 10-14
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 짓기 as J
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False; O = "G:/art2real/out/설명/캐드부품/"
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; del d
e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te]; S = e["S"][te]; L = json.load(open(O + "목록.json", encoding="utf-8"))
A = np.load(O + "학습39/시험예측.npz"); B = np.load(O + "학습42/시험예측.npz"); a = np.load(O + "부피IoU_40_39.npy"); b = np.load(O + "부피IoU_42_42.npy")
부품 = [261, 719, 323, 498, 182]; 부품 += [int(k) + 200 for k in np.argsort(b[:, 0] - b[:, 1]) if int(k) + 200 not in 부품][:2]
fig = plt.figure(figsize=(22, 4.4 * len(부품)))
for r, j in enumerate(부품):
    v, f, H = J.정규메시(L[te[j]]); 정 = J.점유_메시(v, f); 몸, _ = J.몸통37((X[j], F[j], S[j]), H); 점 = lambda q: (q & 정).sum() / max((q | 정).sum(), 1)
    틀 = J.점유_캐드(몸); 판 = [("정답", 정), ("틀만", 틀)] + [(n, J.점유_캐드(J.깎기(몸, M["P"][j], M["D"][j].astype(np.float32), H, True))) for n, M in (("39 (예전 벌점)", A), ("42 (부피 벌점)", B))]
    ix = np.argwhere(정 | 틀); lo, hi = ix.min(0), ix.max(0); s틀 = 점(틀)
    for c, (t, q) in enumerate(판):
        s = 점(q); ax = fig.add_subplot(len(부품), 4, r * 4 + c + 1, projection="3d"); ax.voxels(q, facecolors="tab:green" if c == 0 else "tab:orange", edgecolor="k", linewidth=.05)
        [getattr(ax, "set_%slim" % k)(lo[i] - 1, hi[i] + 2) for i, k in enumerate("xyz")]; ax.set_box_aspect(tuple(np.maximum(hi - lo + 3, 4))); ax.view_init(30, -58); ax.set_axis_off()
        ax.set_title(("%d 번 · " % j if c == 0 else "") + ("%s" % t if c == 0 else "%s %.2f" % (t, s)), fontsize=17, color="k" if c < 2 else ("tab:red" if s < s틀 - .01 else "tab:green" if s > s틀 + .01 else "k"))
fig.suptitle("판정기준42 실제 지은 모양 — 위 5 줄 = 지난번 망친 부품 · 아래 2 줄 = 그 밖에 42 가 가장 많이 망친 부품\n빨강 = 틀보다 나빠짐 · 초록 = 좋아짐", fontsize=20)
plt.savefig(O + "결과42_3d.png", dpi=55, bbox_inches="tight"); print(부품, [(j, round(float(b[j - 200, 0]), 2) if j >= 200 else None) for j in 부품])
