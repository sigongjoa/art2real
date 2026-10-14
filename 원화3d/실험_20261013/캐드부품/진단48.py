# 진단48 — 없는 구멍(261 · 719): 학습 부품 중 위 · 앞 · 옆 그림이 가장 비슷한 것들의 정답 칠 · 10-15
import numpy as np, cv2, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"
d = np.load(O + "데이터.npz"); 시 = d["시험"]; X, Y = d["X"], d["Y"]; del d; e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"], e["S"]
te, tr = np.nonzero(시)[0], np.nonzero(~시)[0]
def 특징(i): return np.concatenate([cv2.resize(cv2.dilate(a[i].astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32), (32, 32), interpolation=cv2.INTER_AREA).ravel() for a in (X, F, S)])
T = np.stack([특징(i) for i in tr]); T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-9
색 = np.array([[1, 1, 1], [.75, .75, .75], [.85, .2, .2], [.3, .5, .9]]); P = np.load(O + "학습42/시험예측.npz")["P"]
fig, ax = plt.subplots(4, 7, figsize=(28, 16))
for r, j in enumerate((261, 719)):
    q = 특징(te[j]); q /= np.linalg.norm(q) + 1e-9; 이웃 = tr[np.argsort(-(T @ q))[:5]]; 구멍 = [float((Y[i] == 2).sum() / max((Y[i] > 0).sum(), 1)) for i in 이웃]
    for c, (im, t) in enumerate([(1 - X[te[j]], "%d 번 · 위 선" % j), (색[Y[te[j]]], "정답 칠"), (색[P[j]], "모델(42) 칠")] + [(1 - X[i], "비슷한 학습 %d · 위 선" % (k + 1)) for k, i in enumerate(이웃[:4])]):
        ax[r * 2, c].imshow(im, cmap="gray" if im.ndim == 2 else None); ax[r * 2, c].axis("off"); ax[r * 2, c].set_title(t, fontsize=14)
    for c in range(3): ax[r * 2 + 1, c].axis("off")
    ax[r * 2 + 1, 0].text(0, .5, "가장 비슷한 학습 부품 5 개 중\n구멍(빨강) 비율 > 30 %% : %d 개" % sum(g > .3 for g in 구멍), fontsize=17, va="center")
    for k, i in enumerate(이웃[:4]): ax[r * 2 + 1, 3 + k].imshow(색[Y[i]]); ax[r * 2 + 1, 3 + k].axis("off"); ax[r * 2 + 1, 3 + k].set_title("그 학습 부품 정답 칠 · 구멍 %.0f %%" % (구멍[k] * 100), fontsize=14)
fig.suptitle("진단48 — 없는 구멍을 뚫는 부품: 학습 부품 중 그림이 비슷한 것들은 정답이 「구멍」이었나?", fontsize=20)
plt.savefig(O + "진단48_구멍.png", dpi=50, bbox_inches="tight"); print("ok")
