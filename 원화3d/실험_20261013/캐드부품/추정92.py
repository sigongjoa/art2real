# 점선(숨은선)으로 깊이를 추정하는 과정 보기 — 사용자 10-19 「점선으로 깊이를 추정할 수 있다며 · 추정 과정을 보여줘」 · 10-19
# ① 정보가 있나: 정답 깊이 끊김(이웃 층 차 ≥ 2) 화소 중 실선이 못 덮고 점선이 덮는 몫 ② 모델이 쓰나: 그 화소 둘레에서 B(점선 없음) · A(점선 있음) 층 맞음
# 사용(venv · ART_MEM_GB=8): 추정92.py → out/설명/캐드부품/추정92.png · 추정92.json
import json, numpy as np, cv2, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"; 이름 = ["위", "아래", "앞", "뒤", "옆", "반옆"]
입 = np.load(O + "입력51.npy", mmap_mode="r"); 숨 = np.load(O + "숨은입력89.npy", mmap_mode="r"); 층 = np.load(O + "층32.npy", mmap_mode="r")
부 = np.load(O + "학습69_넓은숨은/예측부품.npy"); PA = np.load(O + "학습69_넓은숨은/예측.npy", mmap_mode="r"); PB = np.load(O + "학습69_넓은/예측.npy", mmap_mode="r")
K = np.ones((3, 3), np.uint8)
def 끊김(g, 안):   # 정답 층 이웃 차 ≥ 2 (윤곽 안)
    g = g.astype(int); e = np.zeros_like(안)
    e[:-1] |= np.abs(np.diff(g, axis=0)) >= 2; e[:, :-1] |= np.abs(np.diff(g, axis=1)) >= 2; return e & 안
합 = dict(끊김=0, 실선=0, 점선만=0, 둘레=0, A맞음=0, B맞음=0); 부품별 = []
for n, i in enumerate(부):
    s = 0
    for k in range(6):
        안 = 입[i, k, 1] > 0; g = 층[i, k]; e = 끊김(g, 안)
        if not e.any(): continue
        실 = cv2.dilate((입[i, k, 0] > 0).astype(np.uint8), K) > 0; 점 = cv2.dilate((숨[i, k] > 0).astype(np.uint8), K) > 0
        만 = e & ~실 & 점; 둘 = (cv2.dilate(만.astype(np.uint8), K) > 0) & 안   # 점선만 알려 주는 끊김 둘레 화소
        합["끊김"] += e.sum(); 합["실선"] += (e & 실).sum(); 합["점선만"] += 만.sum(); 합["둘레"] += 둘.sum()
        합["A맞음"] += (PA[n, k] == g)[둘].sum(); 합["B맞음"] += (PB[n, k] == g)[둘].sum(); s += 만.sum()
    부품별.append((s, n))
r = {"정답 깊이 끊김 화소": int(합["끊김"]), "실선이 덮음": round(합["실선"] / 합["끊김"], 3), "실선 못 덮고 점선만 덮음": round(합["점선만"] / 합["끊김"], 3),
     "그 둘레 층 맞음 B(점선 없음)": round(합["B맞음"] / 합["둘레"], 3), "그 둘레 층 맞음 A(점선 있음)": round(합["A맞음"] / 합["둘레"], 3), "시험 부품": len(부)}
print(r); json.dump(r, open("추정92.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
# 그림: 점선만 덮는 끊김이 가장 많은 부품 3 개 · 그중 가장 많은 방향 하나씩
열 = ["입력 실선", "입력 점선", "정답 깊이", "끊김: 초록 실선 · 빨강 점선만", "B 점선 없음 · 틀림 빨강", "A 점선 있음 · 틀림 빨강"]
고른 = [n for _, n in sorted(부품별, reverse=True)[:3]]; f, ax = plt.subplots(len(고른), 6, figsize=(18, 3.3 * len(고른)))
for row, n in enumerate(고른):
    i = 부[n]; best = max(range(6), key=lambda k: ((끊김(층[i, k], 입[i, k, 1] > 0)) & (cv2.dilate((숨[i, k] > 0).astype(np.uint8), K) > 0) & ~(cv2.dilate((입[i, k, 0] > 0).astype(np.uint8), K) > 0)).sum()); k = best
    안 = 입[i, k, 1] > 0; g = 층[i, k]; e = 끊김(g, 안); 실 = cv2.dilate((입[i, k, 0] > 0).astype(np.uint8), K) > 0; 점 = cv2.dilate((숨[i, k] > 0).astype(np.uint8), K) > 0
    깊 = lambda p: np.ma.masked_where(~안, p.astype(float))
    ov = np.ones((128, 128, 3)) * .93; ov[안] = .8; ov[e & 실] = (.2, .65, .3); ov[e & ~실 & 점] = (.85, .15, .15); ov[e & ~실 & ~점] = (.2, .2, .2)
    for j, (im, kw) in enumerate([(입[i, k, 0], dict(cmap="gray_r")), (숨[i, k], dict(cmap="Reds")), (깊(g), dict(cmap="viridis", vmin=0, vmax=32)), (ov, {})]):
        ax[row, j].imshow(im, **kw)
    for j, P in ((4, PB), (5, PA)):
        a = ax[row, j]; a.imshow(깊(P[n, k]), cmap="viridis", vmin=0, vmax=32); w = (P[n, k] != g) & 안; t = np.zeros((128, 128, 4)); t[w] = (1, 0, 0, .55); a.imshow(t)
        a.set_xlabel("층 맞음 %.2f" % (P[n, k] == g)[안].mean())
    for j in range(6): ax[row, j].set_xticks([]); ax[row, j].set_yticks([]); ax[row, j].set_title(("부품 %d · %s 방향\n" % (i, 이름[k]) if j == 0 else "\n") + 열[j], fontsize=11)
plt.tight_layout(); f.savefig(O + "추정92.png", dpi=70); print(O + "추정92.png")
