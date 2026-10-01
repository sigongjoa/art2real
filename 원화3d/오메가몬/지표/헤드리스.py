# -*- coding: utf-8 -*-
"""헤드리스 블렌더 도우미 (2026-10-01 밤 패널 자가 개선 1) — 오늘 같은 스크립트를 일곱 번 다시 쓰다 축을 세 번 뒤집었다.
    blender -b -P 헤드리스.py                      → 축 마커 자가검사 렌더 3 장(out/오메가몬2/지표/_축검사_*.png)
    blender -b -P 내스크립트.py  (안에서)          import sys; sys.path.insert(0, r"G:\\art2real\\원화3d\\오메가몬\\지표"); import 헤드리스 as H
좌표 약속(머리 단위 · 뿔 끝 0 · 턱 100): 그림 (x 오른 +, y 아래 +, z 앞 +)  ⇄  블렌더 (x, -z앞, -y).  H.M 이 그 변환.
뷰: H.look(center, yaw, pitch, ortho) — yaw 0 = 정면(앞에서) · 90 = 오른쪽 옆(얼굴이 왼쪽) · 40/12 = 3/4. 세계 축을 직접 쓰지 말고 이 함수만 쓴다.
비싼 것 앞에 싼 확인: H.axis_check() 한 장을 먼저 본다(09-20 메모리). 불리언은 H.boolean() 으로 — 결과가 안 줄면 assert 로 멈춘다(10-01 EXACT 조용한 실패).
점 상한: H.subdivide(obj, max_verts=60000) — 13만 점 + Freestyle 로 세션이 죽었다(10-01). 10 분 넘는 일은 포그라운드에서 한 단계씩."""
import bpy, bmesh, os, math, mathutils

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(R, "out", "오메가몬2", "지표")
M = mathutils.Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))   # 그림(x, y아래, z앞) → 블렌더
BG = (0.02, 0.02, 0.03)

def scene(res=(1000, 860), transparent=True, cavity=True):
    """빈 장면 + Workbench(스튜디오 · 오브젝트 색 · 캐비티). 반환 sc."""
    bpy.ops.wm.read_homefile(use_empty=True); sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.color_type = "OBJECT"; sh.show_cavity = cavity; sh.cavity_type = "BOTH"
    sc.world = bpy.data.worlds.new("w"); sc.world.color = BG; sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.render.film_transparent = transparent; sc.render.image_settings.color_mode = "RGBA"
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); cam.data.type = "ORTHO"; cam.data.clip_end = 5000; sc.camera = cam
    return sc

def look(center=(0, 0, -50), yaw=0, pitch=0, ortho=130, dist=400):
    """center 는 블렌더 좌표. yaw 0 정면 · +90 오른쪽 옆(얼굴 왼쪽) · pitch + 위에서."""
    cam = bpy.context.scene.camera; y, p = math.radians(yaw), math.radians(pitch)
    d = mathutils.Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)))
    cam.location = mathutils.Vector(center) + d * dist; cam.rotation_euler = d.to_track_quat("Z", "Y").to_euler(); cam.data.ortho_scale = ortho

VIEWS = {"정면": (0, 0), "옆": (90, 0), "3/4": (40, 12), "3/4왼": (-40, 12)}

def shot(path):
    sc = bpy.context.scene; os.makedirs(os.path.dirname(path), exist_ok=True); sc.render.filepath = path; bpy.ops.render.render(write_still=True); return path

def swing(prefix, center, yaw0=0, yaw1=90, n=25, pitch=0, ortho=130):
    """정면 → 옆 흔들기 프레임. ffmpeg -framerate 8 -i prefix_%02d.png"""
    out = []
    for i in range(n):
        t = i / max(1, n - 1); look(center, yaw0 + (yaw1 - yaw0) * t, pitch * t, ortho); out.append(shot("%s_%02d.png" % (prefix, i)))
    return out

def load_obj(path, name=None, color=(0.91, 0.91, 0.93, 1), smooth=True):
    """그림 좌표(x, y아래, z앞)로 저장된 OBJ 를 블렌더 좌표로 싣는다."""
    bpy.ops.wm.obj_import(filepath=path, forward_axis="Y", up_axis="Z"); o = bpy.context.selected_objects[0]
    if name: o.name = name
    o.matrix_world = M; o.color = color
    if smooth:
        for pg in o.data.polygons: pg.use_smooth = True
    return o

def mesh_from(verts, faces, name, color=(0.91, 0.91, 0.93, 1)):
    """verts 는 그림 좌표 (x, y아래, z앞). 블렌더 좌표로 바꿔 넣는다."""
    me = bpy.data.meshes.new(name); me.from_pydata([(x, -z, -y) for x, y, z in verts], [], faces); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); o.color = color; return o

def subdivide(obj, levels=1, max_verts=60000):
    """SIMPLE 세분 — 점이 상한을 넘으면 멈춘다(메모리)."""
    n = len(obj.data.vertices) * (4 ** levels)
    assert n <= max_verts, "세분 뒤 점 %d > 상한 %d — levels 를 줄이거나 포그라운드로" % (n, max_verts)
    md = obj.modifiers.new("세분", "SUBSURF"); md.levels = levels; md.subdivision_type = "SIMPLE"; bpy.context.view_layer.objects.active = obj; bpy.ops.object.modifier_apply(modifier=md.name); return obj

def _bbox_vol(o):
    bb = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]; lo = mathutils.Vector(map(min, zip(*bb))); hi = mathutils.Vector(map(max, zip(*bb))); d = hi - lo; return d.x * d.y * d.z

def boolean(obj, cutter, op="INTERSECT", solver="EXACT", must_change=True):
    """불리언을 적용하고 결과가 바뀌었는지 검사한다. 10-01: EXACT 가 열린 프리즘에서 첫 피연산자를 그대로 돌려줬다(면 수 그대로)."""
    f0, v0 = len(obj.data.polygons), _bbox_vol(obj)
    md = obj.modifiers.new("b", "BOOLEAN"); md.operation = op; md.object = cutter; md.solver = solver
    bpy.context.view_layer.objects.active = obj; bpy.ops.object.modifier_apply(modifier=md.name)
    f1, v1 = len(obj.data.polygons), _bbox_vol(obj)
    if must_change and op == "INTERSECT":
        assert f1 != f0 or v1 < v0 * 0.999, "불리언이 아무것도 안 바꿨다(면 %d · 부피 %.0f) — 피연산자가 닫혔는지 확인 · 복셀 교집합(parts_hull_voxel.py)으로" % (f0, v0)
    return obj

def axis_check(out_dir=None):
    """축 마커(앞 = 빨강 화살 · 오른쪽 = 초록 · 위 = 파랑 · 턱 자리 흰 판)를 정면 · 옆 · 3/4 로 렌더. 정면에서 빨강이 보이고 옆에서 빨강이 왼쪽을 가리켜야 맞다."""
    out_dir = out_dir or OUT; sc = scene(transparent=False)
    def arrow(name, vec, color):
        bpy.ops.mesh.primitive_cone_add(radius1=4, depth=16); o = bpy.context.active_object; o.name = name; o.color = color
        o.rotation_euler = mathutils.Vector(vec).to_track_quat("Z", "Y").to_euler(); o.location = mathutils.Vector(vec) * 24
    arrow("앞", (0, -1, 0), (0.9, 0.15, 0.15, 1)); arrow("오른", (1, 0, 0), (0.15, 0.8, 0.2, 1)); arrow("위", (0, 0, 1), (0.2, 0.4, 0.95, 1))
    bpy.ops.mesh.primitive_cube_add(size=1); c = bpy.context.active_object; c.scale = (30, 30, 1); c.location = (0, 0, -100); c.color = (1, 1, 1, 1); c.name = "턱판"
    bpy.ops.mesh.primitive_uv_sphere_add(radius=6); s = bpy.context.active_object; s.location = (0, 0, 0); s.color = (0.9, 0.9, 0.2, 1); s.name = "뿔끝"
    paths = []
    for nm, (yaw, pitch) in VIEWS.items():
        if nm == "3/4왼": continue
        look((0, 0, -50), yaw, pitch, 160); paths.append(shot(os.path.join(out_dir, "_축검사_%s.png" % nm.replace("/", ""))))
    return paths

def composite_front(render_png, art_jpg, box, out_png, ortho=130, center_y=50):
    """정면 렌더(투명) 밑에 원화를 깐다. box = 원화 잘라낸 머리 단위 상자 {x0,x1,y0,y1}. 블렌더 밖(PIL)에서 돌려도 된다."""
    from PIL import Image
    fr = Image.open(render_png).convert("RGBA"); W, H = fr.size; sx = W / ortho; x0, y0 = -ortho / 2, center_y - (ortho * H / W) / 2
    art = Image.open(art_jpg).convert("RGBA").resize((int((box["x1"] - box["x0"]) * sx), int((box["y1"] - box["y0"]) * sx)))
    cv = Image.new("RGBA", (W, H), (40, 40, 60, 255)); cv.paste(art, (int((box["x0"] - x0) * sx), int((box["y0"] - y0) * sx)))
    Image.alpha_composite(cv, fr).convert("RGB").save(out_png); return out_png

if __name__ == "__main__":
    print(axis_check())
