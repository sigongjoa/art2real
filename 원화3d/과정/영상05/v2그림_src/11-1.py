# -*- coding: utf-8 -*-
"""11-1 바의 초이차곡면 4×4: 식 하나 · 지수 두 개(ε1 위→아래 커짐 · ε2 오른쪽→왼쪽 커짐). blender -b -P 11-1.py → _r/11-1.png, 11-1.typ 로 이름표"""
import bpy, sys, os, math
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
sys.path.insert(0, r"G:\art2real\원화3d\과정\영상05")
D = os.path.dirname(os.path.abspath(__file__))
sc = H.scene(res=(1500, 1500)); sc.render.film_transparent = True
sh = sc.display.shading; sh.light = "STUDIO"; sh.color_type = "OBJECT"; sh.show_cavity = False; sh.show_specular_highlight = True
# B357 의 초이차 생성기(그 파일은 렌더까지 돌므로 함수만 옮김)
import bmesh
def sgn_pow(x, e): return math.copysign(abs(x) ** e, x)
def superq(name, e1, e2, n=72, loc=(0, 0, 0), color=(0.85, 0.85, 0.88, 1)):
    vs, fs = [], []
    for i in range(n + 1):
        eta = -math.pi / 2 + math.pi * i / n
        for j in range(n):
            w = -math.pi + 2 * math.pi * j / n
            ce, se, cw, sw = math.cos(eta), math.sin(eta), math.cos(w), math.sin(w)
            vs.append((sgn_pow(ce, e1) * sgn_pow(cw, e2), sgn_pow(ce, e1) * sgn_pow(sw, e2), sgn_pow(se, e1)))
    for i in range(n):
        for j in range(n):
            p = i * n + j; q = i * n + (j + 1) % n; fs.append((p, q, q + n, p + n))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); o.location = loc; o.color = color
    o.rotation_euler = (math.radians(20), math.radians(-25), math.radians(30))
    for p in me.polygons: p.use_smooth = True
    return o
E = [0.3, 1.0, 2.0, 3.0]
COL = [(0.85, 0.2, 0.2, 1), (0.92, 0.45, 0.6, 1), (0.95, 0.78, 0.25, 1), (0.92, 0.9, 0.85, 1), (0.3, 0.65, 0.9, 1), (0.3, 0.7, 0.4, 1)]
for i, e1 in enumerate(E):              # 줄: 위 → 아래 ε1 커짐
    for j, e2 in enumerate(E):          # 칸: 오른쪽 → 왼쪽 ε2 커짐
        x = (3 - j) * 2.7 - 4.05; z = -(i * 2.7 - 4.05)
        superq("sq%d%d" % (i, j), e1, e2, loc=(x, 0, z), color=COL[(i + 2 * j) % len(COL)])
H.look((0, 0, 0), 0, 0, ortho=11.2); H.shot(os.path.join(D, "_r", "11-1.png"))
