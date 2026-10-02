# -*- coding: utf-8 -*-
"""지온_샘플.py 결과를 그린다: 조립(3/4 · 정면) · 분해(조인트 점 + 붙음 선 · 관계 색). blender -b -P 지온_샘플_렌더.py"""
import bpy, os, sys, json, math
from mathutils import Vector
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
O = r"G:\art2real\원화3d\out\샘플\메크머리_CC0\지온"
g = json.load(open(os.path.join(O, "그래프.json"), encoding="utf-8")); 자리 = json.load(open(os.path.join(O, "자리.json"), encoding="utf-8"))
색 = {"투구": (0.55, 0.75, 1.0), "총": (1.0, 0.65, 0.3), "핀": (0.95, 0.3, 0.3)}
관계색 = {"안에-듦": (0.85, 0.1, 0.1), "끝-가운데": (0.1, 0.5, 0.15), "끝-끝": (0.5, 0.2, 0.7), "위에-얹힘": (0.1, 0.3, 0.8)}
sc = H.scene(res=(800, 800), transparent=False); sc.world.color = (1, 1, 1); sh = sc.display.shading; sh.color_type = "OBJECT"; sh.light = "STUDIO"; sh.show_cavity = True
def 불러(접두):
    out = {}
    for p in g["부품들"]:
        k = f'{p["이름"]}/{p["쪽"]}'; f = os.path.join(O, f"{접두}_{k.replace('/', '_')}.obj")
        bpy.ops.wm.obj_import(filepath=f, forward_axis="Y", up_axis="Z"); o = bpy.context.selected_objects[0]; o.color = 색[p["이름"]] + (1,); out[k] = o
    return out
def 막대(a, b, r, col):
    v = b - a; bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=r, depth=max(v.length, 1e-3), location=(a + b) / 2); o = bpy.context.active_object
    o.rotation_euler = v.to_track_quat("Z", "Y").to_euler(); o.color = col + (1,); return o
def 공(c, r, col): bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=c); o = bpy.context.active_object; o.color = col + (1,); return o
조립 = 불러("조립"); c = sum((o.location for o in 조립.values()), Vector()) / len(조립)
bb = [o.matrix_world @ Vector(v) for o in 조립.values() for v in o.bound_box]; ctr = sum(bb, Vector()) / len(bb)
for nm, (yaw, pitch) in {"조립_34": (35, 20), "조립_정면": (0, 5)}.items(): H.look(tuple(ctr), yaw, pitch, 120, dist=500); H.shot(os.path.join(O, nm + ".png"))
for o in 조립.values(): bpy.data.objects.remove(o)
분해 = 불러("분해"); P = {k: Vector(v) for k, v in 자리["펼침"].items()}
for e in g["붙음들"]:
    a = Vector(자리["붙는자리"][e["자식"]]) + P[e["부모"]]; b = Vector(자리["붙는자리"][e["자식"]]) + P[e["자식"]]
    막대(a, b, 0.6, 관계색[e["관계"]]); 공(a, 2.2, (0.15, 0.15, 0.15)); 공(b, 2.2, 관계색[e["관계"]])
for o in 분해.values(): o.color = o.color[:3] + (1,)
for nm, (yaw, pitch) in {"분해_34": (35, 20), "분해_정면": (0, 5)}.items(): H.look(tuple(ctr), yaw, pitch, 190, dist=600); H.shot(os.path.join(O, nm + ".png"))
print("ok")
