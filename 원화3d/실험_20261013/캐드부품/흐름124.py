# 판정기준124 흐름도 — 데이터 · 학습 · 판정 · 가져가는 것 / 안 하는 것 · 10-21
import json, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from PIL import Image
plt.rcParams["font.family"] = "Malgun Gothic"
D = "G:/art2real/out/설명/캐드부품/모델124/"
fig = plt.figure(figsize=(16, 10)); ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, 16); ax.set_ylim(0, 10)
def 상자(x, y, w, h, 글, 색="#eef2f7", 테="#555"): ax.add_patch(plt.Rectangle((x, y), w, h, fc=색, ec=테, lw=2)); ax.text(x + w / 2, y + h / 2, 글, ha="center", va="center", fontsize=13)
def 화살(x0, y0, x1, y1): ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", lw=2.5, color="#333"))
ax.text(8, 9.5, "판정기준124 — 복잡한 부품을 만들어 학습 (모델 구조 · 입력 그대로, 데이터만 복잡하게)", ha="center", fontsize=17, weight="bold")
ex = ax.inset_axes([0.2, 5.6, 4.6, 3.3], transform=ax.transData); ex.imshow(Image.open(D + "예시.png")); ex.axis("off")
상자(0.2, 4.6, 4.6, .8, "① 조립124: 몸 1~6 개를 축 z·x·y 로 붙임\n12000 학습 + 300 시험 (막대 · 판 비율 포함)", "#fff4dc", "#d9a020")
화살(4.9, 5.0, 5.6, 5.0); 상자(5.6, 4.6, 3.0, .8, "② 3면도 세 장\n(123b 와 같은 그림)")
화살(8.7, 5.0, 9.3, 5.0); 상자(9.3, 4.6, 2.6, .8, "③ 얼린 Gemma\n768 × 3")
화살(12.0, 5.0, 12.6, 5.0); 상자(12.6, 4.6, 3.2, .8, "④ MLP 머리 → 몸 칸 6 개\n종류·치수·축·자리·구멍", "#e3f4e6", "#28a050")
상자(5.6, 6.2, 10.2, 2.6, "", "#ffffff", "#999")
ax.text(5.8, 8.5, "판정 (미리 적음 · 모두 넘어야 통과) — 자: 3/4 시점 실루엣 IoU", fontsize=13, weight="bold")
for k, t in enumerate(["1 조립 시험 300  ≥ 0.85", "2 복잡 실물 12 (로봇·거미·부엉이)  ≥ 0.60   ← 123b 0.501", "3 G2 실제 CAD 20  ≥ 0.55   ← 123b 0.452", "4 단순 생성 시험 200  ≥ 0.93   ← 123b 0.960 (잊지 않음)"]): ax.text(6.0, 7.9 - k * .45, t, fontsize=13)
ax.text(6.0, 6.35, "대조: 123b 머리(단순 데이터)를 같은 입력에 · 에폭마다 고정 6 렌더", fontsize=12, color="#555")
상자(0.2, .4, 7.6, 3.6, "", "#f2faf3", "#28a050"); ax.text(0.4, 3.7, "가져가는 것", fontsize=14, weight="bold", color="#28a050")
for k, t in enumerate(["3면도 입력 · 중심선 없음(정답 샘 막은 그대로)", "얼린 Gemma 인코더 · 학습은 머리만", "7 종류 몸 · 구멍 · 홈 · 필렛 낱말", "123b 의 평가 집합(G1 · G2 · 단순 200 · 실물 12)"]): ax.text(0.5, 3.2 - k * .65, "• " + t, fontsize=13)
상자(8.2, .4, 7.6, 3.6, "", "#fdf0f0", "#d8262b"); ax.text(8.4, 3.7, "안 하는 것", fontsize=14, weight="bold", color="#d8262b")
for k, t in enumerate(["새 종류(구 · 톱니 · 나사산) 추가 안 함", "축 맞춤(G2 세우기) 안 함 — 따로 잼", "실물 메시로 학습 안 함(정답 코드가 없음)", "자세 찾기 · 다듬기(121) 안 붙임"]): ax.text(8.5, 3.2 - k * .65, "• " + t, fontsize=13)
fig.savefig(D + "흐름124.png", dpi=70); print("끝")
