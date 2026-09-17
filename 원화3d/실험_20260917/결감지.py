# -*- coding: utf-8 -*-
"""**펴야 할 곳만 찾는다** — 칸보다 얕은데 방향만 흔들리는 면 (2026-09-17). 연구 루프 0 단계 탐침 · 점수 없음.

    python 결감지.py 검사     합성 셋(복셀 구 · 매끈한 구 · 홈 판 구)으로 문턱을 확인 — 틀리면 멈춘다
    python 결감지.py 그림     은둔자 얼굴 메시 넷에 감지된 면만 빨갛게 -> out/은둔자_결감지.png

**규칙 (은둔자에 걸기 전에 적음).**
    칸 h      메시 중앙 변 길이 (마칭큐브 한 칸 ≈ 변 하나)
    기준면    Taubin 으로 편 같은 메시 (부피를 지킨다)
    각        면 법선 ↔ 기준면의 같은 면 법선 > ANG
    얕음      꼭짓점 → 기준면 거리가 주변 RING 고리 안에서 모두 < DEPTH·h
    결        각 ∧ 얕음. 깊은 곳 (눈꺼풀 · 홈 바닥) 옆은 가장자리까지 뺀다
한계: 칸보다 얕은 진짜 모양(0.3mm 선)은 기하만으로 결과 못 가른다.
"""
import os
import sys

import numpy as np
import scipy.sparse as sp
import trimesh
from skimage import measure

ANG, DEPTH, RING, ITERS = 12.0, 0.75, 2, 100   # ITERS: 30 은 홈(폭 3 · 깊이 2 칸)을 94% 결로 잡음 -> 합성 셋만으로 100


def detect(m):
    """-> (면마다 결 여부, h). m 은 꼭짓점이 합쳐진 메시."""
    V, F = np.asarray(m.vertices), np.asarray(m.faces)
    h = float(np.median(m.edges_unique_length))
    s = m.copy()
    trimesh.smoothing.filter_taubin(s, iterations=ITERS)
    d = np.abs(((V - s.vertices) * s.vertex_normals).sum(1)) / h
    e = m.edges_unique
    A = sp.coo_matrix((np.ones(len(e) * 2), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(len(V),) * 2).tocsr()
    deep = d >= DEPTH
    for _ in range(RING):
        deep = deep | (A @ deep.astype(np.float32) > 0)
    cos = np.abs((m.face_normals * s.face_normals).sum(1))
    tilt = np.degrees(np.arccos(np.clip(cos, 0, 1))) > ANG
    return tilt & ~deep[F].any(1), h


def _sphere_vox(r=24, groove=False):
    g = np.mgrid[-32:33, -32:33, -32:33].astype(np.float32)
    rr = np.sqrt((g ** 2).sum(0))
    V, F, _, _ = measure.marching_cubes((rr < r).astype(np.float32), 0.5)
    return trimesh.Trimesh(V - 32, F)


def _sphere_smooth(r=24, groove=0.0):
    m = trimesh.creation.icosphere(subdivisions=5, radius=r)
    V = m.vertices.copy()
    if groove:
        z = V[:, 2]
        w = np.clip(1.5 - np.abs(z), 0, 1)                    # 폭 3 칸 · 가장자리 1 칸 경사
        V *= (1 - groove * w / r)[:, None]
    return trimesh.Trimesh(V, m.faces), (np.abs(m.vertices[:, 2]) < 2.5)[m.faces].all(1)


def selfcheck():
    a, h = detect(_sphere_vox())
    b, _ = detect(_sphere_smooth()[0])
    g_mesh, band = _sphere_smooth(groove=2.0)
    c, _ = detect(g_mesh)
    fa, fb, fc = a.mean(), b.mean(), c[band].mean()
    print("  복셀 구 결 %.2f (> 0.5 여야) · 매끈한 구 %.3f (< 0.05) · 홈(폭 3 · 깊이 2 칸) 안 %.3f (< 0.2) · h %.2f" % (fa, fb, fc, h))
    assert fa > 0.5 and fb < 0.05 and fc < 0.2, "문턱이 합성 셋을 못 가른다 — 은둔자에 걸지 않는다"
    print("  자가검사 통과")


def figure():
    import cv2
    from PIL import Image, ImageDraw
    sys.path.insert(0, os.path.dirname(__file__))
    import 얼굴비교 as FC
    from 계획 import _font
    meshes = [
        ("TripoSG 원출력", "out/은둔자.glb", FC.BOX_NAMU),
        ("+ DetailGen3D 머리 정제", "out/은둔자_머리정제.glb", FC.BOX_NAMU),
        ("A 3판 hull (지금 기본)", "out/은둔자삼면_A.glb", FC.BOX_3),
        ("C′ A 를 DetailGen3D 정제", "out/은둔자삼면_dgA_front.glb", FC.BOX_3),
    ]
    T = FC.T
    cols = []
    for name, path, box in meshes:
        m = FC.load(path)
        x0, x1, z0, z1, az = box
        c = m.triangles_center
        keep = (c[:, 2] > z0 - 0.03) & (c[:, 0] > x0 - 0.05) & (c[:, 0] < x1 + 0.05)
        sub = m.submesh([np.nonzero(keep)[0]], append=True)
        sub.merge_vertices()
        flag, h = detect(sub)
        tint = np.where(flag[:, None], [1.0, 0.25, 0.2], [1.0, 1.0, 1.0])
        tiles = [FC.face(sub, (x0, x1, z0, z1, a), tint=tint) for a in (az, az + 45)]
        print("  %-26s 면 %7d · h %.4f · 결 %.1f%%" % (name, len(flag), h, 100 * flag.mean()), flush=True)
        cols.append((name, flag.mean(), tiles))
    G, LW, TOP, CAP = 10, 110, 80, 30
    im = Image.new("RGB", (LW + len(cols) * (T + G), TOP + 2 * (T + G) + CAP), "white")
    d = ImageDraw.Draw(im)
    d.text((16, 14), "은둔자 얼굴 — 펴야 할 곳(빨강)만 감지", fill="black", font=_font(26))
    d.text((16, 50), "빨강 = 기준면(Taubin)과 %d° 넘게 틀어졌는데 주변 %d 고리 안이 모두 칸의 %.2f 배보다 얕은 면 · 칸 = 메시 중앙 변 길이"
           % (ANG, RING, DEPTH), fill=(90, 90, 90), font=_font(15))
    for i, (name, frac, tiles) in enumerate(cols):
        x = LW + i * (T + G)
        d.text((x, TOP + 4), "%s · 결 %.0f%%" % (name, 100 * frac), fill="black", font=_font(16))
        for r, t in enumerate(tiles):
            im.paste(Image.fromarray(t), (x, TOP + CAP + r * (T + G)))
    for r, lab in enumerate(("원화 시점", "45도")):
        d.text((12, TOP + CAP + r * (T + G) + T // 2), lab, fill="black", font=_font(16))
    q = os.path.join("out", "은둔자_결감지.png")
    im.save(q)
    print(" ->", q)


if __name__ == "__main__":
    a = sys.argv[1:] or ["검사"]
    if a[0] == "검사":
        selfcheck()
    elif a[0] == "그림":
        selfcheck()
        figure()
