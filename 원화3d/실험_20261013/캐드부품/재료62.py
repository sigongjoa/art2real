# 62 편 재료 — 669 번 옛 채점(틀 밖 빨강) · 새 채점 · 겹친 부품 쌍(학습 · 시험 같은 그림) · 10-14
import json, os, hashlib, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/"; A = "G:/art2real/out/영상05/대화/62_채점기/자료/"; os.makedirs(A, exist_ok=True)
d = np.load(O + "데이터.npz"); 시 = d["시험"]; te = np.nonzero(시)[0]; Xa, Ya, Da = d["X"], d["Y"], d["D"]; del d; X = Xa[te]
e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te]; S = e["S"][te]; L = json.load(open(O + "목록.json", encoding="utf-8")); B = np.load(O + "학습42/시험예측.npz")
j = 669; v, f, H = J.정규메시(L[te[j]]); 몸, _ = J.몸통37((X[j], F[j], S[j]), H); s = J.깎기(몸, B["P"][j], B["D"][j].astype(np.float32), H, True)
옛틀, 옛q, 틀, q = J.옛점유_캐드(몸), J.옛점유_캐드(s), J.점유_캐드(몸), J.점유_캐드(s); ix = np.argwhere(틀 | 옛q); lo, hi = ix.min(0), ix.max(0)
def 입체(a, 빨, 이름):
    fig = plt.figure(figsize=(8, 7)); ax = fig.add_subplot(projection="3d"); ax.voxels(a, facecolors=(.9, .55, .2, .55 if 빨 is not None else 1), edgecolor="k", linewidth=.04)
    if 빨 is not None: ax.voxels(빨, facecolors=(.9, .1, .1, .95), edgecolor="k", linewidth=.04)
    [getattr(ax, "set_%slim" % k)(lo[i] - 1, hi[i] + 2) for i, k in enumerate("xyz")]; ax.set_box_aspect(tuple(np.maximum(hi - lo + 3, 4))); ax.view_init(30, -58); ax.set_axis_off()
    fig.subplots_adjust(0, 0, 1, 1); plt.savefig(A + 이름, dpi=80, transparent=True); plt.close(fig)
입체(옛q & 옛틀, 옛q & ~옛틀, "옛.png"); 입체(q, None, "새.png"); 입체(틀, None, "틀.png")
옛q2 = J.옛점유_캐드(s); 입체(옛q2 & 옛틀, 옛q2 & ~옛틀, "옛_두번째.png"); print("두 번째 틀 밖", (옛q2 & ~옛틀).sum())
h = lambda i: hashlib.md5(Xa[i].tobytes() + Ya[i].tobytes() + Da[i].tobytes()).hexdigest(); 학 = {}
for i in np.nonzero(~시)[0]: 학.setdefault(h(i), i)
후 = [i for i in te[200:] if h(i) in 학]; 쌍 = (lambda i: (i, 학[h(i)]))(max(후, key=lambda i: int(Xa[i].sum()) * ((Ya[i] > 0).sum() > 3000)))
for k, i in enumerate(쌍):
    fig = plt.figure(figsize=(6, 6)); plt.imshow(1 - Xa[i], cmap="gray"); plt.axis("off"); fig.subplots_adjust(0, 0, 1, 1); plt.savefig(A + "겹침_%d.png" % k, dpi=80); plt.close(fig)
print("ok", (옛q & ~옛틀).sum(), (q & ~틀).sum(), [L[i] for i in 쌍])
