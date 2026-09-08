# -*- coding: utf-8 -*-
"""**3판을 기하로 깎는다.** 학습 없음, 생성 없음, 지어낼 여지 없음.

    python hull.py                 # 오메가몬 3판 -> out/hull.glb + 증명 그림

정면·측면·후면 실루엣이 각각 기둥을 만들고, 그 교집합이 형상의 **상한**이다
(Laurentini 의 visual hull). 오목부는 못 잡지만 **시점과 치수는 원리적으로 안 무너진다** —
없는 걸 지어내는 단계가 아예 없기 때문이다.

## 원화를 창에 앉히는 규약

턴어라운드 3판은 **같은 인물을 같은 키로** 그린다. 그래서 판마다 실루엣 높이를 창의
z 범위에 맞추면 세 판이 한 배율을 공유한다 — 이게 고전 화법기하의 전제다(Church Part I).
가로는 중심선 정렬.

**지시선을 먼저 뗀다.** `omega_side` 는 지시선 때문에 bbox 가로가 1024 인데 실제 물건은
248 이다(4.1배). 그대로 앉히면 인물이 창 왼쪽 구석으로 쭈그러든다.

## 이게 안 잡는 것

- 오목부 — 겨드랑이, 견갑 안쪽, 다리 사이. hull 은 언제나 실제보다 두껍다
- 3판이 서로 안 맞으면 hull 이 **과하게 깎인다.** 그 손실이 곧 「눈속임의 양」이다
"""
import os
import sys

import numpy as np
import trimesh
from skimage import measure

import win as W

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
IN7 = os.path.normpath(os.path.join(HERE, "..", "트레일", "trail7_part3d", "in"))
N = 256                                          # 복셀 격자. 창 한 변
BACK_SIGN = +1                                   # 이 시트의 후면 좌우 규약. **케이스 데이터**


def declutter(m, minh=8):
    """지시선 제거 — 열 높이가 minh 화소 미만인 열을 버린다 (trail7 규칙)."""
    return m & (m.sum(0) >= minh)[None, :]


def to_win(m):
    """원화 마스크를 창에 앉힌다. **키로 한 번** 재고 가로는 중심 정렬.

    창의 z 는 [-0.1, 1.1] 이고 물건은 z=0..1 에 선다 — `win.normalize` 와 같은 규약."""
    ys, xs = np.where(m)
    c = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h = int(round(W.RES / (W.Z1 - W.Z0)))        # z 1.0 이 차지하는 화소 수
    w = max(1, int(round(c.shape[1] * h / c.shape[0])))
    import cv2
    r = cv2.resize(c.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST).astype(bool)
    out = np.zeros((W.RES, W.RES), bool)
    top = int(round((W.Z1 - 1.0) / (W.Z1 - W.Z0) * W.RES))
    x0 = (W.RES - w) // 2
    ys0, ys1 = max(top, 0), min(top + h, W.RES)
    xs0, xs1 = max(x0, 0), min(x0 + w, W.RES)
    out[ys0:ys1, xs0:xs1] = r[:ys1 - ys0, :xs1 - xs0]
    return out


def carve(masks, back_sign=BACK_SIGN):
    """복셀 격자를 세 시점으로 깎는다. 격자는 창과 같은 좌표에 있다.

    **후면의 좌우 규약은 케이스 데이터다.** 렌더 규약(az180 화면 x = -x)을 그린 그림에
    그대로 대면 안 된다 — 오메가몬은 검과 포가 좌우로 갈린 비대칭 물건이라, 규약이
    뒤집히면 검이 포를 깎는다. 실측: -1 이면 정면 0.577 / 후면 0.554,
    +1 이면 정면 0.933 / 후면 0.919. 이 시트는 +1 이다."""
    u = W.U0 + (np.arange(N) + 0.5) / N * (W.U1 - W.U0)     # x 가로, y 깊이
    z = W.Z0 + (np.arange(N) + 0.5) / N * (W.Z1 - W.Z0)
    X, Y, Z = np.meshgrid(u, u, z, indexing="ij")
    keep = np.ones(X.shape, bool)
    for v, m in masks.items():
        a, sign = W.VIEW_AXIS[v]
        if v == "back":
            sign = back_sign
        py, px = W.topix(sign * (X if a == 0 else Y), Z)
        keep &= m[py, px]
    return keep, (u, u, z)


def mesh_from(vox, axes):
    """복셀 -> 메시. 경계에 0 을 한 겹 둘러 마칭큐브가 닫히게 한다."""
    p = np.pad(vox.astype(np.float32), 1)
    V, F, _, _ = measure.marching_cubes(p, 0.5)
    ux, uy, uz = axes
    sx, sy, sz = ux[1] - ux[0], uy[1] - uy[0], uz[1] - uz[0]
    V = np.stack([ux[0] + (V[:, 0] - 1) * sx,
                  uy[0] + (V[:, 1] - 1) * sy,
                  uz[0] + (V[:, 2] - 1) * sz], 1)
    return V, F


def main():
    os.makedirs(OUT, exist_ok=True)
    src = {"front": "omega_front_clean.png", "side": "omega_side.png", "back": "omega_back.png"}
    raw = {v: W.art_mask(os.path.join(IN7, f)) for v, f in src.items()}
    masks = {}
    for v, m in raw.items():
        d = declutter(m)
        bb = lambda a: (np.where(a.any(0))[0].ptp() + 1, np.where(a.any(1))[0].ptp() + 1)
        print("  %-6s bbox %s -> 지시선 뺀 뒤 %s" % (v, bb(m), bb(d)))
        masks[v] = to_win(d)

    vox, axes = carve(masks)
    print("\n  복셀 %d/%d 남음 (%.1f%%)" % (vox.sum(), vox.size, 100 * vox.sum() / vox.size))
    V, F = mesh_from(vox, axes)
    mesh = trimesh.Trimesh(V, F, process=True)
    mesh.export(os.path.join(OUT, "hull.glb"))
    print("  메시 정점 %d · 면 %d -> out/hull.glb" % (len(mesh.vertices), len(mesh.faces)))

    # 되받아 재기 — hull 은 제 3판과 (거의) 일치해야 한다. 안 그러면 앉히기가 틀린 것
    Vh, Fh = np.asarray(mesh.vertices), np.asarray(mesh.faces)
    print()
    for v in W.VIEWS:
        s = W.silhouette(Vh, Fh, v, BACK_SIGN if v == "back" else None)
        print("  %-6s 원화 대 hull  IoU %.3f" % (v, W.iou(masks[v], s)))
    return masks, mesh


if __name__ == "__main__":
    main()
