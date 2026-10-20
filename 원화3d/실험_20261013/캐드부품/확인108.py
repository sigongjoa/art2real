# 325 · 59 확인 — 세 도면 · 정답 48³ 의 세 방향 투영 · 틀(몸통37) 투영 · 정답 3D 메시 정보 · 10-20
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, cv2
plt.rcParams["font.family"] = "Malgun Gothic"
import 울퉁67 as U
O = "G:/art2real/out/설명/캐드부품/"; d = np.load(O + "데이터.npz"); X, H = d["X"], d["H"]; e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"], e["S"]; h = np.load(O + "숨은선88.npz"); HX, HF, HS = h["HX"], h["HF"], h["HS"]
z = np.load(O + "데이터51.npz"); 틀, 정, 반 = z["틀"], z["정답"], z["반"]; L = json.load(open(O + "목록.json", encoding="utf-8"))
fig, ax = plt.subplots(4, 6, figsize=(22, 15))
for r, (i, 축이름) in enumerate(((325, "325"), (59, "59"))):
    g = U.풀(정[i]).astype(bool); t = U.풀(틀[i]).astype(bool)
    print(i, L[i], "높이비 H", round(float(H[i]), 3), "정답 칸", g.sum(), "틀 칸", t.sum(), "틀 ⊇ 정답", (g & ~t).sum() == 0, "정답 밖 틀", (t & ~g).sum(), "반", np.round(반[i], 3))
    for j, (a, b, nm) in enumerate(((X, HX, "위"), (F, HF, "앞"), (S, HS, "옆"))):
        img = np.ones((128, 128, 3)); img[b[i] > 0] = (.55, .7, 1); img[a[i] > 0] = 0; ax[2 * r, j].imshow(img); ax[2 * r, j].set_title(f"{i} · {nm} 도면 (입력)")
    for j, 축 in enumerate((2, 1, 0)):
        ax[2 * r, 3 + j].imshow(g.any(축), cmap="gray_r"); ax[2 * r, 3 + j].set_title(f"{i} · 정답 48³ 를 축 {축} 로 투영")
        ax[2 * r + 1, 3 + j].imshow(t.any(축).astype(int) + g.any(축), cmap="viridis", vmin=0, vmax=2); ax[2 * r + 1, 3 + j].set_title(f"틀(노랑 = 틀 ∩ 정답 · 초록 = 틀만)")
    for j, 축 in enumerate((2, 1, 0)):
        c = g.shape[축] // 2; sl = np.take(g, c, 축).astype(int) + np.take(t, c, 축); ax[2 * r + 1, j].imshow(sl, cmap="viridis", vmin=0, vmax=2); ax[2 * r + 1, j].set_title(f"가운데 단면 축 {축} (노랑 정답 · 초록 틀만)")
for a in ax.ravel(): a.axis("off")
plt.tight_layout(); plt.savefig(O + "확인108.png", dpi=60); print("저장")
