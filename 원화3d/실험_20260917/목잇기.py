# -*- coding: utf-8 -*-
"""**정제본과 원본을 이음매 없이 잇는 세 길** (2026-09-17). 관찰 그림 — 점수 없음.

    python 목잇기.py 준비    V3 조각(아래 · 위) 메시와 판 크롭 -> 스크래치 dg_parts/
    (DetailGen3D 를 imggen venv 에서 조각마다)
    python 목잇기.py 합침    V1 · V2 · V3 를 겹침 띠에서 거리장으로 섞는다 -> 스크래치 dg_parts/V*.glb
    python 목잇기.py 그림    -> out/은둔자_목잇기.png

    V0  지금 (09-17 머리정제)   목 y 0.72 에서 칼로 바꿔 끼움
    V1  겹침 섞기              TripoSG 원출력 몸 + 머리 정제 — 목 띠 y 0.68→0.74 에서 거리장 가중 평균
    V2  전신 정제 몸 + 머리      몸을 전신 DetailGen3D 본으로 바꾸고 V1 과 같이 섞음
    V3  조각별 정제             아래(y < 0.10) · 위(y > 0.00) 를 따로 정제 -> 띠 0.02→0.08 에서 섞고, 머리는 V2 처럼

거리장: 표면 표본점 최근접 + 그 점 법선으로 부호 (근사 — 표면 가까이에서만 믿는다. 섞는 곳이 표면 옆이라 충분).
"""
import os
import subprocess
import sys

import cv2
import numpy as np
import trimesh
from scipy.spatial import cKDTree
from skimage import measure

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 머리정제 as MR

S = MR.S
OUT = os.path.join(S, "dg_parts")
DG = r"G:\art2real\트레일\trail4_gen3d\DetailGen3D"
PY = r"D:\imggen\venv\Scripts\python.exe"
CELL = 0.0012
PARTS = {"lower": (-9.0, 0.10), "upper": (0.00, 9.0)}


def raw():
    return trimesh.load(MR.RAW, force="mesh")


def crop_y(m, y0, y1):
    c = m.triangles_center[:, 1]
    return m.submesh([np.nonzero((c > y0) & (c < y1))[0]], append=True)


def prepare():
    os.makedirs(OUT, exist_ok=True)
    m = raw()
    for name, (y0, y1) in PARTS.items():
        p = crop_y(m, y0, y1)
        p.export(os.path.join(OUT, name + ".glb"))
        cv2.imencode(".png", MR.face_crop(m, p))[1].tofile(os.path.join(OUT, name + ".png"))
        print("  %s 면 %d · 크기 %s" % (name, len(p.faces), np.round(p.bounding_box.extents, 3)))


def run_dg():
    for name in PARTS:
        if os.path.exists(os.path.join(OUT, "ref", name + ".glb")):
            continue
        q = lambda f: os.path.join(OUT, f).replace("\\", "/")
        subprocess.run([PY, "scripts/inference_detailgen3d.py", "--mesh_input", q(name + ".glb"),
                        "--image_input", q(name + ".png"), "--output_dir", q("ref")], cwd=DG, check=True)


def sdf(mesh, lo, hi, P, n=3_000_000, near=0.01):
    """P 점마다 부호 거리 (밖 +). 영역(lo..hi, 여유 0.03) 안 면에서만 표본을 뽑는다.
    표면에서 near 밖인 점은 거친 표본(10만)으로만 잰다 — 촘촘한 나무에서 먼 점 찾기가 V1 34분의 대부분이었다."""
    c = mesh.triangles_center
    pad = 0.03
    k = np.all((c > lo - pad) & (c < hi + pad), 1)
    sub = mesh.submesh([np.nonzero(k)[0]], append=True)
    pts, fi = trimesh.sample.sample_surface(sub, n)
    nrm = sub.face_normals[fi]
    tree = cKDTree(pts)
    d, j = tree.query(P, distance_upper_bound=near, workers=-1)
    far = ~np.isfinite(d)
    cp, cf = trimesh.sample.sample_surface(sub, 100_000)
    d2, j2 = cKDTree(cp).query(P[far], workers=-1)
    s = np.empty(len(P), np.float32)
    ok = ~far
    s[ok] = np.sign(((P[ok] - pts[j[ok]]) * nrm[j[ok]]).sum(1))
    s[far] = np.sign(((P[far] - cp[j2]) * sub.face_normals[cf][j2]).sum(1))
    d[far] = d2
    return (d * np.where(s == 0, 1, s)).astype(np.float32)


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def field_mesh(parts, lo, hi, ya, yb, cell):
    """lo..hi 상자 안을 거리장 섞기로 뽑는다. parts = (아래 메시, 위 메시) · 가중치 y ≤ ya 아래 · y ≥ yb 위 (smoothstep)."""
    axes = [np.arange(lo[i], hi[i] + cell, cell) for i in range(3)]
    G = np.stack(np.meshgrid(*axes, indexing="ij"), -1).reshape(-1, 3).astype(np.float32)
    w = smooth((G[:, 1] - ya) / (yb - ya))
    f = np.zeros(len(G), np.float32)
    for m, sel, k in ((parts[0], w < 1, 1 - w), (parts[1], w > 0, w)):
        f[sel] += k[sel] * sdf(m, lo, hi, G[sel])
    V, F, _, _ = measure.marching_cubes(f.reshape([len(x) for x in axes]), 0.0, spacing=(cell,) * 3)
    return trimesh.Trimesh(V + lo, F)


def outside(m, lo, hi):
    c = m.triangles_center
    return m.submesh([np.nonzero(~np.all((c > lo) & (c < hi), 1))[0]], append=True)


def neck_join(body):
    """body 의 머리를 정제 머리로 — 정제 전 머리 bbox(+여유) 상자 안에서만 섞는다. 상자 아래 벽 0.64 · 띠 0.68→0.74."""
    ref, head = head_refined()
    lo, hi = head.bounds[0] - 0.02, head.bounds[1] + 0.02
    lo[1] = 0.64
    return trimesh.util.concatenate([outside(body, lo, hi), field_mesh((body, ref), lo, hi, 0.68, 0.74, CELL)])


def head_refined():
    head = trimesh.load(os.path.join(MR.OUT, "head.glb"), force="mesh")
    return MR.back_to_raw(trimesh.load(os.path.join(MR.OUT, "face", "head.glb"), force="mesh"), head), head


def body_refined():
    m = raw()
    return MR.back_to_raw(trimesh.load(os.path.join(S, "dg", "hermit.glb"), force="mesh"), m)


def parts_refined():
    m = raw()
    ps = [MR.back_to_raw(trimesh.load(os.path.join(OUT, "ref", n + ".glb"), force="mesh"), crop_y(m, *PARTS[n])) for n in ("lower", "upper")]
    lo, hi = m.bounds[0] - 0.02, m.bounds[1] + 0.02
    lo[1], hi[1] = 0.00, 0.10
    c0, c1 = ps[0].triangles_center[:, 1], ps[1].triangles_center[:, 1]
    below = ps[0].submesh([np.nonzero(c0 <= lo[1])[0]], append=True)
    above = ps[1].submesh([np.nonzero(c1 >= hi[1])[0]], append=True)
    return trimesh.util.concatenate([below, field_mesh(ps, lo, hi, 0.02, 0.08, 0.002), above])


def merge():
    run = {"V1": lambda: neck_join(raw()), "V2": lambda: neck_join(body_refined()), "V3": lambda: neck_join(parts_refined())}
    for tag, fn in run.items():
        p = os.path.join(OUT, tag + ".glb")
        if os.path.exists(p):
            continue
        m = fn()
        m.export(p)
        print("  %s 면 %d -> %s" % (tag, len(m.faces), p), flush=True)


def figure():
    from PIL import Image, ImageDraw
    import 얼굴비교 as FC
    from 계획 import _font
    cols = [("V0 지금 (칼로 바꿔 끼움)", os.path.join(MR.OUT, "merged_face.glb")),
            ("V1 겹침 띠 섞기", os.path.join(OUT, "V1.glb")),
            ("V2 전신 정제 몸 + 머리 섞기", os.path.join(OUT, "V2.glb")),
            ("V3 조각별 정제 + 섞기", os.path.join(OUT, "V3.glb"))]
    views = [("목 · 원화 시점", (-0.09, 0.17, 0.80, 1.005, 180)),
             ("목 · 45도", (-0.09, 0.17, 0.80, 1.005, 225)),
             ("상체 · 원화 시점", (-0.25, 0.30, 0.45, 1.0, 180))]
    T = FC.T
    G, LW, TOP, CAP = 10, 150, 80, 30
    im = Image.new("RGB", (LW + len(cols) * (T + G), TOP + CAP + len(views) * (T + G)), "white")
    d = ImageDraw.Draw(im)
    d.text((16, 14), "은둔자 — 정제본과 원본을 잇는 세 길", fill="black", font=_font(26))
    d.text((16, 50), "머리는 넷 다 같은 DetailGen3D 머리 정제본 · 다른 것은 몸과 잇는 방법 · 면 법선 명암", fill=(90, 90, 90), font=_font(15))
    for i, (name, path) in enumerate(cols):
        m = FC.load(path)
        x = LW + i * (T + G)
        d.text((x, TOP + 4), name, fill="black", font=_font(16))
        for r, (_, box) in enumerate(views):
            im.paste(Image.fromarray(FC.face(m, box)), (x, TOP + CAP + r * (T + G)))
        print("  그림 %s" % name, flush=True)
    for r, (lab, _) in enumerate(views):
        d.text((12, TOP + CAP + r * (T + G) + T // 2), lab, fill="black", font=_font(16))
    q = os.path.join(HERE, "out", "은둔자_목잇기.png")
    im.save(q)
    print(" ->", q)


if __name__ == "__main__":
    a = sys.argv[1:] or ["준비"]
    {"준비": prepare, "정제": run_dg, "합침": merge, "그림": figure}[a[0]]()
