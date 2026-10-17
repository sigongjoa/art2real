# 73 편 재료 — 판정기준64(영역마다 높이 하나) · 관(오름 1 위) · 기운 판(떨어짐 2 위)의 정답 · 묶기 전 · 묶기 후 턴테이블 48 장 + 모터 판 위 그림 영역 색칠 · 10-17
# 사용(venv): 재료73.py → Remotion public/ep73/<부품>_<종류>/NN.png · 영역/선.png · 영역/색.png
import os, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from PIL import Image; from scipy.ndimage import label
import 그림63 as G
R = "C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/1b9641c4-09e3-416a-8c59-c894cf94f212/scratchpad/motion/work/remotion/public/ep73/"; 장 = 48; D = G.O + "영역64/"
V = np.load(D + "값.npy"); A = np.load(D + "칸_대조.npy"); B = np.load(D + "칸_묶기.npy"); d = V[:, 1] - V[:, 0]
관 = int(np.argsort(-d)[0]); 기운 = [int(k) for k in np.argsort(d) if V[k, 0] > .6][1]
for 이름, k in {"tube": 관, "slant": 기운}.items():
    i = G.예부[k]; v, fc, _ = G.J.정규메시(G.L[i]); m = G.trimesh.Trimesh(v, fc, process=False)
    if len(m.faces) > 30000: m = m.simplify_quadric_decimation(face_count=30000)
    lo, hi = np.asarray(m.vertices).min(0), np.asarray(m.vertices).max(0); c = (lo + hi) / 2; r = (hi - lo).max() * .62
    for 종류, 그 in [("truth", lambda a: G.면(a, np.asarray(m.vertices), np.asarray(m.faces), "#9bd3a8")), ("before", lambda a: G.칸면(a, G.풀(A[k]), "#e8c06a")), ("after", lambda a: G.칸면(a, G.풀(B[k]), "#7fb3e8"))]:
        os.makedirs(R + "%s_%s" % (이름, 종류), exist_ok=True)
        for t in range(장):
            f = plt.figure(figsize=(4.8, 4.8)); a = f.add_subplot(projection="3d"); a.set_axis_off(); a.set_box_aspect((1, 1, 1))
            a.set_xlim(c[0] - r, c[0] + r); a.set_ylim(c[1] - r, c[1] + r); a.set_zlim(c[2] - r, c[2] + r); a.view_init(28, -50 + 360 * t / 장); 그(a)
            for x in a.texts: x.set_visible(False)   # 「비어 있음」 글자는 카드에서 따로
            f.subplots_adjust(0, 0, 1, 1); f.savefig(R + "%s_%s/%02d.png" % (이름, 종류, t), dpi=100, transparent=True); plt.close(f)
    print(이름, k, V[k].round(3), flush=True)
# 모터 판 위 그림: 선 · 영역마다 다른 색
i = G.예부[G.고른[1][1]]; 선 = G.X[i] > 0; L, n = label(~선); 바깥 = L[0, 0]
os.makedirs(R + "영역", exist_ok=True); 색표 = plt.get_cmap("tab20")
s = np.full(선.shape + (4,), 255, np.uint8); s[선] = (40, 40, 50, 255); Image.fromarray(s).resize((512, 512), Image.NEAREST).save(R + "영역/선.png")
c = s.copy()
for q in range(1, n + 1):
    if q != 바깥: c[L == q] = (np.array(색표((q * 3) % 20)[:3]) * 255).astype(np.uint8).tolist() + [255]
Image.fromarray(c).resize((512, 512), Image.NEAREST).save(R + "영역/색.png"); print("영역", n - 1)
