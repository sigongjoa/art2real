# -*- coding: utf-8 -*-
"""smooth_ladder.py 로 고른 조합(스무스 셰이딩 + 데시메이트 0.25)을 구워서 낸다.

    blender -b --python bake_smooth.py -- out/omega8.glb out/omega8_smooth.glb [ratio]

**기하는 안 민다.** 각져 보이는 건 대부분 플랫 셰이딩이지 계단이 아니다(LESSONS 4).
스무스/코렉티브 스무스는 라플라시안이라 판 이음선·가슴 문양·뿔 끝을 같이 지운다 —
1.12M 면 오메가몬에서 0.5x12 를 걸었더니 밀랍 인형이 됐다(lad_5 대 lad_3).
데시메이트 0.25 는 75%를 버리는데 확대해도 1단계와 구분이 안 된다.
"""
import bpy, os, sys

A = sys.argv[sys.argv.index("--")+1:]
SRC, DST = os.path.abspath(A[0]), os.path.abspath(A[1])

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
obs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
for o in obs:
    o.data.transform(o.matrix_world)
    o.matrix_world.identity()
bpy.context.view_layer.objects.active = obs[0]
for o in obs:
    o.select_set(True)
if len(obs) > 1:
    bpy.ops.object.join()
o = bpy.context.view_layer.objects.active
n0 = len(o.data.polygons)

RATIO = float(A[2]) if len(A) > 2 else 0.25

bpy.ops.object.shade_smooth()
m = o.modifiers.new("dec", 'DECIMATE'); m.ratio = RATIO
bpy.ops.object.modifier_apply(modifier="dec")

bpy.ops.export_scene.gltf(filepath=DST, export_format='GLB', use_selection=True)
print("면 %d -> %d  저장 %s" % (n0, len(o.data.polygons), DST))
