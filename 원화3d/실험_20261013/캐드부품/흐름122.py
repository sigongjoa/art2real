# 판정기준122 흐름도 — 머리에 시점 정보를 입력으로 · 10-21
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch as B, FancyArrowPatch as A
plt.rcParams["font.family"] = "Malgun Gothic"
fig = plt.figure(figsize=(18, 9)); W = fig.add_axes([0, 0, 1, 1]); W.set_xlim(0, 18); W.set_ylim(0, 9); W.axis("off")
def 칸(x, y, w, h, t, s, c): W.add_patch(B((x, y), w, h, boxstyle="round,pad=.05", fc=c, ec="#555")); W.text(x + w / 2, y + h - .35, t, ha="center", fontsize=14, weight="bold"); W.text(x + w / 2, y + h / 2 - .2, s, ha="center", va="center", fontsize=10.5)
def 화(a, b): W.add_patch(A(a, b, arrowstyle="-|>", mutation_scale=18, color="#333"))
칸(.3, 6.2, 3.0, 2.0, "그림 (120 과 같음)", "무작위 시점 렌더 6197", "#eeeeee")
칸(.3, 3.9, 3.0, 2.0, "시점 (새로)", "방위 · 고도\n렌더할 때 쓴 값", "#fde68a")
칸(4.0, 6.2, 3.0, 2.0, "Gemma (얼림)", "그림 → 768", "#dbeafe")
칸(7.8, 5.0, 3.6, 2.4, "머리 (다시 학습)", "768 + sin · cos 방위 · 고도\n→ 종류 · 치수 · 구멍 · 홈\n필렛 · 기울임", "#fef3c7")
칸(12.1, 5.0, 2.6, 2.4, "CAD (계산)", "코드 → 3D", "#dcfce7")
칸(15.3, 5.0, 2.4, 2.4, "채점", "같은 시점 IoU\n특징 종류\n구멍 자리 오차", "#dcfce7")
화((3.35, 7.2), (3.95, 7.2)); 화((7.05, 7.0), (7.75, 6.6)); 화((3.35, 4.9), (7.75, 5.6)); 화((11.45, 6.2), (12.05, 6.2)); 화((14.75, 6.2), (15.25, 6.2))
W.text(.3, 3.0, "대조", fontsize=14, weight="bold"); W.text(.3, 2.45, "없음: 시점 없이 같은 학습(120 다시)   ·   섞음: 시점 칸에 다른 짝의 시점 — 칸이 늘어서가 아니라 값 때문인지", fontsize=12)
W.text(.3, 1.7, "통과 (미리 적음)", fontsize=14, weight="bold"); W.text(.3, 1.15, "생성 시험 200: 특징 종류 다 맞음 ≥ 0.75(120 0.66) · 같은 시점 IoU 중앙 > 없음 · 구멍 자리 오차 < 없음 · 섞음은 셋 다 시점보다 나쁨", fontsize=12)
W.text(.3, .45, "가져가는 것: 120 데이터 · 렌더 · 임베딩 그대로(1 분 학습)   |   안 하는 것: 121 다듬기(다음에 붙임) · 여러 장 입력 · 어휘 늘리기", fontsize=11, color="#444")
fig.suptitle("판정기준122 — 모델에 시점 정보를 준다", fontsize=18, y=.99)
plt.savefig("G:/art2real/out/설명/캐드부품/흐름122.png", dpi=75)
