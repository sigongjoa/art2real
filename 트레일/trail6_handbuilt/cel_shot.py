# -*- coding: utf-8 -*-
"""**실제로 보게 될 조건**으로 찍는다 — 셀 셰이딩 + Freestyle 먹선.

    "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe" -b --python cel_shot.py -- pad43.blend pad43_col.png cel

Workbench 평면색으로는 "거슬리는가"를 판정할 수 없다. 원화는 셀이고 먹선이 재질이
아니라 그리는 관습이다 (129). 먹선은 텍스처가 아니라 Freestyle 이 낼 것이다 (130).

캡에 이면각 60도 넘는 엣지가 141개 있다 — 판 선을 기하가 이미 갖고 있는지
여기서 갈린다. 없으면 그때 소켓 링·능선을 지으면 된다.
"""
import bpy, os, sys, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
A = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
BLEND, TEX, PRE = (A + ["pad43.blend", "pad43_col.png", "cel"])[:3]

bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, BLEND))
objs = [x for x in bpy.context.scene.objects if x.type == 'MESH']
bpy.context.view_layer.objects.active = objs[0]
for x in objs:
    x.select_set(True)
if len(objs) > 1:
    bpy.ops.object.join()
o = bpy.context.view_layer.objects.active

# 셀 — 텍스처를 Emission 으로 낸다. 음영은 아직 안 얹는다 (평면 알베도가 재질이다)
m = bpy.data.materials.new("cel"); m.use_nodes = True
nt = m.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL':
        nt.nodes.remove(n)
em = nt.nodes.new("ShaderNodeEmission")
tx = nt.nodes.new("ShaderNodeTexImage")
tx.image = bpy.data.images.load(os.path.join(OUT, TEX)); tx.interpolation = 'Closest'
nt.links.new(tx.outputs["Color"], em.inputs["Color"])
nt.links.new(em.outputs["Emission"], nt.nodes["Material Output"].inputs["Surface"])
o.data.materials.clear(); o.data.materials.append(m)

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = 512
sc.view_settings.view_transform = 'Standard'

# Freestyle — 먹선
sc.render.use_freestyle = True
vl = bpy.context.view_layer
vl.use_freestyle = True
fs = vl.freestyle_settings
fs.as_render_pass = False
lset = fs.linesets.new("ink") if not fs.linesets else fs.linesets[0]
lset.select_silhouette = True
lset.select_border = True
lset.select_crease = True
lset.select_edge_mark = False
fs.crease_angle = math.radians(115)          # 이면각 65도 이상이 능선으로 잡힌다
ls = lset.linestyle or bpy.data.linestyles.new("ink")
lset.linestyle = ls
ls.color = (0.06, 0.06, 0.09)
ls.thickness = 2.2

co = np.array([v.co[:] for v in o.data.vertices])
cx, cy, cz = co.mean(0)
span = max(co.max(0) - co.min(0)) * 1.2
for n, ang in (("front", 0.0), ("q", 40.0), ("back", 180.0)):
    a = math.radians(ang)
    cd = bpy.data.cameras.new(n); cd.type = 'ORTHO'; cd.ortho_scale = span
    c = bpy.data.objects.new(n, cd)
    c.location = (cx + 2*math.sin(a), cy - 2*math.cos(a), cz)
    c.rotation_euler = (math.radians(90), 0, a)
    sc.collection.objects.link(c); sc.camera = c
    sc.render.filepath = os.path.join(OUT, "%s_%s.png" % (PRE, n))
    bpy.ops.render.render(write_still=True)
    print("찍음 %s_%s" % (PRE, n))
