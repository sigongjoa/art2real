# 75 편 재료 — 판정기준69(깊이 32 단계) · 관 · 모터 판의 정답 · 판0(16 단계) · 32 단계 턴테이블 48 장(부품마다 같은 상자로 자름) · 10-18
# 사용(venv): 재료75.py → Remotion public/ep75/<부품>_<종류>/NN.png
import os, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from PIL import Image
import 그림63 as G
R = "C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/1b9641c4-09e3-416a-8c59-c894cf94f212/scratchpad/motion/work/remotion/public/ep75/"; 장 = 48
A0 = np.load(G.O + "영역64/칸_대조.npy"); A2 = np.load(G.O + "학습69_판0/칸.npy")
for 이름, k in [("tube", 622), ("plate", int(G.고른[1][1]))]:
    i = G.예부[k]; v, fc, _ = G.J.정규메시(G.L[i]); m = G.trimesh.Trimesh(v, fc, process=False)
    if len(m.faces) > 30000: m = m.simplify_quadric_decimation(face_count=30000)
    lo, hi = np.asarray(m.vertices).min(0), np.asarray(m.vertices).max(0); c = (lo + hi) / 2; r = (hi - lo).max() * .62; 파 = []
    for 종류, 칸, 색 in [("truth", None, "#9bd3a8"), ("l16", A0, "#e8c06a"), ("l32", A2, "#7fb3e8")]:
        os.makedirs(R + "%s_%s" % (이름, 종류), exist_ok=True)
        for t in range(장):
            f = plt.figure(figsize=(4.8, 4.8)); a = f.add_subplot(projection="3d"); a.set_axis_off(); a.set_box_aspect((1, 1, 1))
            a.set_xlim(c[0] - r, c[0] + r); a.set_ylim(c[1] - r, c[1] + r); a.set_zlim(c[2] - r, c[2] + r); a.view_init(28, -50 + 360 * t / 장)
            G.면(a, np.asarray(m.vertices), np.asarray(m.faces), 색) if 칸 is None else G.칸면(a, G.풀(칸[k]), 색)
            p = R + "%s_%s/%02d.png" % (이름, 종류, t); f.subplots_adjust(0, 0, 1, 1); f.savefig(p, dpi=100, transparent=True); plt.close(f); 파.append(p)
    bs = [b for b in (Image.open(p).split()[3].point(lambda q: 255 if q > 8 else 0).getbbox() for p in 파) if b]
    b = (min(x[0] for x in bs), min(x[1] for x in bs), max(x[2] for x in bs), max(x[3] for x in bs)); w, h = b[2] - b[0], b[3] - b[1]; s = int(max(w, h) * 1.06)
    for p in 파:
        im = Image.open(p).convert("RGBA"); cc = Image.new("RGBA", (s, s), (0, 0, 0, 0)); cc.paste(im.crop(b), ((s - w) // 2, (s - h) // 2)); cc.resize((480, 480), Image.LANCZOS).save(p)
    print(이름, k, flush=True)
