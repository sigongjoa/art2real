# 83 편 재료 — 부품 59 컵 턴테이블 48 장: 정답(truth) · 판0 망 깎기(model) · 포켓 16 층 가설(pocket) · 관통 가설(through) · 같은 48³ 칸 · 같은 상자 · 10-19
# 사용(venv · ART_MEM_GB=8): 재료83.py → Remotion public/ep83/cup_<종류>/NN.png
import os, json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection; from PIL import Image; from skimage import measure; from scipy.ndimage import gaussian_filter
import 평가69 as E, 울퉁67 as U
R = "C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/1b9641c4-09e3-416a-8c59-c894cf94f212/scratchpad/motion/work/remotion/public/ep83/"; O = "G:/art2real/out/설명/캐드부품/"; 장 = 48; i = 59
층 = np.load(O + "층32.npy", mmap_mode="r"); z = np.load(O + "데이터51.npz"); L = json.load(open(O + "목록.json", encoding="utf-8")); 빛 = matplotlib.colors.LightSource(315, 40)
P = np.load(O + "학습69_판0/예측.npy", mmap_mode="r"); 부 = list(np.load(O + "학습69_판0/예측부품.npy")); 입 = np.load(O + "입력51.npy", mmap_mode="r")
import cv2; n, lab = cv2.connectedComponents(((입[i, 0, 0] == 0) & (입[i, 0, 1] > 0)).astype(np.uint8), connectivity=4); 원 = lab == lab[64, 64]
def 깎(t): return U.풀(E.하나((0, L[i], t, z["반"][i], z["틀"][i], z["정답"][i]))[1])
g = np.array(층[i]); 관 = g.copy(); 관[0][원] = 32
판 = [("truth", U.풀(z["정답"][i]), "#9bd3a8"), ("model", 깎(np.array(P[부.index(i)])), "#e8c06a"), ("pocket", 깎(g), "#9bd3a8"), ("through", 깎(관), "#e07070")]
파 = []
for 종류, v, 색 in 판:
    os.makedirs(R + "cup_" + 종류, exist_ok=True); vv, ff, _, _ = measure.marching_cubes(gaussian_filter(np.pad(v, 2).astype(float), .7), .5)
    for t in range(장):
        f = plt.figure(figsize=(4.8, 4.8)); a = f.add_subplot(projection="3d"); a.set_axis_off(); a.set_box_aspect((1, 1, 1)); [s(0, 52) for s in (a.set_xlim, a.set_ylim, a.set_zlim)]; a.view_init(42, -50 + 360 * t / 장)
        a.add_collection3d(Poly3DCollection(vv[ff], facecolors=색, edgecolors=색, linewidths=0, shade=True, lightsource=빛))
        p = R + "cup_%s/%02d.png" % (종류, t); f.subplots_adjust(0, 0, 1, 1); f.savefig(p, dpi=100, transparent=True); plt.close(f); 파.append(p)
bs = [b for b in (Image.open(p).split()[3].point(lambda q: 255 if q > 8 else 0).getbbox() for p in 파) if b]
b = (min(x[0] for x in bs), min(x[1] for x in bs), max(x[2] for x in bs), max(x[3] for x in bs)); w, h = b[2] - b[0], b[3] - b[1]; s = int(max(w, h) * 1.06)
for p in 파:
    im = Image.open(p).convert("RGBA"); cc = Image.new("RGBA", (s, s), (0, 0, 0, 0)); cc.paste(im.crop(b), ((s - w) // 2, (s - h) // 2)); cc.resize((480, 480), Image.LANCZOS).save(p)
print("ok", [(k, int(v.sum())) for k, v, _ in 판])
