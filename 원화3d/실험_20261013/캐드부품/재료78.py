# 78 편 재료 — 판정기준79 · 80 · 비누 모양 부품(시험 82) 정답 · 판0 칸 깎기 · 판0 곡면 맞춤(고친 뒤 · 고치기 전 = 062866c 곡면79 로 다시 지은 것) 턴테이블 48 장(같은 상자로 자름) · 10-18
# 사용(venv): 재료78.py → Remotion public/ep78/soap_<종류>/NN.png
import os, json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection; from PIL import Image
import 짓기 as J
R = "C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/1b9641c4-09e3-416a-8c59-c894cf94f212/scratchpad/motion/work/remotion/public/ep78/"; O = "G:/art2real/out/설명/캐드부품/"; D = O + "곡면79/"; 장 = 48; k = 82
시 = np.load(O + "데이터.npz")["시험"]; te = np.nonzero(시)[0]; 예부 = te[json.load(open(O + "범위46.json"))]; L = json.load(open(O + "목록.json", encoding="utf-8")); 빛 = matplotlib.colors.LightSource(315, 40)
v, f, _ = J.정규메시(L[예부[k]]); 판 = [("truth", np.asarray(v), np.asarray(f), "#9bd3a8")]
옛 = "C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/1b9641c4-09e3-416a-8c59-c894cf94f212/scratchpad/e78/판0맞춤옛_82.npz"   # 고치기 전 장메시(실루엣 테 섞임)
for 종류, 경, 색 in [("cell", D + "판0칸_%d.npz" % k, "#e8c06a"), ("fit", D + "판0맞춤_%d.npz" % k, "#e8c06a"), ("fitold", 옛, "#e8c06a")]:
    z = np.load(경); 판.append((종류, z["v"], z["f"], 색))
lo = np.min([p[1].min(0) for p in 판], 0); hi = np.max([p[1].max(0) for p in 판], 0); c = (lo + hi) / 2; r = (hi - lo).max() * .6; 파 = []
for 종류, vs, fs, 색 in 판:
    os.makedirs(R + "soap_" + 종류, exist_ok=True)
    for t in range(장):
        g = plt.figure(figsize=(4.8, 4.8)); a = g.add_subplot(projection="3d"); a.set_axis_off(); a.set_box_aspect((1, 1, 1))
        a.set_xlim(c[0] - r, c[0] + r); a.set_ylim(c[1] - r, c[1] + r); a.set_zlim(c[2] - r, c[2] + r); a.view_init(28, -50 + 360 * t / 장)
        a.add_collection3d(Poly3DCollection(vs[fs], facecolors=색, edgecolors=색, linewidths=0, shade=True, lightsource=빛))
        p = R + "soap_%s/%02d.png" % (종류, t); g.subplots_adjust(0, 0, 1, 1); g.savefig(p, dpi=100, transparent=True); plt.close(g); 파.append(p)
bs = [b for b in (Image.open(p).split()[3].point(lambda q: 255 if q > 8 else 0).getbbox() for p in 파) if b]
b = (min(x[0] for x in bs), min(x[1] for x in bs), max(x[2] for x in bs), max(x[3] for x in bs)); w, h = b[2] - b[0], b[3] - b[1]; s = int(max(w, h) * 1.06)
for p in 파:
    im = Image.open(p).convert("RGBA"); cc = Image.new("RGBA", (s, s), (0, 0, 0, 0)); cc.paste(im.crop(b), ((s - w) // 2, (s - h) // 2)); cc.resize((480, 480), Image.LANCZOS).save(p)
print("soap", k)
