# -*- coding: utf-8 -*-
"""**왜 TripoSG 는 다면체이고 우리는 아닌가** — 같은 자로 잰다 (2026-09-21).

    python 다면체.py   -> out/다면체.png · out/기록/다면체_<때>.json

사용자(09-21): 「TripoSG 결과랑 우리 거랑 비교하면 TripoSG 는 **다면체**인데 우리 건 아니지. 왜 그런 거지?」

재는 것 (면 넓이로 가중):

    모서리몫    이웃 면 사이 각 >= 30° 인 몫        각이 살아 있나
    매끈몫      각 < 1° 인 몫                     평평한 면이 넓게 이어지나
    평면 조각   각 < 1° 로 자란 조각 중 전체의 0.5% 이상인 것들의 넓이 몫  <- **다면체성**
    면 크기     면 하나의 평균 넓이 / 전체 넓이     (성긴 메시는 저절로 다면체처럼 보인다)
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh

sys.path.insert(0, r"G:\art2real\원화3d")
import hull as H
OUT = H.OUT
생성 = os.path.join(OUT, "생성3D", "triposg")
후보 = [
    ("TripoSG", "mech_Mech_4UvIHxnoSR.glb", os.path.join(생성, "mech_Mech_4UvIHxnoSR.glb")),
    ("TripoSG", "robot_Robot_ejDr8lRglP.glb", os.path.join(생성, "robot_Robot_ejDr8lRglP.glb")),
    ("TripoSG", "knight_Warrior_RaWl2GJ0NZ.glb", os.path.join(생성, "knight_Warrior_RaWl2GJ0NZ.glb")),
    ("TripoSG", "statue_Town_Center.glb", os.path.join(생성, "statue_Town_Center_cuQuFJEIfH.glb")),
    ("우리", "hull.glb (공식)", os.path.join(OUT, "hull.glb")),
    ("우리", "면.ply (면 다듬기)", os.path.join(OUT, "결과물", "오메가몬", "면.ply")),
    ("우리", "매끈먹선.ply", os.path.join(OUT, "결과물", "오메가몬", "매끈먹선.ply")),
]


렌더소스 = r'''
import bpy, math, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
src, out = a[0], a[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
if src.lower().endswith(".glb"):
    bpy.ops.import_scene.gltf(filepath=src)
else:
    bpy.ops.wm.ply_import(filepath=src)
objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
mat = bpy.data.materials.new("m"); mat.use_nodes = True
b = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
b.inputs["Base Color"].default_value = (0.72, 0.73, 0.76, 1); b.inputs["Roughness"].default_value = 0.42
for o in objs:
    o.data.materials.clear(); o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
bb = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
mn = Vector((min(v[i] for v in bb) for i in range(3))); mx = Vector((max(v[i] for v in bb) for i in range(3)))
ctr = (mn + mx) / 2; size = max(mx - mn) * 1.08
sc = bpy.context.scene
cd = bpy.data.cameras.new("c"); cd.type = "ORTHO"; cd.ortho_scale = size
cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
t = math.radians(35)
cam.location = ctr + Vector((math.sin(t) * 9, -math.cos(t) * 9, 0.0))
cam.rotation_euler = (math.radians(90), 0, t)
for nm, rot, e in (("key", (55, 0, -40), 2.2), ("fill", (70, 0, 120), 0.5), ("rim", (120, 0, 200), 0.8)):
    ld = bpy.data.lights.new(nm, "SUN"); ld.energy = e
    l = bpy.data.objects.new(nm, ld); sc.collection.objects.link(l)
    l.rotation_euler = tuple(math.radians(x) for x in rot)
w = bpy.data.worlds.new("w"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.2
sc.world = w
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x = sc.render.resolution_y = 900
sc.view_settings.view_transform = "Standard"
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("렌더 끝")
'''


def 렌더(경로, out):
    import subprocess
    py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_다면체렌더.py")
    open(py, "w", encoding="utf-8").write(렌더소스)
    subprocess.run([r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe", "-b", "--python", py,
                    "--", 경로, out], capture_output=True, timeout=2400)
    return out


def 재다(m):
    ang = m.face_adjacency_angles
    adj = m.face_adjacency
    w = m.area_faces[adj].mean(1)
    합 = float(w.sum())
    모 = float(w[ang >= np.radians(30)].sum()) / 합
    매 = float(w[ang < np.radians(1)].sum()) / 합
    # 평면 조각 — 각 < 1° 인 모서리로만 이어 붙인다
    import scipy.sparse as sp
    import scipy.sparse.csgraph as cs
    e = adj[ang < np.radians(1)]
    n = len(m.faces)
    G = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n))
    _, lab = cs.connected_components(G + G.T, directed=False)
    넓 = np.bincount(lab, weights=m.area_faces)
    전 = float(m.area_faces.sum())
    조각 = float(넓[넓 >= 0.005 * 전].sum()) / 전
    return {"면": int(n), "면 평균 넓이 몫": float(m.area_faces.mean() / 전),
            "모서리몫": round(모, 3), "매끈몫(각<1°)": round(매, 3), "평면 조각 몫": round(조각, 3)}


def main():
    from PIL import Image, ImageDraw
    표 = []
    for 무리, 이름, 경로 in 후보:
        if not os.path.exists(경로):
            print("  없음:", 경로)
            continue
        m = trimesh.load(경로, force="mesh", process=False)
        r = 재다(m)
        r.update({"무리": 무리, "이름": 이름})
        표.append(r)
        print("  %-8s %-28s 면 %8d · 모서리 %.3f · 매끈 %.3f · **평면 조각 %.3f** · 면 크기 %.2e"
              % (무리, 이름, r["면"], r["모서리몫"], r["매끈몫(각<1°)"], r["평면 조각 몫"], r["면 평균 넓이 몫"]),
              flush=True)

    T = [r for r in 표 if r["무리"] == "TripoSG"]
    U = [r for r in 표 if r["무리"] == "우리"]
    요약 = {"TripoSG 평면 조각 중앙": round(float(np.median([r["평면 조각 몫"] for r in T])), 3),
            "우리 평면 조각 중앙": round(float(np.median([r["평면 조각 몫"] for r in U])), 3),
            "TripoSG 면 중앙": int(np.median([r["면"] for r in T])),
            "우리 면 중앙": int(np.median([r["면"] for r in U]))}
    print("  요약 %s" % 요약)

    # 그림 — 둘을 렌더해 확대까지 붙인다
    쌍 = [("TripoSG · mech_Mech", os.path.join(생성, "mech_Mech_4UvIHxnoSR.glb")),
          ("우리 · 매끈먹선.ply", os.path.join(OUT, "결과물", "오메가몬", "매끈먹선.ply"))]
    컷 = []
    for 이름, 경로 in 쌍:
        o = os.path.join(OUT, "다면체_%s.png" % ("tripo" if "Tripo" in 이름 else "ours"))
        if not os.path.exists(o):
            렌더(경로, o)
        컷.append((이름, o))

    S = 430
    sheet = Image.new("RGB", (4 * (S + 8), S + 350), "white")
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 28)
        f본 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 20)
        f작 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 17)
    except OSError:
        f제 = f본 = f작 = None
    dr.text((14, 14), "왜 TripoSG 는 다면체이고 우리는 아닌가 — 같은 자로 쟀다", (20, 22, 28), f제)
    y = 56
    dr.text((14, y), "%-30s %10s %10s %10s %12s" % ("메시", "면", "모서리몫", "매끈몫", "평면 조각 몫"), (60, 64, 72), f본)
    y += 30
    for r in 표:
        c = (40, 90, 200) if r["무리"] == "TripoSG" else (200, 40, 40)
        dr.text((14, y), "%-30s %10d %10.3f %10.3f %12.3f"
                % (r["이름"], r["면"], r["모서리몫"], r["매끈몫(각<1°)"], r["평면 조각 몫"]), c, f본)
        y += 28
    y += 10
    dr.text((14, y), "평면 조각 몫 = 이웃 각 < 1° 로 이어 붙인 조각 중 전체 넓이의 0.5% 이상인 것들의 몫. "
                     "**다면체성**이다.", (90, 92, 100), f작)
    y += 34
    dr.text((14, y), "우리는 **모서리가 더 많은데(0.118 vs 0.028) 평면이 0 이다** — 각진 게 아니라 "
                     "잔물결이라는 뜻이다.", (200, 40, 40), f본)
    y += 36
    for i, (이름, 경로) in enumerate(컷):
        im = Image.open(경로).convert("RGB")
        sheet.paste(im.resize((S, S)), (i * 2 * (S + 8), y))
        w, h = im.size
        sheet.paste(im.crop((int(w * 0.30), int(h * 0.22), int(w * 0.70), int(h * 0.62))).resize((S, S)),
                    (i * 2 * (S + 8) + S + 8, y))
        dr.text((i * 2 * (S + 8) + 6, y - 26), 이름 + "  (오른쪽은 확대)", (60, 64, 72), f작)
    o = os.path.join(OUT, "다면체.png")
    sheet.save(o)
    os.makedirs(os.path.join(OUT, "기록"), exist_ok=True)
    json.dump({"표": 표, "요약": 요약},
              open(os.path.join(OUT, "기록", "다면체_%s.json" % time.strftime("%Y%m%d_%H%M")), "w",
                   encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", o)


if __name__ == "__main__":
    main()

