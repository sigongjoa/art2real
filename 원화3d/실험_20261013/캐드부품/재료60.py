# 60 편 재료 — 182 번(꺾인 판): 3D 전후 · 입력 선 · 칠 비교 · 단면 · 과정 · 포갬 · 10-14
import sys, json, os, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import 짓기 as J
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"; A = "G:/art2real/out/영상05/대화/60_지어낸높이/자료/"; os.makedirs(A, exist_ok=True); j = 182
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0][:200]; X = d["X"][te[j]]; Y = d["Y"][te[j]]; D = d["D"][te[j]].astype(np.float32)
e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te[j]]; S = e["S"][te[j]]; L = json.load(open(O + "목록.json", encoding="utf-8"))
B = np.load(O + "학습2b/시험예측.npz"); P = B["P"][j]; PD = B["D"][j].astype(np.float32)
v, f, H = J.정규메시(L[te[j]]); 정 = J.점유_메시(v, f); 몸, _ = J.몸통37((X, F, S), H); 몸칸 = J.점유_캐드(몸); 끝 = J.점유_캐드(J.깎기(몸, P, PD, H, True))
ix = np.argwhere(정); lo, hi = ix.min(0), ix.max(0)
def 입체(q, 색, 이름, 빨=None):
    fig = plt.figure(figsize=(8, 6)); a = fig.add_subplot(projection="3d"); a.voxels(q, facecolors=색, edgecolor="k", linewidth=.1)
    if 빨 is not None: a.voxels(빨, facecolors=(.9, .2, .2, .35), edgecolor=(.6, 0, 0, .3), linewidth=.1)
    [getattr(a, "set_%slim" % k)(lo[i] - 1, hi[i] + 2) for i, k in enumerate("xyz")]; a.set_box_aspect(tuple(hi - lo + 3)); a.view_init(28, -58); a.set_axis_off()
    fig.subplots_adjust(0, 0, 1, 1); plt.savefig(A + 이름, dpi=80, transparent=True, bbox_inches="tight"); plt.close(fig)
입체(몸칸, "tab:orange", "틀.png"); 입체(끝, "tab:orange", "최종.png"); 입체(정, "tab:green", "정답.png"); 입체(끝, "tab:orange", "지워짐.png", 몸칸 & ~끝)
def 평(im, 이름, cmap=None, **k):
    fig = plt.figure(figsize=(6, 6)); plt.imshow(im, cmap=cmap, **k); plt.axis("off"); fig.subplots_adjust(0, 0, 1, 1); plt.savefig(A + 이름, dpi=80); plt.close(fig)
평(1 - X, "선_위.png", "gray"); 평(1 - F, "선_앞.png", "gray")
색 = np.array([[1, 1, 1], [.75, .75, .75], [.85, .2, .2], [.3, .5, .9]]); 평(색[Y], "칠_정답.png"); 평(색[P], "칠_모델.png")
r = Y.shape[0] // 2; x = np.arange(128)
def 깊(y, dd): return np.where(y == 3, dd, np.where(y == 2, 1., np.where(y == 1, 0., np.nan)))
fig = plt.figure(figsize=(9, 4))
for y, dd, c in ((Y, D, "tab:green"), (P, PD, "tab:red")): plt.fill_between(x, 0, np.nan_to_num(1 - 깊(y, dd)[r], nan=0), step="mid", color=c, alpha=.5)
plt.ylim(0, 1.05); plt.axis("off"); fig.subplots_adjust(0, 0, 1, 1); plt.savefig(A + "단면.png", dpi=90); plt.close(fig)
겹 = np.ones(X.shape + (3,)); 겹[X > 0] = [0, .6, 1]; 겹[F > 0] = [1, 0, .6]
fig = plt.figure(figsize=(6, 6)); plt.imshow(겹); plt.gca().add_patch(Circle((64, 50), 4, fill=False, ec="r", lw=4)); plt.axis("off"); fig.subplots_adjust(0, 0, 1, 1); plt.savefig(A + "포갬.png", dpi=80); plt.close(fig)
print("ok", 몸칸.sum(), 끝.sum(), 정.sum())
# 39 추가(회전 넣은 모델 · 세운 세 그림)
C = np.load(O + "학습39/시험예측.npz"); 입체(J.점유_캐드(J.깎기(몸, C["P"][j], C["D"][j].astype(np.float32), H, True)), "tab:orange", "회전최종.png")
u = (np.arange(128) + .5) / 128 * 1.1 - .55; fig = plt.figure(figsize=(8, 7)); a = fig.add_subplot(projection="3d")
r_, c_ = np.nonzero(X); a.scatter(u[c_], -u[r_], np.full(len(r_), -.55), s=3, c=[(0, .6, 1)])
r_, c_ = np.nonzero(F); a.scatter(u[c_], np.full(len(r_), .55), -u[r_], s=3, c=[(1, 0, .6)])
r_, c_ = np.nonzero(S); a.scatter(np.full(len(r_), .55), u[c_], -u[r_], s=3, c=[(.2, .7, .2)])
a.set_xlim(-.55, .55); a.set_ylim(-.55, .55); a.set_zlim(-.55, .55); a.view_init(22, -60); a.set_box_aspect((1, 1, 1)); a.set_xticks([]); a.set_yticks([]); a.set_zticks([])
fig.subplots_adjust(0, 0, 1, 1); plt.savefig(A + "세움.png", dpi=80, transparent=True); plt.close(fig); print("39 ok")
