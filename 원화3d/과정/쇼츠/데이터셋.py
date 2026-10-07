# -*- coding: utf-8 -*-
"""쇼츠 2편 「피규어 60개를 뜯어 보니」 장면 렌더 (10-07) — Workbench 점토 · 1000×860 · 뼈대.py 도우미를 쓴다.
blender -b --factory-startup --python 원화3d/과정/쇼츠/데이터셋.py -- <장면> <출력(.png 또는 프레임 접두)>
화면에 쓰는 모델은 라이선스가 열린 것만: 메가트론 키트(CC BY) · 콘치 로봇(CC BY-SA) · 폴아웃 로봇(LGPL)."""
import bpy, sys, os, glob, math, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 뼈대 as B
from mathutils import Vector
R = B.R
COLOR = {"RED": (0.85, 0.14, 0.12, 1), "LIGHTGREY": (0.80, 0.81, 0.84, 1), "BLACK": (0.20, 0.20, 0.23, 1), "PURPLE": (0.52, 0.25, 0.75, 1),
         "YELLOW": (0.98, 0.80, 0.15, 1), "없음": (0.55, 0.55, 0.58, 1)}
CLAY = (0.66, 0.66, 0.70, 1)

def pack(objs, W, gap=4):
    """판 위에 줄지어 깐다(긴 것부터). 반환: 전체 높이(음수 아래로)."""
    x, y, rowh = 0, 0, 0
    for o in sorted(objs, key=lambda o: -o.dimensions.y):
        d = o.dimensions
        if x + d.x > W and x > 0: x, y, rowh = 0, y - rowh - gap, 0
        o.location = (x + d.x / 2, y - d.y / 2, d.z / 2); x += d.x + gap; rowh = max(rowh, d.y)
    return y - rowh

def top_cam(cx, cy, size, tilt=30):
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); bpy.context.scene.collection.objects.link(cam)
    cam.data.type = "ORTHO"; cam.data.ortho_scale = size; t = math.radians(tilt)
    cam.location = Vector((cx, cy, 0)) + Vector((0, -math.sin(t), math.cos(t))) * 900; cam.rotation_euler = (t, 0, 0); cam.data.clip_end = 5000
    bpy.context.scene.camera = cam; return cam

def frame_all(margin=1.08):
    """깔린 부품 전체 상자에 맞춰 위에서 본다(1000×860 띠 · 세로가 길면 세로 기준)."""
    bpy.context.view_layer.update(); P = [o.matrix_world @ Vector(b) for o in bpy.data.objects if o.type == "MESH" for b in o.bound_box]
    x0, x1 = min(p.x for p in P), max(p.x for p in P); y0, y1 = min(p.y for p in P), max(p.y for p in P)
    rx, ry = bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y
    return top_cam((x0 + x1) / 2, (y0 + y1) / 2, max(x1 - x0, (y1 - y0) * rx / ry) * margin, tilt=0)

def color_of(n):
    m = re.findall(r"(RED|LIGHTGREY|BLACK|PURPLE|YELLOW)", n.upper()); return m[0] if m else "없음"

def 메가(colored):
    fs = [f for f in sorted(glob.glob(R + "334966_메가트론키트/**/*.stl", recursive=True)) if "face" not in os.path.basename(f).lower()]
    groups = {}
    for f in fs:
        k = color_of(os.path.basename(f)); groups.setdefault(k, []).append(B.load(f, COLOR[k] if colored else CLAY))
    # 색깔별 무더기(색 렌더) · 같은 자리에 회색(회색 렌더) — 두 장을 닦아 넘기면 색이 「칠해진다」
    W = 290; y = 0
    for k in ("LIGHTGREY", "BLACK", "RED", "PURPLE", "YELLOW", "없음"):
        if k not in groups: continue
        h = pack(groups[k], W, gap=3)
        for o in groups[k]: o.location.y += y
        y += h - 10
    frame_all()

def 얼굴():
    a = B.load(glob.glob(R + "334966_메가트론키트/**/face laughing.stl", recursive=True)[0], COLOR["LIGHTGREY"])
    b = B.load(glob.glob(R + "334966_메가트론키트/**/*FACE sneer.stl", recursive=True)[0], COLOR["LIGHTGREY"])
    dx = max(a.dimensions.x, b.dimensions.x); one = os.environ.get("FACEONE")   # 0 = 웃음만 · 1 = 비웃음만(닦아 넘기기용)
    if one is not None:
        bpy.data.objects.remove(b if one == "0" else a)
    else: a.location.x, b.location.x = -max(a.dimensions.x, b.dimensions.x) * 0.65, max(a.dimensions.x, b.dimensions.x) * 0.65
    cam = top_cam(0, 0, dx * (1.9 if os.environ.get("FACEONE") else 3.0), tilt=0)
    v = os.environ.get("FACEVIEW", "below")   # below · front · back · below45
    if v == "below": cam.location.z = -900; cam.rotation_euler = (math.pi, 0, 0)
    elif v == "front": cam.location = (0, -900, 0); cam.rotation_euler = (math.radians(90), 0, 0)
    elif v == "back": cam.location = (0, 900, 0); cam.rotation_euler = (math.radians(90), 0, math.pi)
    elif v == "below45": cam.location = (0, -640, -640); cam.rotation_euler = (math.radians(135), 0, 0)

def 거울(prefix, n=24):
    """콘치 로봇 왼팔 · 오른팔: 오른팔을 거울로 접어 왼팔 위에 포갠다 → 프레임 n 장."""
    l = B.load(glob.glob(R + "1402376_콘치로봇/**/conch_arm_l.stl", recursive=True)[0], (0.35, 0.6, 0.95, 1))
    r = B.load(glob.glob(R + "1402376_콘치로봇/**/conch_arm_r.stl", recursive=True)[0], (0.98, 0.55, 0.18, 1))
    gapx = max(l.dimensions.x, r.dimensions.x) * 0.75; l.location.x = -gapx
    top_cam(0, 0, max(l.dimensions.x, l.dimensions.y) * 3.6, tilt=25)
    for i in range(n):
        u = min(1, i / (n * 0.75)); s = 0.5 - 0.5 * math.cos(math.pi * u)   # 부드럽게
        r.location.x = gapx * (1 - s) - gapx * s; r.scale.x = 1 - 2 * s; r.location.z = 0.5 + 6 * math.sin(math.pi * s)
        bpy.context.scene.render.filepath = "%s_%02d.png" % (prefix, i); bpy.ops.render.render(write_still=True)

def 핀():
    fs = sorted(glob.glob(R + "1402376_콘치로봇/**/conch_pins_*.stl", recursive=True)); objs = [B.load(f, (0.98, 0.80, 0.15, 1)) for f in fs]
    W = 60; h = pack(objs, W, gap=3); frame_all(1.15)

def 폴아웃(whole):
    d = R + "400101_폴아웃로봇/"
    if whole:
        o = B.load(d + "FalloutRobot.stl", CLAY)
        cam = top_cam(0, 0, o.dimensions.z * 1.12, tilt=90); cam.location = (0, -900, 0); cam.rotation_euler = (math.radians(90), 0, 0)
        bpy.context.scene.render.resolution_x = 860   # 세로로 긴 로봇
    else:
        import colorsys
        fs = [f for f in sorted(glob.glob(d + "*.stl")) if not os.path.basename(f).startswith(("FalloutRobot", "HeadClosed"))]
        objs = [B.load(f, (*colorsys.hsv_to_rgb(i / len(fs), 0.55, 0.95), 1)) for i, f in enumerate(fs)]
        W = 220; h = pack(objs, W, gap=6); frame_all()

if __name__ == "__main__":
    which, out = sys.argv[sys.argv.index("--") + 1:][:2]
    B.scene()
    if which == "거울": 거울(out); sys.exit(0)
    {"메가회색": lambda: 메가(False), "메가색": lambda: 메가(True), "얼굴": 얼굴, "핀": 핀, "폴아웃통": lambda: 폴아웃(True), "폴아웃부품": lambda: 폴아웃(False)}[which]()
    bpy.context.scene.render.filepath = out; bpy.ops.render.render(write_still=True); print("저장", out)
