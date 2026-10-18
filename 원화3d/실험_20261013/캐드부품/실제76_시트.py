# 실제76 결과 한 장 — 줄마다 입력 그림 · 틀 · 판0 32 단계(두 각도) · 10-18
# 사용(venv): 실제76_시트.py <이름> [...] → out/설명/캐드부품/실제입력/시트76.png
import sys, numpy as np, cv2, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection; from skimage.measure import marching_cubes
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False; 빛 = matplotlib.colors.LightSource(315, 40)
D = "G:/art2real/out/설명/캐드부품/실제입력/"; 이름 = sys.argv[1:]
def 칸면(b, v, 색, 방):
    vs, fs, _, _ = marching_cubes(np.pad(v, 1).astype(np.float32), .5); b.add_collection3d(Poly3DCollection(((vs - .5) / 48 * 1.1 - .55)[fs], facecolors=색, edgecolors=색, linewidths=0, shade=True, lightsource=빛))
    b.set_axis_off(); b.set_box_aspect((1, 1, 1)); b.set_xlim(-.5, .5); b.set_ylim(-.5, .5); b.set_zlim(-.5, .5); b.view_init(24, 방)
f = plt.figure(figsize=(20, 4 * len(이름)))
for r, n in enumerate(이름):
    a = f.add_subplot(len(이름), 4, 4 * r + 1); a.imshow(cv2.imdecode(np.fromfile(D + n + ".png", np.uint8), 1)[..., ::-1]); a.set_axis_off(); a.set_title(n, fontsize=14)
    for j, (제, 색, 칸, 방) in enumerate([("틀 (세 윤곽 교차)", "#cfcfcf", np.load(D + n + "/틀.npy"), -55), ("판0 32 단계", "#e8c06a", np.load(D + n + "/칸.npy"), -55), ("판0 · 반대쪽", "#e8c06a", np.load(D + n + "/칸.npy"), 125)]):
        칸면(f.add_subplot(len(이름), 4, 4 * r + 2 + j, projection="3d"), 칸, 색, 방); f.axes[-1].set_title(제, fontsize=14)
plt.tight_layout(); f.savefig(D + "시트76.png", dpi=55); print("ok")
