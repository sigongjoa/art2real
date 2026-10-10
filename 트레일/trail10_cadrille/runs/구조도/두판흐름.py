# 선 고리 3 판 흐름도 — 가: 선 뽑기 고치기 · 나: 고리를 깊이로 다시 나누기 (돌리기 전에 승인받는 그림 · 10-10)
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
plt.rcParams["font.family"] = "Malgun Gothic"
fig = plt.figure(figsize=(17, 14), dpi=140); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 170); ax.set_ylim(0, 140); ax.axis("off")
빨 = "#C0392B"
def 상자(x, y, w, h, 번, t, sub, 바뀜=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", fc="#FFF0F0" if 바뀜 else "#F4F6FA", ec=빨 if 바뀜 else "#555", lw=2.1 if 바뀜 else 1.1))
    ax.text(x + 1.4, y + h - 1.5, 번, fontsize=10.5, weight="bold", color="#1F5FAD", va="top"); ax.text(x + 6, y + h - 1.5, t, fontsize=11, weight="bold", va="top")
    for k, l in enumerate(sub): ax.text(x + 6, y + h - 5.1 - k * 2.9, l, fontsize=8.7, color="#333", va="top")
def 화(x, y0, y1): ax.add_patch(FancyArrowPatch((x, y0), (x, y1), arrowstyle="-|>", mutation_scale=13, lw=1.3, color="#333"))
def 칸(x, y, w, h, 제목, 줄, ec, fc):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.5", fc=fc, ec=ec, lw=1.5, ls="--"))
    ax.text(x + 1.4, y + h - 1.4, 제목, fontsize=11, weight="bold", color=ec, va="top")
    for k, l in enumerate(줄): ax.text(x + 1.4, y + h - 5.2 - k * 3.0, l, fontsize=8.9, va="top")
ax.text(3, 137, "선 고리 3 판 — 남은 셋(#4 · #21 · #35)은 「선이 없는 홈」 · 두 갈래를 따로 재고 마지막에 합친다", fontsize=14, weight="bold")
for x0, 제목, 단계 in [(3, "가. 선 뽑기 고치기 — 원화라면 그렸을 선을 흉내 선에도", [
        ("0", "입력 · 바탕 (같음)", ["35 부품 · 윤곽 교차 바탕"], False),
        ("1", "선 다시 뽑기 — 바뀜", ["지금: 깊이 끊김 > 0.03 · 꺾임 > 0.004 (화소 깊이에서)", "새로: 메시 모서리 중 면 각도 ≥ 30° 인 선(보이는 것만)", "= CAD 도면의 「모서리 선」 · 원화의 외곽 · 패널 선에 가깝다"], True),
        ("2", "선 그림 비교 (눈)", ["#4 · #21 · #35 지금 선 / 새 선 나란히 PNG", "오목한 판 테두리가 생겼는지 · 쓸데없는 선이 늘었는지"], False),
        ("3", "벡터 · 고리 · 깊이 · 포켓 (같음)", ["문턱 4 · 조각 검사 · A 정답 깊이 / B AI 깊이", "AI 입력은 학습 때 선 그대로(다시 학습 안 함) · 고리만 새 선"], False),
        ("4", "채점 + 그림", ["통과 · 조각 · 망가뜨림 · #21 단계 PNG"], False)]),
    (88, "나. 고리를 깊이로 다시 나누기 — 선이 없어도 깊이가 보완", [
        ("0", "입력 · 바탕 · 선 (같음)", ["35 부품 · 지금 흉내 선 · 문턱 4"], False),
        ("1", "고리 안 깊이가 두 덩어리인지 — 새로", ["고리 안 깊이(A 정답 / B AI)를 오츠 문턱으로 둘로 가름", "두 덩어리 깊이 차 > 0.02 이고 작은 쪽 ≥ 고리의 10 % 일 때만"], True),
        ("2", "깊은 쪽만 새 고리로 — 새로", ["깊은 덩어리 테두리 → 직선 맞춤 · 스냅(1.5 칸 단순화)", "! 테두리가 화소에서 나옴 = 화소 깎기 냄새 · 조각 검사로 거름"], True),
        ("3", "포켓 (같음)", ["원래 고리 + 새 고리 · 조각 검사 · 부피 가드"], False),
        ("4", "채점 + 그림", ["통과 · 조각 · 망가뜨림 · #21 단계 PNG(나뉜 고리 색)"], False)])]:
    ax.text(x0, 130, 제목, fontsize=12.5, weight="bold", color="#1F5FAD")
    y = 126
    for i, (번, t, sub, 바) in enumerate(단계):
        h = 6 + 2.9 * len(sub); 상자(x0, y - h, 78, h, 번, t, sub, 바)
        if i < len(단계) - 1: 화(x0 + 39, y - h, y - h - 2.4)
        y -= h + 3
칸(3, 3, 78, 37, "판정 (돌리기 전에 고정) · 대조 = 2 판 ③ (A 30 · 조각 5 / B 30 · 조각 5)", [
    "가 · 나 각각:", "  셋(#4 · #21 · #35) 중 2 개 이상이 통과선을 넘고", "  전체 A 통과 ≥ 32 · 조각 합 ≤ 8 이면 → 그 갈래 채택",
    "  통과만 늘고 조각이 8 넘게 늘면 → 「화소 냄새가 돌아왔다」 기각", "가 · 나 둘 다 채택이면 합친 판(가 + 나)도 한 번 잰다",
    "둘 다 기각이면 → 셋은 선 방식 밖(스컬핑 층 몫)으로 넘김", "숫자 + #21 단계 PNG + 선 그림 비교 같이"], "#2E7D32", "#F4FAF4")
칸(88, 3, 78, 37, "이번에 안 하는 것 · 미리 알리는 위험", [
    "· AI 깊이 모델 다시 학습(가 의 새 선으로) — 가 가 채택되면 다음 판",
    "· 기울기 · 곡면 바닥 · 모따기 알아보기 · 붙이기 판정",
    "· 진짜 원화 선(사람 그림) — 흉내 선으로 판이 정해진 뒤",
    "! 가: 모서리 선이 너무 많으면 고리가 잘게 쪼개져 작은 포켓이 늘 수 있음",
    "! 나: 테두리를 화소에서 다시 따므로 부스러기가 돌아올 수 있음",
    "   → 둘 다 조각 검사 · 조각 합을 판정에 넣어 막는다"], 빨, "#FDF3F3")
fig.savefig("두판흐름.png", facecolor="white"); print("ok")
