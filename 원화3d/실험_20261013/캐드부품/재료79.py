# 79 편 재료 — 판정기준83 어려운 묶음 · 딱정벌레(252) · 기운 고리(104) 정답 · 정답 깊이 곡면 깎기(단32맞춤) · 모델 곡면 깎기(판0맞춤) 턴테이블 48 장 + 쉬운 20 · 어려운 20 썸네일 판 · 10-18
# 사용(venv): 재료79.py → Remotion public/ep79/
import os, json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection; from PIL import Image
import 짓기 as J
R = "C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/1b9641c4-09e3-416a-8c59-c894cf94f212/scratchpad/motion/work/remotion/public/ep79/"; O = "G:/art2real/out/설명/캐드부품/"; D = O + "곡면79_어려움/"; 장 = 48
시 = np.load(O + "데이터.npz")["시험"]; te = np.nonzero(시)[0]; 예부 = te[json.load(open(O + "범위46.json"))]; L = json.load(open(O + "목록.json", encoding="utf-8")); 빛 = matplotlib.colors.LightSource(315, 40)
def 정답(k): v, f, _ = J.정규메시(L[예부[k]]); return np.asarray(v), np.asarray(f)
for 이름, k in (("bug", 252), ("ring", 104)):
    판 = [("truth", *정답(k), "#9bd3a8")] + [(종, *(lambda z: (z["v"], z["f"]))(np.load(D + "%s_%d.npz" % (팔, k))), 색) for 종, 팔, 색 in (("ceil", "단32맞춤", "#5a8fd0"), ("model", "판0맞춤", "#e8c06a"))]
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
for 이름, ks in (("easy", json.load(open(O + "곡면79/결과.json", encoding="utf-8"))["요약"]["부품"][:8]), ("hard", json.load(open(O + "복잡83.json", encoding="utf-8"))["부품"][:8])):   # 썸네일 판 4 × 2(투명)
    g = plt.figure(figsize=(9.6, 4.8))
    for n, k in enumerate(ks):
        v, f = 정답(k); a = g.add_subplot(2, 4, n + 1, projection="3d"); a.set_axis_off(); a.set_box_aspect((1, 1, 1)); a.set_xlim(-.5, .5); a.set_ylim(-.5, .5); a.set_zlim(-.5, .5); a.view_init(28, -50)
        a.add_collection3d(Poly3DCollection(v[f], facecolors="#9bd3a8", edgecolors="#9bd3a8", linewidths=0, shade=True, lightsource=빛))
    g.subplots_adjust(0, 0, 1, 1, 0, 0); g.savefig(R + "%s.png" % 이름, dpi=100, transparent=True); plt.close(g); print(이름, ks, flush=True)
