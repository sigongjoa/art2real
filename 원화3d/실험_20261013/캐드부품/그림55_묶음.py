# 묶음 펼쳐 보기 — 사용자 10-16 「시각화해서 보여줘 · 니가 놓치는 게 있겠지 · 잘 돼도 확인」 · 묶음마다 무작위 12 개 · 입력 셋 · 정답 · (나) 판0 CAD · 3D 손실 CAD
# 사용(venv): 그림55_묶음.py <잘됨 | B112 | 천장나쁨 | C168>
import sys, json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from skimage.measure import marching_cubes
import 짓기 as J, 여섯방향_빠른 as S6빠, 평가51나 as E
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"; 묶 = sys.argv[1]
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; del d; e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te]; S = e["S"][te]; L = json.load(open(O + "목록.json", encoding="utf-8"))
범 = json.load(open(O + "범위46.json")); z = np.load(O + "데이터51.npz"); 정, 반 = z["정답"], z["반"]; 풀 = lambda b: np.unpackbits(b)[:48 ** 3].reshape(48, 48, 48).astype(bool)
판 = {}
for 이름, D in (("판0", O + "학습51나_판0전체/"), ("3D", O + "학습54나_판0/")): 판[이름] = (np.load(D + "예측.npy", mmap_mode="r"), {int(i): n for n, i in enumerate(np.load(D + "예측부품.npy"))}, np.load(D + "부피IoU.npy")[:, 0])
천 = np.load(O + "영역53.npy")[:, 0]; 칠천 = np.load(O + "부피IoU_52대조.npy")[:, 1]
자리 = {"잘됨": np.nonzero(판["3D"][2] >= .9)[0], "B112": np.array(json.load(open("묶음54_B112.json", encoding="utf-8"))["자리"]), "천장나쁨": np.nonzero(천 < .5)[0], "C168": np.nonzero(칠천 < .5)[0]}[묶]
고른 = sorted(np.random.default_rng(55).choice(자리, min(12, len(자리)), replace=False))
def 면(ax, q, 색):
    if q.sum() == 0: ax.text2D(.5, .5, "빈 칸", transform=ax.transAxes, ha="center", fontsize=20, color="r"); ax.set_axis_off(); return
    vv, ff, _, _ = marching_cubes(np.pad(q, 1).astype(float), .5); vv = (vv - 1) / 48
    ax.add_collection3d(Poly3DCollection(vv[ff], facecolors=색, linewidths=0, shade=True, lightsource=matplotlib.colors.LightSource(315, 45)))
    lo, hi = vv.min(0), vv.max(0); m = (lo + hi) / 2; r = (hi - lo).max() / 2 + .02
    ax.set_xlim(m[0] - r, m[0] + r); ax.set_ylim(m[1] - r, m[1] + r); ax.set_zlim(m[2] - r, m[2] + r); ax.view_init(35, -58); ax.set_axis_off()
fig = plt.figure(figsize=(30, 4.6 * len(고른)))
for row, k in enumerate(고른):
    j = 범[k]; i = int(te[j]); v, f, H = J.정규메시(L[i]); 몸, _ = J.몸통37((X[j], F[j], S[j]), H)
    for c, (im, t) in enumerate(((X[j], "위"), (F[j], "앞"), (S[j], "옆"))):
        ax = fig.add_subplot(len(고른), 6, row * 6 + c + 1); ax.imshow(1 - im, cmap="gray"); ax.axis("off"); ax.set_title(("%d 번 · " % j if c == 0 else "") + t, fontsize=18)
    ax = fig.add_subplot(len(고른), 6, row * 6 + 4, projection="3d"); 면(ax, 풀(정[i]), "#7fc97f"); ax.set_title("정답 · 천장 %.2f" % 천[k], fontsize=18)
    for col, (이름, 색) in enumerate((("판0", "#9e9ac8"), ("3D", "#5b9bd5"))):
        P, 자, a = 판[이름]; s, _ = S6빠.지킴짓기(몸, E.지도(np.array(P[자[i]]), 반[i])); q = J.점유_캐드(s) if s.vals() else np.zeros((48,) * 3, bool)
        ax = fig.add_subplot(len(고른), 6, row * 6 + 5 + col, projection="3d"); 면(ax, q, 색); ax.set_title(("판0 %.2f" if 이름 == "판0" else "3D 손실 %.2f") % a[k], fontsize=18)
    print(묶, j, flush=True)
이름표 = {"잘됨": "3D 손실 ≥ 0.9(%d 개 중)", "B112": "천장 좋은데 모델이 못 맞힘(%d 개 중)", "천장나쁨": "정답 깊이로도 0.5 아래(%d 개 중)", "C168": "위에서만 칠 천장 < 0.5(%d 개 중)"}[묶] % len(자리)
fig.suptitle("묶음 「%s」 — %s · 무작위 12" % (묶, 이름표), fontsize=26); plt.savefig(O + "묶음55_%s.png" % 묶, dpi=32, bbox_inches="tight")
