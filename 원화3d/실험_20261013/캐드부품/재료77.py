# 77 편 재료 — 곡선77 · 둥근 고리(시험 18 · 곡면 많음) 의 정답 · 정답 깊이 32 단계 깎기(천장32) · 모델(학습69 판0) 턴테이블 48 장(같은 상자로 자름) · 10-18
# 사용(venv): 재료77.py → Remotion public/ep77/ring_<종류>/NN.png
import os, json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection; from skimage.measure import marching_cubes; from PIL import Image
import 짓기 as J
R = "C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/1b9641c4-09e3-416a-8c59-c894cf94f212/scratchpad/motion/work/remotion/public/ep77/"; O = "G:/art2real/out/설명/캐드부품/"; 장 = 48; k = 18
시 = np.load(O + "데이터.npz")["시험"]; L = json.load(open(O + "목록.json", encoding="utf-8")); 예부 = np.nonzero(시)[0][json.load(open(O + "범위46.json"))]
풀 = lambda b: np.unpackbits(b)[:48 ** 3].reshape(48, 48, 48).astype(bool); 빛 = matplotlib.colors.LightSource(315, 40)
v, fc, _ = J.정규메시(L[예부[k]]); 파 = []; v = np.asarray(v); import trimesh; 회 = trimesh.Trimesh(v, fc).principal_inertia_vectors; 회 = 회[[0, 1, 2]] * np.sign(np.linalg.det(회))   # 고리 축(관성 큰 축 · 기울어 있음)을 z 로 — 돌릴 때 옆으로 서지 않게 · 보여 주기만
for 종류, 칸, 색 in [("truth", None, "#9bd3a8"), ("ceil", np.load(O + "천장32/칸.npy")[k], "#7fb3e8"), ("model", np.load(O + "학습69_판0/칸.npy")[k], "#e8c06a")]:
    if 칸 is None: vs, fs = v @ 회.T, np.asarray(fc)
    else: vs, fs, _, _ = marching_cubes(np.pad(풀(칸), 1).astype(np.float32), .5); vs = ((vs - .5) / 48 * 1.1 - .55) @ 회.T
    os.makedirs(R + "ring_" + 종류, exist_ok=True)
    for t in range(장):
        f = plt.figure(figsize=(4.8, 4.8)); a = f.add_subplot(projection="3d"); a.set_axis_off(); a.set_box_aspect((1, 1, 1))
        a.set_xlim(-.5, .5); a.set_ylim(-.5, .5); a.set_zlim(-.5, .5); a.view_init(28, -50 + 360 * t / 장)
        a.add_collection3d(Poly3DCollection(vs[fs], facecolors=색, edgecolors=색, linewidths=0, shade=True, lightsource=빛))
        p = R + "ring_%s/%02d.png" % (종류, t); f.subplots_adjust(0, 0, 1, 1); f.savefig(p, dpi=100, transparent=True); plt.close(f); 파.append(p)
bs = [b for b in (Image.open(p).split()[3].point(lambda q: 255 if q > 8 else 0).getbbox() for p in 파) if b]
b = (min(x[0] for x in bs), min(x[1] for x in bs), max(x[2] for x in bs), max(x[3] for x in bs)); w, h = b[2] - b[0], b[3] - b[1]; s = int(max(w, h) * 1.06)
for p in 파:
    im = Image.open(p).convert("RGBA"); cc = Image.new("RGBA", (s, s), (0, 0, 0, 0)); cc.paste(im.crop(b), ((s - w) // 2, (s - h) // 2)); cc.resize((480, 480), Image.LANCZOS).save(p)
print("ring", k)
