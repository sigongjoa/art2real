# 판정기준97 그림 — 부품마다 깎인 속이 가장 많은 방향 하나: 정답 층 · ∩ 맞음/빠짐 · ∪ 맞음/빠짐 · ∪ 후보 수 · 가운데 가로줄 한 줄 후보 대 정답 · 10-20
# 사용(venv · ART_MEM_GB=8): 후보101_그림.py [부품...] → out/설명/캐드부품/후보101_그림.png
import sys, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 후보101 as P
O = P.O; K = 32
d = np.load(O + "데이터.npz"); P.X = d["X"]; 시 = d["시험"]; e = np.load(O + "데이터_앞옆.npz"); P.F, P.S = e["F"], e["S"]
h = np.load(O + "숨은선88.npz"); P.HX, P.HF, P.HS = h["HX"], h["HF"], h["HS"]; P.반 = np.load(O + "데이터51.npz")["반"]
I = np.load(O + "후보96_색인.npy").astype(np.int64)
층 = np.load(O + "층32.npy", mmap_mode="r"); 입 = np.load(O + "입력51.npy", mmap_mode="r"); 껍 = np.load(O + "껍질32.npy", mmap_mode="r")
부품 = [int(a) for a in sys.argv[1:]] or [59, 0, 14, 66]
bits = lambda q: np.stack([((q >> c) & 1) > 0 for c in range(K)], -1)   # (N, N, 32)
fig, ax = plt.subplots(len(부품), 5, figsize=(22, 4.4 * len(부품)))
for r, i in enumerate(부품):
    C좁 = P.후보(i, False); C넓 = P.후보(i, True)
    g6 = 층[i].astype(np.int64); s6 = 껍[i].astype(np.int64); 안6 = (입[i, :, 1] > 0) & (g6 < K); 깎6 = 안6 & (g6 >= s6 + 2)
    n = int(np.argmax(깎6.sum((1, 2)))); g, 안, 깎 = g6[n], 안6[n], 깎6[n]
    q = {"∩": C넓[n, 0][I[n, 0]] & C넓[n, 1][I[n, 1]], "∪": C넓[n, 0][I[n, 0]] | C넓[n, 1][I[n, 1]], "96": C좁[n, 0][I[n, 0]] & C좁[n, 1][I[n, 1]]}
    q = {k: v.astype(np.int64) for k, v in q.items()}
    def 맞음(v):
        b = bits(v); gg = np.clip(g, 0, K - 1); 곁 = np.zeros_like(안)
        for dd in (-1, 0, 1): 곁 |= np.take_along_axis(b, np.clip(gg + dd, 0, K - 1)[..., None], -1)[..., 0]
        img = np.ones((*g.shape, 3)); img[안] = .85; img[깎 & 곁] = (.15, .65, .3); img[깎 & ~곁] = (.85, .2, .2); return img, (깎 & 곁).sum() / max(깎.sum(), 1)
    gm = np.where(안, g, np.nan); a = ax[r, 0].imshow(gm, cmap="viridis", vmin=0, vmax=31); plt.colorbar(a, ax=ax[r, 0], fraction=.046)
    ax[r, 0].set_title(f"part {i} dir {n}: GT layer (0=front)\ncarved interior = {깎.sum()} px")
    for j, k in ((1, "∩"), (2, "∪")):
        img, f = 맞음(q[k]); ax[r, j].imshow(img); ax[r, j].set_title(f"wide {'AND' if k == '∩' else 'OR'}: GT±1 in candidates\ngreen hit / red miss = {f:.2f} (carved)")
    cnt = np.where(안, bits(q["∪"]).sum(-1), np.nan); a = ax[r, 3].imshow(cnt, cmap="magma", vmin=0, vmax=20); plt.colorbar(a, ax=ax[r, 3], fraction=.046)
    ax[r, 3].set_title(f"wide OR: candidates per px\nmean {np.nanmean(cnt):.1f} (pass needs <= 8)")
    ys = np.nonzero(깎.any(1))[0]; y = int(ys[len(ys) // 2]) if len(ys) else g.shape[0] // 2; ax[r, 0].axhline(y, color="w", lw=.8); xs = np.arange(g.shape[1])
    for k, col, s, dy in (("∪", "#bbbbbb", 30, 0), ("∩", "#2a7fd4", 14, 0), ("96", "#e08a00", 5, 0)):
        b = bits(q[k])[y]; yy, cc = np.nonzero(b.T); ax[r, 4].scatter(cc, yy, s=s, c=col, marker="s", lw=0, label={"∪": "wide OR", "∩": "wide AND", "96": "96 horizontal AND"}[k])
    ax[r, 4].plot(xs, np.where(안[y], g[y], np.nan), "k-", lw=2, label="GT layer"); m = 깎[y]; ax[r, 4].plot(xs[m], g[y][m], "r.", ms=4, label="carved px")
    ax[r, 4].set_ylim(32, -1); ax[r, 4].set_xlim(0, g.shape[1]); ax[r, 4].set_title(f"row y={y}: candidates (squares) vs GT (line)"); ax[r, 4].legend(fontsize=7, loc="lower right")
    for j in range(4): ax[r, j].axis("off")
fig.suptitle("Criterion 97 FAIL: AND misses the carved depth (red), OR covers it (green) but leaves ~11 candidates per pixel", fontsize=15)
plt.tight_layout(); plt.savefig(O + "후보101_그림.png", dpi=80); print("저장")
