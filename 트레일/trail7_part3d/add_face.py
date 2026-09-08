# -*- coding: utf-8 -*-
"""얼굴 크롭 생성물에서 **정면 판만** 떼어 투구 앞에 덧댄다.

    blender -b --python add_face.py -- out/omega.blend

왜 판만 쓰나: 얼굴 크롭(격자 한 칸 0.31 원본화소)은 정면 릴리프가 정교하지만
옆·뒤는 무너진다 — 정면 한 장이 입력이라 지어낼 근거가 없다. 통째로 갈아끼우면
옆모습을 잃는다. 그래서 **앞면만 잘라 기존 투구 위에 얹는다.**

크기는 투구에 맞춘다(모델이 가진 값). 깊이는 투구 앞면에 살짝 겹치게 — 노브.
"""
import bpy, os, sys
import bmesh
import numpy as np

A = sys.argv[sys.argv.index("--")+1:]
SRC = os.path.abspath(A[0])
HERE = os.path.dirname(os.path.abspath(__file__))

FRONT_KEEP = 0.42      # 깊이 앞쪽 이 비율만 남긴다 (노브)
TOP_KEEP   = 0.70      # 세로 위쪽 이 비율만 — 크롭에 목가리개·가슴이 들어와서
                       # 릴리프가 얼굴 같은 띠를 셋 만든다. 맨 위 하나만 쓴다 (노브)
SINK = 0.03            # 판 뒷면이 투구 앞면 안으로 묻히는 깊이 (노브)

bpy.ops.wm.open_mainfile(filepath=SRC)
helmet = bpy.context.scene.objects["helmet"]
hv = np.array([helmet.matrix_world @ v.co for v in helmet.data.vertices])
hlo, hhi = hv.min(0), hv.max(0)
print("투구 bbox %s" % np.round(hhi-hlo, 3))

before = set(o.name for o in bpy.context.scene.objects)
bpy.ops.wm.obj_import(filepath=os.path.join(HERE, "out", "face3_p1.obj"))
face = [o for o in bpy.context.scene.objects if o.name not in before][0]
face.data.transform(face.matrix_world); face.matrix_world.identity()
face.name = face.data.name = "faceplate"

v0 = np.array([v.co[:] for v in face.data.vertices])
print("얼굴 원본 bbox %s" % np.round(v0.max(0)-v0.min(0), 3))

# 1) 앞쪽 판만 남긴다. 카메라가 -Y 에 있으므로 앞 = y 작은 쪽.
bm = bmesh.new(); bm.from_mesh(face.data)
ylo = min(v.co.y for v in bm.verts); yhi = max(v.co.y for v in bm.verts)
cut = ylo + (yhi - ylo) * FRONT_KEEP
kill = [f for f in bm.faces if sum(v.co.y for v in f.verts)/len(f.verts) > cut]
bmesh.ops.delete(bm, geom=kill, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
print("뒤쪽 제거 — 면 %d 지움, %d 남김" % (len(kill), len(bm.faces)))

# 1b) 세로로도 자른다 — 아래쪽 띠(목가리개·가슴)를 버린다
zlo = min(v.co.z for v in bm.verts); zhi = max(v.co.z for v in bm.verts)
zcut = zhi - (zhi - zlo) * TOP_KEEP
kill2 = [f for f in bm.faces if sum(v.co.z for v in f.verts)/len(f.verts) < zcut]
bmesh.ops.delete(bm, geom=kill2, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
print("아래쪽 띠 제거 — 면 %d 지움, %d 남김" % (len(kill2), len(bm.faces)))
bm.to_mesh(face.data); bm.free()

# 2) 투구 가로폭에 맞춘다 (종횡비 유지)
v1 = np.array([v.co[:] for v in face.data.vertices])
s = (hhi[0]-hlo[0]) / (v1[:, 0].max()-v1[:, 0].min())
face.scale = (s, s, s)
bpy.context.view_layer.objects.active = face
for x in bpy.context.scene.objects:
    x.select_set(x is face)
bpy.ops.object.transform_apply(scale=True)

# 3) 투구 앞면에 붙인다 — 가로·세로 중심 맞추고 깊이는 앞으로
v2 = np.array([v.co[:] for v in face.data.vertices])
lo2, hi2 = v2.min(0), v2.max(0)
face.location = ((hlo[0]+hhi[0])/2 - (lo2[0]+hi2[0])/2,
                 (hlo[1] + SINK) - hi2[1],   # 판 **뒷면**을 투구 앞면에 붙인다
                 hhi[2] - hi2[2])   # 판 꼭대기를 투구 꼭대기에
print("얼굴판 배율 %.3f  이동 %s" % (s, np.round(np.array(face.location), 3)))

face.data.materials.clear()
m = bpy.data.materials.new("faceplate"); m.diffuse_color = (0.62, 0.62, 0.66, 1)
face.data.materials.append(m)
md = face.modifiers.new("dec", 'DECIMATE'); md.ratio = 0.25
bpy.ops.object.shade_smooth()

bpy.ops.wm.save_mainfile(filepath=SRC)
print("저장 %s" % SRC)
