# -*- coding: utf-8 -*-
"""**왜 원화와 우리 산출물이 다른가** — 차이를 몫으로 나눈다 (2026-09-21).

    python 왜다른가.py [케이스=오메가몬]   -> out/왜다른가_<케이스>.png · out/기록/왜다른가_*.json

사용자(09-21): 「왜 이미지와 우리 산출물이 다른 건지가 궁금해」

지금까지 안 것: **겉(실루엣)은 안 다르다** (IoU 0.940 · 0.965 · 0.949 · 지어냄은 3 화소 띠).
그러면 다른 것은 **속**인데, 속의 차이가 **색 때문인지 형상 때문인지**를 갈라야 한다.

    ① 회색 렌더          지금 산출물 그대로 (재질 없음)
    ② **원화 색을 입힌 렌더**  원화에서 색을 떠서 정점에 칠하고 **빛 없이**(emission) 렌더
    ③ 원화

    색몫 = 1 - 거리(②, ③) / 거리(①, ③)      색을 입히면 차이가 몇 % 줄어드나
    남은 것이 **형상 차이**다.

거리는 실루엣 **안쪽**에서만 잰다 (배경이 숫자를 지배하지 않게).
"""
import json
import os
import subprocess
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh
from scipy import ndimage

sys.path.insert(0, r"G:\art2real\원화3d")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
import hull as H
import 닮음 as DM
W = H.W
OUT = H.OUT

렌더소스 = r'''
import bpy, math, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
src, out, u0, u1, z0, z1, mode = a[0], a[1], float(a[2]), float(a[3]), float(a[4]), float(a[5]), a[6]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.ply_import(filepath=src)
o = bpy.context.selected_objects[0]
bpy.ops.object.shade_smooth()
mat = bpy.data.materials.new("m"); mat.use_nodes = True
nt = mat.node_tree
b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
if mode == "color":
    out_node = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    em = nt.nodes.new("ShaderNodeEmission")
    vc = nt.nodes.new("ShaderNodeVertexColor")
    names = [a.name for a in o.data.color_attributes] if hasattr(o.data, "color_attributes") else []
    if names:
        vc.layer_name = names[0]
    nt.links.new(vc.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs["Emission"], out_node.inputs["Surface"])   # 빛 없이 색만
else:
    b.inputs["Base Color"].default_value = (0.72, 0.73, 0.76, 1)
    b.inputs["Roughness"].default_value = 0.45
o.data.materials.append(mat)
sc = bpy.context.scene
cd = bpy.data.cameras.new("c"); cd.type = "ORTHO"; cd.ortho_scale = max(u1 - u0, z1 - z0)
cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
cam.location = Vector(((u0 + u1) / 2, -6.0, (z0 + z1) / 2))
cam.rotation_euler = (math.radians(90), 0, 0)
if mode != "color":
    for nm, rot, e in (("key", (55, 0, -40), 2.0), ("fill", (70, 0, 120), 0.5), ("rim", (120, 0, 200), 0.8)):
        ld = bpy.data.lights.new(nm, "SUN"); ld.energy = e
        l = bpy.data.objects.new(nm, ld); sc.collection.objects.link(l)
        l.rotation_euler = tuple(math.radians(x) for x in rot)
w = bpy.data.worlds.new("w"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.0 if mode == "color" else 0.22
sc.world = w
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x = sc.render.resolution_y = 1024
sc.render.film_transparent = True
sc.view_settings.view_transform = "Standard"
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("렌더 끝")
'''


def 색입히기(m, raw, p, bs, case):
    """정점마다 **원화에서 색을 떠서** 칠한다 — 앞을 보면 앞 판, 뒤를 보면 뒤 판."""
    import cv2
    src, base = H.CASES[case]["src"], H.art_dir(case)
    V = np.asarray(m.vertices, float)
    Nn = np.asarray(m.vertex_normals)
    col = np.full((len(V), 4), 200, np.uint8)
    for v, sign, 방향 in (("front", +1, -1), ("back", bs, +1)):
        im = cv2.imdecode(np.fromfile(os.path.join(base, src[v]), np.uint8), cv2.IMREAD_UNCHANGED)
        rgb = cv2.cvtColor(im[:, :, :3], cv2.COLOR_BGR2RGB)
        알 = im[:, :, 3] > 127 if im.ndim == 3 and im.shape[2] == 4 else np.ones(im.shape[:2], bool)
        rgb = np.where(알[:, :, None], rgb, 255).astype(np.uint8)
        # 원화 화소 -> 창 -> 정렬. 세 채널을 마스크와 **같은 변환**으로 옮긴다
        d = H.declutter(raw[v])
        ch = [H.to_win(d, rgb[:, :, k].astype(np.float32))[1] for k in range(3)]
        ch = [H._warp_one(c, v, p) for c in ch]
        py, px = W.topix(sign * V[:, 0], V[:, 2])
        본다 = Nn[:, 1] * 방향 > 0.0
        for k in range(3):
            col[본다, k] = np.clip(ch[k][py[본다], px[본다]], 0, 255).astype(np.uint8)
    out = m.copy()
    out.visual = trimesh.visual.ColorVisuals(out, vertex_colors=col)
    return out


def 거리(a, b, 안):
    d = (a.astype(np.float32) - b.astype(np.float32))[안]
    return float(np.sqrt((d ** 2).mean()))


def main(case="오메가몬"):
    from PIL import Image, ImageDraw
    import cv2
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks = {v: H.to_win(H.declutter(q), np.ones(q.shape, np.float32))[0] for v, q in raw.items()}
    bs = H.CASES[case]["back_sign"] or H.pick_back_sign(masks)
    p = H.align(masks, back_sign=bs)
    masks = H._warp(masks, p)
    m = trimesh.load(os.path.join(OUT, "hull.glb"), force="mesh", process=False)
    색 = 색입히기(m, raw, p, bs, case)
    d = os.path.join(OUT, "왜다른가", case)
    os.makedirs(d, exist_ok=True)
    회ply, 색ply = os.path.join(d, "회색.ply"), os.path.join(d, "색.ply")
    open(회ply, "wb").write(trimesh.exchange.ply.export_ply(m, encoding="ascii"))
    open(색ply, "wb").write(trimesh.exchange.ply.export_ply(색, encoding="ascii"))
    sc = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_왜렌더.py")
    open(sc, "w", encoding="utf-8").write(렌더소스)
    낸 = {}
    for 이름, ply, mode in (("회색", 회ply, "gray"), ("색", 색ply, "color")):
        o = os.path.join(d, "%s.png" % 이름)
        subprocess.run([r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe", "-b", "--python", sc,
                        "--", ply, o, str(W.U0), str(W.U1), str(W.Z0), str(W.Z1), mode],
                       capture_output=True, timeout=1800)
        낸[이름] = o
        print("  렌더 %s -> %s" % (이름, os.path.exists(o)), flush=True)

    # 원화도 같은 창으로
    원im = cv2.imdecode(np.fromfile(os.path.join(base, src["front"]), np.uint8), cv2.IMREAD_UNCHANGED)
    rgb = cv2.cvtColor(원im[:, :, :3], cv2.COLOR_BGR2RGB)
    알 = 원im[:, :, 3] > 127 if 원im.ndim == 3 and 원im.shape[2] == 4 else np.ones(원im.shape[:2], bool)
    rgb = np.where(알[:, :, None], rgb, 255).astype(np.uint8)
    dfr = H.declutter(raw["front"])
    원창 = np.dstack([H._warp_one(H.to_win(dfr, rgb[:, :, k].astype(np.float32))[1], "front", p) for k in range(3)])
    원창 = np.clip(원창, 0, 255).astype(np.uint8)
    안 = ndimage.binary_erosion(masks["front"].astype(bool), iterations=3)

    def 읽기(png):
        im = cv2.imdecode(np.fromfile(png, np.uint8), cv2.IMREAD_UNCHANGED)
        if im.shape[2] == 4:
            a = im[:, :, 3:4] / 255.0
            im = (im[:, :, :3] * a + 255 * (1 - a)).astype(np.uint8)
        return cv2.cvtColor(im, cv2.COLOR_BGR2RGB)

    회 = 읽기(낸["회색"])
    색r = 읽기(낸["색"])
    d회 = 거리(회, 원창, 안)
    d색 = 거리(색r, 원창, 안)
    색몫 = 1 - d색 / max(d회, 1e-6)
    print("  거리(회색, 원화) %.1f · 거리(색, 원화) %.1f · **색몫 %.3f**" % (d회, d색, 색몫), flush=True)

    S = 520
    ims = [("원화", 원창), ("우리 (회색)", 회), ("우리 + 원화 색", 색r)]
    sheet = Image.new("RGB", (3 * (S + 8), S + 150), "white")
    for i, (t, a) in enumerate(ims):
        sheet.paste(Image.fromarray(a).resize((S, S)), (i * (S + 8), 140))
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 27)
        f본 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 20)
        f작 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 17)
    except OSError:
        f제 = f본 = f작 = None
    dr.text((14, 14), "왜 원화와 다른가 — 차이를 색과 형상으로 갈랐다 · %s" % case, (20, 22, 28), f제)
    dr.text((14, 52), "실루엣 안쪽 화소 거리(RGB RMS):  회색 %.1f  ->  원화 색을 입히면 %.1f" % (d회, d색),
            (40, 44, 52), f본)
    dr.text((14, 82), "**색몫 %.1f%%** — 안 닮음의 이만큼은 «색이 없어서»다. 나머지 %.1f%% 가 형상 차이다."
            % (100 * 색몫, 100 * (1 - 색몫)), (200, 40, 40), f본)
    dr.text((14, 112), "색은 원화에서 떠서 정점에 칠하고 빛 없이 렌더했다 (셀 채색과 같은 조건)", (90, 92, 100), f작)
    for i, (t, _) in enumerate(ims):
        dr.text((i * (S + 8) + 6, 120), t, (60, 64, 72), f작)
    o = os.path.join(OUT, "왜다른가_%s.png" % case)
    sheet.save(o)
    os.makedirs(os.path.join(OUT, "기록"), exist_ok=True)
    json.dump({"케이스": case, "거리 회색": round(d회, 2), "거리 색": round(d색, 2), "색몫": round(색몫, 4)},
              open(os.path.join(OUT, "기록", "왜다른가_%s_%s.json" % (case, time.strftime("%Y%m%d_%H%M"))),
                   "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", o)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "오메가몬")
