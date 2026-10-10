# 선 고리 2 판 흐름도 — 작은 고리 문턱 · 조각 검사 (돌리기 전에 승인받는 그림 · 10-10)
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
plt.rcParams["font.family"] = "Malgun Gothic"
fig = plt.figure(figsize=(16, 13), dpi=150); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 160); ax.set_ylim(0, 130); ax.axis("off")
def 상자(x, y, w, h, 번, t, sub, col, ec="#333", lw=1.3):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", fc=col, ec=ec, lw=lw))
    ax.text(x + 1.5, y + h - 1.6, 번, fontsize=11, weight="bold", color="#1F5FAD", va="top"); ax.text(x + 7, y + h - 1.6, t, fontsize=11.5, weight="bold", va="top")
    for k, l in enumerate(sub): ax.text(x + 7, y + h - 5.4 - k * 3.1, l, fontsize=9, color="#333", va="top")
def 화(y0, y1, x): ax.add_patch(FancyArrowPatch((x, y0), (x, y1), arrowstyle="-|>", mutation_scale=14, lw=1.4, color="#333"))
def 칸(x, y, w, h, 제목, 줄, col, ec):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.5", fc=col, ec=ec, lw=1.6, ls="--"))
    ax.text(x + 1.5, y + h - 1.5, 제목, fontsize=11.5, weight="bold", color=ec, va="top")
    for k, l in enumerate(줄): ax.text(x + 1.5, y + h - 5.6 - k * 3.3, l, fontsize=9.3, va="top")
ax.text(3, 127, "선 고리 2 판 — 작은 고리를 면적으로 버리지 말고, 깊이로 정하고 결과로 거른다", fontsize=14, weight="bold")
바뀜 = "#C0392B"
S = [("0", "입력 (1 판과 같음)", ["시험 35 부품 · 앞 · 옆 · 위 흉내 선 128² + 실루엣"], "#EEF2F7", "#333"),
     ("1", "바탕 (같음)", ["윤곽 교차 덩어리 · 24/35"], "#E8F4EA", "#333"),
     ("2", "선 → 벡터 (같음)", ["직선 · 원 맞춤 · 수평/수직 스냅"], "#E7EEFB", "#333"),
     ("3", "닫힌 고리 찾기 — 바뀜", ["1 판: 면적 < 40 칸 버림 (256² 코드에서 베낀 값 · 128² 에선 4 배 큼)", "2 판: 면적 문턱 4 칸(선 굵기 정도)만 · 나머지는 깊이가 정함"], "#FFF0F0", 바뀜),
     ("4", "고리마다 깊이 (같음)", ["(A) 정답 깊이 · (B) AI 깊이 · 바탕보다 0.02 넘게 깊을 때만 판다"], "#FFF4DD", "#333"),
     ("5", "CAD 포켓 + 조각 검사 — 바뀜", ["부피 가드(같음) + 새로: 판 뒤 떨어진 조각이 늘면 그 파기를 되돌림", "(작은 포켓이 부스러기 · 얇은 벽을 만드는 걱정은 여기서 결과로 거름)"], "#FFF0F0", 바뀜),
     ("6", "채점 + 그림 (같음)", ["edge_f1 ≥ 0.42 통과 · 조각 수 · 얇은 부피 · 단계 PNG(#10) + 돌림 비교"], "#F2F2F2", "#333")]
y = 113
for i, (번, t, sub, col, ec) in enumerate(S):
    h = 11 if len(sub) < 2 else 13.5
    상자(3, y - h, 74, h, 번, t, sub, col, ec, 2.2 if ec == 바뀜 else 1.3)
    if i < len(S) - 1: 화(y - h, y - h - 3, 40)
    y -= h + 3.4
칸(84, 90, 73, 28, "세 판 비교 (같은 35 부품)", ["① 1 판 그대로: 문턱 40 · 조각 검사 없음 (이미 있음)", "    A 30/35 · 조각 9 / B 30/35 · 조각 7", "② 문턱 4 · 조각 검사 없음  ← 문턱만의 효과", "③ 문턱 4 + 조각 검사       ← 검사까지", "A(정답 깊이) · B(AI 깊이) 두 판씩 = 4 번 새로 돌림"], "#F5F7FC", "#1F5FAD")
칸(84, 58, 73, 28, "이번에 안 하는 것", ["· 기울기 · 곡면 바닥 · 모따기 알아보기", "· 고리가 파냐 붙이냐 판정", "· 공 · 둥근 껍질(스컬핑 층)", "· 진짜 원화 선 · 학습"], "#FDF3F3", "#C0392B")
칸(84, 18, 73, 36, "판정 (돌리기 전에 고정)", ["③ 이 ① 보다 통과가 늘고(A ≥ 32) 조각 합이 ① 보다", "   늘지 않으면 → 문턱 4 + 조각 검사를 기본값으로", "② 의 조각이 크게 늘면(① 의 3 배 넘게)", "   → 「작은 고리는 정말 부스러기를 만든다」 · 검사가 필요한 이유", "③ 도 통과가 안 늘면 → 버린 고리 탓이 아님 · 다른 원인 찾기", "숫자 + #10 단계 PNG + 바뀐 부품 돌림 그림 같이"], "#F4FAF4", "#2E7D32")
fig.savefig("문턱흐름.png", facecolor="white"); print("ok")
