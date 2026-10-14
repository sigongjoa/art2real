# 진단47 — 틀이 0.3 아래인 부품: 0 점 이유 세기 + 대표 8 개 그림(입력 셋 · 채운 윤곽 · 정답 · 틀) · 10-14
import sys, json, collections, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 짓기 as J
sys.path.append("G:/art2real/원화3d/실험_20261013/구멍"); import 윤곽바탕 as W
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; del d; e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te]; S = e["S"][te]; L = json.load(open(O + "목록.json", encoding="utf-8"))
v = np.load(O + "부피IoU_46_42.npy"); 범 = json.load(open(O + "범위46.json")); 틀점 = dict(zip(범, v[:, 1]))
이유 = collections.Counter(); 예 = {}
for j in [j for j in 범 if 틀점[j] == 0]:
    try:
        vv, f, H = J.정규메시(L[te[j]]); 몸, 길 = J.몸통37((X[j], F[j], S[j]), H); q = J.점유_캐드(몸); 정 = J.점유_메시(vv, f); k = "틀 빔" if q.sum() == 0 else "정답 빔" if 정.sum() == 0 else "겹침 0"
    except Exception as ex: k = "실패 " + type(ex).__name__ + (" " + str(ex)[:20] if "면" in str(ex) else "")
    이유[k] += 1; 예.setdefault(k, j)
print("0 점 이유", dict(이유), 예, flush=True)
낮 = sorted([j for j in 범 if 0 < 틀점[j] < .3], key=lambda j: 틀점[j]); 고른 = 낮[::max(len(낮) // 8, 1)][:8]
fig = plt.figure(figsize=(30, 4.6 * len(고른)))
for r, j in enumerate(고른):
    vv, f, H = J.정규메시(L[te[j]]); 정 = J.점유_메시(vv, f); 몸, 길 = J.몸통37((X[j], F[j], S[j]), H); q = J.점유_캐드(몸)
    for c, (im, t) in enumerate(((X[j], "위"), (F[j], "앞"), (S[j], "옆"))):
        ax = fig.add_subplot(len(고른), 8, r * 8 + c * 2 + 1); ax.imshow(1 - im, cmap="gray"); ax.axis("off"); ax.set_title(("%d 번 · " % j if c == 0 else "") + t + " 선", fontsize=14)
        ax = fig.add_subplot(len(고른), 8, r * 8 + c * 2 + 2); ax.imshow(W.바깥(im)[0], cmap="Greys"); ax.axis("off"); ax.set_title(t + " 채운 윤곽", fontsize=14)
    ix = np.argwhere(정 | q); lo, hi = ix.min(0), ix.max(0)
    for c, (a, t, cc) in enumerate(((정, "정답", "tab:green"), (q, "틀 %.2f · %s" % (틀점[j], 길), "tab:orange"))):
        ax = fig.add_subplot(len(고른), 8, r * 8 + 7 + c, projection="3d"); ax.voxels(a, facecolors=cc, edgecolor="k", linewidth=.04)
        [getattr(ax, "set_%slim" % k)(lo[i] - 1, hi[i] + 2) for i, k in enumerate("xyz")]; ax.set_box_aspect(tuple(np.maximum(hi - lo + 3, 4))); ax.view_init(30, -58); ax.set_axis_off(); ax.set_title(t, fontsize=14)
fig.suptitle("진단47 — 틀만 찍어도 0.3 아래인 부품(712 중 134) · 대표 8 개 · 채운 윤곽이 원인인지 본다", fontsize=20)
plt.savefig(O + "진단47_틀.png", dpi=50, bbox_inches="tight"); print("그림", 고른)
