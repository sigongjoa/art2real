# 판정기준60 그림 — 어려운 217(틀 < 0.5)에서 어디가 틀리나: ① 남는 칸(모델 참 · 정답 거짓) 대 빠진 칸 비율 ② 부품 6 개 등각(입력 위 선 · 정답 · 틀 · 판들) · 10-17
# 사용(venv): 그림60.py 판0예측 HF H → out/설명/판정60_어려운.png · 판정60_부품.png
import sys, json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection; from skimage.measure import marching_cubes
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"; 판들 = sys.argv[1:]
z = np.load(O + "데이터51.npz"); 시 = np.load(O + "데이터.npz")["시험"]; X = np.load(O + "데이터.npz")["X"]; 예부 = np.nonzero(시)[0][json.load(open(O + "범위46.json"))]
풀 = lambda b: np.unpackbits(b)[:48 ** 3].reshape(48, 48, 48).astype(bool)
R = {n: np.load(O + "학습58_%s/부피IoU.npy" % n) for n in 판들}; P = {n: np.load(O + "학습58_%s/예측.npy" % n) for n in 판들}
틀값 = R[판들[0]][:, 1]; 어 = np.nonzero(틀값 < .5)[0]; 이름 = {"판0예측": "전부 학습", "HF": "어려운 것만 이어", "H": "어려운 것만 처음부터"}
# ① 남는 칸 · 빠진 칸 (정답 칸 수로 나눔)
f, ax = plt.subplots(1, 2, figsize=(14, 6)); 표 = {}
for n in 판들:
    남, 빠 = [], []
    for k in 어:
        y, p = 풀(z["정답"][예부[k]]), 풀(P[n][k]); s = max(y.sum(), 1); 남.append((p & ~y).sum() / s); 빠.append((~p & y).sum() / s)
    표[n] = (R[n][어, 0].mean(), np.median(남), np.median(빠))
t = np.array([[(풀(z["틀"][예부[k]]) & ~풀(z["정답"][예부[k]])).sum() / max(풀(z["정답"][예부[k]]).sum(), 1) for k in 어]])
x = np.arange(len(판들)); ax[0].bar(x, [표[n][0] for n in 판들], color=["#888", "#dca01e", "#2a9d4a"][: len(판들)])
for i, n in enumerate(판들): ax[0].text(i, 표[n][0] + .005, "%.3f" % 표[n][0], ha="center", fontsize=14)
ax[0].axhline(.393, ls="--", color="#2a9d4a"); ax[0].text(len(판들) - .5, .395, "통과 0.393", color="#2a9d4a", ha="right", fontsize=12)
ax[0].set_xticks(x); ax[0].set_xticklabels([이름.get(n, n) for n in 판들], fontsize=13); ax[0].set_title("어려운 217 개 칸 IoU", fontsize=15); ax[0].set_ylim(0, max(.5, max(v[0] for v in 표.values()) + .05))
w = .35; ax[1].bar(x - w / 2, [표[n][1] for n in 판들], w, color="#d33", label="남는 칸(정답엔 없음)"); ax[1].bar(x + w / 2, [표[n][2] for n in 판들], w, color="#36c", label="빠진 칸(정답엔 있음)")
for i, n in enumerate(판들): ax[1].text(i - w / 2, 표[n][1] + .02, "%.2f" % 표[n][1], ha="center", fontsize=12); ax[1].text(i + w / 2, 표[n][2] + .02, "%.2f" % 표[n][2], ha="center", fontsize=12)
ax[1].set_xticks(x); ax[1].set_xticklabels([이름.get(n, n) for n in 판들], fontsize=13); ax[1].legend(fontsize=12); ax[1].set_title("틀린 칸 ÷ 정답 칸 (중앙값) · 틀만 쓰면 남는 칸 %.2f" % np.median(t), fontsize=15)
f.suptitle("어려운 부품 217 개: 무엇이 틀리나", fontsize=17); plt.tight_layout(); plt.savefig(O + "../판정60_어려운.png", dpi=95); print({n: [round(float(v), 3) for v in 표[n]] for n in 판들}, "틀 남는 칸 %.2f" % np.median(t))
# ② 부품 6 개(어려운 것 중 IoU 순 고르게)
def 그려(a, v, 색):
    a.set_axis_off(); a.view_init(28, -55); a.set_box_aspect((1, 1, 1)); a.set_xlim(0, 48); a.set_ylim(0, 48); a.set_zlim(0, 48)
    if v.sum() < 8: return
    vs, fs, _, _ = marching_cubes(np.pad(v, 1).astype(float), .5); a.add_collection3d(Poly3DCollection(vs[fs] - 1, facecolors=색, edgecolors=색, linewidths=0, shade=True, lightsource=matplotlib.colors.LightSource(315, 45)))
어 = 어[[풀(z["정답"][예부[k]]).sum() > 50 for k in 어]]; 고른 = 어[np.argsort(R[판들[0]][어, 0])][np.linspace(5, len(어) - 6, 6).astype(int)]; 열 = ["입력(위)", "정답", "틀"] + [이름.get(n, n) for n in 판들]
f = plt.figure(figsize=(3 * len(열), 3 * len(고른)))
for r, k in enumerate(고른):
    i = 예부[k]; a = f.add_subplot(len(고른), len(열), r * len(열) + 1); a.imshow(X[i], cmap="gray_r"); a.set_axis_off()
    if r == 0: a.set_title(열[0], fontsize=15)
    for c, (v, 색, 글) in enumerate([(풀(z["정답"][i]), "#9bd3a8", ""), (풀(z["틀"][i]), "#bbbbc4", "%.2f" % 틀값[k])] + [(풀(P[n][k]), "#e8c06a", "%.2f" % R[n][k, 0]) for n in 판들]):
        a = f.add_subplot(len(고른), len(열), r * len(열) + c + 2, projection="3d"); 그려(a, v, 색); a.set_title((열[c + 1] + "\n" if r == 0 else "") + 글, fontsize=14)
f.suptitle("어려운 부품 6 개 · 숫자 = 정답과 칸 IoU", fontsize=18); plt.tight_layout(rect=(0, 0, 1, .96)); plt.savefig(O + "../판정60_부품.png", dpi=80)
# ③ 어려운 217 을 정답 모양으로 가름: 벽 두께 ≤ 2 칸(한 칸 깎으면 사라짐) · 여러 조각 · 나머지
from scipy.ndimage import binary_erosion
속 = np.array([binary_erosion(풀(z["정답"][예부[k]])).sum() for k in np.nonzero(틀값 < .5)[0]]); 전 = np.nonzero(틀값 < .5)[0]; 조 = R[판들[0]][전, 3]
묶 = [("벽 두께 ≤ 2 칸", 속 == 0), ("여러 조각", (속 > 0) & (조 > 1)), ("두께 있는 한 덩어리", (속 > 0) & (조 <= 1))]
f, a = plt.subplots(figsize=(11, 6)); w = .8 / len(판들)
for j, n in enumerate(판들):
    for i, (nm, m) in enumerate(묶): v = R[n][전[m], 0].mean(); a.bar(i + (j - (len(판들) - 1) / 2) * w, v, w, color=["#888", "#dca01e", "#2a9d4a"][j], label=이름.get(n, n) if i == 0 else None); a.text(i + (j - (len(판들) - 1) / 2) * w, v + .01, "%.2f" % v, ha="center", fontsize=12)
a.set_xticks(range(3)); a.set_xticklabels(["%s\n%d 개" % (nm, m.sum()) for nm, m in 묶], fontsize=13); a.legend(fontsize=12); a.set_ylim(0, .8)
a.set_title("어려운 217 개를 정답 모양으로 가르면 (48³ 칸 · 칸 IoU)", fontsize=15); plt.tight_layout(); plt.savefig(O + "../판정60_모양.png", dpi=95)
