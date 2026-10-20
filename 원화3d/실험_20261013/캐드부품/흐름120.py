# 판정기준120 흐름도 — 얼린 Gemma 인코더 + 학습하는 머리(CAD 코드 출력) · 10-20
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch as B, FancyArrowPatch as A
plt.rcParams["font.family"] = "Malgun Gothic"
fig = plt.figure(figsize=(18, 9)); W = fig.add_axes([0, 0, 1, 1]); W.set_xlim(0, 18); W.set_ylim(0, 9); W.axis("off")
def 칸(x, y, w, h, t, s, c): W.add_patch(B((x, y), w, h, boxstyle="round,pad=.05", fc=c, ec="#555")); W.text(x + w / 2, y + h - .35, t, ha="center", fontsize=14, weight="bold"); W.text(x + w / 2, y + h / 2 - .2, s, ha="center", va="center", fontsize=10.5)
def 화(a, b): W.add_patch(A(a, b, arrowstyle="-|>", mutation_scale=18, color="#333"))
칸(.3, 5.6, 3.2, 2.4, "학습 데이터 (공짜)", "생성기 사양 6000\n→ CadQuery → 무작위 시점 렌더\n(그림, 정답 코드) 짝", "#eeeeee")
칸(4.2, 5.6, 3.0, 2.4, "Gemma 인코더 (얼림)", "그림 → 특징 벡터\n학습 안 함", "#dbeafe")
칸(7.9, 5.6, 3.6, 2.4, "머리 = 모델 (학습)", "특징 → CAD 코드\n종류 7 · 치수 9 칸\n구멍 · 홈 2 칸 · 필렛 · 기울임", "#fef3c7")
칸(12.2, 5.6, 2.6, 2.4, "CAD (계산)", "코드 → 3D\n(설계116 짓기)", "#dcfce7")
칸(15.3, 5.6, 2.4, 2.4, "채점 (계산)", "시점 맞추기 뒤\n실루엣 IoU\n종류 맞음", "#dcfce7")
for a, b in (((3.55, 6.8), (4.15, 6.8)), ((7.25, 6.8), (7.85, 6.8)), ((11.55, 6.8), (12.15, 6.8)), ((14.85, 6.8), (15.25, 6.8))): 화(a, b)
W.text(.3, 4.7, "시험 (119 와 같은 입력 · 155° 그림 한 장)", fontsize=14, weight="bold")
W.text(.3, 4.1, "G1 생성기 어려운 부품 20 (어휘 안)  ·  G2 실제 CAD 20 (어휘 밖 많음 — 모델이 낼 수 없는 모양이 있다)  ·  생성 시험 200 (종류 · 치수 오차)", fontsize=12)
W.text(.3, 3.3, "대조", fontsize=14, weight="bold"); W.text(.3, 2.7, "① 119 라이브러리 고르기(G1 종류 0.95 · IoU 0.97)   ② 종류만 맞히고 치수는 종류 평균(머리가 치수를 배웠나)", fontsize=12)
W.text(.3, 1.9, "통과 (미리 적음)", fontsize=14, weight="bold"); W.text(.3, 1.3, "G1 종류 ≥ 0.95 · G1 IoU 중앙 ≥ 0.97(119 와 같거나 높음) · 생성 시험 IoU 중앙 > 대조②   ·   G2 는 문턱 없이 보고(어휘 밖)", fontsize=12)
W.text(.3, .5, "가져가는 것: 얼린 인코더 · 생성기 · 시점 맞추기 · 119 입력   |   안 하는 것: 인코더 미세 조정 · 영상/글 입력(이번엔 그림만) · 도면으로 치수 다듬기(다음)   |   과정: 에폭마다 시험 6 개 예측 렌더 → 띠 영상", fontsize=11, color="#444")
fig.suptitle("판정기준120 — 인코더 위에 CAD 코드를 내는 모델을 학습한다", fontsize=18, y=.99)
plt.savefig("G:/art2real/out/설명/캐드부품/흐름120.png", dpi=75)
