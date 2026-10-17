# 판정기준69 결과 그림 — 재료67 과 같음 · 정답 · 판0(16 단계) · 32 단계 · 10-18
# 사용(venv): 재료67.py <이름=평면1> → out/설명/판정69_돌림.mp4
import os, sys, subprocess, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 그림63 as G
이름 = sys.argv[1] if len(sys.argv) > 1 else "판0"; D = G.O + "판정69_돌림/"; os.makedirs(D, exist_ok=True); 장 = 36
A0 = np.load(G.O + "영역64/칸_대조.npy"); V0 = np.load(G.O + "영역64/값.npy"); U0 = np.load(G.O + "울퉁67.npy")[:, 2]
A7 = np.load(G.O + "학습69_%s/칸.npy" % 이름); V7 = np.load(G.O + "학습69_%s/값.npy" % 이름)
고 = [("모터 판", int(G.고른[1][1])), ("관", 622), ("기운 판", 422), ("ㄱ자 막대", 580)]
메 = []
for nm, k in 고:
    v, fc, _ = G.J.정규메시(G.L[G.예부[k]]); m = G.trimesh.Trimesh(v, fc, process=False)
    if len(m.faces) > 20000: m = m.simplify_quadric_decimation(face_count=20000)
    lo, hi = np.asarray(m.vertices).min(0), np.asarray(m.vertices).max(0); 메.append((m, (lo + hi) / 2, (hi - lo).max() * .6))
울 = lambda a, k: a[k, 0] / max(a[k, 1], 1)
for t in range(장):
    f = plt.figure(figsize=(12, 3.1 * len(고)))
    for r, ((nm, k), (m, c, rr)) in enumerate(zip(고, 메)):
        for j, (제, 색, 칸, F, U) in enumerate([("정답", "#9bd3a8", None, None, None), ("판0", "#e8c06a", A0[k], V0[k, 0], 울(U0, k)), ("32 단계", "#7fb3e8", A7[k], V7[k, 0], 울(V7[:, 2:], k))]):
            a = f.add_subplot(len(고), 3, r * 3 + j + 1, projection="3d"); a.set_axis_off(); a.set_box_aspect((1, 1, 1))
            a.set_xlim(c[0] - rr, c[0] + rr); a.set_ylim(c[1] - rr, c[1] + rr); a.set_zlim(c[2] - rr, c[2] + rr); a.view_init(28, -50 + 360 * t / 장)
            G.면(a, np.asarray(m.vertices), np.asarray(m.faces), 색) if 칸 is None else G.칸면(a, G.풀(칸), 색)
            a.set_title(("%s\n" % 제 if r == 0 else "") + ("" if F is None else "F %.2f · 울퉁 %.1f %%" % (F, 100 * U)), fontsize=13)
            if j == 0: a.text2D(-.08, .5, nm, transform=a.transAxes, rotation=90, va="center", fontsize=14)
    f.suptitle("판정기준69 — 깊이를 32 단계로 나누면", fontsize=16); plt.tight_layout(rect=(0, 0, 1, .97)); f.savefig(D + "%02d.png" % t, dpi=60); plt.close(f)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i", D + "%02d.png", "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p", "-c:v", "libx264", "-crf", "20", G.O + "../판정69_돌림.mp4"], check=True); print("ok")
