# -*- coding: utf-8 -*-
"""블렌더 안에서 실행 (MCP execute_blender_code 로 exec) — 블록아웃.json 을 읽어 카메라 6 + 겹 부품 시작 도형을 만들고 세 카메라로 렌더한다.
   코드가 메시를 짓는 게 아니라 블렌더 도구를 누른다: 기본 도형 · 볼록 껍질 · 솔리디파이 · 직교 카메라 · 배경 그림 · 워크벤치 렌더."""
import bpy, bmesh, json, os
from mathutils import Vector, Matrix
B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"; 스펙 = json.load(open(os.path.join(B, "블록아웃.json"), encoding="utf-8"))
# 0 씬 비우기
bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections): bpy.data.collections.remove(c)
def 컬렉션(n):
    c = bpy.data.collections.new(n); bpy.context.scene.collection.children.link(c); return c
C카 = 컬렉션("카메라"); C부 = 컬렉션("겹부품"); C참 = 컬렉션("참고")
# 1 카메라(직교 · 배경 그림)
for k in 스펙["카메라"]:
    cam = bpy.data.cameras.new(k["이름"]); cam.type = "ORTHO"; cam.ortho_scale = k["ortho_scale"]; cam.sensor_fit = "HORIZONTAL"; cam.clip_start = 1; cam.clip_end = 2000
    ob = bpy.data.objects.new("카메라_" + k["이름"], cam); C카.objects.link(ob); ob.matrix_world = Matrix(k["행렬"])
    img = bpy.data.images.load(k["파일"]); bg = cam.background_images.new(); bg.image = img; bg.alpha = 0.6; bg.frame_method = "FIT"; cam.show_background_images = True
    ob["W"], ob["H"] = k["W"], k["H"]
# 2 겹 부품
def 재질(n, rgb):
    m = bpy.data.materials.new(n); m.diffuse_color = (*rgb, 1); return m
색 = {"소체": (0.25, 0.25, 0.28), "부리": (0.9, 0.9, 0.92), "눈L": (0.1, 0.3, 0.8), "눈R": (0.1, 0.3, 0.8), "볼날개L": (0.85, 0.85, 0.9), "볼날개R": (0.85, 0.85, 0.9), "뿔": (0.8, 0.8, 0.85), "안테나L": (0.85, 0.7, 0.2), "안테나R": (0.85, 0.7, 0.2)}
def 새메시(n, bm):
    me = bpy.data.meshes.new(n); bm.to_mesh(me); bm.free(); ob = bpy.data.objects.new(n, me); C부.objects.link(ob); ob.data.materials.append(재질(n, 색.get(n, (0.7, 0.7, 0.7)))); ob["출처"] = ""; return ob
for p in 스펙["부품"]:
    bm = bmesh.new()
    if p["꼴"] == "타원체":
        bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.0); r = p["반지름B"]; bmesh.ops.scale(bm, vec=(r[0], r[1], r[2]), verts=bm.verts); bmesh.ops.translate(bm, vec=p["중심B"], verts=bm.verts)
    elif p["꼴"] == "껍질":
        vs = [bm.verts.new(Vector(q)) for q in p["점B"]]; bmesh.ops.convex_hull(bm, input=vs)
    elif p["꼴"] == "판":
        vs = [bm.verts.new(Vector(q)) for q in p["점B"]]; bm.faces.new(vs)
    elif p["꼴"] == "원뿔":
        a, b = Vector(p["밑B"]), Vector(p["끝B"]); d = b - a; L = d.length; R = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=p["반지름"], radius2=0.5, depth=L); bmesh.ops.translate(bm, vec=(0, 0, L / 2), verts=bm.verts); bmesh.ops.transform(bm, matrix=R, verts=bm.verts); bmesh.ops.translate(bm, vec=a, verts=bm.verts)
    ob = 새메시(p["이름"], bm); ob["출처"] = p["출처"]
    if p["꼴"] == "판":
        m = ob.modifiers.new("두께", "SOLIDIFY"); m.thickness = p["두께"]; m.offset = 0
# 3 참고: 시각 껍질(와이어 · 숨김)
if os.path.exists(스펙["껍질"]):
    bpy.ops.import_mesh.stl(filepath=스펙["껍질"]); h = bpy.context.selected_objects[0]; h.name = "껍질_참고"
    for c in h.users_collection: c.objects.unlink(h)
    C참.objects.link(h); h.matrix_world = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, -1, 0, 0), (0, 0, 0, 1))); h.display_type = "WIRE"; h.hide_render = True; h.hide_viewport = True
# 4 세 카메라 워크벤치 렌더(투명 배경) → PNG
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sc.render.film_transparent = True; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"; sc.display.shading.show_object_outline = True
for n in ("02_정면", "02_3-4", "02_옆"):
    ob = bpy.data.objects["카메라_" + n]; sc.camera = ob; sc.render.resolution_x = ob["W"]; sc.render.resolution_y = ob["H"]; sc.render.resolution_percentage = 100
    sc.render.filepath = os.path.join(B, "렌더_" + n + ".png"); bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(B, "오메가몬_블록아웃.blend"))
print("완료", [o.name for o in C부.objects])
