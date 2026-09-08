# -*- coding: utf-8 -*-
"""납작한 머리 혹을 **제대로 된 투구**로 갈아끼운다.

    blender -b --python swap_head.py -- out/omega.blend

왜: 전신 실행(6파트·1536토큰)이 머리를 붙여서 내긴 했는데 혹이다 —
세로 0.09(몸 높이의 9%)에 얼굴이 없다. 얼굴은 머리만 크롭해 뽑은 실행(head4)에 있다.

기준은 **모델이 가진 값**이다. 원화 y 를 그대로 쓰면 안 된다(생성 몸통이 세로로 늘어나 있다):
    어깨    y 0.615~0.736  폭 0.71
    머리 혹 y 0.760~0.850  폭 0.42  깊이 0.25   <- 갈아끼울 구간
    뿔      y 0.857~       깊이 0.03 (종잇장)
투구 배율은 **목 폭 0.42 에 맞춘다.** 자리는 혹이 있던 자리 그대로.
"""
import bpy, os, sys
import bmesh
import numpy as np

A = sys.argv[sys.argv.index("--")+1:]
SRC = os.path.abspath(A[0])
HERE = os.path.dirname(os.path.abspath(__file__))

NECK_Y = 0.755      # 실측: 어깨 위, 혹 아래 — 여기 위를 걷어낸다
CHIN_Y = 0.715      # 턱을 어깨에 살짝 묻는다 (어깨 꼭대기 0.736)
HEAD_FRAC = 0.124   # 원화 비율: 투구 115px / 전체 924px. **폭이 아니라 높이로 잡는다**
FIG_H = 1.97        # 전체 figure 세로 (실측)
# 폭으로 잡았더니 두 배로 커졌다 — 투구 메시에 목가리개가 붙어 폭이 부풀어 있다.

bpy.ops.wm.open_mainfile(filepath=SRC)
body = bpy.context.scene.objects["body"]

# 1) 혹 + 종잇장 뿔을 걷어낸다 (전부 NECK_Y 위)
bm = bmesh.new(); bm.from_mesh(body.data)
kill = [f for f in bm.faces if all(v.co.z > NECK_Y for v in f.verts)]
bmesh.ops.delete(bm, geom=kill, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
print("혹·뿔 제거 — 면 %d 지움, %d 남김" % (len(kill), len(bm.faces)))
bm.to_mesh(body.data); bm.free()

# 2) 투구와 뿔을 들여온다 (같은 실행이라 서로 좌표계가 맞다)
before = set(o.name for o in bpy.context.scene.objects)
for f in ("hd_helm.obj", "hd_fins.obj"):
    bpy.ops.wm.obj_import(filepath=os.path.join(HERE, "out", f))
new = [o for o in bpy.context.scene.objects if o.name not in before]
for o in new:
    o.data.transform(o.matrix_world); o.matrix_world.identity()
helm = [o for o in new if "helm" in o.name][0]
co = {o.name: np.array([v.co[:] for v in o.data.vertices]) for o in new}

# 3) 투구 **높이**를 원화 비율에 맞춘다. 뿔도 같은 배율로 (비율을 안 깬다)
hh = co[helm.name][:, 2].ptp()
s = (HEAD_FRAC * FIG_H) / hh
hv = co[helm.name] * s
bodyv = np.array([v.co[:] for v in body.data.vertices])
top = bodyv[bodyv[:, 2] > NECK_Y - 0.1]
cx = (top[:, 0].min() + top[:, 0].max()) / 2 if len(top) else bodyv[:, 0].mean()
cy = (top[:, 1].min() + top[:, 1].max()) / 2 if len(top) else bodyv[:, 1].mean()
off = np.array([cx - (hv[:, 0].min() + hv[:, 0].max())/2,
                cy - (hv[:, 1].min() + hv[:, 1].max())/2,
                CHIN_Y - hv[:, 2].min()])
for o in new:
    o.scale = (s, s, s)
    bpy.context.view_layer.objects.active = o
    for x in bpy.context.scene.objects:
        x.select_set(x is o)
    bpy.ops.object.transform_apply(scale=True)
    o.location = tuple(off)
    o.name = "helmet" if o is helm else "fins"
    o.data.materials.clear()
    m = bpy.data.materials.new(o.name); m.diffuse_color = (0.62, 0.62, 0.66, 1)
    o.data.materials.append(m)
    md = o.modifiers.new("dec", 'DECIMATE'); md.ratio = 0.25
    bpy.ops.object.shade_smooth()

print("투구 배율 %.3f  투구 세로 %.3f  턱 y %.3f  이동 %s" % (s, hh*s, CHIN_Y, np.round(off, 3)))
bpy.ops.wm.save_mainfile(filepath=SRC)
print("저장 %s" % SRC)
