# -*- coding: utf-8 -*-
"""6-10 일부만 보이는 물체를 온전히 그리고 → 분할 → 새 시점 → 3D (Ozguroglu 외 2024 pix2gestalt Fig.1 의 생각)
줄 1 기둥 뒤의 네발 동물 · 줄 2 울타리 뒤의 의자. python 6-10.py → ../6-10.png"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _bl as B
D = B.passdir("6-10")

if B.bpy:
    import bpy, math
    def ground():
        B.box("땅", (0, 2, -0.05), (16, 12, 0.1), (0.62, 0.7, 0.5))
    def extra(tag, target, cam_loc, look, new_loc, gray_loc):
        """물체만 남기고 새 시점(색) · 3D(회색) 렌더."""
        for o in bpy.context.scene.objects:
            if o.type == "MESH": o.hide_render = o not in target
        B.camera(new_loc, look, lens=45); B.shot(os.path.join(D, f"new{tag}.png"))
        for o in target: o.color = (0.6, 0.6, 0.62, 1)
        B.camera(gray_loc, look, lens=45); B.shot(os.path.join(D, f"gray{tag}.png"))
    # 줄 1: 기둥 뒤의 동물
    B.scene((640, 640)); ground()
    c = (0.55, 0.35, 0.2)
    animal = [B.ell("몸", (0.4, 0, 1.35), (1.25, 0.5, 0.5), c),
              B.ell("목", (-0.85, 0, 1.75), (0.45, 0.25, 0.25), c, rot=(0, 0.7, 0)),
              B.ell("머리", (-1.25, 0, 2.05), (0.4, 0.2, 0.22), c, rot=(0, 0.3, 0)),
              B.cyl("꼬리", (1.7, 0, 1.2), 0.06, 0.8, c, rot=(0, 0.5, 0))]
    for x in (-0.4, 1.2):
        for y in (-0.25, 0.25):
            animal.append(B.cyl("다리", (x, y, 0.5), 0.12, 1.1, c, verts=24))
    B.box("기둥", (0.2, -1.6, 1.7), (1.3, 0.8, 3.4), (0.7, 0.7, 0.68))
    look = (0.2, 0, 1.2)
    B.camera((0.6, -8, 2.2), look, lens=62)
    B.passes(D, [animal], tag="a")
    extra("a", animal, None, look, (-5, -6, 3), (6, -5, 3.5))
    # 줄 2: 울타리 뒤의 의자
    B.scene((640, 640)); ground()
    w = (0.6, 0.3, 0.18)
    chair = [B.box("앉음판", (0, 0, 0.9), (1.1, 1.0, 0.1), w),
             B.box("등판", (0, 0.45, 1.7), (1.1, 0.08, 0.5), w),
             B.box("등살", (-0.25, 0.45, 1.2), (0.08, 0.08, 0.6), w),
             B.box("등살", (0.25, 0.45, 1.2), (0.08, 0.08, 0.6), w)]
    for x in (-0.48, 0.48):
        chair.append(B.box("뒷다리", (x, 0.45, 0.95), (0.1, 0.1, 1.9), w))
        chair.append(B.box("앞다리", (x, -0.42, 0.45), (0.1, 0.1, 0.9), w))
    for i in range(6):
        B.box("울타리", (-1.25 + i * 0.5, -1.2, 0.9), (0.28, 0.08, 1.8), (0.92, 0.92, 0.9))
    B.box("울타리가로", (0, -1.28, 1.2), (3.2, 0.06, 0.15), (0.92, 0.92, 0.9))
    look = (0, 0, 0.9)
    B.camera((0.8, -6, 1.6), look, lens=62)
    B.passes(D, [chair], tag="b")
    extra("b", chair, None, look, (-4.5, -3.5, 2.8), (4, -4, 3.2))
else:
    B.run(os.path.abspath(__file__))
    import numpy as np
    from PIL import ImageDraw
    cv = B.canvas(); S = 260; gap = 30; X0 = (1920 - 5 * S - 4 * gap - 50) // 2; Y0 = 240
    heads = ["입력", "완성", "분할", "새 시점", "3D"]
    for r, tag in enumerate("ab"):
        y = Y0 + r * (S + 70)
        full = B.on_white(B.load(D, f"beauty{tag}.png")); fade = full * 0.35 + 0.65
        al = B.load(D, f"alone{tag}_1.png"); m = al[..., 3] > 0.5
        comp = fade.copy(); comp = al[..., :3] * al[..., 3:4] + comp * (1 - al[..., 3:4])
        seg = B.tint(fade, m, (0.85, 0.3, 0.75), 0.55); seg[B.outline(m, 5)] = (0.75, 0.2, 0.65)
        new = B.on_white(B.load(D, f"new{tag}.png")); gray = B.on_white(B.load(D, f"gray{tag}.png"))
        ims = [full, comp, seg, new, gray]
        for k, im in enumerate(ims):
            x = X0 + k * (S + gap) + (50 if k >= 1 else 0)
            pil = B.to_img(im)
            if k >= 3:
                a = B.load(D, f"{'new' if k == 3 else 'gray'}{tag}.png")[..., 3] > 0.05
                ys, xs = np.nonzero(a); pil = pil.crop((xs.min() - 20, ys.min() - 20, xs.max() + 20, ys.max() + 20))
                pil = B.fit(pil, (S, S)); cv.paste(pil, (x + (S - pil.size[0]) // 2, y + (S - pil.size[1]) // 2))
            else:
                cv.paste(pil.resize((S, S)), (x, y))
            if r == 0: B.label(cv, (x + S // 2, Y0 - 40), heads[k], 30)
        B.arrow(cv, (X0 + S + 12, y + S // 2), (X0 + S + gap + 38, y + S // 2), w=5)
    cv.save(os.path.join(B.OUT, "6-10.png"))
