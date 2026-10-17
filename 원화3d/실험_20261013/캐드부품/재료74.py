# 74 편 재료 — 판정기준65 · 66(면 맞춤) · 기운 판 정답 · 66 결과 · ㄱ자 막대 65 · 66 결과 턴테이블 48 장 + 모터 판 위 그림 영역 색칠 · 10-17
# 사용(venv): 재료73.py → Remotion public/ep74/<부품>_<종류>/NN.png · 영역/선.png · 영역/색.png
import os, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from PIL import Image; from scipy.ndimage import label
import 그림63 as G
R = "C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/1b9641c4-09e3-416a-8c59-c894cf94f212/scratchpad/motion/work/remotion/public/ep74/"; 장 = 48; D = G.O + "영역64/"
C5 = np.load(G.O + "면65/칸.npy"); C6 = np.load(G.O + "면66/칸.npy")
for 이름, k, 판들 in [("slant", 422, [("truth", None, "#9bd3a8"), ("f66", C6, "#7fb3e8")]), ("bar", 580, [("truth", None, "#9bd3a8"), ("f65", C5, "#c48be0"), ("f66", C6, "#7fb3e8")])]:
    i = G.예부[k]; v, fc, _ = G.J.정규메시(G.L[i]); m = G.trimesh.Trimesh(v, fc, process=False)
    if len(m.faces) > 30000: m = m.simplify_quadric_decimation(face_count=30000)
    lo, hi = np.asarray(m.vertices).min(0), np.asarray(m.vertices).max(0); c = (lo + hi) / 2; r = (hi - lo).max() * .62
    for 종류, 칸, 색 in 판들:
        그 = (lambda a, 색=색: G.면(a, np.asarray(m.vertices), np.asarray(m.faces), 색)) if 칸 is None else (lambda a, 칸=칸, 색=색: G.칸면(a, G.풀(칸[k]), 색))
        os.makedirs(R + "%s_%s" % (이름, 종류), exist_ok=True)
        for t in range(장):
            f = plt.figure(figsize=(4.8, 4.8)); a = f.add_subplot(projection="3d"); a.set_axis_off(); a.set_box_aspect((1, 1, 1))
            a.set_xlim(c[0] - r, c[0] + r); a.set_ylim(c[1] - r, c[1] + r); a.set_zlim(c[2] - r, c[2] + r); a.view_init(28, -50 + 360 * t / 장); 그(a)
            for x in a.texts: x.set_visible(False)   # 「비어 있음」 글자는 카드에서 따로
            f.subplots_adjust(0, 0, 1, 1); f.savefig(R + "%s_%s/%02d.png" % (이름, 종류, t), dpi=100, transparent=True); plt.close(f)
    print(이름, k, flush=True)
