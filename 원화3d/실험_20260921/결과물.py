# -*- coding: utf-8 -*-
"""**파이프라인 결과물을 본다** — 원화 3 판 -> 메시 -> 렌더 (2026-09-21).

    python 결과물.py [케이스=오메가몬] [격자=384]   -> out/결과물/<케이스>/{결과.ply, 결과_선.ply, 렌더_*.png} · out/결과물_<케이스>.png

사용자(09-21): 「이제는 벤치가 아니라 **파이프라인 결과물**을 보고 싶다고. 아직도 개판이구만」

오늘 얻은 것을 한 줄로 잇는다 — 표도 문턱도 없다. **눈으로 본다.**

    원화 3 판 -> 지시선 제거 · 창에 앉히기 · 정렬 (`hull.py` 배관)
             -> **연속 장 타원 hull** (`장타원.타원장` · 복셀 이진화 없음) -> 마칭큐브
             -> 제일 큰 덩어리만
             -> (곁가지) 도안의 판 경계를 앞 · 뒤에서 새긴 판본
             -> Blender 렌더 4 각도
"""
import os
import subprocess
import sys

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh

sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
import 장타원 as JT
import 세우기 as SE
H, W, LR = JT.H, JT.W, JT.LR
HERE = JT.HERE
BLENDER = r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe"
렌더py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_렌더.py")

렌더소스 = r'''
import bpy, math, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
src, out, tag = a[0], a[1], a[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.ply_import(filepath=src)
o = bpy.context.selected_objects[0]
bpy.ops.object.shade_smooth()
mat = bpy.data.materials.new("m"); mat.use_nodes = True
b = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
b.inputs["Base Color"].default_value = (0.62, 0.64, 0.68, 1); b.inputs["Roughness"].default_value = 0.55
o.data.materials.append(mat)
bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
mn = Vector((min(v[i] for v in bb) for i in range(3))); mx = Vector((max(v[i] for v in bb) for i in range(3)))
ctr = (mn + mx) / 2; size = max(mx - mn) * 1.12
sc = bpy.context.scene
cd = bpy.data.cameras.new("c"); cd.type = "ORTHO"; cd.ortho_scale = size
cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
for nm, rot, e in (("key", (55, 0, -40), 1.6), ("fill", (70, 0, 120), 0.4), ("rim", (120, 0, 200), 0.7)):
    ld = bpy.data.lights.new(nm, "SUN"); ld.energy = e
    l = bpy.data.objects.new(nm, ld); sc.collection.objects.link(l)
    l.rotation_euler = tuple(math.radians(x) for x in rot)
w = bpy.data.worlds.new("w"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.18
sc.world = w
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x = sc.render.resolution_y = 900
sc.view_settings.view_transform = "Standard"
for name, az in (("앞", 0), ("사선", 40), ("옆", 90), ("뒤", 180)):
    t = math.radians(az)
    cam.location = ctr + Vector((math.sin(t) * 6, -math.cos(t) * 6, 0.0))
    cam.rotation_euler = (math.radians(90), 0, t)
    sc.render.filepath = "%s/렌더_%s_%s.png" % (out, tag, name)
    bpy.ops.render.render(write_still=True)
print("렌더 끝", tag)
'''


def 큰덩어리(m):
    ps = m.split(only_watertight=False)
    return max(ps, key=lambda x: len(x.faces)) if len(ps) > 1 else m


def 새기기(m, masks, raw, p, bs):
    V = np.asarray(m.vertices, float).copy()
    N = np.asarray(m.vertex_normals)
    for 폴더, v, sign, 방향 in (("앞", "front", +1, -1), ("뒤", "back", bs, +1)):
        선 = SE.창에(SE.경계지도(폴더, raw[v]), v, raw, p)
        본다 = N[:, 1] * 방향 > SE.법선문턱
        py, px = W.topix(sign * V[:, 0], V[:, 2])
        on = 본다 & 선[py, px]
        V[on, 1] -= 방향 * SE.홈깊이
    return trimesh.Trimesh(V, np.asarray(m.faces), process=False)


def main(case="오메가몬", N=384):
    from PIL import Image
    d = os.path.join(HERE, "out", "결과물", case)
    os.makedirs(d, exist_ok=True)
    _, masks, p, bs, raw = SE.껍질(case)
    g, ax = JT.타원장(masks, bs, N=N)
    m = 큰덩어리(JT.메시(g, ax))
    print("  메시 면 %d · 닫힘 %s · 격자 %d" % (len(m.faces), m.is_watertight, N), flush=True)
    m.export(os.path.join(d, "결과.ply"))
    판본 = [("결과", "결과.ply")]
    if case == "오메가몬" and os.path.exists(os.path.join(SE.도안디, "앞", "labels_grown.npy")):
        새기기(m, masks, raw, p, bs).export(os.path.join(d, "결과_선.ply"))
        판본.append(("선", "결과_선.ply"))
    open(렌더py, "w", encoding="utf-8").write(렌더소스)
    for tag, f in 판본:
        r = subprocess.run([BLENDER, "-b", "--python", 렌더py, "--", os.path.join(d, f), d, tag],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1500)
        print("  렌더 %s: %s" % (tag, "OK" if "렌더 끝" in (r.stdout or "") else (r.stdout or "")[-400:] + (r.stderr or "")[-400:]), flush=True)
    # 한 장으로
    src = os.path.join(HERE, "out", "누끼", "%s_front" % case, "흰바탕.png")
    rows = []
    for tag, _ in 판본:
        ims = [Image.open(src).convert("RGB").resize((900, 900))] if os.path.exists(src) else []
        ims += [Image.open(os.path.join(d, "렌더_%s_%s.png" % (tag, n))).convert("RGB") for n in ("앞", "사선", "옆", "뒤")]
        rows.append(ims)
    Wd = sum(im.size[0] for im in rows[0]) + 10 * (len(rows[0]) - 1)
    sheet = Image.new("RGB", (Wd, 900 * len(rows) + 10 * (len(rows) - 1)), "white")
    for i, ims in enumerate(rows):
        x = 0
        for im in ims:
            sheet.paste(im, (x, i * 910))
            x += im.size[0] + 10
    out = os.path.join(HERE, "out", "결과물_%s.png" % case)
    sheet.save(out)
    print("  ->", out)


if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else "오메가몬"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 384
    main(c, n)
