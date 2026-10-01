# -*- coding: utf-8 -*-
"""생성 메시 위에 조각 — TripoSG 가 만든 큰 형태를 바탕으로 디테일을 손으로 더하고 깎는다(10-01 「tripoSG 를 바탕으로 스컬핑을 해야 하지 않아?」).
    blender -b --factory-startup -P 생성위조각.py -- <모델.glb(영문 경로)> <출력폴더> [총프레임=534 | 시험]
단계: ① TripoSG 머리 그대로(3/4 · 살짝 돎) ② 다듬기: 가짜 웃는 얼굴 · 가슴 갈비뼈 굴곡을 문질러 지움(스무스 붓)
      ③ 깎기: 눈구멍 두 개(상자 칼 · 불리언 차 · 좌우 거울) ④ 더하기: 부리꼴 마스크(V 판 세 장 · 계단처럼 포갬)  ⑤ 옆으로 돌아 확인
위치는 메시에서 잰다: 얼굴 앞점 = 머리 높이대에서 가장 앞(−Y) 정점 · 머리 폭 = 그 높이대 |x| 범위. 무거워서 먼저 줄인다(디시메이트 0.15)."""
import sys, os, math, numpy as np, bpy, bmesh
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; src, 출 = a[0], a[1]; 시험 = "시험" in a; 총 = next((int(x) for x in a[2:] if x.isdigit()), 534); os.makedirs(출, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=src)
objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
for o in bpy.context.scene.objects: o.select_set(o in objs)
bpy.context.view_layer.objects.active = objs[0]
if len(objs) > 1: bpy.ops.object.join()
m = bpy.context.view_layer.objects.active; bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM"); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
d = m.modifiers.new("줄임", "DECIMATE"); d.ratio = 0.15; bpy.ops.object.modifier_apply(modifier=d.name)
for p in m.data.polygons: p.use_smooth = True
V = np.array([v.co[:] for v in m.data.vertices]); zmax, zmin = V[:, 2].max(), V[:, 2].min(); H = zmax - zmin
# 얼굴 앞점: 위쪽 8~16 % 높이대 · |x| 작은 곳에서 가장 앞(−y) · 얼굴 가운데 x 는 0 이 아니다(앞점 x 를 쓴다) · 머리 반폭 = 0.035 H(정면 렌더에서 잼)
띠 = (V[:, 2] < zmax - 0.08 * H) & (V[:, 2] > zmax - 0.17 * H) & (np.abs(V[:, 0]) < 0.06 * H)
i앞 = np.where(띠)[0][np.argmin(V[띠, 1])]; 앞 = V[i앞]
머리 = (np.abs(V[:, 2] - 앞[2]) < 0.05 * H) & (np.abs(V[:, 0]) < 0.12 * H) & (V[:, 1] < 앞[1] + 0.12 * H)
폭 = 0.035 * H; 얼x = float(앞[0]); print("얼굴 앞점", np.round(앞, 3), "머리 반폭", round(float(폭), 3), "H", round(float(H), 3))
점토 = (0.86, 0.83, 0.78, 1); m.color = 점토
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "MATCAP"; sh.color_type = "OBJECT"; sh.show_cavity = True
sc.render.resolution_x, sc.render.resolution_y = 1080, 880; sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.02, 0.02, 0.025)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 85
중심 = Vector((얼x, 앞[1] + 폭 * 0.8, 앞[2] - 폭 * 0.8))
def 카메라(각, 거리=폭 * 16, 높이=0.12):
    p = 중심 + Vector((math.sin(각), -math.cos(각), 높이)) * 거리; cam.location = p; cam.rotation_euler = (중심 - p).to_track_quat("-Z", "Y").to_euler()
# 눈 · 부리 자리(머리 폭 비율 · 02 판 정면: 눈은 얼굴 위쪽 바깥 · 부리꼴은 눈 아래 가운데)
눈 = Vector((얼x + 폭 * 0.6, 앞[1] + 폭 * 0.35, 앞[2] - 폭 * 0.05)); 눈크기 = Vector((폭 * 0.5, 폭 * 0.9, 폭 * 0.3))      # 정면 렌더에서 잼: 이마 아래 · 볼 위
부리 = Vector((얼x, 앞[1] - 폭 * 0.05, 앞[2] - 폭 * 0.55))                                   # 웃는 입 자리를 덮는다
if 시험:
    for p_ in (Vector(앞), 눈, Vector((2 * 얼x - 눈.x, 눈.y, 눈.z)), 부리):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=폭 * 0.06, location=p_); bpy.context.active_object.color = (1, 0.2, 0.2, 1)
    for 이름, 각 in (("정면", 0.0), ("3-4", -0.6)):
        카메라(각); sc.render.filepath = os.path.join(출, 이름 + ".png"); bpy.ops.render.render(write_still=True)
    sys.exit()
# ② 다듬기 목표: 이웃 평균을 여러 번(얼굴 · 가슴 띠에만 쓴다)
bm = bmesh.new(); bm.from_mesh(m.data); bm.verts.ensure_lookup_table()
이웃 = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]; bm.free()
src_ = V.copy(); 매끈 = V.copy()
for _ in range(25):
    매끈 = np.array([매끈[n].mean(0) if n else 매끈[k] for k, n in enumerate(이웃)])
가슴 = Vector((얼x, 앞[1] + 폭 * 0.6, 앞[2] - 폭 * 3.2))
def 무게(c, r): return np.exp(-(np.linalg.norm(V - np.array(c), axis=1) / r) ** 2)
w얼굴 = 무게(Vector(앞) + Vector((0, 폭 * 0.3, -폭 * 0.15)), 폭 * 0.75); w가슴 = 무게(가슴, 폭 * 2.2)
# ③ 눈구멍 칼
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(눈.x, 눈.y - 폭 * 1.5, 눈.z)); 칼 = bpy.context.active_object; 칼.scale = 눈크기; 칼.rotation_euler = (0, math.radians(-14), 0); 칼.hide_render = True
bpy.ops.object.empty_add(location=(얼x, 0, 0)); 거울축 = bpy.context.active_object
mm = 칼.modifiers.new("거울", "MIRROR"); mm.use_axis[0] = True; mm.mirror_object = 거울축
b = m.modifiers.new("눈구멍", "BOOLEAN"); b.operation = "DIFFERENCE"; b.object = 칼; b.solver = "FAST"
# ④ 부리꼴 마스크: V 판 세 장(쐐기) — 위에서 아래로 계단처럼 포갬
판들 = []
for k in range(3):
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=폭 * (0.8 - 0.17 * k), radius2=폭 * 0.06, depth=폭 * 0.6, location=(0, 0, 0)); o = bpy.context.active_object
    o.rotation_euler = (math.radians(90 + 25), 0, math.radians(180)); o.scale = (1, 0.35, 1); o.color = 점토; 판들.append(o)
    bpy.ops.object.shade_flat()
붓 = None
bpy.ops.mesh.primitive_torus_add(major_radius=폭 * 0.35, minor_radius=폭 * 0.025, rotation=(math.pi / 2, 0, 0)); 붓 = bpy.context.active_object; 붓.color = (1, 0.9, 0.2, 1)
T = {k: int(총 * r) for k, r in dict(보기끝=0.12, 다듬끝=0.38, 깎기=0.40, 깎기끝=0.58, 판=0.60, 판끝=0.80, 궤도=0.82, 끝=1.0).items()}
def 단(t, a_, b_): return max(0.0, min(1.0, (t - a_) / max(1, b_ - a_)))
def 부드(x): return 0.5 - 0.5 * math.cos(math.pi * x)
for f in range(총):
    # ② 다듬기: 붓이 얼굴 → 가슴 순서로 지나간 만큼 매끈하게
    s = 단(f, T["보기끝"], T["다듬끝"]); s1, s2 = 부드(min(1, s * 2)), 부드(max(0, s * 2 - 1))
    cur = src_ + (매끈 - src_) * (np.clip(w얼굴 * s1, 0, 1)[:, None] * 0.9 + np.clip(w가슴 * s2, 0, 1)[:, None] * 0.9)
    m.data.vertices.foreach_set("co", cur.ravel()); m.data.update()
    # ③ 칼이 앞에서 들어온다
    c_ = 부드(단(f, T["깎기"], T["깎기끝"])); 칼.location.y = 눈.y - 폭 * 1.5 + 폭 * 1.5 * c_
    # ④ 판이 하나씩 내려와 붙는다
    for k, o in enumerate(판들):
        g = 부드(단(f, T["판"] + k * (T["판끝"] - T["판"]) // 3, T["판"] + (k + 1) * (T["판끝"] - T["판"]) // 3))
        o.hide_render = g <= 0; o.location = (얼x, 부리.y - 폭 * 0.08 * k, 부리.z - 폭 * 0.3 * k + 폭 * 0.6 * (1 - g))
    # 붓
    붓.hide_render = False
    if f < T["보기끝"]: 붓.hide_render = True
    elif f < T["다듬끝"]:
        q = (Vector(앞) + Vector((0, -폭 * 0.1, -폭 * 0.1))) if s < 0.5 else (가슴 + Vector((0, -폭 * 0.9, 0)))
        붓.location = q + Vector((폭 * 0.4 * math.cos(f * 0.4), 0, 폭 * 0.3 * math.sin(f * 0.4)))
    elif f < T["깎기끝"]: 붓.location = (눈.x, 앞[1] - 폭 * 0.1, 눈.z)
    elif f < T["판끝"]: 붓.location = (얼x, 부리.y - 폭 * 0.3, 부리.z)
    else: 붓.hide_render = True
    o_ = 부드(단(f, T["궤도"], T["끝"] - 1)); 카메라(-0.55 + 0.06 * math.sin(f / 40) - 1.0 * o_)
    sc.render.filepath = os.path.join(출, "f%04d.png" % f); bpy.ops.render.render(write_still=True)
print("프레임", 총)
