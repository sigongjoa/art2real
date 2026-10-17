# 실제 부품 모양 — 입력 세 장 · 정답 메시 · 틀 · 모델(58) 칸 결과 · 숫자 = 새 자 F@1 칸 · 10-17 사용자 「실제 하드서피스를 보여 달라」
# 사용(venv): 그림63.py → out/설명/판정63_부품.png
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection; from skimage.measure import marching_cubes; from scipy.ndimage import binary_erosion
import trimesh, 짓기 as J
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"
d = np.load(O + "데이터.npz"); X, 시 = d["X"], d["시험"]; e = np.load(O + "데이터_앞옆.npz"); Fv, Sv = e["F"], e["S"]; z = np.load(O + "데이터51.npz"); 정b, 틀b = z["정답"], z["틀"]
L = json.load(open(O + "목록.json", encoding="utf-8")); 예부 = np.nonzero(시)[0][json.load(open(O + "범위46.json"))]
P = np.load(O + "학습58_판0예측/예측.npy"); R = np.load(O + "자63.npy"); 거 = np.load(O + "거름62.npy"); t = np.load(O + "학습58_H/부피IoU.npy")[:, 1]
풀 = lambda b: np.unpackbits(b)[:48 ** 3].reshape(48, 48, 48).astype(bool)
얇 = np.array([not binary_erosion(풀(정b[i])).any() for i in 예부]) & (t < .5)
rng = np.random.default_rng(63)
def 고르기(m, k=3):   # 묶음 안에서 모델 F 순으로 고르게(최고 · 가운데 · 낮은 쪽)
    ix = np.nonzero(m)[0]; ix = ix[np.argsort(-R[ix, 3])]; return ix[np.linspace(0, len(ix) - 1, k + 2).astype(int)[1:-1]]
묶 = [("쉬움", 거 & (t >= .5)), ("어려움(잴 수 있음)", 거 & (t < .5)), ("얇음", 얇)]
고른 = [(nm, k) for nm, m in 묶 for k in 고르기(m)]
빛 = matplotlib.colors.LightSource(315, 40)
def 면(a, vs, fs, 색):
    a.add_collection3d(Poly3DCollection(vs[fs], facecolors=색, edgecolors=색, linewidths=0, shade=True, lightsource=빛))
def 축(a, lo=-.55, hi=.55):
    a.set_axis_off(); a.view_init(26, -50); a.set_box_aspect((1, 1, 1)); a.set_xlim(lo, hi); a.set_ylim(lo, hi); a.set_zlim(lo, hi)
def 칸면(a, v, 색):
    if v.sum() < 1: a.text2D(.5, .5, "비어 있음", ha="center", transform=a.transAxes, fontsize=14, color="#d33"); return
    vs, fs, _, _ = marching_cubes(np.pad(v, 1).astype(np.float32), .5); 면(a, (vs - 1 + .5) / 48 * 1.1 - .55, fs, 색)
열 = ["위", "앞", "옆", "정답 (실제 CAD)", "틀 (윤곽 교집합)", "모델 결과"]
f = plt.figure(figsize=(3.1 * len(열), 3.1 * len(고른)))
for r, (nm, k) in enumerate(고른):
    i = 예부[k]
    for c, im in enumerate((X[i], Fv[i], Sv[i])):
        a = f.add_subplot(len(고른), len(열), r * len(열) + c + 1); a.imshow(im, cmap="gray_r"); a.set_xticks([]); a.set_yticks([])
        if c == 0: a.set_ylabel(nm, fontsize=15)
        if r == 0: a.set_title(열[c], fontsize=15)
    v, fc, _ = J.정규메시(L[i]); m = trimesh.Trimesh(v, fc, process=False)
    if len(m.faces) > 40000: m = m.simplify_quadric_decimation(face_count=40000)
    a = f.add_subplot(len(고른), len(열), r * len(열) + 4, projection="3d"); 축(a); 면(a, np.asarray(m.vertices), np.asarray(m.faces), "#9bd3a8"); a.set_title((열[3] + "\n" if r == 0 else ""), fontsize=15)
    for c, (b, 색, F) in enumerate([(풀(틀b[i]), "#bbbbc4", R[k, 2]), (풀(P[k]), "#e8c06a", R[k, 3])]):
        a = f.add_subplot(len(고른), len(열), r * len(열) + 5 + c, projection="3d"); 축(a); 칸면(a, b, 색); a.set_title((열[4 + c] + "\n" if r == 0 else "") + "F %.2f" % F, fontsize=14)
f.suptitle("실제 부품 9 개 — 입력 세 장 → 정답 · 틀 · 모델 (F = 정답 표면 1 칸 안 비율)", fontsize=19); plt.tight_layout(rect=(0, 0, 1, .97)); plt.savefig(O + "../판정63_부품.png", dpi=72)
