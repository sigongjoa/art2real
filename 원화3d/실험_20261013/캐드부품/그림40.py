# 판정기준40 결과 — 앞 200 개 대 새 803 개 · 10-14
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False; O = "G:/art2real/out/설명/캐드부품/"
r39, r40 = json.load(open(O + "결과39.json", encoding="utf-8")), json.load(open(O + "결과40.json", encoding="utf-8")); a = np.load(O + "부피IoU_40_39.npy"); b = np.load(O + "부피IoU_40_2b.npy")
f, ax = plt.subplots(1, 2, figsize=(17, 7))
x = ax[0]; 묶 = [("앞 200 개\n(39 에서 잰 것)", .694, .678, .703), ("새 803 개\n(처음 재 봄)", r40["39"]["틀만"], r40["2b"]["부피IoU"], r40["39"]["부피IoU"])]
for i, (t, 틀, 예, 회) in enumerate(묶):
    for k, (v, c, n) in enumerate(((틀, "#999", "틀만"), (예, "tab:red", "예전 모델"), (회, "tab:green", "회전 모델"))):
        x.bar(i * 4 + k, v, color=c, label=n if i == 0 else None); x.text(i * 4 + k, v + .002, "%.3f" % v, ha="center", fontsize=14)
x.set_xticks([1, 5], [m[0] for m in 묶], fontsize=14); x.set_ylim(.6, .72); x.legend(fontsize=13); x.set_title("평균 점수 — 회전 모델은 두 묶음 모두 예전보다 +0.02 · 틀보다는 +0.006 ~ 0.009", fontsize=14)
x = ax[1]; 틀 = a[:, 1]
x.hist(np.clip(b[:, 0] - 틀, -.6, .6), bins=40, range=(-.6, .6), color="tab:red", alpha=.45, label="예전 모델 - 틀 (망침 %d)" % r40["2b"]["망침"]); x.hist(np.clip(a[:, 0] - 틀, -.6, .6), bins=40, range=(-.6, .6), color="tab:green", alpha=.55, label="회전 모델 - 틀 (망침 %d)" % r40["39"]["망침"])
x.axvline(0, color="k", lw=1); x.set_xlabel("모델이 깎은 뒤 - 틀만 (0 보다 왼쪽 = 망침)", fontsize=14); x.legend(fontsize=13); x.set_title("새 803 개 · 부품마다 · 회전 모델도 44 % 는 틀보다 나빠짐", fontsize=14)
f.suptitle("판정기준40 — 새 부품 803 개에서도 회전은 통한다(예전보다 +0.023) · 그래도 틀을 확실히 넘지 못해 실패(A · D)", fontsize=17)
plt.savefig(O + "결과40.png", dpi=75, bbox_inches="tight")
