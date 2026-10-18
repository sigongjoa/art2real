# 76 편 재료 — 실제76(정답 없는 GPT · Gemini 3면도) 결과 턴테이블 48 장(부품마다 같은 상자로 자름) + 입력 그림 · 10-18
# 사용(venv): 재료76.py → Remotion public/ep76/<부품>_<종류>/NN.png · public/ep76/<부품>_그림.png
import os, shutil, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection; from skimage.measure import marching_cubes
from PIL import Image
R = "C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/1b9641c4-09e3-416a-8c59-c894cf94f212/scratchpad/motion/work/remotion/public/ep76/"; D = "G:/art2real/out/설명/캐드부품/실제입력/"; 장 = 48
빛 = matplotlib.colors.LightSource(315, 40)
for 이름, 원 in [("helmet", "피규어_gpt_투구"), ("shoulder", "피규어_gemini_어깨"), ("bracket", "gpt_L브래킷")]:
    os.makedirs(R, exist_ok=True); shutil.copy(D + 원 + ".png", R + "%s_그림.png" % 이름); 파 = []
    for 종류, 파일, 색 in [("frame", "틀", "#cfcfcf"), ("ai", "칸", "#e8c06a")]:
        v = np.load(D + 원 + "/%s.npy" % 파일); vs, fs, _, _ = marching_cubes(np.pad(v, 1).astype(np.float32), .5); vs = (vs - .5) / 48 * 1.1 - .55
        os.makedirs(R + "%s_%s" % (이름, 종류), exist_ok=True)
        for t in range(장):
            f = plt.figure(figsize=(4.8, 4.8)); a = f.add_subplot(projection="3d"); a.set_axis_off(); a.set_box_aspect((1, 1, 1))
            a.set_xlim(-.5, .5); a.set_ylim(-.5, .5); a.set_zlim(-.5, .5); a.view_init(24, -55 + 360 * t / 장)
            a.add_collection3d(Poly3DCollection(vs[fs], facecolors=색, edgecolors=색, linewidths=0, shade=True, lightsource=빛))
            p = R + "%s_%s/%02d.png" % (이름, 종류, t); f.subplots_adjust(0, 0, 1, 1); f.savefig(p, dpi=100, transparent=True); plt.close(f); 파.append(p)
    bs = [b for b in (Image.open(p).split()[3].point(lambda q: 255 if q > 8 else 0).getbbox() for p in 파) if b]
    b = (min(x[0] for x in bs), min(x[1] for x in bs), max(x[2] for x in bs), max(x[3] for x in bs)); w, h = b[2] - b[0], b[3] - b[1]; s = int(max(w, h) * 1.06)
    for p in 파:
        im = Image.open(p).convert("RGBA"); cc = Image.new("RGBA", (s, s), (0, 0, 0, 0)); cc.paste(im.crop(b), ((s - w) // 2, (s - h) // 2)); cc.resize((480, 480), Image.LANCZOS).save(p)
    print(이름, flush=True)
shutil.copy(D + "예시_40.png", R + "learned_그림.png")
