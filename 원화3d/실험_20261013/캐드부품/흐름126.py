# 감사126 흐름도 — 파이프라인 단계마다 무엇을 비교하나 · 10-22
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, os
plt.rcParams["font.family"] = "Malgun Gothic"
D = "G:/art2real/out/설명/캐드부품/감사126/"; os.makedirs(D, exist_ok=True)
fig = plt.figure(figsize=(18, 9.5)); ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, 18); ax.set_ylim(0, 9.5)
ax.text(9, 9.05, "감사126 — 데이터가 넘어가는 자리마다 비교 (학습 없음 · 지금 모델 그대로)", ha="center", fontsize=19, weight="bold")
단 = ["사양\n(덩어리 · 자리)", "메시\n(CadQuery)", "3면도\n세 장", "Gemma\n벡터 3×768", "머리\n(MLP · 트랜스포머)", "칸 6×41", "사양 → 다시 짓기", "3/4 렌더\n→ IoU"]
for i, t in enumerate(단):
    x = .3 + i * 2.2; ax.add_patch(plt.Rectangle((x, 6.6), 1.9, 1.3, fc="#eef2f7", ec="#555", lw=2)); ax.text(x + .95, 7.25, t, ha="center", va="center", fontsize=12)
    if i < len(단) - 1: ax.annotate("", xy=(x + 2.2, 7.25), xytext=(x + 1.9, 7.25), arrowprops=dict(arrowstyle="-|>", lw=2))
검 = [("S1 라벨 왕복", 0, 7, "#d8262b", "정답 칸 → 디코드 → 다시 짓기 = 정답?\n덩어리 2+ IoU ≥ 0.98"),
      ("S2 입력 그림", 1, 2, "#d9a020", "3면도 위에 덩어리 자리 겹쳐 보기\n(눈으로)"),
      ("S3 탐침", 2, 3, "#28a050", "벡터만으로 자리 · 종류가 풀리나\nGemma 대 화소 대 평균"),
      ("S4 하나만 옮긴 짝", 2, 3, "#16a2b8", "덩어리 하나 옮기면 벡터가 바뀌나\n다른 부품 거리와 비교"),
      ("S5 채점 자", 6, 7, "#9b59b6", "자리 5 · 10 · 20 % 옮기면\nIoU 가 떨어지나"),
      ("S6 모델 안", 4, 4, "#4a7bd1", "칸 6 개가 세 그림 중\n어디를 보나(주의)")]
for k, (이름, a, b, c, 글) in enumerate(검):
    x0 = .3 + a * 2.2; x1 = .3 + b * 2.2 + 1.9; y = 5.9 - (k % 3) * .25
    ax.plot([x0, x1], [y + .5 - k * 0, y + .5 - k * 0], color=c, lw=5, alpha=.8) if False else ax.add_patch(plt.Rectangle((x0, 6.45 - k * .12), x1 - x0, .08, fc=c))
    bx = .3 + k * 2.95; ax.add_patch(plt.Rectangle((bx, 1.2), 2.75, 3.6, fc="#ffffff", ec=c, lw=3))
    ax.text(bx + 1.375, 4.35, 이름, ha="center", fontsize=14, weight="bold", color=c); ax.text(bx + 1.375, 3.0, 글, ha="center", va="center", fontsize=11.5)
    ax.text(bx + 1.375, 1.6, f"구간: {단[a].split(chr(10))[0]} → {단[b].split(chr(10))[0]}", ha="center", fontsize=10, color="#555")
ax.text(9, .5, "가져가는 것: 124 MLP · 125 트랜스포머 · 같은 시험 부품   ·   안 하는 것: 새 학습 · 구조 바꾸기 · 판정 전에 고치기", ha="center", fontsize=13)
fig.savefig(D + "흐름126.png", dpi=70); print("끝")
