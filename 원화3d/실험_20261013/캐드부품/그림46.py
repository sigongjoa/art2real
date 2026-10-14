# 판정기준46 — 옛 채점(누수 섞임) 대 새 채점(중복 뺀 712) · 틀 · 39 · 42 · 10-14
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"
r40, r42, r46 = (json.load(open(O + "결과%d.json" % k, encoding="utf-8")) for k in (40, 42, 46))
옛 = [r40["39"]["틀만"], r40["39"]["부피IoU"], r42["42"]["부피IoU"]]; 새 = [r46["42"]["틀"], r46["39"]["평균"], r46["42"]["평균"]]
f, ax = plt.subplots(1, 2, figsize=(18, 7)); x = np.arange(3); 이름 = ["틀만", "39\n(예전 학습)", "42\n(부피 벌점)"]
for a, v, t, c in ((ax[0], 옛, "옛 채점 · 803 개(같은 부품 91 섞임)\n— 철회", ["#bbb"] * 3), (ax[1], 새, "새 채점 · 학습과 같은 부품 뺀 712 개", ["#777", "tab:red", "tab:green"])):
    a.bar(x, v, color=c); [a.text(i, v[i] + .001, "%.3f" % v[i], ha="center", fontsize=16) for i in range(3)]; a.axhline(v[0] + .01, ls="--", c="k"); a.text(2.45, v[0] + .0105, "기준", fontsize=13, ha="right")
    a.set_xticks(x, 이름, fontsize=15); a.set_ylim(.62, .675); a.set_title(t, fontsize=16)
ax[1].text(1, .624, "42 망침 247 / 712 (35 %) · 크게 62 (9 %)\n39 망침 298 · 크게 84 · 기준 못 넘음", ha="center", fontsize=14)
f.suptitle("판정기준46 — 채점기를 고치고 겹친 부품을 빼도 42 는 기준을 넘는다(+0.018) · 39 는 못 넘는다(+0.007)", fontsize=18)
plt.savefig(O + "결과46.png", dpi=70, bbox_inches="tight")
