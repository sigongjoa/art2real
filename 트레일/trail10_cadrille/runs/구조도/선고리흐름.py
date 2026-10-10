# 선 고리 → 스케치 → 포켓 시험 흐름도 (돌리기 전에 승인받는 그림 · 10-10)
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
plt.rcParams["font.family"] = "Malgun Gothic"
fig = plt.figure(figsize=(16, 13), dpi=150); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 160); ax.set_ylim(0, 130); ax.axis("off")
def 상자(x, y, w, h, 번, t, sub, col, ec="#333"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", fc=col, ec=ec, lw=1.3))
    ax.text(x + 1.5, y + h - 1.6, 번, fontsize=11, weight="bold", color="#1F5FAD", va="top")
    ax.text(x + 7, y + h - 1.6, t, fontsize=11.5, weight="bold", va="top")
    for k, l in enumerate(sub): ax.text(x + 7, y + h - 5.4 - k * 3.1, l, fontsize=9, color="#333", va="top")
def 화(y0, y1, x=40): ax.add_patch(FancyArrowPatch((x, y0), (x, y1), arrowstyle="-|>", mutation_scale=14, lw=1.4, color="#333"))
def 칸(x, y, w, h, 제목, 줄, col, ec):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.5", fc=col, ec=ec, lw=1.6, ls="--"))
    ax.text(x + 1.5, y + h - 1.5, 제목, fontsize=11.5, weight="bold", color=ec, va="top")
    for k, l in enumerate(줄): ax.text(x + 1.5, y + h - 5.6 - k * 3.3, l, fontsize=9.3, va="top")
ax.text(3, 127, "선 고리 시험 흐름 — 그림의 닫힌 선을 그대로 스케치로 쓰고, 깊이만 정해 판다 (학습 없음)", fontsize=14, weight="bold")
W = 74; X = 3; H = 12.5
S = [("0", "입력", ["시험 35 부품 · 앞 · 옆 · 위 선 그림 128² (깊이학습 시험.npz 의 L 칸 = 실물에서 뽑은 흉내 선)", "+ 실루엣 (S 칸)"], "#EEF2F7"),
     ("1", "바탕 = 윤곽 교차 덩어리", ["윤곽0 의 %02d_교차.step 그대로 (바탕만 24/35 · 중앙 0.558)"], "#E8F4EA"),
     ("2", "선 → 벡터", ["선 화소 → 가늘게(골격) → 이어진 선 조각 → 직선 · 원호 맞춤", "수평 · 수직 · 같은 길이 스냅 (각 1.5° · 길이 1 칸 안이면 맞춤)"], "#E7EEFB"),
     ("3", "닫힌 고리 찾기", ["벡터 선으로 평면을 나눈 면(영역) 하나 = 고리 하나", "바깥 윤곽 고리는 뺌(이미 바탕) · 면적 < 40 칸은 뺌"], "#E7EEFB"),
     ("4", "고리마다 깊이 정하기 — 두 판", ["(A) 정답 깊이 = 천장: 고리 안 실물 깊이 중앙값", "(B) AI 깊이: 깊이 U-Net 1 판(모델.pt) 의 고리 안 중앙값", "바탕보다 0.02 넘게 깊을 때만 「판다」 · 아니면 그대로 둠"], "#FFF4DD"),
     ("5", "CAD 포켓", ["고리(직선 · 원호 그대로) = 스케치 → 그 깊이까지 밀어내 빼기 · 평평한 바닥", "부피가 양수이고 실제로 줄 때만 받음 (오늘 #18 · #21 가드 그대로)"], "#FFF4DD"),
     ("6", "채점 + 그림", ["같은 자 edge_f1 ≥ 0.42 통과 · 부스러기 수(새로: 떨어진 조각 + 두께 < 1 칸 면)", "6 부품 돌림 GIF (사람 / 바탕 / 화소 깎기 / 선 고리)"], "#F2F2F2")]
y = 113
for i, (번, t, sub, col) in enumerate(S):
    h = H if len(sub) < 3 else H + 2.5
    상자(X, y - h, W, h, 번, t, sub, col)
    if i < len(S) - 1: 화(y - h, y - h - 3.2, X + W / 2)
    y -= h + 3.6
# 오른쪽 칸들
칸(84, 88, 73, 30, "그대로 가져가는 것", ["· 윤곽 교차 바탕 (1 단계)", "· 깊이 U-Net 1 판 — 고리 깊이 숫자로만 (B 판)", "· CadQuery 빼기 + 부피 가드", "· 같은 채점 자 · 같은 35 부품", "· 대조 결과: 화소 깎기 정답 깊이 33/35 · 0.590", "                    화소 깎기 AI 깊이 32/35 · 0.553"], "#F4FAF4", "#2E7D32")
칸(84, 52, 73, 32, "이번에 안 하는 것 (빼는 이유)", ["· 기울기 · 곡면 바닥 — 먼저 평평한 포켓으로 선 방식만 잼", "· 붙이기(튀어나온 판) — 고리가 파냐 붙이냐는 다음 판", "· 공 · 둥근 껍질 — 스컬핑 층 몫 (구조도 ②)", "· 뒷면 홈 (세 장에 안 그려진 것)", "· 진짜 원화 선 — 흉내 선이 통과한 뒤에", "· 학습 — 이번은 천장 재기"], "#FDF3F3", "#C0392B")
칸(84, 12, 73, 36, "판정 (돌리기 전에 고정)", ["(A) 정답 깊이 선 고리:", "   부스러기 수가 화소 깎기보다 적고 통과 ≥ 30 이면", "   「선 방식이 하드서페이스 바탕으로 쓸 만하다」", "(B) AI 깊이 선 고리:", "   통과 > 24 (바탕) 이고 부스러기가 화소 깎기보다 적으면", "   「그림 + AI 깊이로 깔끔한 CAD 가 나온다」", "부스러기 수는 화소 깎기 두 판에도 같은 자로 다시 잼"], "#F5F7FC", "#1F5FAD")
fig.savefig("선고리흐름.png", facecolor="white"); print("ok")
