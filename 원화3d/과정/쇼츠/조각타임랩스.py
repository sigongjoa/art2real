# -*- coding: utf-8 -*-
"""조각 타임랩스 — 평평한 판(AI 가 본 얼굴)에서 시작해, 두 장으로 잰 깊이(시차바탕.npz)를 붓질처럼 부위별로 눌러 넣는다.
    blender -b -P 조각타임랩스.py -- <출력폴더> [시험] [붓당 프레임=12]   -> <출력폴더>/f0000.png … (Workbench · 점토 매트캡 · 1080×880)
손 조각이 아니라 **잰 깊이를 적용하는 과정**을 조각처럼 보인 것이다(10-01 「스컬핑 과정 비슷하게 보여줘야지」).
붓 순서 = 움직임이 큰 곳부터(부리 → 눈구멍 → …) · 붓마다 12 프레임 · 끝에 옆으로 돌아 부리가 앞인 걸 보인다."""
import sys, os, math, numpy as np, bpy, bmesh
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; 출 = a[0]; 시험 = "시험" in a[1:]; 붓수 = next((int(x) for x in a[1:] if x.isdigit()), 12); os.makedirs(출, exist_ok=True)
z = np.load(r"G:\art2real\원화3d\out\오메가몬2\블렌더\시차바탕.npz"); V, Fc = z["V"].astype(float), z["F"]
D = 1                                                                                   # 깊이 축 = 블렌더 y
목표 = V.copy(); 평 = V.copy(); 평[:, D] = np.median(V[:, D])                           # 시작 = 평평한 판
c = V.mean(0); 크기 = np.ptp(V, 0).max()

bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
me = bpy.data.meshes.new("판"); me.from_pydata(평.tolist(), [], Fc.tolist()); me.update()
ob = bpy.data.objects.new("판", me); sc.collection.objects.link(ob)
for p in me.polygons: p.use_smooth = True
# 붓 고리
bpy.ops.mesh.primitive_torus_add(major_radius=0.08 * 크기, minor_radius=0.006 * 크기); 붓 = bpy.context.active_object; 붓.color = (1, 0.9, 0.2, 1)
ob.color = (0.85, 0.82, 0.78, 1)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 50
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "MATCAP"; sh.color_type = "OBJECT"
sc.render.resolution_x, sc.render.resolution_y = 1080, 880; sc.render.film_transparent = False
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.02, 0.02, 0.025)
def 카메라(각, 높이=0.12, 거리=1.75):
    p = Vector(c) + Vector((math.sin(각), -math.cos(각), 높이)) * 거리 * 크기 * (1 if not 정면반대 else 1)
    if 정면반대: p = Vector(c) + Vector((math.sin(각), math.cos(각), 높이)) * 거리 * 크기
    cam.location = p; cam.rotation_euler = (Vector(c) - p).to_track_quat("-Z", "Y").to_euler()
정면반대 = os.environ.get("뒤", "") == "1"
if 시험:                                                                                # 방향 확인: 두 쪽에서 한 장씩
    me.vertices.foreach_set("co", 목표.ravel()); me.update(); 붓.hide_render = True
    for 이름, 각 in (("a_정면", 0.0), ("b_3-4", 0.6), ("c_옆", 1.45)):
        카메라(각); sc.render.filepath = os.path.join(출, 이름 + ".png"); bpy.ops.render.render(write_still=True)
    sys.exit()
# 붓 중심: 움직임이 큰 정점들을 거리로 묶어 16 곳 · 큰 곳부터
차 = np.abs(목표[:, D] - 평[:, D]); 반경 = 0.09 * 크기; 남 = 차.copy(); 중심 = []
for _ in range(16):
    i = int(np.argmax(남)); 중심.append(i); 남[np.linalg.norm(V[:, [0, 2]] - V[i, [0, 2]], axis=1) < 반경 * 1.6] = 0
cur = 평.copy(); f = 0; 붓당 = 붓수
def 찍기(각):
    global f
    me.vertices.foreach_set("co", cur.ravel()); me.update(); 카메라(각); sc.render.filepath = os.path.join(출, "f%04d.png" % f); bpy.ops.render.render(write_still=True); f += 1
총 = len(중심) * 붓당
for s, i in enumerate(중심):
    for k in range(붓당):
        t = (s * 붓당 + k) / 총; 각 = 0.35 + 0.25 * math.sin(t * math.pi)                # 살짝 돌며 본다
        q = V[i].copy(); q[0] += 0.3 * 반경 * math.cos(k * 0.9); q[2] += 0.3 * 반경 * math.sin(k * 0.9)   # 붓이 원을 그린다
        w = np.exp(-(np.linalg.norm(V[:, [0, 2]] - q[[0, 2]], axis=1) / 반경) ** 2)
        cur[:, D] += (목표[:, D] - cur[:, D]) * w * (0.28 * 12 / 붓당)
        붓.location = Vector((q[0], cur[i, D] - 0.02 * 크기 * (1 if not 정면반대 else -1), q[2])); 붓.rotation_euler = (math.pi / 2, 0, 0)
        찍기(각)
붓.hide_render = True
for k in range(20):                                                                   # 남은 곳을 매끈하게 마저 채움
    cur += (목표 - cur) * 0.2; 찍기(0.35)
cur = 목표.copy()
for k in range(80):                                                                   # 옆으로 돌아 부리가 앞인 걸 본다
    찍기(0.35 + 1.1 * (0.5 - 0.5 * math.cos(math.pi * k / 79)))
print("프레임", f)
