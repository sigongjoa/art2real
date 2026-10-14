# 판정기준38 그림 — 위에서 본 그림 · 모델이 칠한 구멍 · 38 규칙 뒤 · 10-14
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 평가38 as E
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0][:200]; X = d["X"][te]; Y = d["Y"][te]
P = np.load(O + "학습2b/시험예측.npz")["P"][:200]; a = np.load(O + "부피IoU_38_2b.npy")
색 = np.array([[1, 1, 1], [.75, .75, .75], [.85, .2, .2], [.3, .5, .9]])   # 빈 곳 · 윗면 · 뚫음 · 들어감
f, ax = plt.subplots(3, 4, figsize=(12, 9.5))
for c, j in enumerate([182, 129, 131, 0]):
    for r, (im, t) in enumerate([(색[Y[j]], "정답 구멍"), (색[P[j]], "모델이 칠한 구멍"), (색[E.갇힌만(P[j], X[j])], "38 규칙 뒤 · %.2f" % a[j, 0])]):
        ax[r, c].imshow(im); ax[r, c].set_title(("%d 번 · " % j if r == 0 else "") + t, fontsize=13); ax[r, c].axis("off")
f.suptitle("빨강 = 뚫는 곳 · 가장자리에 닿는 빨강만 메우는 규칙 → 182 번은 빨강이 안쪽에 갇혀 그대로", fontsize=14)
plt.tight_layout(); plt.savefig(O + "결과38.png", dpi=80)
