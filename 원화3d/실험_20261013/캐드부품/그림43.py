# 판정기준43 — 깎기 CAD 깨짐 예시(원래 · 고친 = 깎은 칸 ∩ 틀) + 점수 · 10-14
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 짓기 as J
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False; O = "G:/art2real/out/설명/캐드부품/"
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; del d
e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te]; S = e["S"][te]; L = json.load(open(O + "목록.json", encoding="utf-8"))
B = np.load(O + "학습42/시험예측.npz"); v = np.load(O + "진단43_42.npy"); 고른 = [int(k) + 200 for k in np.argsort(-v[:, 3])[:3]]
fig = plt.figure(figsize=(24, 5.2 * len(고른) + 4))
for r, j in enumerate(고른):
    vv, f, H = J.정규메시(L[te[j]]); 정 = J.점유_메시(vv, f); 몸, _ = J.몸통37((X[j], F[j], S[j]), H); 틀 = J.점유_캐드(몸); s = J.깎기(몸, B["P"][j], B["D"][j].astype(np.float32), H, True); q = J.점유_캐드(s)
    점 = lambda a: (a & 정).sum() / max((a | 정).sum(), 1); ix = np.argwhere(정 | 틀 | q); lo, hi = ix.min(0), ix.max(0)
    for c, (t, a, cc, 빨) in enumerate((("정답", 정, "tab:green", None), ("틀 %.2f" % 점(틀), 틀, "tab:orange", None), ("깎은 결과 (CAD 깨짐) %.2f" % 점(q), q & 틀, "tab:orange", q & ~틀), ("고친 채점: 틀 안만 %.2f" % 점(q & 틀), q & 틀, "tab:orange", None))):
        ax = fig.add_subplot(len(고른) + 1, 4, r * 4 + c + 1, projection="3d"); ax.voxels(a, facecolors=cc, edgecolor="k", linewidth=.04)
        if 빨 is not None: ax.voxels(빨, facecolors=(.9, .1, .1, .8), edgecolor="k", linewidth=.04)
        [getattr(ax, "set_%slim" % k)(lo[i] - 1, hi[i] + 2) for i, k in enumerate("xyz")]; ax.set_box_aspect(tuple(np.maximum(hi - lo + 3, 4))); ax.view_init(30, -58); ax.set_axis_off()
        ax.set_title(("%d 번 · " % j if c == 0 else "") + t + (" · 빨강 = 틀 밖으로 튄 칸 %d" % (q & ~틀).sum() if c == 2 else ""), fontsize=15)
r43 = json.load(open(O + "결과43.json", encoding="utf-8")); ax = fig.add_subplot(len(고른) + 1, 2, 2 * len(고른) + 1)
이름 = ["틀만", "39 원래", "39 고침", "42 원래", "42 고침"]; 값 = [r43["42"]["틀 평균"], r43["39"]["원래 평균"], r43["39"]["고친 평균"], r43["42"]["원래 평균"], r43["42"]["고친 평균"]]
ax.bar(이름, 값, color=["#999", "#e99", "tab:red", "#9d9", "tab:green"]); [ax.text(i, 값[i] + .001, "%.3f" % 값[i], ha="center", fontsize=14) for i in range(5)]; ax.axhline(r43["42"]["틀 평균"] + .01, ls="--", c="k"); ax.set_ylim(.64, .672); ax.set_title("새 803 개 평균 · 점선 = 기준(틀 + 0.01)", fontsize=15)
ax = fig.add_subplot(len(고른) + 1, 2, 2 * len(고른) + 2); ax.axis("off")
ax.text(0, .5, "틀 밖으로 튄 칸이 있는 부품: 39 → %d 개 · 42 → %d 개 (803 개 중)\n깎은 CAD 가 무효: 39 → %d · 42 → %d · 틀 자체 무효 2\n고친 채점으로 42: 망침 282 → %d · 크게 망침 73 → %d → 판정42 유지" % (r43["39"]["틀 밖 칸 있는 부품"], r43["42"]["틀 밖 칸 있는 부품"], r43["39"]["깎은 모양 무효"], r43["42"]["깎은 모양 무효"], r43["42"]["고친 망침"], r43["42"]["고친 크게 망침"]), fontsize=17, va="center")
fig.suptitle("판정기준43 — 깎기 CAD 깨짐: 약 1 할 부품에서 틀 밖으로 칸이 튄다 · 틀 안으로 자르면 점수는 조금 오르고 판정42 는 그대로", fontsize=19)
plt.savefig(O + "결과43.png", dpi=55, bbox_inches="tight"); print(고른)
