# 어려움102 그림 — 렉스 · 오메가몬 머리: 세 도면 · 합집합 화소당 후보 수 지도 / 규칙별 「정답 ±1 이 후보에 있음」 대 같은 수 무작위 · 10-20
# 사용(venv): 어려움102_그림.py → out/설명/캐드부품/어려움102/그림.png
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
import 후보96 as H, 후보101 as P
O = "G:/art2real/out/설명/캐드부품/"; D = O + "어려움102/"; K = 32; N = 128
z = np.load(D + "자료.npz"); 결 = json.load(open(D + "결과.json", encoding="utf-8")); 우 = json.load(open(O + "후보101_우연.json", encoding="utf-8")); I = np.load(O + "후보96_색인.npy").astype(np.int64)
fig = plt.figure(figsize=(20, 12)); gs = fig.add_gridspec(3, 5, height_ratios=[1, 1, 1.15])
for r, 이름 in enumerate(["렉스", "오메가몬머리"]):
    g = lambda a: z[f"{이름}__{a}"]
    for j, (a, b, nm) in enumerate((("X", "HX", "위"), ("F", "HF", "앞"), ("S", "HS", "옆"))):
        ax = fig.add_subplot(gs[r, j]); img = np.ones((N, N, 3)); img[g(b) > 0] = (.55, .7, 1); img[g(a) > 0] = 0; ax.imshow(img); ax.set_title(f"{이름} · {nm} 도면 (검정 실선 · 하늘 숨은선)"); ax.axis("off")
    H.열후보 = P.열후보_넓게; C = H.하나(g("X"), g("F"), g("S"), g("HX"), g("HF"), g("HS"), g("반"))
    n = int(np.argmax([((g("입")[k, 1] > 0) & (g("층")[k] < K)).sum() for k in range(6)])); q = (C[n, 0][I[n, 0]] | C[n, 1][I[n, 1]]).astype(np.int64)
    c = np.unpackbits(q.astype("<u4").view(np.uint8).reshape(N, N, 4), axis=-1).sum(-1); 안 = (g("입")[n, 1] > 0) & (g("층")[n] < K)
    ax = fig.add_subplot(gs[r, 3]); m = ax.imshow(np.where(안, c, np.nan), cmap="magma", vmin=0, vmax=32); plt.colorbar(m, ax=ax, fraction=.046); ax.axis("off")
    ax.set_title(f"{H.방[n]}에서 본 화소마다 합집합 후보 수\n(층은 32 개 · 평균 {c[안].mean():.1f})")
    ax = fig.add_subplot(gs[r, 4]); ax.hist(c[안], bins=np.arange(34) - .5, color="#8a45c8"); ax.set_xlabel("화소당 후보 수 (32 이면 모든 층이 후보)"); ax.set_title("후보 수 분포")
ax = fig.add_subplot(gs[2, :]); 줄 = [("CAD 시험 300", {k: (우[k]["깎인 속 ±1"], 우[k]["무작위 같은 수 ±1"]) for k in 우})] + [(nm, {k: (v["깎인 속 ±1"], v["무작위 후보 같은 수 ±1"]) for k, v in 결[nm].items()}) for nm in 결]
규칙 = ["96 수평 ∩", "넓게 ∩", "넓게 ∪"]; 색 = ["#e08a00", "#2a7fd4", "#8a45c8"]; w = .27
for j, k in enumerate(규칙):
    xs = np.arange(len(줄)) + (j - 1) * w; 진 = [s[k][0] for _, s in 줄]; 무 = [s[k][1] for _, s in 줄]
    ax.bar(xs, 진, w * .9, color=색[j], label=f"{k}: 도면 후보"); ax.bar(xs, 무, w * .9, color="none", edgecolor="k", hatch="//", lw=.8, label=f"{k}: 같은 수를 무작위로" if j == 0 else None)
    for x, a, b in zip(xs, 진, 무): ax.text(x, a + .01, f"+{a - b:.2f}", ha="center", fontsize=8)
ax.set_xticks(np.arange(len(줄))); ax.set_xticklabels([n for n, _ in 줄]); ax.set_ylim(0, 1.08); ax.set_ylabel("깎인 속 정답 ±1 이 후보에 있는 몫")
ax.set_title("빗금 = 같은 개수의 층을 무작위로 찍었을 때 · 막대 위 숫자 = 도면이 무작위보다 나은 만큼 · 합집합(보라)은 거의 무작위와 같다", fontsize=12); ax.legend(ncol=4, fontsize=9, loc="lower right")
fig.suptitle("어려운 모양에서 안 되는 것: 선이 너무 많아 한 화소에 후보가 15~24 개 → 「정답이 후보에 있다」가 공짜가 된다", fontsize=15)
plt.tight_layout(); plt.savefig(D + "그림.png", dpi=75); print("저장")
