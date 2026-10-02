# -*- coding: utf-8 -*-
"""6-6 겹쳐 앉은 동물 셋 + 통나무: 영역 · 앞뒤 순서 · 경계 · 물체마다 보이는 곳 + 가려진 몸까지 파란 윤곽 (Zhu 외 2017 Fig.1 의 생각)
python 6-6.py → ../6-6.png"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _bl as B
D = B.passdir("6-6")

def animal(name, x, y, s, color):
    """앉은 네발 동물(몸통 · 머리 · 귀 · 주둥이 · 앞다리)."""
    import math
    z = 0
    P = [B.ell(name + "몸", (x, y + 0.2 * s, z + 0.75 * s), (0.62 * s, 0.75 * s, 0.8 * s), color),
         B.ell(name + "머리", (x, y - 0.25 * s, z + 1.75 * s), (0.5 * s, 0.45 * s, 0.45 * s), color),
         B.ell(name + "주둥이", (x, y - 0.68 * s, z + 1.62 * s), (0.2 * s, 0.25 * s, 0.16 * s), color),
         B.cone(name + "귀", (x - 0.28 * s, y - 0.2 * s, z + 2.25 * s), 0.18 * s, 0.0, 0.45 * s, color, rot=(0, -0.35, 0)),
         B.cone(name + "귀", (x + 0.28 * s, y - 0.2 * s, z + 2.25 * s), 0.18 * s, 0.0, 0.45 * s, color, rot=(0, 0.35, 0))]
    for dx in (-0.25, 0.25):
        P.append(B.cyl(name + "다리", (x + dx * s, y - 0.4 * s, z + 0.4 * s), 0.12 * s, 0.8 * s, color, verts=24))
    return P

if B.bpy:
    import math
    B.scene((960, 640))
    a1 = animal("가", -0.95, -1.0, 1.0, (0.92, 0.72, 0.45))
    a2 = animal("나", -0.05, 0.0, 1.1, (0.86, 0.66, 0.40))
    a3 = animal("다", 0.95, 1.0, 1.15, (0.80, 0.62, 0.38))
    log = [B.cyl("통나무", (0.2, 2.6, 1.1), 0.75, 7.5, (0.45, 0.32, 0.22), rot=(0, math.pi / 2, 0.12))]
    B.camera((0.3, -11, 3.0), (0.1, 0.5, 1.3), lens=58)
    B.passes(D, [a1, a2, a3, log])
else:
    B.run(os.path.abspath(__file__))
    import numpy as np
    from PIL import Image, ImageDraw
    rgb = B.on_white(B.load(D, "beauty.png")); ids = B.ids(D); n = 4
    names = ["동물, 앞뒤 1", "동물, 앞뒤 2", "동물, 앞뒤 3", "통나무, 앞뒤 4"]
    pal = np.array([(1, 1, 1), (0.98, 0.85, 0.2), (0.9, 0.3, 0.6), (0.55, 0.8, 0.45), (0.5, 0.6, 0.75)], np.float32)
    seg = B.tint(rgb, ids > 0, (1, 1, 1), 0.0)
    for i in range(1, n + 1): seg = B.tint(seg, ids == i, pal[i], 0.6)
    order = np.ones_like(rgb)
    for i in range(1, n + 1): order[ids == i] = 0.25 + 0.15 * i   # 앞일수록 어둡게
    bnd = np.ones_like(rgb); edge = np.zeros(ids.shape, bool)
    edge[:-1] |= ids[:-1] != ids[1:]; edge[:, :-1] |= ids[:, :-1] != ids[:, 1:]
    bnd[B.outline(edge, 3) | edge] = 0.1
    cv = B.canvas(); W, H = 390, 260; X0 = (1920 - 4 * W - 3 * 40) // 2
    for k, (im, t) in enumerate(((rgb, "장면"), (seg, "영역"), (order, "앞뒤 순서"), (bnd, "경계"))):
        x = X0 + k * (W + 40); y = 150
        cv.paste(B.to_img(im).resize((W, H)), (x, y)); ImageDraw.Draw(cv).rectangle([x, y, x + W, y + H], outline=(190, 190, 190), width=2)
        B.label(cv, (x + W // 2, y + H + 34), t, 30)
    # 아래 줄: 물체마다 보이는 픽셀 + 가려진 몸까지 파란 윤곽
    for i in range(1, n + 1):
        am = B.amodal(D, i); vis = ids == i
        im = np.ones_like(rgb); im[vis] = rgb[vis]
        line = B.outline(am, 5); im[line] = (0.1, 0.2, 0.95)
        crop = B.to_img(B.crop_to(im, am, 14)); crop = B.fit(crop, (W, 330))
        x = X0 + (i - 1) * (W + 40) + (W - crop.size[0]) // 2; y = 520 + (330 - crop.size[1])
        cv.paste(crop, (x, y)); B.label(cv, (X0 + (i - 1) * (W + 40) + W // 2, 900), names[i - 1], 30)
    cv.save(os.path.join(B.OUT, "6-6.png"))
