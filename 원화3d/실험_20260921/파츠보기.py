# -*- coding: utf-8 -*-
"""**분할된 파츠를 따로 뽑아 본다** — 색칠 · 분해 (2026-09-21).

    python 파츠보기.py [케이스=오메가몬]   -> out/파츠/<케이스>/부위_NN.ply · out/파츠_<케이스>.png

사용자(09-21): 「**분할된 파츠를 보여주고**」. 바퀴 2 는 union 메시 하나로 보여줘서
어디가 어느 부품인지 안 보였다. 부품마다 **따로 깎아 따로 저장**하고, 색칠 · 분해로 본다.

부품 하나 = `면자르기` 의 분수령 한 덩이. 깎는 법은 `부위깎기` 와 같다 (가로는 제 그림자,
깊이는 옆 소유 몫 >= 0.5 면 잰 값 · 아니면 원통 가정 · 마지막에 hull 장으로 덮개).
"""
import json
import os
import subprocess
import sys

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh
from scipy import ndimage

sys.path.insert(0, r"G:\art2real\원화3d")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
import hull as H
import 결과물 as RS
import 면자르기 as MJ
import 부위깎기 as BK
W = H.W
OUT = H.OUT
N = MJ.N

색판 = [(0.90, 0.32, 0.30), (0.30, 0.55, 0.88), (0.32, 0.74, 0.46), (0.94, 0.68, 0.20),
        (0.66, 0.42, 0.85), (0.20, 0.74, 0.78), (0.90, 0.50, 0.70), (0.55, 0.59, 0.25),
        (0.48, 0.48, 0.80), (0.78, 0.36, 0.24), (0.36, 0.67, 0.36), (0.82, 0.59, 0.82),
        (0.59, 0.43, 0.27), (0.39, 0.74, 0.94), (0.98, 0.47, 0.35)]

렌더소스 = r'''
import bpy, math, sys, glob, os
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
d, out, tag, explode = a[0], a[1], a[2], float(a[3])
cols = eval(a[4])
bpy.ops.wm.read_factory_settings(use_empty=True)
objs = []
for i, f in enumerate(sorted(glob.glob(os.path.join(d, "부위_*.ply")))):
    bpy.ops.wm.ply_import(filepath=f)
    o = bpy.context.selected_objects[0]
    bpy.ops.object.shade_smooth()
    mat = bpy.data.materials.new("m%d" % i); mat.use_nodes = True
    b = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    c = cols[i % len(cols)]
    b.inputs["Base Color"].default_value = (c[0], c[1], c[2], 1)
    b.inputs["Roughness"].default_value = 0.5
    o.data.materials.append(mat)
    objs.append(o)
allb = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
mn = Vector((min(v[i] for v in allb) for i in range(3))); mx = Vector((max(v[i] for v in allb) for i in range(3)))
ctr = (mn + mx) / 2; size = max(mx - mn) * (1.12 + explode * 1.4)
if explode:
    for o in objs:
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        c = sum(bb, Vector((0, 0, 0))) / 8
        v = c - ctr
        if v.length > 1e-6:
            o.location = o.location + v.normalized() * (size * explode)
sc = bpy.context.scene
cd = bpy.data.cameras.new("c"); cd.type = "ORTHO"; cd.ortho_scale = size
cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
for nm, rot, e in (("key", (55, 0, -40), 1.6), ("fill", (70, 0, 120), 0.4), ("rim", (120, 0, 200), 0.7)):
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
for name, az in (("앞", 0), ("사선", 40), ("옆", 90)):
    t = math.radians(az)
    cam.location = ctr + Vector((math.sin(t) * 6, -math.cos(t) * 6, 0.0))
    cam.rotation_euler = (math.radians(90), 0, t)
    sc.render.filepath = "%s/파츠_%s_%s.png" % (out, tag, name)
    bpy.ops.render.render(write_still=True)
print("렌더 끝", tag)
'''


def 내보내기(m, path):
    """**ascii PLY 로** 쓴다 — trimesh 의 바이너리 판을 Blender 4.0 임포터가 간혹 거절한다
    (「Invalid face size, must be between 1 and 255」· 같은 메시가 ascii 로는 들어간다 · 09-21)."""
    open(path, "wb").write(trimesh.exchange.ply.export_ply(m, encoding="ascii"))


def 파츠만들기(case, p=2.0):
    """부품마다 **따로** 장을 풀어 메시로. p > 2 면 초타원(각진 단면)."""
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks = {v: H.to_win(H.declutter(m), np.ones(m.shape, np.float32))[0] for v, m in raw.items()}
    bs = H.CASES[case]["back_sign"] or H.pick_back_sign(masks)
    masks = H._warp(masks, H.align(masks, back_sign=bs))
    g, (u, _, z) = H.field_default(masks, back_sign=bs, n=N)
    f, _ = H.field_hull(masks, back_sign=bs, n=N)
    cell = (W.U1 - W.U0) / N
    배 = W.RES / N
    _, lab, _ = MJ.부위(g > 0)
    옆주, 옆주2 = BK.주인(lab, 0), BK.주인(lab, 0, 뒤=True)
    조각 = []
    for L in [int(i) for i in np.unique(lab) if i > 0]:
        M = lab == L
        앞투, 옆투 = M.any(1), M.any(0)
        쓴다 = float(((옆주 == L) | (옆주2 == L)).sum()) / max(옆투.sum(), 1) >= 0.5
        gl = np.full_like(g, -2.0)
        for k in range(N):
            fx = 앞투[:, k]
            if not fx.any() or not 옆투[:, k].any():
                continue
            X, A = H._축값([(int(s * 배), int(e * 배)) for s, e in H._구간(fx)], u)
            if 쓴다:
                Y, B = H._축값([(int(s * 배), int(e * 배)) for s, e in H._구간(옆투[:, k])], u)
            else:
                ys = np.where(M[:, :, k])[1]
                cy, a = u[int(ys.mean())], float(np.median(A[fx]))
                Y, B = ((u - cy) / a) ** 2, np.full(N, a, np.float32)
            q = (1.0 - X[:, None] ** (p / 2) - Y[None, :] ** (p / 2))      # p=2 면 타원 · 클수록 각진다
            gl[:, :, k] = q * np.minimum(A[:, None], B[None, :]) / 2 / cell
        gl = np.minimum(np.maximum(ndimage.gaussian_filter1d(gl, H.SMOOTH_Z, axis=2), gl - H.SMOOTH_GUARD), f)
        if not (gl > 0).any():
            continue
        V, Fc = H.mesh_from_field(gl, (u, u, z))
        if len(Fc) < 50:
            continue                                                    # 빈 · 부스러기 부위. PLY 로 내보내면 임포터가 깨진다
        m = RS.큰덩어리(trimesh.Trimesh(V, Fc, process=False))
        if len(m.faces) < 50:
            continue
        if m.volume < 0:
            m.invert()
        조각.append((L, m, float((lab == L).sum()) / max((lab > 0).sum(), 1)))
    조각.sort(key=lambda t: -t[2])
    return 조각, masks, bs


def main(case="오메가몬", p=2.0):
    from PIL import Image, ImageDraw
    d = os.path.join(OUT, "파츠", case)
    os.makedirs(d, exist_ok=True)
    for old in os.listdir(d):
        if old.startswith("부위_") and old.endswith(".ply"):
            os.remove(os.path.join(d, old))
    조각, masks, bs = 파츠만들기(case, p)
    for i, (L, m, 몫) in enumerate(조각):
        내보내기(m, os.path.join(d, "부위_%02d.ply" % i))
    print("  파츠 %d 개 -> %s" % (len(조각), d), flush=True)
    for i, (L, m, 몫) in enumerate(조각):
        print("   %02d  부피 몫 %.3f · 면 %6d · 닫힘 %s" % (i, 몫, len(m.faces), m.is_watertight), flush=True)

    py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_파츠렌더.py")
    open(py, "w", encoding="utf-8").write(렌더소스)
    for tag, ex in (("조립", 0.0), ("분해", 0.16)):
        subprocess.run([RS.BLENDER, "-b", "--python", py, "--", d, d, tag, str(ex), repr(색판)],
                       capture_output=True, timeout=1800)
    S = 600
    흰 = os.path.join(OUT, "누끼", "%s_front" % case, "흰바탕.png")
    원 = Image.open(흰).convert("RGB").resize((S, S)) if os.path.exists(흰) else Image.new("RGB", (S, S), "white")
    rows = []
    for tag in ("조립", "분해"):
        rows.append([원] + [Image.open(os.path.join(d, "파츠_%s_%s.png" % (tag, n))).convert("RGB").resize((S, S))
                            for n in ("앞", "사선", "옆")])
    sheet = Image.new("RGB", (4 * (S + 8), 2 * (S + 8) + 72), "white")
    for i, ims in enumerate(rows):
        for j, im in enumerate(ims):
            sheet.paste(im, (j * (S + 8), 72 + i * (S + 8)))
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 28)
        f본 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 20)
    except OSError:
        f제 = f본 = None
    dr.text((14, 14), "분할된 파츠 %d 개 · %s   (위 조립 · 아래 분해)" % (len(조각), case), (20, 22, 28), f제)
    dr.text((14, 46), "부피 몫 " + " · ".join("%.2f" % q for _, _, q in 조각[:10])
            + "   · 파일 out/파츠/%s/부위_NN.ply" % case, (90, 92, 100), f본)
    o = os.path.join(OUT, "파츠_%s.png" % case)
    sheet.save(o)
    sheet.resize((sheet.size[0] // 2, sheet.size[1] // 2)).save(o.replace(".png", "_작게.png"))
    json.dump({"케이스": case, "p": p, "파츠": [{"i": i, "부피 몫": round(q, 4), "면": len(m.faces),
                                              "닫힘": bool(m.is_watertight)} for i, (_, m, q) in enumerate(조각)]},
              open(os.path.join(d, "파츠.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", o)


if __name__ == "__main__":
    a = sys.argv
    main(a[1] if len(a) > 1 else "오메가몬", float(a[2]) if len(a) > 2 else 2.0)

