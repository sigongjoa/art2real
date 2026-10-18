# 80 편 재료 — 판정기준84 · 85 · 톱니 축(635) · 돌기 원판(206) 정답 · 모델(판0맞춤) · 도면만 회전(회전만 · 85 고친 판) 턴테이블 48 장 + CAD 강좌 스토리보드 한 칸 · 10-18
# 사용(venv): 재료80.py → Remotion public/ep80/
import os, json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection; from PIL import Image
import 짓기 as J
R = "C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/1b9641c4-09e3-416a-8c59-c894cf94f212/scratchpad/motion/work/remotion/public/ep80/"; O = "G:/art2real/out/설명/캐드부품/"; D = O + "회전85/"; 장 = 48
시 = np.load(O + "데이터.npz")["시험"]; te = np.nonzero(시)[0]; 예부 = te[json.load(open(O + "범위46.json"))]; L = json.load(open(O + "목록.json", encoding="utf-8")); 빛 = matplotlib.colors.LightSource(315, 40)
for 이름, k in (("gear", 635), ("boss", 206)):
    v, f, _ = J.정규메시(L[예부[k]]); 판 = [("truth", np.asarray(v), np.asarray(f), "#9bd3a8")] + [(종, *(lambda z: (z["v"], z["f"]))(np.load(D + "%s_%d.npz" % (팔, k))), 색) for 종, 팔, 색 in (("model", "판0맞춤", "#e8c06a"), ("rev", "회전만", "#b07ad0"))]
    lo = np.min([p[1].min(0) for p in 판], 0); hi = np.max([p[1].max(0) for p in 판], 0); c = (lo + hi) / 2; r = (hi - lo).max() * .6; 파 = []
    for 종류, vs, fs, 색 in 판:
        os.makedirs(R + "%s_%s" % (이름, 종류), exist_ok=True)
        for t in range(장):
            g = plt.figure(figsize=(4.8, 4.8)); a = g.add_subplot(projection="3d"); a.set_axis_off(); a.set_box_aspect((1, 1, 1))
            a.set_xlim(c[0] - r, c[0] + r); a.set_ylim(c[1] - r, c[1] + r); a.set_zlim(c[2] - r, c[2] + r); a.view_init(28, -50 + 360 * t / 장)
            a.add_collection3d(Poly3DCollection(vs[fs], facecolors=색, edgecolors=색, linewidths=0, shade=True, lightsource=빛))
            p = R + "%s_%s/%02d.png" % (이름, 종류, t); g.subplots_adjust(0, 0, 1, 1); g.savefig(p, dpi=100, transparent=True); plt.close(g); 파.append(p)
    bs = [b for b in (Image.open(p).split()[3].point(lambda q: 255 if q > 8 else 0).getbbox() for p in 파) if b]
    b = (min(x[0] for x in bs), min(x[1] for x in bs), max(x[2] for x in bs), max(x[3] for x in bs)); w, h = b[2] - b[0], b[3] - b[1]; s = int(max(w, h) * 1.06)
    for p in 파:
        im = Image.open(p).convert("RGBA"); cc = Image.new("RGBA", (s, s), (0, 0, 0, 0)); cc.paste(im.crop(b), ((s - w) // 2, (s - h) // 2)); cc.resize((480, 480), Image.LANCZOS).save(p)
    print(이름, k, flush=True)
sb = Image.open("G:/art2real/claudedocs/CAD제작과정/A_나사톱니/B8A_11o7QZ0/sb_06.jpg"); w, h = sb.size; sb.crop((0, 0, w // 3, h // 3)).resize((960, 540), Image.LANCZOS).save(R + "tutorial.png"); print("tutorial", sb.size)
