# 판정기준54 그림 — (나) 판0(층 손실) 대 3D 손실 · 가장 오른 4 · 가장 내린 4 · 정해 둔 2(942 · 264) · 정답 · 판0 CAD · 3D 손실 CAD · 10-16
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from skimage.measure import marching_cubes
import 짓기 as J, 여섯방향_빠른 as S6빠, 평가51나 as E
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; del d; e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te]; S = e["S"][te]; L = json.load(open(O + "목록.json", encoding="utf-8"))
범 = json.load(open(O + "범위46.json")); 자리 = {j: k for k, j in enumerate(범)}; z = np.load(O + "데이터51.npz"); 정, 반 = z["정답"], z["반"]; 풀 = lambda b: np.unpackbits(b)[:48 ** 3].reshape(48, 48, 48).astype(bool)
판 = {}
for 이름, D in (("판0", O + "학습51나_판0전체/"), ("3D", O + "학습54나_판0/")): 판[이름] = (np.load(D + "예측.npy", mmap_mode="r"), {int(i): n for n, i in enumerate(np.load(D + "예측부품.npy"))}, np.load(D + "부피IoU.npy")[:, 0])
차 = 판["3D"][2] - 판["판0"][2]; 오 = list(np.argsort(-차)[:4]); 내 = list(np.argsort(차)[:4]); 고른 = [(범[k], "오름") for k in 오] + [(범[k], "내림") for k in 내] + [(942, "정해 둔"), (264, "정해 둔")]
def 면(ax, q, 색):
    if q.sum() == 0: ax.text2D(.5, .5, "빈 칸", transform=ax.transAxes, ha="center", fontsize=20, color="r"); ax.set_axis_off(); return
    vv, ff, _, _ = marching_cubes(np.pad(q, 1).astype(float), .5); vv = (vv - 1) / 48
    ax.add_collection3d(Poly3DCollection(vv[ff], facecolors=색, linewidths=0, shade=True, lightsource=matplotlib.colors.LightSource(315, 45)))
    lo, hi = vv.min(0), vv.max(0); m = (lo + hi) / 2; r = (hi - lo).max() / 2 + .02
    ax.set_xlim(m[0] - r, m[0] + r); ax.set_ylim(m[1] - r, m[1] + r); ax.set_zlim(m[2] - r, m[2] + r); ax.view_init(35, -58); ax.set_axis_off()
fig = plt.figure(figsize=(22, 5.2 * len(고른)))
for row, (j, 종) in enumerate(고른):
    k = 자리[j]; i = int(te[j]); v, f, H = J.정규메시(L[i]); 몸, _ = J.몸통37((X[j], F[j], S[j]), H)
    ax = fig.add_subplot(len(고른), 4, row * 4 + 1); ax.imshow(1 - X[j], cmap="gray"); ax.axis("off"); ax.set_title("%d 번 · %s" % (j, 종), fontsize=20)
    ax = fig.add_subplot(len(고른), 4, row * 4 + 2, projection="3d"); 면(ax, 풀(정[i]), "#7fc97f"); ax.set_title("정답", fontsize=22)
    for col, (이름, 색) in enumerate((("판0", "#9e9ac8"), ("3D", "#5b9bd5"))):
        P, 자, a = 판[이름]; s, _ = S6빠.지킴짓기(몸, E.지도(np.array(P[자[i]]), 반[i])); q = J.점유_캐드(s) if s.vals() else np.zeros((48,) * 3, bool)
        ax = fig.add_subplot(len(고른), 4, row * 4 + 3 + col, projection="3d"); 면(ax, q, 색); ax.set_title(("층 손실(판0) %.2f" if 이름 == "판0" else "3D 손실 %.2f") % a[k], fontsize=22)
    print(j, flush=True)
fig.suptitle("판정기준54 — 손실을 3D 로 · 712 개 평균 0.696 → 0.698 · 망침 124 → 87 · 조각내기 59 → 43", fontsize=26)
plt.savefig(O + "결과54.png", dpi=36, bbox_inches="tight")
