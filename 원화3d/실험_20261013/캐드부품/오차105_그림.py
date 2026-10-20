# 오차105 그림 — 영역마다 「몇 층 틀렸나」 화소 몫 대 손실 몫(시험 300) · 10-20
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"
D = "G:/art2real/out/설명/캐드부품/손실103/"; d = json.load(open(D + "오차.json", encoding="utf-8"))["시험"]
색 = ["#1f9a50", "#9ccc65", "#f0c040", "#f08030", "#d8262b"]; fig, ax = plt.subplots(figsize=(13, 5.5)); y = 0; 표 = []
for k, v in d.items():
    for 줄, 키 in (("화소", "화소 몫"), ("손실", "손실 몫")):
        x = 0
        for j, (칸, b) in enumerate(v.items()):
            w = b[키]; ax.barh(y, w, left=x, color=색[j], edgecolor="w", label=칸 if y == 0 else None)
            if w > .04: ax.text(x + w / 2, y, f"{w:.2f}", ha="center", va="center", fontsize=9)
            x += w
        표.append(f"{k} · {줄}"); y += 1
    y += .5
ax.set_yticks([i + (i // 2) * .5 for i in range(len(표))]); ax.set_yticklabels(표); ax.invert_yaxis(); ax.set_xlim(0, 1); ax.legend(ncol=5, loc="upper center", bbox_to_anchor=(.5, -.08))
ax.set_title("판0 시험 300 · 몇 층 틀렸나 — 맞거나 1 층만 틀린 화소(초록 둘)가 안 전체 손실의 절반(0.48)을 낸다", fontsize=13)
plt.tight_layout(); plt.savefig(D + "오차.png", dpi=80); print("저장")
