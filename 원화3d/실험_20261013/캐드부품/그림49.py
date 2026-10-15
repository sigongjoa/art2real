# 판정기준49 1 단계 그림 — 48³ 틀 < 0.3 인 134 개: 48 대 96 틀 점수 · 10-15
import json, os, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False; O = "G:/art2real/out/설명/캐드부품/"; 조 = O + "평가49/"
v48 = np.load(O + "부피IoU_46_42.npy"); 범 = json.load(open(O + "범위46.json")); v = {}
for fn in os.listdir(조):
    d = json.load(open(조 + fn, encoding="utf-8")); v.update({k: x[:2] for k, x in zip(d["자리"], d["값"])})
ks = sorted(v); a = v48[ks, 1]; b = np.array([v[k][1] for k in ks]); 차 = b - a
print("오름 > 0.1:", (차 > .1).sum(), " > 0.3:", (차 > .3).sum(), " 그대로(±0.02):", (abs(차) < .02).sum(), " 내림 < -0.02:", (차 < -.02).sum(), " 48 0 점:", (a == 0).sum(), "→ 96 도 0:", ((a == 0) & (b == 0)).sum())
print("많이 오른 자리(시험 번호):", [(범[ks[i]], round(a[i], 2), round(b[i], 2)) for i in np.argsort(-차)[:6]])
fig, ax = plt.subplots(1, 2, figsize=(16, 7))
ax[0].scatter(a, b, s=30, c=np.where(차 > .1, "tab:green", "tab:gray")); ax[0].plot([0, 1], [0, 1], "k--"); ax[0].plot([0, .9], [.1, 1], ":", c="tab:green")
ax[0].set_xlabel("48 칸 틀 점수", fontsize=16); ax[0].set_ylabel("96 칸 틀 점수", fontsize=16); ax[0].set_xlim(-.02, .5); ax[0].set_ylim(-.02, 1); ax[0].set_title("134 개 · 초록 = 0.1 넘게 오름 %d 개" % (차 > .1).sum(), fontsize=18)
ax[1].hist(차, bins=30, color="tab:blue"); ax[1].axvline(.1, c="tab:green", ls=":"); ax[1].set_xlabel("96 - 48", fontsize=16); ax[1].set_title("평균 +%.3f (기준 +0.1) → B 실패" % 차.mean(), fontsize=18)
fig.suptitle("판정기준49 1 단계 — 칸을 반으로 줄여도 틀 0.108 → 0.161", fontsize=22); plt.savefig(O + "결과49_낮.png", dpi=70, bbox_inches="tight")
