# -*- coding: utf-8 -*-
"""v2 그림 블렌더 도우미 (6-6 ~ 7-5 공용).
씬 스크립트는 두 번 돈다: 시스템 파이썬으로 부르면 run(__file__) 가 블렌더를 -b 로 띄워 같은 파일을 돌리고(패스 렌더),
돌아와서 PIL 로 합성한다. 블렌더 안에서는 bpy 가 있으니 장면을 짓고 패스만 굽는다.
패스: beauty(Workbench 스튜디오 · 투명 배경) · ids(평면색 = 물체 번호 · AA 끔) · alone_<이름>(그 물체만 = 아모달 마스크)."""
import os, sys, subprocess
SRC = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(SRC)
BLENDER = r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe"
FONT = r"C:\Windows\Fonts\malgun.ttf"

def passdir(scene):
    d = os.path.join(SRC, "_패스", scene); os.makedirs(d, exist_ok=True); return d

def run(script):
    """시스템 파이썬에서: 블렌더로 같은 스크립트를 돌린다."""
    r = subprocess.run([BLENDER, "-b", "--factory-startup", "-P", script], capture_output=True, text=True, encoding="utf-8", errors="replace")
    tail = "\n".join(r.stdout.splitlines()[-15:])
    assert r.returncode == 0 and "Traceback" not in r.stdout + r.stderr, tail + r.stderr[-3000:]

# ---------------- 블렌더 쪽 ----------------
try:
    import bpy, mathutils, math
except ImportError:
    bpy = None

def scene(res=(960, 720)):
    bpy.ops.wm.read_homefile(use_empty=True); sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading
    sh.light = "STUDIO"; sh.color_type = "OBJECT"; sh.show_cavity = True; sh.cavity_type = "BOTH"
    sc.world = bpy.data.worlds.new("w"); sc.world.color = (1, 1, 1)
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.render.film_transparent = True; sc.render.image_settings.color_mode = "RGBA"; sc.render.dither_intensity = 0
    sc.view_settings.view_transform = "Standard"
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.clip_end = 1000
    return sc

def camera(loc, target, ortho=None, lens=50):
    cam = bpy.context.scene.camera; cam.location = loc
    d = mathutils.Vector(target) - mathutils.Vector(loc); cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    if ortho: cam.data.type = "ORTHO"; cam.data.ortho_scale = ortho
    else: cam.data.type = "PERSP"; cam.data.lens = lens

def _new(name, color, parent=None):
    o = bpy.context.active_object; o.name = name; o.color = (*color[:3], 1)
    for p in o.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o

def ell(name, loc, scale, color, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=loc, rotation=rot); o = _new(name, color); o.scale = scale; return o

def cyl(name, loc, r, depth, color, rot=(0, 0, 0), verts=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot); o = _new(name, color)
    for p in o.data.polygons: p.use_smooth = False
    return o

def cone(name, loc, r1, r2, depth, color, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=r1, radius2=r2, depth=depth, location=loc, rotation=rot); return _new(name, color)

def box(name, loc, size, color, rot=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot); o = _new(name, color); o.scale = size
    for p in o.data.polygons: p.use_smooth = False
    if bevel:
        bpy.ops.object.transform_apply(scale=True); m = o.modifiers.new("b", "BEVEL"); m.width = bevel; m.segments = 3
    return o

def join(name, objs, color):
    """여러 조각을 한 물체로(마스크는 물체 단위)."""
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join(); o = bpy.context.active_object; o.name = name; o.color = (*color[:3], 1); return o

def shot(path):
    sc = bpy.context.scene; sc.render.filepath = path; bpy.ops.render.render(write_still=True)

def passes(d, objs, tag="", beauty=True, alone=True):
    """beauty · ids · alone_<i> 를 d 에 굽는다. objs 순서가 번호(1..) · 원소는 물체 하나 또는 물체 목록(한 덩어리)."""
    sc = bpy.context.scene; sh = sc.display.shading
    objs = [g if isinstance(g, (list, tuple)) else [g] for g in objs]
    if beauty: shot(os.path.join(d, f"beauty{tag}.png"))
    if alone:
        hid = {o.name: o.hide_render for o in sc.objects}
        for i, g in enumerate(objs, 1):
            for p in sc.objects:
                if p.type == "MESH": p.hide_render = p not in g
            shot(os.path.join(d, f"alone{tag}_{i}.png"))
        for p in sc.objects: p.hide_render = hid[p.name]
    # (alone 은 스튜디오 음영 그대로 · 마스크는 알파)
    old = {o.name: tuple(o.color) for o in sc.objects if o.type == "MESH"}
    aa = sc.display.render_aa; light, cav = sh.light, sh.show_cavity
    vt = sc.view_settings.view_transform
    sc.display.render_aa = "OFF"; sh.light = "FLAT"; sh.show_cavity = False; sc.view_settings.view_transform = "Raw"
    for o in sc.objects:
        if o.type == "MESH": o.color = (0, 0, 0, 1)
    for i, g in enumerate(objs, 1):
        for o in g: o.color = (i * 20 / 255.0, 0, 0, 1)
    shot(os.path.join(d, f"ids{tag}.png"))
    for o in sc.objects:
        if o.name in old: o.color = old[o.name]
    sc.display.render_aa = aa; sh.light = light; sh.show_cavity = cav; sc.view_settings.view_transform = vt

# ---------------- 합성 쪽 (시스템 파이썬) ----------------
def load(d, name):
    import numpy as np; from PIL import Image
    return np.asarray(Image.open(os.path.join(d, name)).convert("RGBA")).astype(np.float32) / 255.0

def ids(d, tag=""):
    import numpy as np
    a = load(d, f"ids{tag}.png"); return np.where(a[..., 3] > 0.5, np.round(a[..., 0] * 255 / 20).astype(int), 0)

def amodal(d, i, tag=""):
    return load(d, f"alone{tag}_{i}.png")[..., 3] > 0.5

def on_white(rgba, bg=(1, 1, 1)):
    import numpy as np
    a = rgba[..., 3:4]; return rgba[..., :3] * a + np.array(bg, np.float32) * (1 - a)

def to_img(rgb):
    import numpy as np; from PIL import Image
    return Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8))

def outline(mask, w=5):
    """마스크 윤곽 띠(두께 약 w 픽셀 · w 홀수)."""
    import numpy as np; from PIL import Image, ImageFilter
    m = Image.fromarray(mask.astype(np.uint8) * 255)
    return (np.asarray(m.filter(ImageFilter.MaxFilter(w))) > 127) & ~(np.asarray(m.filter(ImageFilter.MinFilter(w))) > 127)

def tint(rgb, mask, color, a=0.5):
    import numpy as np
    out = rgb.copy(); out[mask] = out[mask] * (1 - a) + np.array(color, np.float32) * a; return out

def canvas():
    from PIL import Image
    return Image.new("RGB", (1920, 1080), (255, 255, 255))

def label(img, xy, text, size=34, anchor="mm", fill=(20, 20, 20)):
    from PIL import ImageDraw, ImageFont
    ImageDraw.Draw(img).text(xy, text, font=ImageFont.truetype(FONT, size), fill=fill, anchor=anchor)

def arrow(img, p, q, w=6, fill=(30, 30, 30)):
    from PIL import ImageDraw; import math
    dr = ImageDraw.Draw(img); dr.line([p, q], fill=fill, width=w)
    a = math.atan2(q[1] - p[1], q[0] - p[0]); L = 4 * w
    dr.polygon([q, (q[0] - L * math.cos(a - 0.45), q[1] - L * math.sin(a - 0.45)), (q[0] - L * math.cos(a + 0.45), q[1] - L * math.sin(a + 0.45))], fill=fill)

def fit(img, box):
    """img(PIL) 를 box=(w,h) 안에 비율 유지로 맞춘다."""
    from PIL import Image
    w, h = img.size; s = min(box[0] / w, box[1] / h); return img.resize((max(1, int(w * s)), max(1, int(h * s))), Image.LANCZOS)

def crop_to(mask_or_img_arr, mask, pad=10):
    import numpy as np
    ys, xs = np.nonzero(mask); y0, y1, x0, x1 = max(ys.min() - pad, 0), ys.max() + pad, max(xs.min() - pad, 0), xs.max() + pad
    return mask_or_img_arr[y0:y1, x0:x1]

def frame(img, xy, size, color, w=8):
    from PIL import ImageDraw
    x, y = xy; ImageDraw.Draw(img).rectangle([x - w // 2, y - w // 2, x + size[0] + w // 2, y + size[1] + w // 2], outline=color, width=w)
