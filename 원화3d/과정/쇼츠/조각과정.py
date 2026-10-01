# -*- coding: utf-8 -*-
"""조각 과정 타임랩스 — 기본형에서 더하고 깎는다(10-01 「기본형을 만들고 이거를 깎거나 더하거나 해야지」).
    blender -b --factory-startup -P 조각과정.py -- <출력폴더> [총프레임=534]  -> f0000.png … (Workbench 점토 · 1080×880)
단계(치수는 과정/머리/값.json · 블렌더/부리점.json — 잰 값):
  ① 기본형: 구 → 투구 비율(폭 ±39.7 · 앞뒤 28.5 · 높이 28)
  ② 더하기: 얼굴 아래 덩어리 → 붓으로 앞으로 당겨 부리(끝 = 부리점 z앞 최대 · 두 장 시차가 말한 「부리가 앞」)
  ③ 깎기: 상자 칼이 들어와 눈구멍을 판다(불리언 차 · 좌우 거울)
  ④ 더하기: 뿔이 자란다(밑 · 끝 = 정면 면 1 측정)
  ⑤ 옆으로 돌아 부리가 앞인 걸 본다
좌표: 머리 단위(뿔 끝 0 · 턱 100) · 블렌더 = (x, −z, −y) → 앞 = −y, 위 = +z."""
import sys, os, math, json, numpy as np, bpy, bmesh
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; 출 = a[0]; 총 = int(a[1]) if len(a) > 1 else 534; os.makedirs(출, exist_ok=True)
값 = json.load(open(r"G:\art2real\원화3d\과정\머리\값.json", encoding="utf-8"))
부리 = json.load(open(r"G:\art2real\원화3d\out\오메가몬2\블렌더\부리점.json", encoding="utf-8"))["줄"]
끝 = max(부리, key=lambda r: r["z앞"]); 부리끝y, 부리끝z = -끝["z앞"], -끝["y"]                     # 블렌더 y(앞 = −), z

bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "MATCAP"; sh.color_type = "OBJECT"; sh.show_cavity = True
sc.render.resolution_x, sc.render.resolution_y = 1080, 880
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.02, 0.02, 0.025)
점토 = (0.86, 0.83, 0.78, 1)
def 단(t, a, b): return max(0.0, min(1.0, (t - a) / (b - a)))
def 부드(x): return 0.5 - 0.5 * math.cos(math.pi * x)

# ① 기본형
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.0, location=(0, 33.5, -28)); 투구 = bpy.context.active_object; 투구.color = 점토
bpy.ops.object.shade_smooth()
# ② 얼굴 덩어리(잘게 나눈 상자 → 붓으로 당긴다)
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 14, -74)); 얼굴 = bpy.context.active_object; 얼굴.color = 점토
bm = bmesh.new(); bm.from_mesh(얼굴.data); bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=8, use_grid_fill=True); bm.to_mesh(얼굴.data); bm.free()
얼굴.modifiers.new("매끈", "SUBSURF").levels = 2; bpy.ops.object.shade_smooth()
얼굴.scale = (13, 13, 24); 원 = np.array([v.co[:] for v in 얼굴.data.vertices])                  # 지역 좌표(−1..1)
# ③ 뿔: 밑이 원점인 네모 원뿔
v = 값["뿔"]; x, y밑 = v["밑"]; 밑 = Vector((x, 10.0, -y밑)); 뿔끝 = Vector((x, -4.0, -v["끝y"])); d = 뿔끝 - 밑
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=max(6.0, v["반지름"] * 2), radius2=0.3, depth=d.length, location=(0, 0, 0)); 뿔 = bpy.context.active_object; 뿔.color = 점토
for vv in 뿔.data.vertices: vv.co.z += d.length / 2
뿔.location = 밑; 뿔.rotation_mode = "QUATERNION"; 뿔.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
# ④ 눈구멍 칼(렌더에 안 보임) + 불리언
x0, x1, y0, y1 = 값["눈구멍L_상자"]
bpy.ops.mesh.primitive_cube_add(size=1.0, location=((x0 + x1) / 2, -30.0, -(y0 + y1) / 2)); 칼 = bpy.context.active_object; 칼.scale = (x1 - x0, 24.0, y1 - y0); 칼.hide_render = True
mm = 칼.modifiers.new("거울", "MIRROR"); mm.use_axis[0] = True; mm.mirror_object = 투구
b = 투구.modifiers.new("눈구멍", "BOOLEAN"); b.operation = "DIFFERENCE"; b.object = 칼; b.solver = "EXACT"
# 붓 고리
bpy.ops.mesh.primitive_torus_add(major_radius=9, minor_radius=0.8, rotation=(math.pi / 2, 0, 0)); 붓 = bpy.context.active_object; 붓.color = (1, 0.9, 0.2, 1)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 50
중심 = Vector((0, 22, -40))
def 카메라(각, 높이=0.18, 거리=255):
    p = 중심 + Vector((math.sin(각), -math.cos(각), 높이)) * 거리; cam.location = p; cam.rotation_euler = (중심 - p).to_track_quat("-Z", "Y").to_euler()

# 시간표(총 프레임 비율)
T = {k: int(총 * r) for k, r in dict(기본=0.0, 기본끝=0.06, 얼굴=0.07, 얼굴끝=0.10, 부리끝=0.27, 깎기=0.28, 깎기끝=0.40, 뿔=0.44, 뿔끝=0.58, 궤도=0.62, 끝=1.0).items()}
for f in range(총):
    # ① 구 → 투구 비율
    s = 부드(단(f, T["기본"], T["기본끝"])); r0 = 22.0
    투구.scale = (r0 + (39.7 - r0) * s, r0 + (28.5 - r0) * s, r0 + (28.0 - r0) * s)
    # ② 얼굴 덩어리 등장 → 앞으로 당겨 부리
    g = 부드(단(f, T["얼굴"], T["얼굴끝"])); 얼굴.hide_render = g <= 0; 얼굴.scale = (13 * g + 1e-3, 13 * g + 1e-3, 24 * g + 1e-3)
    p = 부드(단(f, T["얼굴끝"], T["부리끝"]))
    co = 원.copy(); 앞 = np.clip(-co[:, 1], 0, 1)                                               # 앞면일수록 1
    w = np.exp(-((co[:, 2] * 24 - 0) / 14.0) ** 2) * 앞                                         # 덩어리 가운데 높이(부리 끝 근처)
    co[:, 1] -= p * w * (1 - 부리끝y) / 13                                                      # 당김: 앞면(y 1) → 부리끝y
    co[:, 0] *= 1 - 0.45 * p * w                                                                # 끝으로 갈수록 좁게(칼날)
    얼굴.data.vertices.foreach_set("co", co.ravel()); 얼굴.data.update()
    # ③ 뿔 자람
    h = 부드(단(f, T["뿔"], T["뿔끝"])); 뿔.hide_render = h <= 0; 뿔.scale = (1, 1, max(h, 1e-3))
    # ④ 칼이 들어와 눈구멍
    c = 부드(단(f, T["깎기"], T["깎기끝"])); 칼.location.y = -30.0 + 42.0 * c                                         # 끝 y 12: 칼 뒷면 24 가 둥근 앞면(눈 자리 y≈19)을 5 쯤 판다
    # 붓 위치
    붓.hide_render = False
    if f < T["기본끝"]: 붓.location = (24 * math.cos(f * 0.3), 33.5 - 30 * 1, -28 + 20 * math.sin(f * 0.3))
    elif f < T["부리끝"]: 붓.location = (3 * math.cos(f * 0.5), float(1 - p * (1 - 부리끝y)) - 6, 부리끝z + 4 * math.sin(f * 0.5))
    elif f < T["깎기끝"]: 붓.location = ((x0 + x1) / 2, 6, -(y0 + y1) / 2)
    elif f < T["뿔"]: 붓.hide_render = True
    elif f < T["뿔끝"]: 붓.location = tuple(밑 + d * h + Vector((0, -4, 0)))
    else: 붓.hide_render = True
    # 카메라: 3/4 에서 살짝 흔들다 끝에 옆으로
    o = 부드(단(f, T["궤도"], T["끝"] - 1))
    카메라(-0.55 + 0.08 * math.sin(f / 40) - 0.95 * o + 0.0)
    sc.render.filepath = os.path.join(출, "f%04d.png" % f); bpy.ops.render.render(write_still=True)
print("프레임", 총)
