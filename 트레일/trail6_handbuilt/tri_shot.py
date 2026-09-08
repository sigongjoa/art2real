# -*- coding: utf-8 -*-
"""생성된 GLB 를 원화와 **같은 정사영 창**에 맞춰 찍는다.

    blender -b --python tri_shot.py -- out/tri_pauldron.glb out/tri

TripoSG 출력은 자기 좌표계다. 원화와 비교하려면 정면 실루엣을 기준으로
크기·위치를 맞춰야 한다 — 여기서는 **정면 bbox 를 견갑 실측 상자에 맞춘다**
(그게 정렬의 전부다. 깊이는 안 건드린다 — 그게 이 모델이 아는 것이니까).
"""
import bpy, os, sys, math

HERE = os.path.dirname(os.path.abspath(__file__))
# 견갑 + 뿔 실측 상자 (tri_in_pauldron.png 를 자른 창과 같아야 한다)
U0, U1, Z0, Z1 = 0.112, 0.245, 0.788, 0.990


def main():
    a = sys.argv[sys.argv.index("--") + 1:]
    glb, tag = a[0], a[1]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
    obs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bpy.context.view_layer.objects.active = obs[0]
    for o in obs:
        o.select_set(True)
    if len(obs) > 1:
        bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active

    # glTF 는 Y-up 으로 들어온다. 임포터가 Z-up 으로 돌려주지만 명시적으로 확인
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    co = [o.matrix_world @ v.co for v in o.data.vertices]
    xs = [c.x for c in co]; ys = [c.y for c in co]; zs = [c.z for c in co]
    print("GLB bbox x %.3f..%.3f  y %.3f..%.3f  z %.3f..%.3f" % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))

    # 정면(x,z) bbox 를 실측 창에 맞춘다. 한 배율 — 종횡비를 안 깬다
    sx = (U1 - U0) / max(max(xs) - min(xs), 1e-9)
    sz = (Z1 - Z0) / max(max(zs) - min(zs), 1e-9)
    s = min(sx, sz)
    o.scale = (s, s, s)
    bpy.ops.object.transform_apply(scale=True)
    co = [o.matrix_world @ v.co for v in o.data.vertices]
    xs = [c.x for c in co]; ys = [c.y for c in co]; zs = [c.z for c in co]
    o.location = ((U0 + U1) / 2 - (min(xs) + max(xs)) / 2,
                  0.027 - (min(ys) + max(ys)) / 2,
                  (Z0 + Z1) / 2 - (min(zs) + max(zs)) / 2)
    bpy.ops.object.transform_apply(location=True)
    print("맞춘 배율 %.4f  (sx %.4f sz %.4f)" % (s, sx, sz))

    m = bpy.data.materials.new("f")
    m.diffuse_color = (0.30, 0.31, 0.50, 1)
    o.data.materials.clear(); o.data.materials.append(m)

    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'
    sc.display.shading.color_type = 'MATERIAL'
    sc.display.shading.show_cavity = True
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = 1024
    sc.view_settings.view_transform = 'Standard'
    for n, loc, rot in (("front", (0.0, -2.0, 0.5), (math.radians(90), 0, 0)),
                        ("side", (2.0, 0.0, 0.5), (math.radians(90), 0, math.radians(90))),
                        ("q", (0.184 + 1.2 * math.sin(math.radians(40)),
                               0.027 - 1.2 * math.cos(math.radians(40)), 0.885),
                         (math.radians(90), 0, math.radians(40)))):
        cd = bpy.data.cameras.new(n)
        cd.type = 'ORTHO'
        cd.ortho_scale = 0.30 if n == "q" else 1.2
        c = bpy.data.objects.new(n, cd)
        c.location = loc; c.rotation_euler = rot
        sc.collection.objects.link(c)
        sc.camera = c
        sc.render.filepath = os.path.join(HERE, "%s_%s.png" % (tag, n))
        bpy.ops.render.render(write_still=True)
        print("TRI", n)
    print("면 %d 정점 %d" % (len(o.data.polygons), len(o.data.vertices)))


main()
