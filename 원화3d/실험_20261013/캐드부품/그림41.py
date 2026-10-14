# 판정기준41 — 뚫음 무게 3 → 1 · 크게 망친 부품의 칠(정답 · 39 · 41) + 41 로 지은 모양 · 10-14
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 짓기 as J
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False; O = "G:/art2real/out/설명/캐드부품/"
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; Y = d["Y"][te]; del d
e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te]; S = e["S"][te]; L = json.load(open(O + "목록.json", encoding="utf-8"))
A = np.load(O + "학습39/시험예측.npz"); B = np.load(O + "학습41/시험예측.npz"); a = np.load(O + "부피IoU_40_39.npy"); b = np.load(O + "부피IoU_41_41.npy"); 차 = b[:, 0] - b[:, 1]
면 = (Y[200:] > 0).sum((1, 2)); 거 = ((B["P"][200:] == 2) & (Y[200:] != 2)).sum((1, 2)) / np.maximum(면, 1)
다른 = [int(k) for k in np.argsort(차) if 차[k] < -.1 and 거[k] < .02][:3]; 고른 = [61, 519] + 다른   # 261 · 719 + 거짓 뚫음 아닌 큰 망침 3
색 = np.array([[1, 1, 1], [.75, .75, .75], [.85, .2, .2], [.3, .5, .9]])
fig = plt.figure(figsize=(26, 5 * len(고른)))
for r, k in enumerate(고른):
    j = k + 200
    for c, (im, t) in enumerate(((1 - X[j], "위 선 그림"), (색[Y[j]], "정답 칠"), (색[A["P"][j]], "39 칠 (무게 3) · %.2f" % a[k, 0]), (색[B["P"][j]], "41 칠 (무게 1) · %.2f" % b[k, 0]))):
        ax = fig.add_subplot(len(고른), 6, r * 6 + c + 1); ax.imshow(im, cmap="gray" if c == 0 else None); ax.axis("off"); ax.set_title(("%d 번 · " % j if c == 0 else "") + t, fontsize=16)
    v, f, H = J.정규메시(L[te[j]]); 정 = J.점유_메시(v, f); 몸, _ = J.몸통37((X[j], F[j], S[j]), H); q = J.점유_캐드(J.깎기(몸, B["P"][j], B["D"][j].astype(np.float32), H, True))
    ix = np.argwhere(정); lo, hi = ix.min(0), ix.max(0)
    for c, (qq, t, cc) in enumerate(((정, "정답", "tab:green"), (q, "41 로 지음 (틀 %.2f)" % b[k, 1], "tab:orange"))):
        ax = fig.add_subplot(len(고른), 6, r * 6 + 5 + c, projection="3d"); ax.voxels(qq, facecolors=cc, edgecolor="k", linewidth=.05)
        [getattr(ax, "set_%slim" % kk)(lo[i] - 1, hi[i] + 2) for i, kk in enumerate("xyz")]; ax.set_box_aspect(tuple(np.maximum(hi - lo + 3, 4))); ax.view_init(30, -58); ax.set_axis_off(); ax.set_title(t, fontsize=16)
fig.suptitle("판정기준41 — 뚫음 벌점 3 → 1 · 위 2 줄 = 지난번 없는 구멍 뚫던 부품 · 아래 3 줄 = 41 에서 구멍 말고 다른 이유로 크게 망친 부품\n칠: 회색 윗면 · 빨강 뚫음 · 파랑 들어감", fontsize=19)
plt.savefig(O + "결과41.png", dpi=55, bbox_inches="tight"); print(고른)
