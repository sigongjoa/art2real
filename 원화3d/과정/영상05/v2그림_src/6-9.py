# -*- coding: utf-8 -*-
"""6-9 식탁의 겹친 그릇 · 잔을 하나씩 떼어 내 가려진 곳까지 채우고, 순서와 자리를 바꿔 다시 놓는다 (Zhan 외 2020 Fig.1 의 생각)
python 6-9.py → ../6-9.png"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _bl as B
D = B.passdir("6-9")

if B.bpy:
    import bpy, math
    B.scene((800, 600))
    def torus(name, loc, R, r, color, rot=(0, 0, 0)):
        bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc, rotation=rot, major_segments=48, minor_segments=16); return B._new(name, color)
    B.box("식탁", (0, 0, -0.06), (7, 5, 0.1), (0.35, 0.28, 0.24))
    plate = [B.cyl("접시", (0.0, 0.2, 0.05), 1.5, 0.1, (0.93, 0.93, 0.9), verts=64)]
    bowls = [B.cone("그릇1", (0.45, 0.45, 0.33), 0.38, 0.62, 0.45, (0.35, 0.55, 0.85)),
             B.cone("그릇2", (0.55, 0.5, 0.68), 0.36, 0.58, 0.4, (0.35, 0.55, 0.85))]
    cup = [B.cyl("잔", (-0.55, -0.55, 0.45), 0.35, 0.7, (0.85, 0.3, 0.25)),
           torus("손잡이", (-0.95, -0.55, 0.45), 0.2, 0.06, (0.85, 0.3, 0.25), rot=(math.pi / 2, 0, 0))]
    donut = [torus("도넛", (0.55, -0.75, 0.2), 0.38, 0.16, (0.85, 0.6, 0.3))]
    glass = [B.cyl("유리잔", (-0.35, 0.95, 0.75), 0.28, 1.4, (0.7, 0.85, 0.9))]
    objs = [plate, bowls, cup, donut, glass]
    B.camera((0, -6.5, 4.2), (0, 0.15, 0.4), lens=45)
    B.passes(D, objs)
    # 다시 놓기: 자리 바꾸고 접시는 뒤로
    def move(g, x, y):   # 덩어리 첫 조각을 (x, y) 로, 나머지는 같이
        dx, dy = x - g[0].location.x, y - g[0].location.y
        for o in g: o.location.x += dx; o.location.y += dy
    move(plate, 0.5, 0.8); move(donut, 0.5, 0.9); move(bowls, -1.4, -0.4); move(glass, 1.6, -0.5); move(cup, 0.1, -1.1)
    B.shot(os.path.join(D, "beauty_다시.png"))
else:
    B.run(os.path.abspath(__file__))
    import numpy as np
    from PIL import ImageDraw
    a = B.to_img(B.on_white(B.load(D, "beauty.png"))); c = B.to_img(B.on_white(B.load(D, "beauty_다시.png")))
    cv = B.canvas(); W, H = 480, 360; Y = 300
    cv.paste(a.resize((W, H)), (130, Y)); cv.paste(c.resize((W, H)), (1310, Y))
    # 가운데: 떼어 내 채운 물건들 (2 줄)
    tiles = []
    for i in range(1, 6):
        r = B.load(D, f"alone_{i}.png"); m = r[..., 3] > 0.05
        tiles.append(B.fit(B.to_img(B.on_white(B.crop_to(r, m, 6))), (150, 150)))
    pos = [(705, Y + 20), (865, Y + 20), (1025, Y + 20), (785, Y + 200), (945, Y + 200)]
    for t, (x, y) in zip(tiles, pos):
        cv.paste(t, (x + (150 - t.size[0]) // 2, y + (150 - t.size[1]) // 2))
    dr = ImageDraw.Draw(cv); dr.rectangle([690, Y, 1190, Y + H], outline=(190, 190, 190), width=2)
    B.arrow(cv, (625, Y + H // 2), (680, Y + H // 2)); B.arrow(cv, (1200, Y + H // 2), (1298, Y + H // 2))
    for x, t in ((130 + W // 2, "원래 장면"), (940, "떼어 내고 가려진 곳 채우기"), (1310 + W // 2, "다시 놓기")):
        B.label(cv, (x, Y + H + 60), t, 32)
    cv.save(os.path.join(B.OUT, "6-9.png"))
