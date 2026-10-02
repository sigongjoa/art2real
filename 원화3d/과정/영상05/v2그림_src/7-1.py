# -*- coding: utf-8 -*-
"""7-1 부조 vs 입체: 정면에서는 꽉 찬 입체처럼 보여도 옆에서 보면 납작하다 (Belhumeur 외 1999 Fig.1 의 생각)
머리는 블렌더 수잔(일반 머리). python 7-1.py → ../7-1.png"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _bl as B
D = B.passdir("7-1")
STONE = (0.82, 0.8, 0.76)

if B.bpy:
    import bpy, math
    def head(name, depth, y):
        bpy.ops.mesh.primitive_monkey_add(location=(0, y, 0)); o = B._new(name, STONE)
        m = o.modifiers.new("s", "SUBSURF"); m.levels = 2; m.render_levels = 2
        o.scale = (1, depth, 1); return o
    B.scene((640, 720)); sh = bpy.context.scene.display.shading; sh.light = "MATCAP"; sh.studio_light = "basic_1.exr"
    for kind, depth in (("부조", 0.2), ("입체", 1.0)):
        for o in list(bpy.context.scene.objects):
            if o.type == "MESH": bpy.data.objects.remove(o)
        h = head(kind, depth, 0)
        if kind == "부조": B.box("바탕", (0, 0.2, 0), (3.2, 0.1, 2.8), STONE)
        for view, ang in (("정면", 0), ("옆", 68)):
            a = math.radians(ang); B.camera((-12 * math.sin(a), -12 * math.cos(a), 0.3), (0, 0, 0), ortho=3.4)
            B.shot(os.path.join(D, f"{kind}_{view}.png"))
else:
    B.run(os.path.abspath(__file__))
    from PIL import ImageDraw
    cv = B.canvas(); W, H = 360, 405; gap = 30; X0 = (1920 - 4 * W - 3 * gap - 80) // 2; Y = 270
    for k, (kind, view) in enumerate((("부조", "정면"), ("부조", "옆"), ("입체", "정면"), ("입체", "옆"))):
        im = B.to_img(B.on_white(B.load(D, f"{kind}_{view}.png"), (0.93, 0.93, 0.93))).resize((W, H))
        x = X0 + k * (W + gap) + (80 if k >= 2 else 0); cv.paste(im, (x, Y))
        B.label(cv, (x + W // 2, Y + H + 45), f"{kind} · {view}", 32)
    cv.save(os.path.join(B.OUT, "7-1.png"))
