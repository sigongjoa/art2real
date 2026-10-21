# 판정기준121 흐름도 — 예측 코드 → 다시 그려 입력과 맞추며 치수 다듬기 · 10-21
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch as B, FancyArrowPatch as A
plt.rcParams["font.family"] = "Malgun Gothic"
fig = plt.figure(figsize=(18, 9)); W = fig.add_axes([0, 0, 1, 1]); W.set_xlim(0, 18); W.set_ylim(0, 9); W.axis("off")
def 칸(x, y, w, h, t, s, c): W.add_patch(B((x, y), w, h, boxstyle="round,pad=.05", fc=c, ec="#555")); W.text(x + w / 2, y + h - .35, t, ha="center", fontsize=14, weight="bold"); W.text(x + w / 2, y + h / 2 - .2, s, ha="center", va="center", fontsize=10.5)
def 화(a, b): W.add_patch(A(a, b, arrowstyle="-|>", mutation_scale=18, color="#333"))
칸(.3, 5.6, 3.0, 2.4, "그림 한 장", "G1 · G2 · G3\n생성 시험 40", "#eeeeee")
칸(3.9, 5.6, 3.2, 2.4, "모델120 (그대로)", "Gemma(얼림) + 머리\n→ 종류 상위 2\n→ 시작 코드", "#fef3c7")
칸(7.7, 5.6, 4.4, 2.4, "다듬기 (계산 · 새로)", "코드 → 3D → 같은 시점 렌더\n입력과 실루엣 · 모서리 비교\n치수 · 기울임 · 구멍 자리를\n±25 → 10 → 4 % 씩 바꿔 나은 쪽", "#dcfce7")
칸(12.7, 5.6, 2.4, 2.4, "고르기", "종류 후보 중\n점수 높은 코드", "#dcfce7")
칸(15.6, 5.6, 2.2, 2.4, "채점", "입력 시점 IoU\n다른 시점 IoU\n(+90°, 정답 3D)", "#dbeafe")
W.annotate("", xy=(8.2, 5.55), xytext=(11.6, 5.55), arrowprops=dict(arrowstyle="-|>", connectionstyle="arc3,rad=-.5", color="#28a050")); W.text(9.9, 4.85, "되풀이", ha="center", color="#28a050", fontsize=11)
for a, b in (((3.35, 6.8), (3.85, 6.8)), ((7.15, 6.8), (7.65, 6.8)), ((12.15, 6.8), (12.65, 6.8)), ((15.15, 6.8), (15.55, 6.8))): 화(a, b)
W.text(.3, 4.0, "대조", fontsize=14, weight="bold"); W.text(.3, 3.4, "120 다듬기 없음(같은 부품)   ·   ③ 같은 다듬기를 「종류 + 평균 치수」에서 시작(생성 시험) — 모델 시작값이 쓸모 있나", fontsize=12)
W.text(.3, 2.6, "통과 (미리 적음)", fontsize=14, weight="bold"); W.text(.3, 2.0, "G1 입력 시점 IoU 중앙 ≥ 0.97   ·   G1 다른 시점 IoU > 120   ·   생성 시험 다른 시점 IoU > 120     (G2 · G3 보고만)", fontsize=12)
W.text(.3, 1.2, "다른 시점을 따로 재는 이유: 다듬기는 입력 그림에 맞추는 일이라 입력 시점 IoU 는 저절로 오른다 — 안 보이던 쪽도 맞았나를 본다", fontsize=11.5, color="#444")
W.text(.3, .5, "가져가는 것: 모델120 그대로 · 118b 시점 맞추기 · 생성기   |   안 하는 것: 재학습 · 여러 시점 입력(다음 판) · 특징 종류 바꾸기 · 어휘 늘리기", fontsize=11, color="#444")
fig.suptitle("판정기준121 — 모델이 낸 코드를 다시 그려 보고 치수를 다듬는다", fontsize=18, y=.99)
plt.savefig("G:/art2real/out/설명/캐드부품/흐름121.png", dpi=75)
