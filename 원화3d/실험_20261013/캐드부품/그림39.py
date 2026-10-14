# 판정기준39 결과 그림 — 부품마다 2b 대 39 · 막대 · 10-14
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"
a = np.load(O + "부피IoU_37_2b.npy"); b = np.load(O + "부피IoU_39_39.npy"); 틀 = b[:, 1]
f, ax = plt.subplots(1, 2, figsize=(16, 7))
x = ax[0]; x.scatter(틀, a[:, 0], s=18, c="tab:red", alpha=.5, label="예전 모델(포갬)"); x.scatter(틀, b[:, 0], s=18, c="tab:green", alpha=.6, label="회전 넣은 모델"); x.plot([0, 1], [0, 1], "k--", lw=1)
x.annotate("182 번", (틀[182], b[182, 0]), (틀[182] - .35, b[182, 0] + .02), fontsize=13, arrowprops=dict(arrowstyle="->")); x.annotate("", (틀[182], a[182, 0]), (틀[182], b[182, 0]), arrowprops=dict(arrowstyle="<-", color="g", lw=2))
x.set_xlabel("틀만 찍은 점수", fontsize=14); x.set_ylabel("모델이 깎은 뒤 점수", fontsize=14); x.legend(fontsize=13); x.set_title("점선 위 = 모델이 좋게 만듦 · 아래 = 망침", fontsize=15)
x = ax[1]; 이름 = ["틀만", "예전 모델\n(포갬)", "회전 넣은\n모델"]; v = [틀.mean(), a[:, 0].mean(), b[:, 0].mean()]; c = ["#999", "tab:red", "tab:green"]
x.bar(이름, v, color=c); [x.text(i, v[i] + .003, "%.3f" % v[i], ha="center", fontsize=15) for i in range(3)]; x.axhline(.704, color="k", ls="--"); x.text(-.4, .7055, "기준 0.704", fontsize=13, va="bottom")
x.set_ylim(.6, .72); x.set_title("시험 200 개 평균 · 망친 부품 97 → 87 · 깊이 오차 0.077 → 0.023", fontsize=15)
f.suptitle("판정기준39 회전 넣기 — 182 번 0.17 → 0.89 · 평균은 기준에 0.001 모자라 실패", fontsize=18)
plt.savefig(O + "결과39.png", dpi=75, bbox_inches="tight")
