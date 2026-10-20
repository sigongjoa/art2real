# 판정기준97 해석용 — 부품 하나를 가로줄 하나로 자른 단면: 실제 면(정답 층) 위에 다른 도면에서 온 깊이 후보를 겹침 · 성공(59) 대 실패(66) · 10-20
# 사용(venv · ART_MEM_GB=8): 후보101_단면.py → out/설명/캐드부품/후보101_단면.png
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
import 후보101 as P
O = P.O; K = 32
d = np.load(O + "데이터.npz"); P.X = d["X"]; e = np.load(O + "데이터_앞옆.npz"); P.F, P.S = e["F"], e["S"]
h = np.load(O + "숨은선88.npz"); P.HX, P.HF, P.HS = h["HX"], h["HF"], h["HS"]; P.반 = np.load(O + "데이터51.npz")["반"]
I = np.load(O + "후보96_색인.npy").astype(np.int64)
층 = np.load(O + "층32.npy", mmap_mode="r"); 입 = np.load(O + "입력51.npy", mmap_mode="r"); 껍 = np.load(O + "껍질32.npy", mmap_mode="r")
bits = lambda q: np.stack([((q >> c) & 1) > 0 for c in range(K)], -1)
경우 = [(59, 0, 64, "성공: 컵 (바닥이 평평)"), (66, 1, 63, "실패: 누운 원기둥 (면이 둥글다)")]
fig, ax = plt.subplots(2, 2, figsize=(16, 11), gridspec_kw={"width_ratios": [1, 2.4]})
for r, (i, n, y, 제목) in enumerate(경우):
    C = P.후보(i, True); 교 = bits((C[n, 0][I[n, 0]] & C[n, 1][I[n, 1]]).astype(np.int64))[y]; 합 = bits((C[n, 0][I[n, 0]] | C[n, 1][I[n, 1]]).astype(np.int64))[y]
    g = 층[i, n].astype(np.int64); 안 = (입[i, n, 1] > 0) & (g < K); 깎 = 안 & (g >= 껍[i, n].astype(np.int64) + 2)
    a = ax[r, 0]; a.imshow(np.where(안, 1 - 입[i, n, 0].astype(float), .4), cmap="gray", vmin=0, vmax=1); a.axhline(y, color="r", lw=2)
    a.set_title(f"부품 {i} · 이 방향에서 본 모습\n빨간 줄을 따라 자른다"); a.axis("off")
    a = ax[r, 1]; xs = np.arange(g.shape[1]); gy = np.where(안[y], g[y], np.nan)
    a.fill_between(xs, gy, K, where=안[y], color="#e8e8e8", step="mid", label="실제 물체 (보이는 면 뒤)")
    for x in xs:
        if not 안[y, x]: continue
        for c in np.nonzero(합[x])[0]: a.add_patch(plt.Rectangle((x - .5, c - .5), 1, 1, color="#2a7fd4" if 교[x, c] else "#f0a030", lw=0))
    a.step(xs, gy, "k-", where="mid", lw=2.5, label="실제 면 = 정답 깊이")
    m = 깎[y]; a.plot(xs[m], gy[m], "o", color="r", ms=3, label="깎아야 하는 곳")
    a.add_patch(plt.Rectangle((0, 0), 0, 0, color="#2a7fd4", label="후보: 다른 두 도면 모두에 선이 있는 깊이 (교집합)"))
    a.add_patch(plt.Rectangle((0, 0), 0, 0, color="#f0a030", label="후보: 한 도면에만 선이 있는 깊이 (합집합에 더해짐)"))
    a.set_ylim(K, -1); a.set_xlim(xs[안[y]].min() - 3, xs[안[y]].max() + 3); a.set_xlabel("가로 위치"); a.set_ylabel("깊이 (0 = 맨 앞)")
    hit교 = sum(교[x, max(g[y, x] - 1, 0):g[y, x] + 2].any() for x in xs[m]); hit합 = sum(합[x, max(g[y, x] - 1, 0):g[y, x] + 2].any() for x in xs[m]); nc = 합[안[y]].sum(1).mean()
    a.set_title(f"{제목} — 단면\n깎을 곳 {m.sum()}칸 중 파랑으로 맞음 {hit교} · 주황까지 넣으면 {hit합} · 한 칸 위 후보 평균 {nc:.1f}개", fontsize=13)
    a.legend(loc="lower right", fontsize=9)
fig.suptitle("검은 선(진짜 면)이 색칸(후보) 위를 지나면 맞음.  컵: 파랑만으로 맞음.  원기둥: 파랑은 빗나가고, 주황을 넣으면 맞지만 엉뚱한 주황도 많아 고를 수 없음", fontsize=13)
plt.tight_layout(); plt.savefig(O + "후보101_단면.png", dpi=85); print("저장")
