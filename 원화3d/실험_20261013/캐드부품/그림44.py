# 판정기준44 — 고친 짓기로 다시 채점 · 전후 막대 + 남은 틀 밖 칸(669 번 · CAD 는 유효 · 메시가 안 닫힘) · 10-14
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 짓기 as J
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False; O = "G:/art2real/out/설명/캐드부품/"
r40, r42, r44 = (json.load(open(O + "결과%d.json" % k, encoding="utf-8")) for k in (40, 42, 44))
fig = plt.figure(figsize=(24, 8))
ax = fig.add_subplot(1, 3, 1); 이름 = ["틀만", "39", "42"]; 전 = [r40["39"]["틀만"], r40["39"]["부피IoU"], r42["42"]["부피IoU"]]; 후 = [r44["42"]["틀 평균"], r44["39"]["원래 평균"], r44["42"]["원래 평균"]]
x = np.arange(3); ax.bar(x - .2, 전, .4, color="#bbb", label="고치기 전"); ax.bar(x + .2, 후, .4, color=["#777", "tab:red", "tab:green"], label="고친 뒤")
[ax.text(i + dx, v + .001, "%.3f" % v, ha="center", fontsize=13) for i in range(3) for dx, v in ((-.2, 전[i]), (.2, 후[i]))]; ax.axhline(후[0] + .01, ls="--", c="k"); ax.set_xticks(x, 이름, fontsize=15); ax.set_ylim(.64, .675); ax.legend(fontsize=13); ax.set_title("새 803 개 평균 · 점선 = 기준(틀 + 0.01)", fontsize=15)
ax = fig.add_subplot(1, 3, 2); ax.axis("off")
ax.text(0, .5, "깎은 CAD 무효: 63 → 0 개\n틀 밖 칸 있는 부품: 68 → 34 개\n  (대부분 1 ~ 5 칸 · 큰 것 3 개)\n42 망침: 282 → 266 · 크게 망침: 73 → 63\n39 도 고친 뒤 0.658 → 기준(0.658) 넘음\n\n판정 A 실패(34 > 5) · 판정 B(42 유지) 통과", fontsize=18, va="center")
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; del d; e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te]; S = e["S"][te]; L = json.load(open(O + "목록.json", encoding="utf-8"))
B = np.load(O + "학습42/시험예측.npz"); j = 669; v, f, H = J.정규메시(L[te[j]]); 몸, _ = J.몸통37((X[j], F[j], S[j]), H); 틀 = J.점유_캐드(몸); q = J.점유_캐드(J.깎기(몸, B["P"][j], B["D"][j].astype(np.float32), H, True))
ix = np.argwhere(틀 | q); lo, hi = ix.min(0), ix.max(0); ax = fig.add_subplot(1, 3, 3, projection="3d"); ax.voxels(q & 틀, facecolors=(.9, .55, .2, .3), edgecolor="k", linewidth=.03); ax.voxels(q & ~틀, facecolors=(.9, .1, .1, .9), edgecolor="k", linewidth=.03)
[getattr(ax, "set_%slim" % k)(lo[i] - 1, hi[i] + 2) for i, k in enumerate("xyz")]; ax.set_box_aspect(tuple(np.maximum(hi - lo + 3, 4))); ax.view_init(30, -58); ax.set_axis_off()
ax.set_title("남은 것: 669 번 · CAD 는 유효 · 부피도 맞게 줄었는데\n칸으로 바꾸는 메시가 안 닫혀 빨강 %d 칸이 생김" % (q & ~틀).sum(), fontsize=15)
fig.suptitle("판정기준44 — 맞닿은 다각형 고침: 깨진 CAD 는 0 · 남은 틀 밖 칸은 「CAD → 칸」 바꾸기 쪽 문제", fontsize=19)
plt.savefig(O + "결과44.png", dpi=60, bbox_inches="tight")
