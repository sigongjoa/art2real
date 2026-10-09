# 단면 보기: python 단면.py <idx> <축 0/1/2> <위치들 쉼표> <out.png>  — 실물 단면 = 회색 채움, 바탕 단면 = 빨간 선, 격자 10
import sys, json, numpy as np, trimesh
from PIL import Image, ImageDraw
R = "G:/art2real/트레일/trail10_cadrille/runs/"
P = [r["부품"] for k in range(3) for r in json.load(open(R + "사전0/결과%d.json" % k, encoding="utf-8"))]
def norm(m):
    lo, hi = m.bounds; m.apply_translation(-(lo + hi) / 2); m.apply_scale(100 / (hi - lo).max()); m.apply_translation([50] * 3); return m
i, ax, pos, out = int(sys.argv[1]), int(sys.argv[2]), [float(x) for x in sys.argv[3].split(",")], sys.argv[4]
g = norm(trimesh.load("G:/art2real/원화3d/out/레퍼런스/사람분할/" + P[i], force="mesh"))
b = trimesh.load(R + "윤곽0/결과/%02d_교차.stl" % i);
if b.bounds[1].max() < 2: b.apply_translation([1, 1, 1]); b.apply_scale(50)  # 바탕 stl 단위 맞추기
print("gt bounds", g.bounds.round(1).tolist(), "base bounds", b.bounds.round(1).tolist())
uv = [k for k in range(3) if k != ax]; S = 3; C = 100 * S + 20
im = Image.new("RGB", (C * len(pos), C + 20), "white"); d = ImageDraw.Draw(im)
for j, p in enumerate(pos):
    ox = j * C + 10
    for t in range(0, 101, 10):
        d.line([(ox + t * S, 10), (ox + t * S, 10 + 100 * S)], fill=(225, 225, 225)); d.line([(ox, 10 + t * S), (ox + 100 * S, 10 + t * S)], fill=(225, 225, 225))
    n = np.zeros(3); n[ax] = 1; o = np.zeros(3); o[ax] = p
    for mesh, mode in ((g, "fill"), (b, "line")):
        s = mesh.section(plane_origin=o, plane_normal=n)
        if s is None: continue
        for e in s.entities:
            q = s.vertices[e.points][:, uv]; pts = [(ox + x * S, 10 + (100 - y) * S) for x, y in q]
            if mode == "line": d.line(pts, fill=(220, 0, 0), width=1)
            else: d.line(pts, fill=(0, 0, 0), width=2)
    d.text((ox, C), "ax%d=%g  (h:%s v:%s)" % (ax, p, "xyz"[uv[0]], "xyz"[uv[1]]), fill=(0, 0, 0))
im.save(out)
