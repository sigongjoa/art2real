# -*- coding: utf-8 -*-
"""6-8 보이는 마스크 · 안 보이는 마스크 · 아모달 마스크 (Ao 외 2023 Fig.2 의 생각) — 앞 차(초록)가 뒤 차(파랑)를 가린다.
python 6-8.py  → 블렌더 패스 렌더 후 합성 → ../6-8.png"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _bl as B
D = B.passdir("6-8")

def car(name, loc, color, yaw=0):
    import math
    x, y, z = loc; c = math.cos(yaw); s = math.sin(yaw)
    P = lambda dx, dy, dz: (x + dx * c - dy * s, y + dx * s + dy * c, z + dz)
    parts = [B.box(name + "몸", P(0, 0, 0.75), (4.0, 1.8, 0.75), color, rot=(0, 0, yaw), bevel=0.25),
             B.box(name + "지붕", P(-0.25, 0, 1.4), (2.2, 1.6, 0.8), color, rot=(0, 0, yaw), bevel=0.3)]
    for dx in (-1.3, 1.3):
        for dy in (-0.9, 0.9):
            parts.append(B.cyl(name + "바퀴", P(dx, dy, 0.4), 0.4, 0.3, (0.12, 0.12, 0.13), rot=(math.pi / 2, 0, yaw)))
    return parts

if B.bpy:
    B.scene((900, 640))
    back = car("뒤차", (0.7, 2.4, 0), (0.25, 0.35, 0.85), 0.0)
    front = car("앞차", (-0.6, -0.6, 0), (0.25, 0.75, 0.55), 0.0)
    B.camera((2.5, -11.5, 3.2), (0.0, 0.8, 0.9), lens=58)
    B.passes(D, [front, back])
else:
    B.run(os.path.abspath(__file__))
    import numpy as np
    from PIL import Image, ImageDraw
    rgb = B.on_white(B.load(D, "beauty.png")); ids = B.ids(D)
    vis_f, vis_b = ids == 1, ids == 2; amo_b = B.amodal(D, 2); inv_b = amo_b & ~vis_b
    G, BL, RD = (0.2, 0.85, 0.3), (0.25, 0.35, 0.95), (0.9, 0.15, 0.15)
    # 왼쪽: 보이는 마스크
    L = B.tint(B.tint(rgb, vis_f, G, 0.45), vis_b, BL, 0.45)
    L[B.outline(vis_f, 7)] = G; L[B.outline(vis_b, 7)] = BL
    # 가운데: 마스크만 — 앞차 초록 · 뒤차 보이는 곳 파랑 · 안 보이는 곳 빨강 빗금
    M = np.ones_like(rgb); M[vis_f] = (0.55, 0.95, 0.6); M[vis_b] = (0.5, 0.55, 1.0)
    yy, xx = np.mgrid[:M.shape[0], :M.shape[1]]; hatch = ((xx + yy) // 9) % 2 == 0
    M[inv_b] = (0.95, 0.2, 0.2); M[inv_b & hatch] = (0.6, 0.05, 0.05)
    M[B.outline(vis_f, 7)] = G; M[B.outline(vis_b, 5)] = BL; M[B.outline(inv_b, 3)] = (0.3, 0.3, 0.6)
    # 오른쪽: 아모달 마스크 = 보이는 + 안 보이는
    R = B.tint(rgb, amo_b, BL, 0.5); R[B.outline(amo_b, 7)] = BL
    cv = B.canvas(); W, H = 540, 384
    for k, (im, t) in enumerate(((L, "보이는 마스크"), (M, "안 보이는 마스크"), (R, "아모달 마스크"))):
        x = 150 + k * 560; y = 300
        cv.paste(B.to_img(im).resize((W, H)), (x, y)); B.label(cv, (x + W // 2, y + H + 60), t)
    ImageDraw.Draw(cv).rectangle([150, 300, 150 + W, 300 + H], outline=(200, 200, 200), width=2)
    ImageDraw.Draw(cv).rectangle([1270, 300, 1270 + W, 300 + H], outline=(200, 200, 200), width=2)
    cv.save(os.path.join(B.OUT, "6-8.png"))
