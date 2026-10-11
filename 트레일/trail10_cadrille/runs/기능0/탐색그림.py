# 자동 찾기 결과 눈 검사 — 사람 / 손 / 자동(복셀 그대로) · 10-11
import os, sys, json, numpy as np, trimesh
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R); sys.path[:0] = [os.path.join(T0, "s0")]
import 탐색 as T
from render import render
from PIL import Image, ImageDraw, ImageFont
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); C = 220
부 = np.load(os.path.join(R, "깊이학습", "시험.npz"))["부품"]; X = T.X_("시험"); ids = [int(a) for a in sys.argv[1:]]
def 정(m):
    m = m.copy(); m.apply_translation(-m.bounds.mean(0)); m.apply_scale(0.9 / max(m.extents)); m.apply_translation([.5] * 3); return m
def 그(m, v, 색): return Image.fromarray(np.asarray(render(np.asarray(m.vertices), np.asarray(m.faces), v, img_size=C, cols=None if 색 is None else np.tile(색, (len(m.faces), 1)))))
def 자동V(i):
    x = X[i].astype(np.float32); S = x[0] > .5; 후 = T.후보들(S, x[3], x[2]); r = T.찾기(x); V = T.교차(S)
    # 같은 순서 다시 적용(찾기와 같은 결정)
    import itertools
    고른 = [s for s in r["순서"]]; 남 = list(후)
    for s in 고른:
        j = next(j for j, (nm, p, w) in enumerate(남) if nm == s["기능"] and all(p.get(k) == s.get(k) for k in p))
        V &= ~남[j][2]
    return V, r
V_ = ([1, .6, .8], [-1, -.6, -.8]); w = 2 * C + 20
im = Image.new("RGB", (100 + 3 * w, 100 + len(ids) * (C + 40)), "white"); d = ImageDraw.Draw(im)
d.text((20, 15), "자동 찾기 눈 검사: 사람 / 손 / 자동(복셀)", font=F(28), fill="black")
for j, t in enumerate(("사람 부품", "손 기능", "자동 찾기(복셀 그대로)")): d.text((100 + j * w + C, 75), t, font=F(22), fill=(31, 95, 173), anchor="mm")
for r_, i in enumerate(ids):
    y = 95 + r_ * (C + 40); d.text((10, y + C // 2), "#%d" % i, font=F(28), fill="black")
    V, r = 자동V(i); mv = trimesh.voxel.VoxelGrid(np.pad(V, 1)).marching_cubes
    ms = [trimesh.load("G:/art2real/원화3d/out/레퍼런스/사람분할/" + str(부[i]), force="mesh"), trimesh.load(os.path.join(H, "결과", "%02d.stl" % i)), mv]
    for j, m in enumerate(ms):
        for q, v in enumerate(V_): im.paste(그(정(m), v, (None, (0.98, 0.62, 0.35), (0.6, 0.6, 0.9))[j]), (100 + j * w + q * C, y))
    d.text((100 + 2 * w + C, y + C + 14), "기능 %d 개 · IoU %.2f → %.2f" % (len(r["순서"]), r["교차 IoU"], r["끝 IoU"]), font=F(19), fill="black", anchor="mm")
im.save(os.path.join(H, "탐색그림.png")); print("ok")
