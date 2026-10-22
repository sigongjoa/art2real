# 판정기준125 흐름도 — 머리만 바꿈(MLP → 트랜스포머) · 가져가는 것 / 안 하는 것 · 10-22
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"
D = "G:/art2real/out/설명/캐드부품/모델125/"
fig = plt.figure(figsize=(16, 10)); ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, 16); ax.set_ylim(0, 10)
def 상자(x, y, w, h, 글, 색="#eef2f7", 테="#555", fs=13): ax.add_patch(plt.Rectangle((x, y), w, h, fc=색, ec=테, lw=2)); ax.text(x + w / 2, y + h / 2, 글, ha="center", va="center", fontsize=fs)
def 화살(x0, y0, x1, y1): ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", lw=2.5, color="#333"))
ax.text(8, 9.5, "판정기준125 — 머리만 MLP 에서 트랜스포머로 (입력 · 데이터 · loss 그대로)", ha="center", fontsize=18, weight="bold")
상자(.3, 7.4, 2.6, 1.2, "3면도 세 장\n(124 와 같음)"); 화살(3.0, 8.0, 3.6, 8.0); 상자(3.6, 7.4, 2.8, 1.2, "얼린 Gemma\n벡터 3 개 × 768")
화살(6.5, 8.0, 7.1, 8.0)
상자(7.1, 5.6, 5.0, 3.0, "", "#e3f4e6", "#28a050"); ax.text(9.6, 8.25, "트랜스포머 머리 (새로)", ha="center", fontsize=14, weight="bold", color="#28a050")
for i in range(3): 상자(7.4 + i * 1.5, 7.2, 1.3, .6, f"그림 {('위','앞','옆')[i]}", "#ffffff", "#28a050", 11)
for i in range(6): 상자(7.3 + i * .78, 5.8, .68, .6, f"칸{i+1}", "#fff4dc", "#d9a020", 10)
ax.text(9.6, 6.75, "칸 6 개가 그림 3 장을 보고(cross) · 칸끼리도 봄(self) · 4 층", ha="center", fontsize=11)
화살(12.2, 7.1, 12.8, 7.1); 상자(12.8, 6.5, 2.9, 1.2, "칸마다 41 숫자\n(124 와 같은 꼴)", "#fff4dc", "#d9a020")
상자(.3, 5.6, 6.4, 1.3, "대조 = 모델124 MLP (같은 입력)\n시험 0.638 · 학습 0.669 · 자리 loss 시험 1.33", "#ffffff", "#999", 12)
상자(.3, 3.9, 15.4, 1.4, "", "#ffffff", "#999")
ax.text(.5, 5.0, "판정 (미리 적음 · 모두 넘어야 통과) — 자: 3/4 실루엣 IoU · 확인124 와 같은 학습 300 · 시험 299", fontsize=13, weight="bold")
ax.text(.6, 4.25, "1 조립 시험 ≥ 0.70      2 학습 300 ≥ 0.75      3 자리 loss 시험 ≤ 1.00      ·  셋 다 MLP ± 0.03 이면 → 머리 탓 아님, 입력 탓", fontsize=13)
상자(.3, .3, 7.6, 3.3, "", "#f2faf3", "#28a050"); ax.text(.5, 3.25, "가져가는 것", fontsize=14, weight="bold", color="#28a050")
for k, t in enumerate(["데이터 조립124 12269 (시험 300 따로)", "loss 식 그대로 (부피 순 칸 짝 · 항목 10)", "얼린 Gemma 벡터 입력 · 60 에폭 · 배치 128", "평가 자 · 부품 목록 (확인124 와 같음)"]): ax.text(.6, 2.6 - k * .6, "• " + t, fontsize=13)
상자(8.1, .3, 7.6, 3.3, "", "#fdf0f0", "#d8262b"); ax.text(8.3, 3.25, "안 하는 것", fontsize=14, weight="bold", color="#d8262b")
for k, t in enumerate(["Gemma 조각별 특징(화소 위치)은 아직 안 씀", "칸 짝 바꾸기(헝가리안) 안 함", "학습률만 3e-4 (트랜스포머 표준 · MLP 1e-3)", "단순 200 · G2 · 실물 평가는 이번엔 안 함"]): ax.text(8.4, 2.6 - k * .6, "• " + t, fontsize=13)
fig.savefig(D + "흐름125.png", dpi=70); print("끝")
