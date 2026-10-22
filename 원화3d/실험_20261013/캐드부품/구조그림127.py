# 모델127 구조 그림 — 입력부터 출력까지 텐서 모양 · 층보기 시트의 열이 어디인지 · 10-22
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"
D = "G:/art2real/out/설명/캐드부품/모델127/"
fig = plt.figure(figsize=(20, 11)); ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, 20); ax.set_ylim(0, 11)
ax.text(10, 10.5, "모델127 구조 — 3면도 → CNN(그림마다 같은 가중치) → 조각 토큰 192 → 트랜스포머 디코더(칸 6) → 칸마다 숫자 41", ha="center", fontsize=18, weight="bold")
def 상자(x, y, w, h, 글, fc="#eef2f7", ec="#555", fs=12): ax.add_patch(plt.Rectangle((x, y), w, h, fc=fc, ec=ec, lw=2)); ax.text(x + w / 2, y + h / 2, 글, ha="center", va="center", fontsize=fs)
def 화(x0, y0, x1, y1): ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", lw=2.2, color="#333"))
def 열(x, y, t): ax.text(x, y, t, ha="center", fontsize=12, color="#d8262b", weight="bold")
# 윗줄: 입력 → CNN 4 블록
상자(.2, 7.0, 2.2, 2.2, "입력 3면도\n위 · 앞 · 옆\n각 128 × 128\n회색 · 선 = 1\n(3, 1, 128, 128)", "#fff4dc", "#d9a020"); 열(1.3, 9.4, "1열")
블 = [("블록 1", "3×3 합성곱 · 보폭 2\n1 → 32 채널\nGroupNorm · GELU\n3×3 합성곱 · 보폭 1\nGroupNorm · GELU", "(32, 64, 64)", "2열"), ("블록 2", "같은 꼴\n32 → 64", "(64, 32, 32)", "3열"), ("블록 3", "같은 꼴\n64 → 128", "(128, 16, 16)", "4열"), ("블록 4", "같은 꼴\n128 → 256", "(256, 8, 8)", "5열")]
for i, (이름, 설, 모, 열이름) in enumerate(블):
    x = 3.0 + i * 3.0; 화(x - .55, 8.1, x, 8.1); 상자(x, 7.0, 2.5, 2.2, f"CNN {이름}\n{설}", "#e3f4e6", "#28a050", 10.5); ax.text(x + 1.25, 6.7, 모, ha="center", fontsize=12); 열(x + 1.25, 9.4, 열이름)
ax.text(8.5, 6.2, "세 그림이 같은 CNN 을 따로 지남 · 한 화소가 보는 범위(수용 영역): 블록 1 = 7 · 2 = 19 · 3 = 43 · 4 = 91 화소", ha="center", fontsize=12, color="#555")
# 토큰
화(15.6, 8.1, 16.2, 8.1); 상자(16.2, 7.0, 3.6, 2.2, "조각 토큰\n8 × 8 = 64 조각 × 3 그림 = 192\n각 256 숫자\n+ 조각 위치 표시(학습)\n+ 그림 표시(위 · 앞 · 옆)", "#f3e8fb", "#9b59b6", 11); 열(18.0, 9.4, "6열")
# 아랫줄: 디코더
화(18.0, 6.95, 18.0, 5.6)
상자(.2, 2.6, 3.2, 2.4, "칸 질문 6 개\n(학습되는 숫자 256 × 6)\n처음엔 부품과 무관", "#fff4dc", "#d9a020", 12)
for k in range(4):
    x = 4.0 + k * 3.35; 화(x - .55, 3.8, x, 3.8)
    상자(x, 2.2, 2.9, 3.2, f"디코더 {k + 1}층\n\n① 칸끼리 주의\n(6 ↔ 6)\n② 칸 → 토큰 192 주의\n= 어텐션 맵\n③ 256 → 1024 → 256", "#eaf1fb", "#4a7bd1", 10.5)
열(4.0 + 3 * 3.35 + 1.45, 5.6, "7 · 8 · 9열 = 4층 ②")
ax.plot([18.0, 18.0, 15.5], [5.6, 5.6, 5.6], color="#9b59b6", lw=2, ls="--"); ax.text(16.6, 5.75, "토큰 192 를 네 층 모두 ②에서 봄", fontsize=11, color="#9b59b6", ha="center")
화(17.5, 3.8, 18.0, 3.8); 상자(18.0, 2.6, 1.8, 2.4, "칸마다\n256 → 41\n있음 · 종류\n치수 · 축\n자리 · 구멍", "#fdf0f0", "#d8262b", 10.5)
ax.text(10, 1.4, "1열 ×(예측 자리) = 마지막 상자의 「자리」 3 숫자 · 2~5열 = 각 블록 출력의 채널 평균 크기(앞 그림) · 6열 = 토큰 크기 · 7~9열 = 4층 ② 에서 칸 1 · 2 · 3 의 주의", ha="center", fontsize=13)
ax.text(10, .7, "파라미터 541 만 · loss = 칸 t 의 41 숫자 ↔ 부피 t 번째 덩어리(지금) · 문제 자리: ② 주의가 덩어리로 모이지 않음", ha="center", fontsize=13, color="#d8262b")
fig.savefig(D + "구조127.png", dpi=65); print("끝")
