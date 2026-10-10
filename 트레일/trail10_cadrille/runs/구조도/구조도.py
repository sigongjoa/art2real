# 모델 구조도(논문 그림 식) — (a) 지금 구조: 화소 깊이 → 덩어리에서 빼기  (b) 바로잡은 구조: 하드서페이스(형상 목록 → CAD) + 스컬핑(곡면만 메시) 분리
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
fig = plt.figure(figsize=(16, 11), dpi=150); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 160); ax.set_ylim(0, 110); ax.axis("off")
C = dict(입력="#EEF2F7", 기하="#E8F4EA", 학습="#E7EEFB", CAD="#FFF4DD", 메시="#F9E8EF", 출력="#F2F2F2", 틀림="#FDECEC")
def 상자(x, y, w, h, t, col, sub=None, lw=1.2, ec="#333", fs=11, bold=True):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", fc=col, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2 + (1.6 if sub else 0), t, ha="center", va="center", fontsize=fs, weight="bold" if bold else "normal")
    if sub: ax.text(x + w / 2, y + h / 2 - 2.2, sub, ha="center", va="center", fontsize=8.5, color="#444")
def 화(x0, y0, x1, y1, t=None, col="#333", ls="-", rad=0.0, fs=8.5, dy=1.4):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=13, lw=1.3, color=col, linestyle=ls, connectionstyle="arc3,rad=%g" % rad))
    if t: ax.text((x0 + x1) / 2, (y0 + y1) / 2 + dy, t, ha="center", va="bottom", fontsize=fs, color=col)
def 묶음(x, y, w, h, t, col):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=2", fc="none", ec=col, lw=1.6, ls="--"))
    ax.text(x + 1.5, y + h - 1.8, t, ha="left", va="top", fontsize=10.5, color=col, weight="bold")

# ── (a) 지금 구조 ──────────────────────────────────────────
ax.text(3, 106, "(a) 지금 구조 — 출력이 화소이고, 덩어리에서 빼기만 한다 (= 스컬핑)", fontsize=13, weight="bold")
상자(4, 84, 20, 13, "입력", C["입력"], "앞 · 옆 · 위 선 그림")
상자(32, 89, 22, 9, "윤곽 교차", C["기하"], "세 실루엣 교집합 → 덩어리")
상자(32, 77, 22, 9, "깊이 U-Net", C["학습"], "선 · 실루엣 → 깊이 화소 256²")
상자(63, 83, 30, 11, "주머니 = 화소 영역", C["틀림"], "깊이 차 > 0.02 · 테두리 화소 따라 다각형", ec="#C0392B", lw=1.8)
상자(102, 83, 26, 11, "기둥 10~40 번 빼기", C["틀림"], "평평 · 기울기 · 곡면 바닥", ec="#C0392B", lw=1.8)
상자(137, 83, 19, 11, "메시 하나", C["출력"], "부스러기 · 계단")
화(24, 92, 32, 93.5); 화(24, 88, 32, 81.5); 화(54, 93.5, 63, 90); 화(54, 81.5, 63, 86); 화(93, 88.5, 102, 88.5); 화(128, 88.5, 137, 88.5)
ax.text(80, 77.5, "× 홈 · 구멍(하드)과 공 · 곡면(스컬핑)을 같은 칼로 판다", fontsize=10, color="#C0392B", ha="center")
ax.text(80, 74.2, "× 자(모서리 F1)가 부스러기를 벌하지 않는다 — 33/35 인데 눈으로는 부서짐", fontsize=10, color="#C0392B", ha="center")
ax.plot([3, 157], [70.5, 70.5], color="#999", lw=0.8)

# ── (b) 바로잡은 구조 ──────────────────────────────────────
ax.text(3, 67, "(b) 바로잡은 구조 — 하드서페이스는 형상 목록(CAD), 스컬핑은 곡면만 따로(메시)", fontsize=13, weight="bold")
상자(4, 36, 20, 22, "입력", C["입력"], "앞 · 옆 · 위 선 그림")
# 공유 인코더
상자(30, 40, 18, 14, "인코더", C["학습"], "그림 → 특징 (얼림)")
화(24, 47, 30, 47)
# 하드서페이스 가지
묶음(53, 37, 66, 26, "① 하드서페이스 모델", "#1F5FAD")
상자(56, 50, 24, 9, "형상 디코더", C["학습"], "슬롯 12 칸 · 어휘 + 치수")
상자(56, 39.5, 24, 8, "윤곽 교차 덩어리", C["기하"], "밀어내기 바탕")
상자(87, 50, 29, 9, "형상 목록 (CAD 프로그램)", C["CAD"], "사각 홈 12×6 d3 · 구멍 Ø4 · 모따기")
상자(87, 39.5, 29, 8, "CAD 커널 (CadQuery)", C["CAD"], "스냅 · 대칭 · B-rep → STEP")
화(48, 50, 56, 54.5); 화(48, 44, 56, 43.5); 화(80, 54.5, 87, 54.5); 화(101.5, 50, 101.5, 47.5); 화(80, 43.5, 87, 43.5)
# 곡면 판정 + 스컬핑 가지
상자(56, 23, 24, 9, "깊이 U-Net (지금 것)", C["학습"], "중간 단서로만 씀")
상자(87, 23, 29, 9, "곡면 영역 판정", C["학습"], "평면 맞춤 오차 → 나중엔 학습")
화(48, 42, 56, 28, rad=0.15); 화(80, 27.5, 87, 27.5)
화(70, 32, 87, 49.5, col="#1F5FAD", ls="--", rad=-0.25); ax.text(84.5, 34.2, "형상 위치 힌트", fontsize=8, color="#1F5FAD", ha="center")
묶음(53, 3, 66, 17, "② 스컬핑 모델 (따로)", "#A0336A")
상자(56, 5.5, 60, 9, "곡면 영역만 메시 변형", C["메시"], "공 · 둥근 껍질 · 곡면 틈 → 목표 깊이로 매끈하게 (불리언 아님)")
화(101.5, 23, 101.5, 14.5, col="#A0336A"); ax.text(103, 18.5, "곡면 마스크", fontsize=8, color="#A0336A", ha="left")
# 합치기 · 출력
상자(126, 39.5, 30, 20, "합치기", C["출력"], "CAD(STEP) + 스컬핑 층(메시)\n따로 보관 · 출력 때 합침", fs=12)
화(116, 43.5, 126, 46); 화(116, 10, 141, 39.5, rad=0.25)
# 학습 신호
ax.text(3, 29, "학습 신호", fontsize=10.5, weight="bold", color="#1F5FAD")
for k, t in enumerate(["· 합성 형상 목록 (정답 있음)", "· 진짜 부품 2,883 개: 형상 어휘를", "  최적화로 맞춘 목록 = 가짜 정답", "· 손실: 윤곽 · 깊이 · 모서리", "  + 부스러기 벌점 (조각 수 · 얇은 면)"]):
    ax.text(3, 25.5 - k * 3.2, t, fontsize=9, color="#333")
ax.text(3, 8.5, "채점", fontsize=10.5, weight="bold", color="#333")
ax.text(3, 5.2, "① 부스러기 0 + 모서리 점수", fontsize=9); ax.text(3, 2.2, "② 곡면 매끈함(명암) + 깊이 오차", fontsize=9)
fig.savefig("모델구조.png", facecolor="white"); print("ok")
