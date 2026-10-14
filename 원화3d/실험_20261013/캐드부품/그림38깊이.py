# 182 · 0 번 — 위에서 판 깊이: 정답 vs 모델 · 가운데 줄 단면 · 10-14
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0][:200]; Y = d["Y"][te]; D = d["D"][te].astype(float)
B = np.load(O + "학습2b/시험예측.npz"); P = B["P"][:200]; PD = B["D"][:200].astype(float)
def 깊이(y, dd): return np.where(y == 3, dd, np.where(y == 2, 1., np.where(y == 1, 0., np.nan)))   # 0 = 안 팜 · 1 = 뚫음
def 단면(y, dd):   # 가운데 줄 · 남는 재료 높이 = 1 − 판 깊이
    k = 깊이(y, dd); r = k.shape[0] // 2; return 1 - k[r]
f, ax = plt.subplots(2, 3, figsize=(15, 8.5), gridspec_kw={"width_ratios": [1, 1, 1.6]})
for i, j in enumerate([182, 0]):
    for c, (y, dd, t) in enumerate([(Y[j], D[j], "정답"), (P[j], PD[j], "모델")]):
        im = ax[i, c].imshow(깊이(y, dd), cmap="magma_r", vmin=0, vmax=1); ax[i, c].axhline(y.shape[0] // 2, color="c", lw=1.5, ls="--")
        ax[i, c].set_title("%d 번 · %s가 판 깊이" % (j, t), fontsize=15); ax[i, c].axis("off")
    a = ax[i, 2]; x = np.arange(Y[j].shape[1])
    for y, dd, 색, t in [(Y[j], D[j], "tab:green", "정답"), (P[j], PD[j], "tab:red", "모델")]:
        h = 단면(y, dd); a.fill_between(x, 0, np.nan_to_num(h, nan=0), step="mid", color=색, alpha=.45, label=t + " 남는 재료")
    a.set_ylim(0, 1.05); a.set_title("하늘색 점선을 옆에서 자른 모습 (아래가 바닥)", fontsize=14); a.legend(fontsize=12, loc="lower right"); a.set_yticks([0, 1], ["바닥", "꼭대기"]); a.set_xticks([])
f.colorbar(im, ax=ax[:, :2], shrink=.6, label="위에서 판 깊이 (어두울수록 깊게)")
f.suptitle("색은 같은데 모델이 더 깊게 판다 — 182 번은 바닥 직전까지", fontsize=17)
plt.savefig(O + "결과38_깊이.png", dpi=80, bbox_inches="tight")
