# 선 고리 4 판 흐름도 — 어휘에 셸(속 비우기) 추가 (돌리기 전에 승인받는 그림 · 10-10)
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
plt.rcParams["font.family"] = "Malgun Gothic"
fig = plt.figure(figsize=(16, 13), dpi=150); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 160); ax.set_ylim(0, 130); ax.axis("off")
빨 = "#C0392B"
def 상자(x, y, w, h, 번, t, sub, 바뀜=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", fc="#FFF0F0" if 바뀜 else "#F4F6FA", ec=빨 if 바뀜 else "#555", lw=2.1 if 바뀜 else 1.1))
    ax.text(x + 1.4, y + h - 1.5, 번, fontsize=10.5, weight="bold", color="#1F5FAD", va="top"); ax.text(x + 6, y + h - 1.5, t, fontsize=11, weight="bold", va="top")
    for k, l in enumerate(sub): ax.text(x + 6, y + h - 5.1 - k * 2.9, l, fontsize=8.9, color="#333", va="top")
def 화(x, y0, y1): ax.add_patch(FancyArrowPatch((x, y0), (x, y1), arrowstyle="-|>", mutation_scale=13, lw=1.3, color="#333"))
def 칸(x, y, w, h, 제목, 줄, ec, fc):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.5", fc=fc, ec=ec, lw=1.5, ls="--"))
    ax.text(x + 1.4, y + h - 1.4, 제목, fontsize=11, weight="bold", color=ec, va="top")
    for k, l in enumerate(줄): ax.text(x + 1.4, y + h - 5.2 - k * 3.1, l, fontsize=9.1, va="top")
ax.text(3, 127, "선 고리 4 판 — 속이 빈 껍질은 CAD 「셸(속 비우기)」 한 줄로 · 화소 깎기는 비교 대상에서 뺀다", fontsize=14, weight="bold")
S = [("0", "입력 · 바탕 (같음)", ["35 부품 · 윤곽 교차 바탕"], False),
     ("1", "선 = 가 판 메시 모서리 선 (기본값으로)", ["3 판에서 전체가 나았던 선 · 문턱 4 · 조각 검사 그대로"], True),
     ("2", "열린 면 찾기 — 새로", ["여섯 방향마다: 진짜(A) / AI(B) 깊이가 바탕보다 「부품 두께의 30 %」 넘게", "깊은 영역이 실루엣의 20 % 넘으면 = 그쪽이 열린 껍질", "(겉의 얕은 홈과 갈리는 기준 = 깊이 + 넓이)"], True),
     ("3", "벽 두께 정하기 — 새로", ["열린 면 그림에서 실루엣 테두리 ~ 열린 영역 테두리 거리(중앙값)", "= 둘레 벽 두께 · 1.5 ~ 12 (긴 변 100 기준) 밖이면 안 씀"], True),
     ("4", "셸 → 포켓 — 새로", ["바탕.faces(열린 쪽).shell(-두께) 한 줄 · 실패하면 셸 없이", "그다음 겉 고리 포켓 (열린 면 쪽 고리는 이미 비었으니 뺌)"], True),
     ("5", "채점 + 그림 (눈 먼저)", ["셋(#4 · #21 · #35) + 셸이 걸린 모든 부품 돌림 그림", "통과 · 조각 · 망가뜨림 · CAD 코드에 shell 한 줄이 보이는지"], False)]
y = 113
for i, (번, t, sub, 바) in enumerate(S):
    h = 6 + 2.9 * len(sub); 상자(3, y - h, 76, h, 번, t, sub, 바)
    if i < len(S) - 1: 화(41, y - h, y - h - 2.6)
    y -= h + 3.2
칸(85, 82, 72, 31, "대조 (같은 35 부품)", ["① 2 판 ③ : 지금 선 · 문턱 4 · 조각 검사  A 30 · 조각 5", "② 3 판 가 : 새 선  A 31 · 조각 5 · 중앙 0.575", "③ 4 판 : 새 선 + 셸  ← 이번", "화소 깎기는 대조에서 뺌 (점수만 통과 · 눈으로는 부서짐)", "A(정답 깊이) · B(AI 깊이) 두 판"], "#1F5FAD", "#F5F7FC")
칸(85, 46, 72, 32, "판정 (돌리기 전에 고정)", ["눈: 셋 중 2 개 이상이 「속 빈 껍질」로 보이고 구멍 · 조각이 없을 것", "숫자: A 통과 ≥ 32 · 조각 합 ≤ 8", "셸이 잘못 걸린 부품(속이 찬 부품을 비움)이 3 개 넘으면 기각", "  → 그 부품 이름과 그림을 같이 보고", "눈 · 숫자 둘 다 넘으면 셸을 어휘 기본으로"], "#2E7D32", "#F4FAF4")
칸(85, 10, 72, 32, "이번에 안 하는 것 · 위험", ["· 열린 면이 둘 이상인 껍질(통 · 고리) — 한 면만", "· 벽 두께가 곳마다 다른 껍질 — 한 두께만", "· 휜 판(#4)은 셸 결과가 「ㄷ자 상자」로 나올 수 있음", "  (곡면은 여전히 스컬핑 층 몫 · 이번엔 속 비움만 봄)", "· AI 다시 학습 · 모따기 · 붙이기 판정"], 빨, "#FDF3F3")
fig.savefig("셸흐름.png", facecolor="white"); print("ok")
