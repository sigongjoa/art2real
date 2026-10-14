# 61 편 재료 — 261 · 323 · 605 · 30 번(시험) · 39 · 41 · 42 예측 · 10-14
import json, os, numpy as np, torch, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/"; A = "G:/art2real/out/영상05/대화/61_부피벌점/자료/"; os.makedirs(A, exist_ok=True)
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; Y = d["Y"][te]; D = d["D"][te].astype(np.float32); del d
e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te]; S = e["S"][te]; L = json.load(open(O + "목록.json", encoding="utf-8"))
M = {k: np.load(O + "학습%s/시험예측.npz" % k) for k in ("39", "41", "42")}
def 입체(q, 색, 이름, lo, hi):
    fig = plt.figure(figsize=(8, 6)); a = fig.add_subplot(projection="3d"); a.voxels(q, facecolors=색, edgecolor="k", linewidth=.08)
    [getattr(a, "set_%slim" % k)(lo[i] - 1, hi[i] + 2) for i, k in enumerate("xyz")]; a.set_box_aspect(tuple(np.maximum(hi - lo + 3, 4))); a.view_init(30, -58); a.set_axis_off()
    fig.subplots_adjust(0, 0, 1, 1); plt.savefig(A + 이름, dpi=80, transparent=True); plt.close(fig)
for j, 판 in ((261, ("39", "42")), (323, ("39", "42"))):
    v, f, H = J.정규메시(L[te[j]]); 정 = J.점유_메시(v, f); 몸, _ = J.몸통37((X[j], F[j], S[j]), H); 틀 = J.점유_캐드(몸); ix = np.argwhere(정 | 틀); lo, hi = ix.min(0), ix.max(0)
    입체(틀, "tab:orange", "%d_틀.png" % j, lo, hi)
    for k in 판: 입체(J.점유_캐드(J.깎기(몸, M[k]["P"][j], M[k]["D"][j].astype(np.float32), H, True)), "tab:orange", "%d_%s.png" % (j, k), lo, hi)
def 평(im, 이름, cmap=None):
    fig = plt.figure(figsize=(6, 6)); plt.imshow(im, cmap=cmap); plt.axis("off"); fig.subplots_adjust(0, 0, 1, 1); plt.savefig(A + 이름, dpi=80); plt.close(fig)
색 = np.array([[1, 1, 1], [.75, .75, .75], [.85, .2, .2], [.3, .5, .9]])
평(1 - X[261], "선_261.png", "gray"); 평(1 - X[30], "선_30.png", "gray"); 평(색[Y[261]], "칠_261_정답.png"); 평(색[M["41"]["P"][261]], "칠_261_41.png")
def 기둥(y, dd, n=20):
    y = y[::2, ::2]; dd = dd[::2, ::2]; h = np.where(y == 1, 1., np.where(y == 3, 1 - dd, 0.)); z = (np.arange(n) + .5) / n
    return ((y > 0)[..., None] & (z[None, None] < h[..., None])).transpose(1, 0, 2)[:, ::-1]
for j, 이름 in ((261, "기둥_261.png"), (605, "기둥_605.png")):
    fig = plt.figure(figsize=(8, 6)); a = fig.add_subplot(projection="3d"); a.voxels(기둥(M["39"]["P"][j], M["39"]["D"][j].astype(np.float32)), facecolors="tab:orange", edgecolor="k", linewidth=.03)
    a.set_xlim(0, 64); a.set_ylim(0, 64); a.set_zlim(0, 20); a.set_box_aspect((64, 64, 20)); a.view_init(35, -60); a.set_axis_off(); fig.subplots_adjust(0, 0, 1, 1); plt.savefig(A + 이름, dpi=80, transparent=True); plt.close(fig)
print("ok")
