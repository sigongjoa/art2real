# 진단59 그림 — 데이터 양 곡선(학습 부품 수 → 712 CAD · 층 맞음) · 폭 2 배 판은 나오면 점 하나 더 · 10-17
import json, os, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"
n = np.array([2205, 4410, 8821]); cad = np.array([json.load(open(O + "진단59_%s/결과.json" % d, encoding="utf-8"))["CAD 평균"] for d in ("F25", "F50")] + [0.6964]); 층 = np.array([0.765, 0.804, 0.817])
f, ax = plt.subplots(1, 2, figsize=(15, 6))
for a, y, 제 in ((ax[0], cad, "712 개 CAD 부피 IoU"), (ax[1], 층, "깊이 층 맞음(통째 아닌 곳)")):
    a.plot(n, y, "o-", color=(.16, .63, .31), lw=3, ms=10)
    for x, v in zip(n, y): a.annotate("%.3f" % v, (x, v), textcoords="offset points", xytext=(0, 12), ha="center", fontsize=14)
    k = np.polyfit(np.log2(n[1:]), y[1:], 1); xs = np.array([8821, 17642, 55310]); a.plot(xs, np.polyval(k, np.log2(xs)), "--", color=(.6, .6, .65), lw=2)
    a.annotate("추정 %.3f\n(5.5 만 · 뒤 두 점 기울기)" % np.polyval(k, np.log2(55310)), (55310, np.polyval(k, np.log2(55310))), textcoords="offset points", xytext=(-10, -45), ha="right", fontsize=12, color=(.4, .4, .45))
    a.set_xscale("log", base=2); a.set_xticks([2205, 4410, 8821, 17642, 55310]); a.set_xticklabels(["2,205\n(25 %)", "4,410\n(50 %)", "8,821\n(지금)", "17,642", "55,310\n(받아 둔 전부)"]); a.set_title(제, fontsize=16); a.grid(alpha=.3)
if os.path.exists(O + "진단59_W2/결과.json"):
    w = json.load(open(O + "진단59_W2/결과.json", encoding="utf-8"))["CAD 평균"]; ax[0].plot([8821], [w], "s", color=(.86, .2, .2), ms=12); ax[0].annotate("폭 2 배 %.3f" % w, (8821, w), textcoords="offset points", xytext=(14, -4), fontsize=13, color=(.86, .2, .2))
ax[0].axhline(0.9, color=(.86, .63, .12), ls=":", lw=2); ax[0].text(2300, 0.893, "목표 0.9", color=(.86, .63, .12), fontsize=12); ax[0].axhline(0.803, color=(.5, .5, .5), ls=":", lw=1.5); ax[0].text(2300, 0.796, "깎기 천장 0.803", color=(.4, .4, .4), fontsize=12)
f.suptitle("진단59 — 데이터를 두 배로 늘릴 때마다 오르는 폭: CAD +0.032 → +0.012 · 층 +0.039 → +0.013", fontsize=17); plt.tight_layout(); plt.savefig(O + "../진단59_데이터곡선.png", dpi=80); print("ok")
