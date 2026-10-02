# -*- coding: utf-8 -*-
"""7-2 깊이만 바꾼 머리 넷 — 옆모습은 다르지만 정면은 거의 같다 (Belhumeur 외 1999 Fig.2 · 얕은 부조 모호성의 생각)
머리는 블렌더 수잔(일반 머리). 깊이 f → λf + νy 로 바꾸고 빛을 s → (sx, sy, νsy + λsz) 로 같이 바꾼다(GBR).
python 7-2.py → ../7-2.png"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _bl as B
D = B.passdir("7-2")
ROWS = [("진짜", 1.0, 0.0), ("절반으로 누름", 0.5, 0.0), ("1.5배로 늘임", 1.5, 0.0), ("누르고 기울임", 0.6, 0.35)]
S = (0.35, 0.45, 0.82)   # 빛 쪽 방향 (그림 x 오른 · y 위 · z 보는 사람 쪽)

def light(lam, nu):
    sx, sy, sz = S; v = (sx, sy, nu * sy + lam * sz); n = math.sqrt(sum(c * c for c in v)); return tuple(c / n for c in v)

if B.bpy:
    import bpy, mathutils
    for k, (name, lam, nu) in enumerate(ROWS):
        sc = B.scene((600, 600))
        try: sc.render.engine = "BLENDER_EEVEE"
        except TypeError: sc.render.engine = "BLENDER_EEVEE_NEXT"
        sc.eevee.use_soft_shadows = True; sc.world.color = (0.02, 0.02, 0.02)
        bpy.ops.mesh.primitive_monkey_add(); o = B._new("머리", (0.8, 0.8, 0.8))
        o.data.transform(mathutils.Matrix(((1, 0, 0, 0), (0, lam, -nu, 0), (0, 0, 1, 0), (0, 0, 0, 1))))
        m = o.modifiers.new("s", "SUBSURF"); m.levels = m.render_levels = 2
        mat = bpy.data.materials.new("m"); mat.use_nodes = True
        bs = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        bs.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1); bs.inputs["Roughness"].default_value = 1.0
        for key in ("Specular IOR Level", "Specular"):
            if key in bs.inputs: bs.inputs[key].default_value = 0.0
        o.data.materials.append(mat)
        sx, sy, sz = light(lam, nu); d = mathutils.Vector((sx, -sz, sy))
        sun = bpy.data.objects.new("해", bpy.data.lights.new("해", "SUN")); sc.collection.objects.link(sun)
        sun.data.energy = 4.0; sun.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        B.camera((0, -12, 0), (0, 0, 0), ortho=3.0); B.shot(os.path.join(D, f"정면{k}.png"))
        B.camera((-12, 0, 0), (0, 0, 0), ortho=3.0); B.shot(os.path.join(D, f"옆{k}.png"))
else:
    B.run(os.path.abspath(__file__))
    from PIL import ImageDraw
    cv = B.canvas(); P = 330; gap = 40; X0 = (1920 - 4 * P - 3 * gap) // 2; BG = (0.16, 0.16, 0.17)
    dr = ImageDraw.Draw(cv)
    for k, (name, lam, nu) in enumerate(ROWS):
        x = X0 + k * (P + gap)
        for r, view in enumerate(("정면", "옆")):
            y = 130 + r * (P + 30)
            cv.paste(B.to_img(B.on_white(B.load(D, f"{view}{k}.png"), BG)).resize((P, P)), (x, y))
            if view == "옆":   # 해와 빛 화살 (옆 화면: 오른쪽 = 보는 사람 쪽)
                sx, sy, sz = light(lam, nu); c = (x + P / 2, y + P / 2)
                sun = (c[0] + sz * P * 0.47, c[1] - sy * P * 0.47)
                dr.ellipse([sun[0] - 11, sun[1] - 11, sun[0] + 11, sun[1] + 11], outline=(255, 255, 255), width=3)
                for i in range(8):
                    a = i * math.pi / 4; dr.line([(sun[0] + 15 * math.cos(a), sun[1] + 15 * math.sin(a)), (sun[0] + 22 * math.cos(a), sun[1] + 22 * math.sin(a))], fill=(255, 255, 255), width=3)
                B.arrow(cv, (sun[0] - sz * 34, sun[1] + sy * 34), (sun[0] - sz * 120, sun[1] + sy * 120), w=4, fill=(255, 255, 255))
        B.label(cv, (x + P // 2, 130 + 2 * P + 30 + 45), name, 30)
    B.label(cv, (X0 - 50, 130 + P // 2), "정면", 30); B.label(cv, (X0 - 50, 160 + P + P // 2), "옆", 30)
    cv.save(os.path.join(B.OUT, "7-2.png"))
