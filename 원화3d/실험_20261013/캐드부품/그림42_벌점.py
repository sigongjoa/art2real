# 판정기준42 부피 벌점이 실제 부품에서 무엇을 보나 — 칸 벌점(틀린 칸 비율) 대 부피 벌점 · 39 예측(학습 안 함 · 그림만) · 10-14
import numpy as np, torch, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 학습42 as T
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False; O = "G:/art2real/out/설명/캐드부품/"
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; Y = d["Y"][te]; D = d["D"][te].astype(np.float32); del d
C = np.load(O + "학습39/시험예측.npz"); P = C["P"]; PD = C["D"].astype(np.float32)
oh = lambda c: torch.nn.functional.one_hot(torch.tensor(c).long(), 4).permute(0, 3, 1, 2).float() * 50
def 벌(j):
    안 = Y[j] > 0; 칸 = float(((P[j] != Y[j]) & 안).sum() / 안.sum())
    부 = float(T.부피벌점(oh(P[j][None]), torch.tensor(PD[j][None]), torch.tensor(Y[j][None]).long(), torch.tensor(D[j][None])))
    return 칸, 부
벌들 = np.array([벌(j) for j in range(len(te))]); 비교 = int(np.argmax(벌들[:, 0] - 3 * 벌들[:, 1]))   # 칸은 많이 틀렸는데 부피는 거의 같은 부품
def 기둥(y, dd, n=20):   # 칸마다 재료 기둥(바닥부터 1 − 깊이) → 복셀 (64 · 64 로 줄여서)
    y = y[::2, ::2]; dd = dd[::2, ::2]; h = np.where(y == 1, 1., np.where(y == 3, 1 - dd, 0.)); z = (np.arange(n) + .5) / n
    return (y > 0)[..., None] & (z[None, None] < h[..., None])
색 = np.array([[1, 1, 1], [.75, .75, .75], [.85, .2, .2], [.3, .5, .9]])
fig = plt.figure(figsize=(28, 13))
for r, j in enumerate((261, 비교)):
    칸, 부 = 벌들[j]
    for c, (im, t) in enumerate(((1 - X[j], "%d 번 · 입력 위 선 그림" % j), (색[Y[j]], "정답 칠"), (색[P[j]], "모델 칠 (39)"))):
        ax = fig.add_subplot(2, 6, r * 6 + c + 1); ax.imshow(im, cmap="gray" if c == 0 else None); ax.axis("off"); ax.set_title(t, fontsize=17)
    for c, (q, t, cc) in enumerate(((기둥(Y[j], D[j]), "정답 재료 기둥", "tab:green"), (기둥(P[j], PD[j]), "모델 칠로 세운 재료 기둥", "tab:orange"))):
        ax = fig.add_subplot(2, 6, r * 6 + 4 + c, projection="3d"); ax.voxels(q.transpose(1, 0, 2)[:, ::-1], facecolors=cc, edgecolor="k", linewidth=.03)
        ax.set_box_aspect((64, 64, 20)); ax.view_init(35, -60); ax.set_axis_off(); ax.set_title(t, fontsize=17)
    ax = fig.add_subplot(2, 6, r * 6 + 6); ax.axis("off")
    ax.barh([1, 0], [칸, 부], color=["#999", "tab:red"]); ax.set_xlim(0, 1.05); [ax.text(v + .02, k, "%.2f" % v, va="center", fontsize=20) for k, v in ((1, 칸), (0, 부))]
    ax.text(0, 1.45, "예전 벌점: 틀린 칸 비율", fontsize=16, color="#555"); ax.text(0, .45, "새 벌점: 부피 (1 - 겹침)", fontsize=16, color="tab:red"); ax.set_ylim(-.5, 1.9)
fig.suptitle("예전 벌점(틀린 칸 비율)은 두 부품을 똑같이 0.9 넘게 나쁘다고 본다 · 새 부피 벌점은 다르게 본다\n위 261 번: 재료 기둥이 통째로 사라짐 → 0.89 · 아래 605 번: 색은 다 틀렸어도 기둥 높이는 거의 같음 → 0.04  (시험 부품은 설명용 · 학습엔 학습 부품만)", fontsize=19)
plt.savefig(O + "벌점42.png", dpi=55, bbox_inches="tight"); print(261, 벌들[261], 비교, 벌들[비교])
