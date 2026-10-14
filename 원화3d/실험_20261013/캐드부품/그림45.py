# 새 칸 재기 — 669 번: 옛(tessellate + open3d) 대 새(기둥 선 교차) · 틀 · 깎은 것 · 10-14
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 짓기 as J
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; del d; e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te]; S = e["S"][te]; L = json.load(open(O + "목록.json", encoding="utf-8"))
B = np.load(O + "학습42/시험예측.npz"); 부품 = (669, 345); fig = plt.figure(figsize=(24, 6 * len(부품)))
for r, j in enumerate(부품):
    v, f, H = J.정규메시(L[te[j]]); 몸, _ = J.몸통37((X[j], F[j], S[j]), H); s = J.깎기(몸, B["P"][j], B["D"][j].astype(np.float32), H, True)
    옛정, 옛틀, 옛q = J.옛점유_메시(v, f), J.옛점유_캐드(몸), J.옛점유_캐드(s); 정, 틀, q = J.점유_메시(v, f), J.점유_캐드(몸), J.점유_캐드(s)
    점 = lambda a, b: (a & b).sum() / max((a | b).sum(), 1); ix = np.argwhere(정 | 틀 | 옛q); lo, hi = ix.min(0), ix.max(0)
    for c, (t, a, 빨) in enumerate((("정답", 정, None), ("옛 채점: 깎은 것 %.2f\n빨강 = 틀 밖 %d 칸" % (점(옛q, 옛정), (옛q & ~옛틀).sum()), 옛q & 옛틀, 옛q & ~옛틀), ("새 채점: 틀 %.2f" % 점(틀, 정), 틀, None), ("새 채점: 깎은 것 %.2f\n틀 밖 %d 칸" % (점(q, 정), (q & ~틀).sum()), q, None))):
        ax = fig.add_subplot(len(부품), 4, r * 4 + c + 1, projection="3d"); ax.voxels(a, facecolors="tab:green" if c == 0 else (.9, .55, .2, .5 if 빨 is not None else 1), edgecolor="k", linewidth=.03)
        if 빨 is not None: ax.voxels(빨, facecolors=(.9, .1, .1, .9), edgecolor="k", linewidth=.03)
        [getattr(ax, "set_%slim" % k)(lo[i] - 1, hi[i] + 2) for i, k in enumerate("xyz")]; ax.set_box_aspect(tuple(np.maximum(hi - lo + 3, 4))); ax.view_init(30, -58); ax.set_axis_off(); ax.set_title(("%d 번 · " % j if c == 0 else "") + t, fontsize=16)
fig.suptitle("채점기 고침 — 옛: CAD 를 메시로 바꿀 때 면이 빠져 칸이 틀 밖으로 튐 · 새: 기둥마다 선을 쏴 CAD 면과 만나는 점 사이만 채움\n새 채점기 검사: 틀 밖 0 · 두 번 재도 같음 · CAD 직접 판정과 무작위 300 점 모두 일치(문제 부품 6 개)", fontsize=18)
plt.savefig(O + "결과45_채점기.png", dpi=60, bbox_inches="tight")
