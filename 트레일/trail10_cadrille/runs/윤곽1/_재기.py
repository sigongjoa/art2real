# 실물 단면 격자: python _재기.py idx [축 위치들...]  → _단면NN.png (축 x,y,z 각 5 장, 0~100 좌표)
import sys, json, os, numpy as np, trimesh, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
R = "G:/art2real/트레일/trail10_cadrille/runs/"
P = [r["부품"] for k in range(3) for r in json.load(open(R + "사전0/결과%d.json" % k, encoding="utf-8"))]
i = int(sys.argv[1]); fr = [float(a) for a in sys.argv[2:]] or [15, 30, 50, 70, 85]
m = trimesh.load("G:/art2real/원화3d/out/레퍼런스/사람분할/" + P[i], force="mesh")
lo, hi = m.bounds; m.apply_translation(-(lo + hi) / 2); m.apply_scale(100 / (hi - lo).max()); m.apply_translation([50] * 3)
print("bounds", m.bounds.round(1).tolist(), "watertight", m.is_watertight, "faces", len(m.faces))
fig, ax = plt.subplots(3, len(fr), figsize=(3.2 * len(fr), 9.6))
for a in range(3):
    for j, f in enumerate(fr):
        n = np.zeros(3); n[a] = 1; o = np.full(3, 50.); o[a] = f
        s = m.section(plane_origin=o, plane_normal=n); A = ax[a, j]
        uv = [k for k in range(3) if k != a]
        if s is not None:
            for e in s.discrete: A.plot(e[:, uv[0]], e[:, uv[1]], "k-", lw=.8)
        A.set_xlim(0, 100); A.set_ylim(0, 100); A.set_aspect("equal"); A.grid(alpha=.4); A.set_xticks(range(0, 101, 20)); A.set_yticks(range(0, 101, 20))
        A.set_title("%s=%g (%s,%s)" % ("xyz"[a], f, "xyz"[uv[0]], "xyz"[uv[1]]), fontsize=9)
plt.tight_layout(); plt.savefig(R + "윤곽1/_단면%02d.png" % i, dpi=60)
