# -*- coding: utf-8 -*-
"""11-6 ShapeAssembly: 상자 재료가 처음엔 한가운데 겹침 → 붙이기 ①②③ → ④⑤ → 거울 ⑥ 으로 의자. 판 넷을 따로 렌더(_r/11-6_k.png)."""
import bpy, sys, os, math
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
D = os.path.dirname(os.path.abspath(__file__))
YE = (1.0, 0.95, 0.2, 1); BL = (0.35, 0.35, 1.0, 1); RD = (1.0, 0.3, 0.3, 1); GN = (0.2, 0.85, 0.35, 1); OR = (0.98, 0.65, 0.35, 1)
SIZE = {"c0": (0.6, 0.6, 0.6), "c1": (0.6, 0.6, 0.2), "c2": (0.6, 0.2, 0.9), "c3": (0.2, 0.4, 0.2), "c4": (0.2, 0.4, 0.2)}   # (x, y 깊이, z 높이)
COL = {"c0": YE, "c1": BL, "c2": RD, "c3": GN, "c4": OR}
FINAL = {"c0": (0, 0, 0.3), "c1": (0, 0, 0.7), "c2": (0, 0.2, 1.25), "c3": (-0.2, -0.1, 0.9), "c4": (0.2, -0.1, 0.9)}
PANELS = [{"c0": "mid", "c1": "mid", "c2": "mid", "c3": "mid"}, {"c0": 1, "c1": 1, "c2": 1, "c3": "mid"}, {"c0": 1, "c1": 1, "c2": 1, "c3": 1}, {"c0": 1, "c1": 1, "c2": 1, "c3": 1, "c4": 1}]
sc = H.scene(res=(900, 900)); sc.render.film_transparent = False; sc.world.color = (1, 1, 1); sc.view_settings.view_transform = "Standard"
sh = sc.display.shading; sh.light = "FLAT"; sh.show_cavity = False; sh.show_xray = True; sh.xray_alpha = 0.5; sh.show_object_outline = True
for k, panel in enumerate(PANELS):
    for o in list(sc.objects):
        if o.type == "MESH": bpy.data.objects.remove(o)
    for n, st in panel.items():
        loc = (0, 0, 0.9) if st == "mid" else FINAL[n]
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.scale = SIZE[n]; o.color = COL[n]
        bpy.ops.object.shade_flat(); w = o.modifiers.new("w", "WIREFRAME"); w.thickness = 0.014; w.use_replace = False
        o.rotation_euler = (0, 0, math.radians(-35))
        x, y, z = loc; c, s = math.cos(math.radians(-35)), math.sin(math.radians(-35)); o.location = (c * x - s * y, s * x + c * y, z)
    H.look((0, 0, 0.85), 0, 18, ortho=2.4); H.shot(os.path.join(D, "_r", "11-6_%d.png" % k))
