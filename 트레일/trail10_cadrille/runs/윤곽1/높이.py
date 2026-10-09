# 높이 지도: python 높이.py <idx> <축 0/1/2> <쪽 -1(낮은 쪽에서)/+1> [간격]  — 그 축 방향으로 쏜 광선의 첫 닿음 좌표(정수), 빈 곳 '.'
import sys, json, numpy as np, trimesh
R = "G:/art2real/트레일/trail10_cadrille/runs/"
P = [r["부품"] for k in range(3) for r in json.load(open(R + "사전0/결과%d.json" % k, encoding="utf-8"))]
i, ax, sd = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]); st = float(sys.argv[4]) if len(sys.argv) > 4 else 4
m = trimesh.load("G:/art2real/원화3d/out/레퍼런스/사람분할/" + P[i], force="mesh")
lo, hi = m.bounds; m.apply_translation(-(lo + hi) / 2); m.apply_scale(100 / (hi - lo).max()); m.apply_translation([50] * 3)
uv = [k for k in range(3) if k != ax]; g = np.arange(st / 2, 100, st)
U, V = np.meshgrid(g, g); n = U.size
o = np.zeros((n, 3)); o[:, uv[0]] = U.ravel(); o[:, uv[1]] = V.ravel(); o[:, ax] = -10 if sd < 0 else 110
d = np.zeros((n, 3)); d[:, ax] = 1 if sd < 0 else -1
loc, ri, _ = m.ray.intersects_location(o, d, multiple_hits=True)
h = np.full(n, np.nan)
for p, k in zip(loc[:, ax], ri):
    if np.isnan(h[k]) or (p < h[k] if sd < 0 else p > h[k]): h[k] = p
h = h.reshape(U.shape)
print("행 = %s (위가 큼), 열 = %s:" % ("xyz"[uv[1]], "xyz"[uv[0]]), " ".join("%3d" % x for x in g))
for r_ in range(len(g) - 1, -1, -1):
    print("%5.0f  " % g[r_] + " ".join("  ." if np.isnan(x) else "%3d" % round(x) for x in h[r_]))
