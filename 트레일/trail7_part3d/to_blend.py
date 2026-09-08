# -*- coding: utf-8 -*-
"""생성 GLB 를 **작업 가능한 .blend** 로 만든다. 여기서부터는 블렌더 작업이다.

    blender -b --python to_blend.py -- out/omega6t.glb out/omega.blend

하는 일:
  * 파트를 오브젝트로 갈라 자리로 이름을 붙인다 (머리/몸통/왼팔/오른팔/다리/방패...)
  * 월드행렬을 메시에 굽는다 (glTF 부모 회전 제거)
  * 스무스 셰이딩 + 데시메이트 0.25 를 걸어둔다 — LESSONS 4·9, 기하는 안 민다
  * 파트마다 재질 하나. 나중에 부위별로 다르게 칠하려면 여기가 손잡이다

이름은 **자리로 정한다**(위/아래, 좌/우, 크기). 원화 라벨이 없으니 그게 유일한 근거다.
"""
import bpy, os, sys
import numpy as np

A = sys.argv[sys.argv.index("--")+1:]
GLB, DST = os.path.abspath(A[0]), os.path.abspath(A[1])

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
obs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
for o in obs:
    o.data.transform(o.matrix_world)
    o.matrix_world.identity()

co = np.vstack([np.array([v.co[:] for v in o.data.vertices]) for o in obs])
LO, HI = co.min(0), co.max(0)
CX, CZ = (LO[0]+HI[0])/2, (LO[2]+HI[2])/2


# GLB 파트 순서대로 이름. **자리로 추정하지 않고 보고 정했다** (out/parts_sheet.png).
# 자리 추정으로 붙였더니 방패를 다리로, 캐논을 팔로 잘못 불렀다.
NAMES = ["forearm", "body", "legs", "sword", "cannon", "shoulder"]


for i, o in enumerate(obs):
    v = np.array([x.co[:] for x in o.data.vertices])
    o.name = o.data.name = NAMES[i] if i < len(NAMES) else "part%d" % i
    lo, hi = v.min(0), v.max(0)
    print("%-8s 면 %7d  bbox %s  중심 %s" % (o.name, len(o.data.polygons),
          np.round(hi-lo, 3), np.round((lo+hi)/2, 3)))

    bpy.context.view_layer.objects.active = o
    for x in obs:
        x.select_set(x is o)
    bpy.ops.object.shade_smooth()
    m = o.modifiers.new("dec", 'DECIMATE'); m.ratio = 0.25
    mat = bpy.data.materials.new(o.name)
    mat.diffuse_color = (0.62, 0.62, 0.66, 1)
    o.data.materials.clear(); o.data.materials.append(mat)

os.makedirs(os.path.dirname(DST), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=DST)
print("저장 %s  오브젝트 %d개" % (DST, len(obs)))
