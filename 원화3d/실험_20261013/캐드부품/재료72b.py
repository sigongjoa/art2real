# 72 편 2 판 재료 — 부품 셋(모터판 · 톱니링 · 관)의 정답 · 모델을 한 바퀴 돌리는 턴테이블(48 장 · 투명 PNG) · 10-17 사용자 「이미지를 보여줄 거면 회전 넣어서」
# 사용(venv): 재료72b.py → Remotion public/ep72/<부품>_<종류>/<번호>.png
import os, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 그림63 as G
R = "C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/1b9641c4-09e3-416a-8c59-c894cf94f212/scratchpad/motion/work/remotion/public/ep72/"; 장 = 48
쓸 = {"plate": G.고른[1][1], "gear": G.고른[3][1], "tube": G.고른[8][1]}
for 이름, k in 쓸.items():
    i = G.예부[k]; v, fc, _ = G.J.정규메시(G.L[i]); m = G.trimesh.Trimesh(v, fc, process=False)
    if len(m.faces) > 30000: m = m.simplify_quadric_decimation(face_count=30000)
    lo, hi = np.asarray(m.vertices).min(0), np.asarray(m.vertices).max(0); c = (lo + hi) / 2; r = (hi - lo).max() * .62   # 같은 부품의 정답 · 모델은 같은 상자
    for 종류, 그 in [("truth", lambda a: G.면(a, np.asarray(m.vertices), np.asarray(m.faces), "#9bd3a8")), ("model", lambda a: G.칸면(a, G.풀(G.P[k]), "#e8c06a"))]:
        os.makedirs(R + "%s_%s" % (이름, 종류), exist_ok=True)
        for t in range(장):
            f = plt.figure(figsize=(4.8, 4.8)); a = f.add_subplot(projection="3d"); a.set_axis_off(); a.set_box_aspect((1, 1, 1))
            a.set_xlim(c[0] - r, c[0] + r); a.set_ylim(c[1] - r, c[1] + r); a.set_zlim(c[2] - r, c[2] + r); a.view_init(28, -50 + 360 * t / 장); 그(a)
            f.subplots_adjust(0, 0, 1, 1); f.savefig(R + "%s_%s/%02d.png" % (이름, 종류, t), dpi=100, transparent=True); plt.close(f)
        print(이름, 종류, flush=True)
