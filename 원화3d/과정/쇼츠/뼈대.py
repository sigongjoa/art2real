# -*- coding: utf-8 -*-
"""쇼츠 「이 세 피규어, 뼈대가 똑같습니다」 장면 렌더 (10-07) — Workbench 점토 · 1000×860.
blender -b --factory-startup --python 원화3d/과정/쇼츠/뼈대.py -- <장면> <출력.png>
  깔기   : Dummy 13 부품을 뼈대(회색) · 갑옷(주황) · 손(파랑) 무리로 판에 깐다
  머리   : Dummy 13 frame-head(회색) 와 블랙나이트 frame-head(주황) 를 나란히 + 겹침
라이선스: Dummy 13 (CC BY) · 블랙나이트 D13 (CC BY-SA) — 설명란에 출처."""
import bpy, sys, os, glob, math
from mathutils import Vector
R = "G:/art2real/원화3d/out/레퍼런스/사람분할/"
FRAME, ARMOR, HAND = (0.62, 0.64, 0.68, 1), (0.98, 0.55, 0.18, 1), (0.35, 0.6, 0.95, 1)

def scene():
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"; sc.render.resolution_x, sc.render.resolution_y = 1000, 860
    sh = sc.display.shading; sh.light = "STUDIO"; sh.color_type = "OBJECT"; sh.show_cavity = True; sh.cavity_type = "BOTH"; sh.show_shadows = True
    sc.render.film_transparent = False; sc.world = bpy.data.worlds.new("w"); sh.background_type = "VIEWPORT"; sh.background_color = (0.05, 0.05, 0.06)
    return sc

def load(path, color):
    n0 = set(bpy.data.objects)
    try: bpy.ops.wm.stl_import(filepath=path)
    except AttributeError: bpy.ops.import_mesh.stl(filepath=path)
    o = [x for x in bpy.data.objects if x not in n0][0]; o.color = color
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS"); o.location = (0, 0, 0); o.select_set(False)
    return o

def camera(target, size, tilt=35):
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); bpy.context.scene.collection.objects.link(cam)
    cam.data.type = "ORTHO"; cam.data.ortho_scale = size
    t = math.radians(tilt); cam.location = Vector(target) + Vector((0, -math.sin(t), math.cos(t))) * 500
    cam.rotation_euler = (t, 0, 0); cam.data.clip_end = 5000; bpy.context.scene.camera = cam

def 깔기():
    fs = sorted(glob.glob(R + "981111_Dummy13/**/*.stl", recursive=True))
    skip = ("all-", "runner-", "adapter-")
    rows = {"frame": [], "armor": [], "hand": []}
    for f in fs:
        n = os.path.basename(f).lower()
        if n.startswith(skip): continue
        k = "frame" if n.startswith("frame") else "armor" if n.startswith("armor") else "hand"
        rows[k].append(load(f, {"frame": FRAME, "armor": ARMOR, "hand": HAND}[k]))
    # 무리마다 줄을 채워 깐다(폭 W 넘으면 다음 줄) · 무리 사이 틈
    W, gap, y = 230, 4, 0
    for k in ("frame", "hand", "armor"):
        x, rowh = 0, 0
        for o in sorted(rows[k], key=lambda o: -o.dimensions.y):
            d = o.dimensions
            if x + d.x > W: x, y, rowh = 0, y - rowh - gap, 0
            o.location = (x + d.x / 2, y - d.y / 2, d.z / 2); x += d.x + gap; rowh = max(rowh, d.y)
        y -= rowh + 14
    print("부품", {k: len(v) for k, v in rows.items()})
    camera((W / 2, y / 2, 0), max(W, -y) * 1.08)

def 머리():
    a = load(glob.glob(R + "981111_Dummy13/**/frame-head.stl", recursive=True)[0], FRAME)
    b = load(glob.glob(R + "1630920_블랙나이트_D13/**/frame-head.stl", recursive=True)[0], ARMOR)
    a.location.x, b.location.x = -9, 9
    print("부피", round(a.dimensions.x, 1), round(b.dimensions.x, 1))
    camera((0, 0, 0), 34, tilt=50)

# 관절 표(10-07 · 위에서 본 윤곽의 원 검출 · 부품 좌표 u 가로 · v 세로 mm, 상자 왼쪽 아래 0)
#   공 반지름 3.0 · 소켓 2.1~2.2 · 무릎 · 팔꿈치 경첩 핀 두 개는 6 mm 간격
J = {"head": {"아래소켓": (4.5, 2.2)}, "neck": {"위공": (3, 13.0), "아래공": (3, 3.1)},
     "chest": {"위소켓": (9, 22.3), "아래소켓": (9, 2.2), "왼공": (15, 16.3), "오른공": (3, 16.3)},
     "abdomen": {"위공": (4.5, 15.3), "아래소켓": (4.5, 2.3)}, "waist": {"위공": (4.5, 13.2), "아래소켓": (4.5, 2.2)},
     "hips": {"가운데공": (11, 3.0), "왼공": (18.9, 2.9), "오른공": (2.9, 3.0)},
     "hip-and-shoulder-4x": {"소켓": (4.5, 9.9), "원판": (4.5, 1.2)}, "clavicle-2x": {"소켓": (4.5, 2.2), "공": (4.5, 9.2)},
     "thigh-2x": {"홈": (3.9, 23.0), "핀": (3.9, 2.6)}, "upper-arm-2x": {"홈": (3.9, 15.1), "핀": (3.9, 2.5)},
     "shin-2x": {"핀": (3, 31.0), "공": (3, 3.1)}, "forearm-2x": {"핀": (3, 18.0), "공": (3, 3.1)},
     "knee-and-elbow-4x": {"위": (4.5, 4.6), "아래": (10.5, 4.6)}, "ankle-2x": {"소켓": (4.5, 7.0)}}

def part(name, color=FRAME, d13="981111_Dummy13"):
    """부품을 싣고 원점을 상자 왼쪽 아래(두께는 가운데)로 — 그러면 관절 표 (u, v) 가 그대로 로컬 좌표."""
    n0 = set(bpy.data.objects)
    p = glob.glob(R + d13 + "/**/frame-" + name + ".stl", recursive=True)[0]
    try: bpy.ops.wm.stl_import(filepath=p)
    except AttributeError: bpy.ops.import_mesh.stl(filepath=p)
    o = [x for x in bpy.data.objects if x not in n0][0]; o.color = color
    lo = Vector([min(v.co[i] for v in o.data.vertices) for i in range(3)]); hi = Vector([max(v.co[i] for v in o.data.vertices) for i in range(3)])
    shift = Vector((-lo.x, -lo.y, -(lo.z + hi.z) / 2))
    for v in o.data.vertices: v.co += shift
    o.rotation_mode = "XYZ"; return o

def put(o, uv, world, spin=0.0, side=False):
    """로컬 (u, v) 점을 world(X, Z) 에 둔다. 출력면(로컬 xy)을 정면(XZ)으로 세우고, spin 은 그 면 안에서 도는 각(도).
    side=True 면 팔다리처럼 면을 옆(YZ)으로 돌린다(경첩 축이 좌우 → 앞뒤로 굽음)."""
    from mathutils import Matrix
    M = Matrix.Rotation(math.radians(90), 4, "X")                       # 로컬 y → 위(Z)
    M = Matrix.Rotation(math.radians(spin), 4, "Y") @ M                 # 정면 안에서 돌기
    if side: M = Matrix.Rotation(math.radians(90), 4, "Z") @ M
    p = (M @ Vector((uv[0], uv[1], 0, 1))).xyz
    o.matrix_world = Matrix.Translation(Vector((world[0], 0, world[1])) - p) @ M

def 뼈대(color=FRAME):
    """머리부터 발까지 공 중심 = 소켓 중심으로 잇는다(차렷). 반환: 부품 목록 · 손목 공 자리."""
    W = {}; Z0 = 100.0
    def at(name, key, world, spin=0.0, side=False, uvoff=None):
        o = part(name, color); uv = J[name][key]; put(o, uv, world, spin, side)
        return o, (lambda k: tuple((o.matrix_world @ Vector((J[name][k][0], J[name][k][1], 0))).xz))
    ch, C = at("chest", "아래소켓", (0, Z0 + 2.2 - 2.2 + 2.2)); W["chest"] = ch
    nk, N = at("neck", "아래공", C("위소켓")); hd, _ = at("head", "아래소켓", N("위공"))
    ab, A = at("abdomen", "위공", C("아래소켓")); wa, Wa = at("waist", "위공", A("아래소켓")); hp, H = at("hips", "가운데공", Wa("아래소켓"))
    wrist = []
    for s in (+1, -1):
        hs, HS = at("hip-and-shoulder-4x", "소켓", H("왼공" if s > 0 else "오른공"))
        th, T = at("thigh-2x", "홈", HS("원판"), side=True)
        for dy in (-1, 1):   # 경첩 판은 다리 양옆에 하나씩
            kn, _ = at("knee-and-elbow-4x", "위", T("핀"), spin=90, side=True); kn.location.x += dy * 4.2
        sh, S_ = at("shin-2x", "핀", (T("핀")[0], T("핀")[1] - 6.0), side=True)
        an, _ = at("ankle-2x", "소켓", S_("공"))
        cl, CL = at("clavicle-2x", "소켓", C("왼공" if s > 0 else "오른공"), spin=90 * s)
        so, SO = at("hip-and-shoulder-4x", "소켓", CL("공"))
        ua, U = at("upper-arm-2x", "홈", SO("원판"), side=True)
        for dy in (-1, 1):
            el, _ = at("knee-and-elbow-4x", "위", U("핀"), spin=90, side=True); el.location.x += dy * 4.2
        fa, F_ = at("forearm-2x", "핀", (U("핀")[0], U("핀")[1] - 6.0), side=True)
        wrist.append((s, F_("공")))
    return wrist

def 조립(yaw=0):
    wrist = 뼈대()
    for s, (x, z) in wrist:   # 손: 상자 위 가운데를 손목 공에(근사 — 손 소켓은 아직 안 잼)
        o = load(glob.glob(R + "981111_Dummy13/**/hand-fist-%s.stl" % ("left" if s > 0 else "right"), recursive=True)[0], HAND)
        o.rotation_euler = (math.radians(90), 0, 0); bpy.context.view_layer.update(); o.location = (x, 0, z - o.dimensions.z / 2 + 1.5)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); bpy.context.scene.collection.objects.link(cam)
    cam.data.type = "ORTHO"; cam.data.ortho_scale = 160; t = math.radians(yaw)
    cam.location = (300 * math.sin(t), -300 * math.cos(t), 70); cam.rotation_euler = (math.radians(90), 0, t); bpy.context.scene.camera = cam

J_D13 = "G:/art2real/원화3d/out/쇼츠/뼈대/갑옷_D13.json"
FLIP = set(os.environ.get("FLIP", "").split(",")) - {""}
ROT = dict((a, (b, float(c))) for a, b, c in (x.split(":") for x in os.environ.get("ROT", "").split(",") if x))   # 이름@쪽:축:도 — 제자리 돌리기
MOVE = dict((a, tuple(map(float, b.split("/")))) for a, b in (x.split(":") for x in os.environ.get("MOVE", "").split(",") if x))   # 이름@쪽:dx/dy/dz
SKIP = set(os.environ.get("SKIP", "").split(",")) - {""}   # 갑옷 이름@쪽 → 뼈대 세로축 둘레로 180° (맞춤 점수가 앞뒤를 못 가른 것 · 렌더 보고 채움)

def 갑옷(fit_json, d13="981111_Dummy13", yaw=0, frame=True, zoom=None, palette=False):
    import json
    from mathutils import Matrix
    if frame: 뼈대()
    for r in json.load(open(fit_json, encoding="utf-8")):
        if r["갑옷"] + "@" + r["쪽"] in SKIP or r["갑옷"] in SKIP: continue
        n0 = set(bpy.data.objects); p = R + d13 + "/armor-%s.stl" % r["갑옷"]
        try: bpy.ops.wm.stl_import(filepath=p)
        except AttributeError: bpy.ops.import_mesh.stl(filepath=p)
        o = [x for x in bpy.data.objects if x not in n0][0]; o.color = ARMOR   # 파일 좌표 그대로 — 맞춤 M 이 파일 좌표 기준
        M = Matrix(r["M"]); key = r["갑옷"] + "@" + r["쪽"]
        if key in FLIP:   # 덮는 뼈대 중심을 지나는 세로축으로 180°
            c = M @ (sum((Vector(b) for b in o.bound_box), Vector()) / 8)
            M = Matrix.Translation(c) @ Matrix.Rotation(math.pi, 4, "Z") @ Matrix.Translation(-c) @ M
        if key in ROT:
            c = M @ (sum((Vector(b) for b in o.bound_box), Vector()) / 8); ax, deg = ROT[key]
            M = Matrix.Translation(c) @ Matrix.Rotation(math.radians(deg), 4, ax) @ Matrix.Translation(-c) @ M
        if r["쪽"] == "C":   # 가운데 부품은 좌우 대칭 — 맞춤이 옆으로 비낀 것을 바로잡는다
            c = M @ (sum((Vector(b) for b in o.bound_box), Vector()) / 8); M = Matrix.Translation(Vector((-c.x, 0, 0))) @ M
        o.matrix_world = M
        if palette:   # 부품마다 다른 색(앞뒤 가리기용)
            import colorsys; i = abs(hash(r["갑옷"])) % 12; o.color = (*colorsys.hsv_to_rgb(i / 12, 0.7, 0.95), 1); print("색", r["갑옷"], r["쪽"], [round(c, 2) for c in o.color[:3]])
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); bpy.context.scene.collection.objects.link(cam)
    cam.data.type = "ORTHO"; cam.data.ortho_scale = zoom[0] if zoom else 160; t = math.radians(yaw)
    cam.location = (300 * math.sin(t), -300 * math.cos(t), zoom[1] if zoom else 76); cam.rotation_euler = (math.radians(90), 0, t); bpy.context.scene.camera = cam

COL = {"d13": (0.98, 0.55, 0.18, 1), "bk": (0.30, 0.31, 0.35, 1), "bs": (0.45, 0.37, 0.30, 1)}
def 입힘(model, yaw=0, zoom=None, frame=True):
    """갑옷맞춤.py 가 월드 좌표로 저장한 STL 을 불러온다. ROT · SKIP 은 이름@쪽, 가운데(C) 부품은 좌우 중심 0."""
    import json
    from mathutils import Matrix
    # 렌더 보고 고친 것(10-07): D13 허리 갑옷 180° · 베르세르크 가슴 반쪽 둘은 정면 가운데로 겹쳐 뺌 · 블랙나이트 투구 6 mm 내림
    DEF = {"d13": ({"armor-waist@C": ("Z", 180.0)}, {}, set()), "bk": ({}, {"armor-helmet@C": (0, 0, -6.0)}, set()),
           "bs": ({}, {}, {"2-chestplate-v3-hotfix#0", "2-chestplate-v3-hotfix#1"})}[model]
    ROT_, MOVE_, SKIP_ = {**DEF[0], **ROT}, {**DEF[1], **MOVE}, DEF[2] | SKIP
    if frame: 뼈대()
    armor = []
    for r in json.load(open("G:/art2real/원화3d/out/쇼츠/뼈대/입힘_%s/목록.json" % model, encoding="utf-8")):
        key = r["갑옷"] + "@" + r["쪽"]
        if key in SKIP_ or r["갑옷"] in SKIP_: continue
        n0 = set(bpy.data.objects)
        try: bpy.ops.wm.stl_import(filepath=r["파일"])
        except AttributeError: bpy.ops.import_mesh.stl(filepath=r["파일"])
        o = [x for x in bpy.data.objects if x not in n0][0]; o.color = HAND if r.get("손") and model != "bs" else COL[model]
        c = sum((Vector(b) for b in o.bound_box), Vector()) / 8; M = Matrix.Identity(4)
        if key in ROT_: ax, deg = ROT_[key]; M = Matrix.Translation(c) @ Matrix.Rotation(math.radians(deg), 4, ax) @ Matrix.Translation(-c)
        if r["쪽"] == "C": M = Matrix.Translation(Vector((-(M @ c).x, 0, 0))) @ M
        if key in MOVE_: M = Matrix.Translation(Vector(MOVE_[key])) @ M
        o.matrix_world = M; armor.append(o)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); bpy.context.scene.collection.objects.link(cam)
    cam.data.type = "ORTHO"; cam.data.ortho_scale = zoom[0] if zoom else 175; t = math.radians(yaw)
    cam.location = (300 * math.sin(t), -300 * math.cos(t), zoom[1] if zoom else 76); cam.rotation_euler = (math.radians(90), 0, t); bpy.context.scene.camera = cam
    return armor

def 벗기기(model, prefix, n=30, yaw=20, reverse=False):
    """갑옷이 몸 밖으로 날아가 사라진다(reverse = 날아와 입는다). 프레임 n 장 → prefix_00.png …"""
    armor = 입힘(model, yaw=yaw); bpy.context.view_layer.update()
    home = {o.name: o.matrix_world.copy() for o in armor}
    for i in range(n):
        u = i / (n - 1); u = 1 - u if reverse else u; e = u * u * (3 - 2 * u)   # 부드럽게
        for o in armor:
            c = home[o.name] @ (sum((Vector(b) for b in o.bound_box), Vector()) / 8)
            d = Vector((c.x * 1.4, -18, (c.z - 75) * 0.6)); d = d.normalized() if d.length > 1e-6 else Vector((0, -1, 0))
            from mathutils import Matrix
            o.matrix_world = Matrix.Translation(d * e * 70) @ home[o.name]; o.hide_render = e > 0.97
        bpy.context.scene.render.filepath = "%s_%02d.png" % (prefix, i); bpy.ops.render.render(write_still=True)

def 내보내기(out):
    """조립한 뼈대를 월드 좌표로 npz 에(이름@쪽 → 점 · 면). 갑옷 맞춤(갑옷맞춤.py)이 읽는다."""
    import numpy as np
    뼈대(); bpy.context.view_layer.update(); D = {}
    for o in bpy.data.objects:
        if o.type != "MESH": continue
        Mw = o.matrix_world; v = np.array([(Mw @ x.co)[:] for x in o.data.vertices]); f = np.array([p.vertices[:] for p in o.data.polygons])
        side = "L" if v[:, 0].mean() > 3 else "R" if v[:, 0].mean() < -3 else "C"
        k = o.name.split(".")[0].replace("frame-", "") + "@" + side; i = 0
        while "%s#%d" % (k, i) in D: i += 1
        D["%s#%d" % (k, i)] = (v, f)
    np.savez(out, **{k + "|v": v for k, (v, f) in D.items()}, **{k + "|f": f for k, (v, f) in D.items()}); print("내보냄", len(D), sorted(D)[:40])

if __name__ == "__main__":
    which, out = sys.argv[sys.argv.index("--") + 1:][:2]
    if which == "내보내기": 내보내기(out); sys.exit(0)
    scene()
    if which.startswith("벗기기"):   # 벗기기:모델:프레임수[:입기]
        a = which.split(":"); 벗기기(a[1], out, int(a[2]), reverse=len(a) > 3); sys.exit(0)
    if which.startswith("입힘"):   # 입힘:모델[:yaw]
        a = which.split(":"); 입힘(a[1], yaw=float(a[2]) if len(a) > 2 else 0, zoom=(float(a[3]), float(a[4])) if len(a) > 4 else None)
    else: {"깔기": 깔기, "머리": 머리, "조립": 조립, "조립34": lambda: 조립(35),
     "갑옷": lambda: 갑옷(J_D13), "갑옷34": lambda: 갑옷(J_D13, yaw=35), "갑옷뒤": lambda: 갑옷(J_D13, yaw=180),
     "몸앞": lambda: 갑옷(J_D13, yaw=0, zoom=(70, 95), palette=True), "몸뒤": lambda: 갑옷(J_D13, yaw=180, zoom=(70, 95), palette=True),
     "골반": lambda: 갑옷(J_D13, yaw=0, zoom=(50, 80))}[which]()
    bpy.context.scene.render.filepath = out; bpy.ops.render.render(write_still=True); print("저장", out)
