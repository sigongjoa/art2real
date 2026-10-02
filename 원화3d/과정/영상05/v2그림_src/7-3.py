# -*- coding: utf-8 -*-
"""7-3 원기둥이 상자를 꿰뚫었나, 뒤로 지나가나 — 평행하게 정면에서 보면 그림은 똑같다 (Kellman & Shipley 1991 Fig.19 의 생각)
python 7-3.py → ../7-3.png · 두 정면 그림이 같은지 assert."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _bl as B
D = B.passdir("7-3")

if B.bpy:
    for name, cy in (("꿰뚫기", 0.0), ("뒤로", 2.2)):
        sc = B.scene((600, 600)); sc.display.shading.show_cavity = False   # 캐비티는 교선에 어둠을 넣어 두 그림을 갈라 놓는다
        B.box("상자", (0, 0, 0), (2.6, 1.0, 1.0), (0.12, 0.12, 0.13))
        B.cyl("원기둥", (0.2, cy, 0), 0.38, 3.4, (0.55, 0.58, 0.72), verts=64)
        B.camera((0, -20, 0), (0, 0, 0), ortho=4.4); B.shot(os.path.join(D, f"{name}_정면.png"))
        a, p = math.radians(-55), math.radians(18)
        B.camera((20 * math.sin(a) * math.cos(p), -20 * math.cos(a) * math.cos(p), 20 * math.sin(p)), (0, 1.0, 0), ortho=5.6)
        B.shot(os.path.join(D, f"{name}_비스듬.png"))
else:
    B.run(os.path.abspath(__file__))
    import numpy as np
    f1, f2 = (B.on_white(B.load(D, f"{n}_정면.png")) for n in ("꿰뚫기", "뒤로"))
    assert np.abs(f1 - f2).max() < 0.02, "정면 그림이 다르다"
    cv = B.canvas(); P = 360; xs = (520, 1040); ys = (110, 560)
    for c, n in enumerate(("꿰뚫기", "뒤로")):
        for r, v in enumerate(("정면", "비스듬")):
            im = B.to_img(B.on_white(B.load(D, f"{n}_{v}.png"))).resize((P, P)); cv.paste(im, (xs[c], ys[r]))
    B.label(cv, ((xs[0] + P + xs[1]) // 2, ys[0] + P // 2), "=", 80)
    B.label(cv, (xs[0] - 150, ys[0] + P // 2), "정면에서", 32); B.label(cv, (xs[0] - 150, ys[1] + P // 2), "비스듬히", 32)
    B.label(cv, (xs[0] + P // 2, ys[1] + P + 30), "꿰뚫기", 32); B.label(cv, (xs[1] + P // 2, ys[1] + P + 30), "뒤로 지나감", 32)
    cv.save(os.path.join(B.OUT, "7-3.png"))
