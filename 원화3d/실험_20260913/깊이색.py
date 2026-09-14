# -*- coding: utf-8 -*-
"""**결을 깊이색 + 등깊이선으로 본다** — 명암 렌더러가 두 번 틀려서 조명을 뺐다.

    python 깊이색.py     -> out/깊이색_오메가몬.png · out/깊이색_도형.png

화소마다 **제일 가까운 면의 깊이**(z 버퍼)를 색으로 칠하고, 깊이를 일정 간격으로 끊은 **등깊이선**을 검게 긋는다.
매끈한 면이면 등깊이선이 매끈한 곡선이고, 계단진 면이면 선이 톱니처럼 끊긴다 — 결이 선의 모양으로 보인다.
조명 · 법선을 안 쓰므로 `앨리어싱.py` 렌더러의 두 실패(큰 면 · 명암 반전)가 여기선 안 생긴다.

    오메가몬   out/앨리어싱_<기준|ITK|가우시안>.glb  (앨리어싱.py 가 낸 것)
    도형       복셀 hull (오라클.build 의 plain) vs 정확 hull (정확hull.exact_hull) — 원기둥 · 원뿔 · 구 · 토러스세움 · 치마

같은 줄 안에서는 **틀(화면 범위)과 깊이 범위를 기준 판본 하나에 맞춘다** — 판본끼리 색이 같은 깊이를 뜻한다.
"""
import os
import sys

import cv2
import numpy as np
import trimesh

HERE = r"G:\art2real\원화3d"
SCR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, SCR)
os.chdir(HERE)
LINES = 40                                        # 깊이 범위를 몇 칸으로 끊어 선을 긋나


def project(mesh, az, frame, S):
    a = np.radians(az)
    c, s = np.cos(a), np.sin(a)
    V = np.asarray(mesh.vertices)
    X, Y, Z = c * V[:, 0] - s * V[:, 1], s * V[:, 0] + c * V[:, 1], V[:, 2]
    (x0, z0), span = frame
    return np.stack([(X - x0) / span * S, (1 - (Z - z0) / span) * S, Y], 1)


def zbuffer(mesh, az, frame, S):
    """화소마다 제일 가까운(−y 쪽) 깊이. 2 배로 그려 2×2 최솟값으로 줄인다 — 화소보다 작은 삼각형이 구멍을 안 남기게."""
    R = 2 * S
    P = project(mesh, az, frame, R)[np.asarray(mesh.faces)]          # (n, 3, 3) x · y · 깊이
    zb = np.full((R, R), np.inf)
    lo = np.clip(np.floor(P[:, :, :2].min(1)), 0, R - 1).astype(int)
    hi = np.clip(np.ceil(P[:, :, :2].max(1)), 0, R - 1).astype(int)
    for i in range(len(P)):
        (x1, y1, d1), (x2, y2, d2), (x3, y3, d3) = P[i]
        den = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
        if abs(den) < 1e-12:
            continue
        gx, gy = np.meshgrid(np.arange(lo[i, 0], hi[i, 0] + 1) + 0.5, np.arange(lo[i, 1], hi[i, 1] + 1) + 0.5)
        l1 = ((y2 - y3) * (gx - x3) + (x3 - x2) * (gy - y3)) / den
        l2 = ((y3 - y1) * (gx - x3) + (x1 - x3) * (gy - y3)) / den
        l3 = 1 - l1 - l2
        m = (l1 >= -1e-9) & (l2 >= -1e-9) & (l3 >= -1e-9)
        if not m.any():
            continue
        d = l1 * d1 + l2 * d2 + l3 * d3
        sub = zb[lo[i, 1]:hi[i, 1] + 1, lo[i, 0]:hi[i, 0] + 1]
        up = m & (d < sub)
        sub[up] = d[up]
    return zb.reshape(S, 2, S, 2).min((1, 3))


def colorize(zb, drange):
    """깊이 -> turbo 색 (가까울수록 빨강) + 등깊이선 검정 · 배경 흰색."""
    d0, d1 = drange
    on = np.isfinite(zb)
    t = np.clip((zb - d0) / max(d1 - d0, 1e-9), 0, 1)
    img = cv2.applyColorMap(((1 - t) * 255).astype(np.uint8), cv2.COLORMAP_TURBO)
    band = np.where(on, np.floor(t * LINES), -1)
    edge = np.zeros(zb.shape, bool)
    edge[:, 1:] |= (band[:, 1:] != band[:, :-1]) & on[:, 1:] & on[:, :-1]
    edge[1:, :] |= (band[1:, :] != band[:-1, :]) & on[1:, :] & on[:-1, :]
    img[edge] = (20, 20, 20)
    img[~on] = (250, 250, 250)
    return img[:, :, ::-1]                                           # RGB


def depth_range(mesh, az):
    a = np.radians(az)
    V = np.asarray(mesh.vertices)
    Y = np.sin(a) * V[:, 0] + np.cos(a) * V[:, 1]
    return float(Y.min()), float(Y.max())


def grid(rows, cols, title, sub, path, S=400):
    """rows: [(이름, [타일 RGB ...])]"""
    from PIL import Image, ImageDraw
    from 계획 import _font
    G, LW, TOP = 10, 150, 96
    im = Image.new("RGB", (LW + len(cols) * (S + G), TOP + len(rows) * (S + G)), "white")
    d = ImageDraw.Draw(im)
    d.text((18, 14), title, fill=(20, 20, 20), font=_font(24))
    d.text((18, 50), sub, fill=(90, 90, 90), font=_font(14))
    for j, c in enumerate(cols):
        d.text((LW + j * (S + G), TOP - 22), c, fill=(40, 40, 40), font=_font(16))
    for i, (name, tiles) in enumerate(rows):
        d.text((18, TOP + i * (S + G) + S // 2), name, fill=(20, 20, 20), font=_font(17))
        for j, t in enumerate(tiles):
            im.paste(Image.fromarray(cv2.resize(t, (S, S), interpolation=cv2.INTER_NEAREST)), (LW + j * (S + G), TOP + i * (S + G)))
    im.save(path)
    print("  -> %s" % os.path.relpath(path, HERE))


def omega():
    import 앨리어싱 as AL
    names = ("기준", "ITK", "ITK국소", "가우시안")
    meshes = {n: trimesh.load(os.path.join(HERE, "out", "앨리어싱_%s.glb" % n), force="mesh") for n in names}
    rows = []
    views = ((-90, 1.0), (45, 1.0))
    fr = {az: AL.frame_of(meshes["기준"], az) for az, _ in views}
    dr = {az: depth_range(meshes["기준"], az) for az, _ in views}
    # 옆 가슴 확대 — 옆 틀의 가로 25~75% · 세로 20~50% 만 3 배 해상도로
    (x0, z0), span = fr[-90]
    zoom = ((x0 + 0.30 * span, z0 + 0.45 * span), 0.35 * span)
    for n in names:
        tiles = [colorize(zbuffer(meshes[n], az, fr[az], 400), dr[az]) for az, _ in views]
        tiles.append(colorize(zbuffer(meshes[n], -90, zoom, 400), dr[-90]))
        rows.append((n, tiles))
        print("  %s 그림" % n, flush=True)
    grid(rows, ["옆 (az −90)", "45도", "옆 가슴 확대"], "오메가몬 hull — 깊이색 + 등깊이선 (조명 없음 · z 버퍼)",
         "빨강 = 가깝다 · 파랑 = 멀다 · 검은 선 = 같은 깊이. 선이 매끈하면 면이 매끈하고, 톱니면 계단이다. 같은 열은 틀 · 깊이 범위가 같다",
         os.path.join(HERE, "out", "깊이색_오메가몬.png"))


def shapes(names=("원기둥", "원뿔", "구", "토러스세움", "치마")):
    import 오라클 as O
    import 정확hull as EX
    O.H.register_sheets()
    vox_row, ex_row = [], []
    for n in names:
        case = "도형_" + n
        truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
        plain, _, axes, _ = O.build(case, truth, 0.20, "파이프")
        vh, eh = O.C.to_mesh(plain, axes), EX.exact_hull(truth)
        import 앨리어싱 as AL
        fr, dr = AL.frame_of(vh, 45), depth_range(vh, 45)
        vox_row.append(colorize(zbuffer(vh, 45, fr, 400), dr))
        ex_row.append(colorize(zbuffer(eh, 45, fr, 400), dr))
        print("  %s 그림" % n, flush=True)
    grid([("복셀 hull", vox_row), ("정확 hull", ex_row)], list(names),
         "도형 — 복셀 hull vs 정확 hull · 깊이색 + 등깊이선 (45도 · z 버퍼)",
         "같은 열은 틀 · 깊이 범위가 같다. 등깊이선이 톱니면 계단, 매끈하면 매끈한 면",
         os.path.join(HERE, "out", "깊이색_도형.png"))


def selfcheck():
    """구 하나 — z 버퍼 깊이가 해석 깊이와 맞아야 한다 (가운데 화소 = 구의 앞 끝 −r)."""
    m = trimesh.creation.icosphere(subdivisions=4, radius=0.5)
    fr = ((-0.6, -0.6), 1.2)
    zb = zbuffer(m, 0, fr, 120)
    mid = zb[60, 60]
    assert abs(mid - (-0.5)) < 0.01, "z 버퍼: 구 가운데 깊이 %.4f (답 −0.5)" % mid
    assert np.isfinite(zb).sum() > 0.5 * np.pi * 50 ** 2, "z 버퍼: 구멍이 많다"
    print("  자가검사 통과 — 구 가운데 깊이 %.4f (답 −0.5)" % mid)


if __name__ == "__main__":
    selfcheck()
    what = sys.argv[1] if len(sys.argv) > 1 else "둘"
    if what in ("오메가몬", "둘"):
        omega()
    if what in ("도형", "둘"):
        shapes()
