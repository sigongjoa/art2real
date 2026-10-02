# -*- coding: utf-8 -*-
"""7-5 돼지 모델: a 음영 · b 윤곽선 만화 칠 · c 옆에서 본 장면 — 카메라 a 쪽을 보는 앞면(살구) · 등진 뒷면(파랑) · 그 경계 = 윤곽(빨강)
(Bénard & Hertzmann 2019 Fig.1.1 의 생각) python 7-5.py → ../7-5.png"""
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _bl as B
D = B.passdir("7-5")
PINK = (0.93, 0.78, 0.76)

if B.bpy:
    import bpy, mathutils
    sc = B.scene((800, 640))
    P = [B.ell("몸", (0, 0, 1.1), (1.5, 1.0, 0.95), PINK),
         B.ell("머리", (-1.3, 0, 1.35), (0.75, 0.7, 0.65), PINK),
         B.cyl("코", (-2.15, 0, 1.2), 0.38, 0.6, PINK, rot=(0, math.pi / 2, 0), verts=32),
         B.cone("귀", (-1.2, -0.45, 2.0), 0.25, 0.02, 0.6, PINK, rot=(0.5, -0.4, 0)),
         B.cone("귀", (-1.2, 0.45, 2.0), 0.25, 0.02, 0.6, PINK, rot=(-0.5, -0.4, 0))]
    for x in (-0.8, 0.8):
        for y in (-0.5, 0.5):
            P.append(B.cyl("다리", (x, y, 0.3), 0.2, 0.6, PINK, verts=24))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.18, minor_radius=0.05, location=(1.55, 0, 1.6), rotation=(math.pi / 2, 0, 0)); P.append(B._new("꼬리", PINK))
    for o in P:   # 매끈하게 + 점 늘리기(경계가 고르게)
        m = o.modifiers.new("s", "SUBSURF"); m.levels = 2; m.subdivision_type = "SIMPLE" if o.name.startswith(("코", "다리", "귀")) else "CATMULL_CLARK"
        bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier=m.name)
    ca = mathutils.Vector((-7, -6, 3.2)); tgt = mathutils.Vector((-0.4, 0, 1.0))
    B.camera(ca, tgt, ortho=5.2)
    B.passes(D, P, tag="a", alone=False)
    # c: 앞면/뒷면을 꼭짓점 색으로 (카메라 a 는 평행 투영 → 보는 방향 하나)
    v = (ca - tgt).normalized()
    for o in P:
        me = o.data; att = me.color_attributes.new("앞뒤", "FLOAT_COLOR", "POINT"); R = o.matrix_world.to_3x3()
        for i, vt in enumerate(me.vertices):
            d = (R @ vt.normal).normalized().dot(v)
            att.data[i].color = (0.9, 0.15, 0.15, 1) if abs(d) < 0.05 else ((0.93, 0.8, 0.55, 1) if d > 0 else (0.35, 0.65, 0.78, 1))
        me.color_attributes.active_color = att
    sh = sc.display.shading; sh.color_type = "VERTEX"; sh.show_cavity = False
    yaw = math.atan2(ca.y - tgt.y, ca.x - tgt.x) + math.radians(90)
    cc = tgt + mathutils.Vector((9 * math.cos(yaw), 9 * math.sin(yaw), 2.0))
    B.camera(cc, tgt, ortho=5.2); B.shot(os.path.join(D, "옆.png"))
    # 카메라 a 가 보는 방향을 c 화면에 투영(화살용)
    cam = sc.camera; rx = cam.matrix_world.to_3x3() @ mathutils.Vector((1, 0, 0)); uy = cam.matrix_world.to_3x3() @ mathutils.Vector((0, 1, 0))
    look = -v; json.dump({"dx": look.dot(rx), "dy": -look.dot(uy)}, open(os.path.join(D, "화살.json"), "w"))
else:
    B.run(os.path.abspath(__file__))
    import numpy as np
    from PIL import ImageDraw
    a = B.on_white(B.load(D, "beautya.png")); ids = B.ids(D, "a")
    toon = np.ones_like(a); toon[ids > 0] = (0.99, 0.9, 0.88)
    lum = a.mean(-1); toon[(ids > 0) & (lum < 0.62)] = (0.9, 0.76, 0.75)   # 그림자 한 단
    e = np.zeros(ids.shape, bool); e[:-1] |= ids[:-1] != ids[1:]; e[:, :-1] |= ids[:, :-1] != ids[:, 1:]
    toon[B.outline(e, 5) | e] = 0.08
    c = B.to_img(B.on_white(B.load(D, "옆.png")))
    cv = B.canvas(); W, H = 500, 400; gap = 50; X0 = (1920 - 3 * W - 2 * gap) // 2; Y = 280
    for k, (im, t) in enumerate(((B.to_img(a), "a 음영"), (B.to_img(toon), "b 윤곽선"), (c, "c 옆에서 본 장면"))):
        x = X0 + k * (W + gap); cv.paste(im.resize((W, H)), (x, Y)); B.label(cv, (x + W // 2, Y + H + 50), t, 32)
    j = json.load(open(os.path.join(D, "화살.json"))); n = math.hypot(j["dx"], j["dy"]); dx, dy = j["dx"] / n, j["dy"] / n
    x = X0 + 2 * (W + gap); cx, cy = x + W // 2, Y + H // 2
    p = (cx - dx * 255, cy - dy * 255 - 70); q = (cx - dx * 175, cy - dy * 175 - 70)   # 화살은 코 위로 비켜 그린다
    B.arrow(cv, p, q, w=5); B.label(cv, (p[0] + 10, p[1] - 30), "카메라 a 쪽", 26)
    for (tx, ty, t, col) in ((x + W - 90, Y + H - 95, "앞면", (190, 150, 70)), (x + W - 90, Y + H - 60, "뒷면", (60, 130, 160)), (x + W - 90, Y + H - 25, "윤곽", (220, 40, 40))):
        B.label(cv, (tx, ty), t, 26, anchor="lm", fill=col)
    cv.save(os.path.join(B.OUT, "7-5.png"))
