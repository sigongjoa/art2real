# 판정기준123 흐름도 — 3면도 세 장 → 얼린 Gemma 장마다 → 이어 붙여 같은 머리 · 10-21
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch as B, FancyArrowPatch as A
plt.rcParams["font.family"] = "Malgun Gothic"
fig = plt.figure(figsize=(18, 9)); W = fig.add_axes([0, 0, 1, 1]); W.set_xlim(0, 18); W.set_ylim(0, 9); W.axis("off")
def 칸(x, y, w, h, t, s, c): W.add_patch(B((x, y), w, h, boxstyle="round,pad=.05", fc=c, ec="#555")); W.text(x + w / 2, y + h - .35, t, ha="center", fontsize=13, weight="bold"); W.text(x + w / 2, y + h / 2 - .2, s, ha="center", va="center", fontsize=10.5)
def 화(a, b): W.add_patch(A(a, b, arrowstyle="-|>", mutation_scale=18, color="#333"))
for k, (nm, y) in enumerate((("위", 7.0), ("앞", 5.4), ("옆", 3.8))):
    칸(.3, y, 3.0, 1.3, f"3면도 · {nm}", "실선 검정 · 숨은선 회색 점선 · 중심선 빨강", "#fde68a"); 칸(4.0, y, 2.6, 1.3, "Gemma (얼림)", "그림 → 768", "#dbeafe"); 화((3.35, y + .65), (3.95, y + .65)); 화((6.65, y + .65), (7.55, 5.95))
칸(7.6, 4.8, 3.6, 2.4, "머리 (120 과 같은 구조)", "768 × 3 = 2304 이어 붙임\n→ 종류 · 치수 · 구멍 · 홈\n필렛 · 기울임", "#fef3c7")
칸(11.9, 4.8, 2.6, 2.4, "CAD (계산)", "코드 → 3D", "#dcfce7"); 칸(15.1, 4.8, 2.6, 2.4, "채점", "같은 3/4 시점 IoU\n특징 종류\n구멍 자리 오차", "#dcfce7")
화((11.25, 6.0), (11.85, 6.0)); 화((14.55, 6.0), (15.05, 6.0))
W.text(.3, 2.9, "대조", fontsize=14, weight="bold"); W.text(.3, 2.35, "120: 무작위 시점 그림 한 장(특징 다 맞음 0.66 · 구멍 자리 0.312)   ·   한 장씩: 위만 · 앞만 · 옆만 — 세 장을 합친 덕인지", fontsize=12)
W.text(.3, 1.6, "통과 (미리 적음)", fontsize=14, weight="bold"); W.text(.3, 1.05, "생성 시험 200: 특징 다 맞음 ≥ 0.75 · 구멍 자리 오차 < 120 · 3/4 IoU > 120   ·   G1 3/4 IoU ≥ 0.97   ·   G2 보고만", fontsize=12)
W.text(.3, .4, "가져가는 것: 같은 사양 6197 · 같은 나눔 · 얼린 Gemma · 같은 머리 · 숨은선88   |   안 하는 것: 121 다듬기 · 인코더 학습 · 어휘 늘리기   |   시간: 3면도 약 15 분 · 임베딩 18,600 장 약 1 시간", fontsize=11, color="#444")
fig.suptitle("판정기준123 — 그림 한 장 대신 3면도 세 장 · 모델 구조는 그대로", fontsize=18, y=.99)
plt.savefig("G:/art2real/out/설명/캐드부품/흐름123.png", dpi=75)
