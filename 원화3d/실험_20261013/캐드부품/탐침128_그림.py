# 탐침128 결과 한 장 — 블록별 구조 가르기 · 곡률 R² (학습 CNN · 무작위 CNN · 화소) + 예시 + 혼동 · 10-22
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from PIL import Image
plt.rcParams["font.family"] = "Malgun Gothic"
D = "G:/art2real/out/설명/캐드부품/탐침128/"; j = json.load(open(D + "결과.json", encoding="utf-8"))
fig = plt.figure(figsize=(20, 12)); fig.suptitle("탐침128 — 모델127 CNN 은 곡률 · 접합 · 교차를 잘 못 가름 (기준: 구조 ≥ 0.90 · 곡률 R² ≥ 0.80)", fontsize=18, weight="bold")
for t, (키, 제, 기준) in enumerate((("구조 6 종", "구조 6 종 가르기 정확도 (찍기 0.17)", .9), ("곡률 R²", "곡선 log 반지름 R²", .8))):
    ax = fig.add_axes([.04 + t * .32, .55, .28, .35]); b = np.arange(4)
    for k, (이름, c, S) in enumerate((("127 CNN(학습)", "#28a050", "128"), ("127 CNN(학습)", "#9b59b6", "256"), ("무작위 CNN", "#888", "128"))):
        v = [max(j[f"{이름} 블록 {i + 1}"][S][키], -.2) for i in range(4)]; ax.bar(b + (k - 1) * .27, v, .27, color=c, label=f"{이름} · {S}")
    ax.axhline(j["가운데 15×15 화소"]["128"][키], color="#d8262b", ls="--", lw=2, label="가운데 15×15 화소 그대로"); ax.axhline(기준, color="k", ls=":", lw=1.5, label="기준")
    ax.set_xticks(b); ax.set_xticklabels([f"블록 {i + 1}\n(시야 {r} 화소)" for i, r in enumerate((7, 19, 43, 91))], fontsize=11); ax.set_ylim(-.2, 1); ax.set_title(제, fontsize=14); ax.legend(fontsize=10, loc="upper left"); ax.spines[["top", "right"]].set_visible(False)
ax = fig.add_axes([.68, .5, .3, .42]); ax.imshow(Image.open(D + "예시.png")); ax.axis("off"); ax.set_title("합성 그림 예시 (빨강 + = 구조 가운데 · 그 칸 특징으로 탐침)", fontsize=13)
ax = fig.add_axes([.03, .02, .62, .45]); ax.imshow(Image.open(D + "혼동.png")); ax.axis("off")
ax = fig.add_axes([.68, .05, .3, .38]); ax.axis("off")
for k, s in enumerate(["• 학습이 무언가는 배웠다: 블록 4 0.59 vs 무작위 0.33", "• 그런데 가운데 15×15 화소를 그대로 쓴 것(0.62)과 비슷", "• 곡률 R² 0.43 — 곡선 · T 접합이 가장 헷갈림", "• 같은 CNN 에 256 그림을 넣으면 0.59 → 0.76", "   (T 접합 0.43 → 0.75 · 실선×숨은선 0.55 → 0.86)", "• 블록 1 · 2 는 시야 7 · 19 화소라 구조 전체를", "   못 봄(탐침 설계상 낮은 게 정상)"]):
    ax.text(0, .95 - k * .13, s, fontsize=13.5)
fig.savefig(D + "그림_탐침128.png", dpi=62); print("끝")
