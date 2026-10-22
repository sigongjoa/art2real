# 모델127 수식 — 합성곱 · GroupNorm · GELU · 블록 · 수용 영역 · 곡률 조합 · 토큰 · 교차 주의 · matplotlib mathtext 로 PNG · 10-22
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["mathtext.fontset"] = "cm"
줄 = [
 ("1. 합성곱 (3×3 · 블록마다 두 번 · 첫째 보폭 s = 2, 둘째 s = 1)", r"$y_{o,i,j} = b_o + \sum_{c}\ \sum_{u=-1}^{1}\ \sum_{v=-1}^{1}\ W_{o,c,u,v}\ x_{c,\ s i+u,\ s j+v}$"),
 ("    출력 크기 (p = 1, k = 3) — 보폭 2 면 128 → 64", r"$H_{out} = \left\lfloor \frac{H + 2p - k}{s} \right\rfloor + 1$"),
 ("2. GroupNorm (채널 8 묶음 g · 묶음 안 모든 채널 · 화소로 평균 · 분산)", r"$\hat{y} = \gamma\ \frac{y - \mu_g}{\sqrt{\sigma_g^2 + \epsilon}} + \beta$"),
 ("3. GELU (음수는 누르고 양수는 통과 · Φ = 정규분포 누적함수)", r"$\mathrm{GELU}(z) = z\ \Phi(z) \approx z\ \sigma(1.702\, z)$"),
 ("4. 블록과 CNN 전체 — 그림마다 같은 가중치", r"$B(x) = \mathrm{GELU}\left(\mathrm{GN}\left(\mathrm{Conv}_{s=1}\left(\mathrm{GELU}\left(\mathrm{GN}\left(\mathrm{Conv}_{s=2}(x)\right)\right)\right)\right)\right),\quad F = B_4 \circ B_3 \circ B_2 \circ B_1(\mathrm{image}) \in \mathbb{R}^{256 \times 8 \times 8}$"),
 ("5. 시야(수용 영역) — r: 3, 7, 11, 19, 27, 43, 59, 91 화소", r"$r_l = r_{l-1} + (k-1)\ j_{l-1},\qquad j_l = j_{l-1}\ s_l,\qquad r_0 = j_0 = 1$"),
 ("6. 곡률이 생기는 꼴 — 1 층 방향 선분 검출기 E 를 이웃마다 Δθ 씩 돌려 더함 (Δθ ∝ 곡률)", r"$\kappa(p) \approx \mathrm{GELU}\left( \sum_{k} w_k\ E_{\theta + k\Delta\theta}(p + k\,d) \right)$"),
 ("7. 조각 토큰 — 조각 특징 + 조각 위치 표시 + 그림(위 · 앞 · 옆) 표시", r"$t_{v,i} = F_v[:, i] + P_i + V_v,\qquad v \in \{1,2,3\},\ i \in \{1,\dots,64\}$"),
 ("8. 교차 주의 (칸 q → 토큰 192) = 어텐션 맵 a", r"$a_i = \mathrm{softmax}_i\left( \frac{(W_q q)^{\top} (W_k t_i)}{\sqrt{256}} \right),\qquad \mathrm{out} = \sum_{i=1}^{192} a_i\ W_v t_i$"),
 ("    빈 조각은 F 가 거의 상수 c → 조각끼리 다른 건 위치 P 뿐 → 그 조각에 쏠리면 내용 아닌 위치로 답함", r"$W_k t_i \approx W_k (c + P_i + V_v)$"),
]
fig = plt.figure(figsize=(16, 15)); fig.patch.set_facecolor("white"); ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
ax.text(.03, .975, "모델127 수식 — CNN(합성곱) → 조각 토큰 → 교차 주의", fontsize=22, weight="bold", va="top")
y = .92
for 설, 식 in 줄:
    ax.text(.03, y, 설, fontsize=14, color="#444", va="top"); ax.text(.06, y - .03, 식, fontsize=21, va="top"); y -= .092
fig.savefig("G:/art2real/out/설명/캐드부품/모델127/수식127.png", dpi=80); print("끝")
