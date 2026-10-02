# -*- coding: utf-8 -*-
"""6-7 같은 물체를 두 번 칠한다: 빨간 틀 = 보이는 픽셀만 · 초록 틀 = 가려진 곳까지 (Zhu 외 2017 Fig.2 의 생각)
예 1 다리에 밟힌 판 · 예 2 사람 뒤의 장. python 6-7.py → ../6-7.png"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _bl as B
D = B.passdir("6-7")

if B.bpy:
    import math
    # 예 1: 바닥의 판 위에 선 두 다리 (위에서 비스듬히)
    B.scene((600, 800))
    board = B.box("판", (0, 0, 0.1), (1.5, 4.6, 0.18), (0.78, 0.6, 0.3), rot=(0, 0, 0.45), bevel=0.55)
    legs = []
    for x, y in ((-0.15, 0.9), (0.35, -0.9)):
        legs.append(B.cyl("다리", (x, y, 1.5), 0.32, 2.8, (0.25, 0.25, 0.3)))
        legs.append(B.ell("발", (x + 0.1, y - 0.3, 0.38), (0.4, 0.6, 0.22), (0.85, 0.35, 0.45)))
    B.camera((0, -4.5, 9.5), (0, 0, 0.3), lens=40)
    B.passes(D, [board, legs], tag="a")
    # 예 2: 사람 뒤의 키 큰 장
    B.scene((600, 800))
    cab = B.box("장", (0.2, 1.0, 2.0), (1.6, 1.0, 4.0), (0.85, 0.75, 0.5), bevel=0.04)
    man = [B.ell("몸", (-0.15, -0.6, 2.1), (0.55, 0.35, 0.9), (0.2, 0.2, 0.25)),
           B.ell("머리", (-0.1, -0.6, 3.25), (0.3, 0.3, 0.35), (0.85, 0.7, 0.6)),
           B.cyl("다리", (-0.35, -0.6, 0.65), 0.17, 1.3, (0.2, 0.2, 0.25)),
           B.cyl("다리", (0.08, -0.6, 0.65), 0.17, 1.3, (0.2, 0.2, 0.25)),
           B.box("봉투", (0.5, -0.8, 1.2), (0.5, 0.15, 0.8), (0.95, 0.95, 0.95))]
    B.camera((0.6, -9, 2.4), (0.1, 0, 2.0), lens=45)
    B.passes(D, [cab, man], tag="b")
else:
    B.run(os.path.abspath(__file__))
    import numpy as np, cv2
    from PIL import ImageDraw
    cv = B.canvas(); W, H = 330, 440; gap = 40; X0 = (1920 - 4 * W - 3 * gap - 60) // 2; Y = 250
    RED, GRN = (230, 40, 40), (40, 200, 60)
    k = 0
    for tag in ("a", "b"):
        rgb = B.on_white(B.load(D, f"beauty{tag}.png")); ids = B.ids(D, tag)
        for mask, col in ((ids == 1, RED), (B.amodal(D, 1, tag), GRN)):
            im = B.tint(rgb, mask, (0.95, 0.7, 0.2), 0.5)
            pil = B.to_img(im); dr = ImageDraw.Draw(pil)
            cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            for c in cs:
                if cv2.contourArea(c) < 200: continue
                p = cv2.approxPolyDP(c, 6, True)[:, 0]
                dr.line([tuple(map(int, q)) for q in p] + [tuple(map(int, p[0]))], fill=(40, 60, 200), width=3)
                for q in p: dr.ellipse([q[0] - 9, q[1] - 9, q[0] + 9, q[1] + 9], outline=(120, 120, 140), fill=(225, 225, 235), width=2)
            a = B.load(D, f"beauty{tag}.png")[..., 3] > 0.05; ys, xs = np.nonzero(a)
            pil = B.fit(pil.crop((xs.min() - 30, ys.min() - 30, xs.max() + 30, ys.max() + 30)), (W - 20, H - 20))
            x = X0 + k * (W + gap) + (60 if k >= 2 else 0)
            cv.paste(pil, (x + (W - pil.size[0]) // 2, Y + (H - pil.size[1]) // 2)); B.frame(cv, (x, Y), (W, H), col, 10)
            B.label(cv, (x + W // 2, Y + H + 50), "보이는 곳만" if col == RED else "가려진 곳까지", 30)
            k += 1
    cv.save(os.path.join(B.OUT, "6-7.png"))
