# -*- coding: utf-8 -*-
"""**판으로 부품을 가른다. 짓지 않고 잘라낸다.**

    python 부품.py        ->  out/부품.glb + out/부품.png + 부품표

## 왜 짓지 않고 자르나

판마다 3D 물체를 따로 만들어 세우는 길은 이 저장소에서 두 번 죽었다. 스킬의 `relief.py`
문서가 그대로 적어놨다 — 「판 49개를 각각 물체로 만들고 각각 **guessed 깊이**로 밀면 서로
겹치고 파편이 된다. 부품 IoU 0.892 가 전체 0.619 로 무너진 게 그것이다.」

죽은 원인은 **지어낸 깊이**였다. 지금은 `hull.py` 가 잰 덩어리를 준다. 그래서 뒤집는다:

    지으면   부품마다 깊이를 지어내고 -> 겹치거나 뜨거나 한다
    자르면   하나의 잰 덩어리를 나눈다 -> **겹칠 수가 없고 뜰 수가 없다**

부품들의 부피 합은 원래 덩어리와 정확히 같다. 그게 이 파일의 자체검사다.

## 어느 판에 주나

복셀마다 앞면·뒷면 중 **가까운 쪽 껍질의 판**을 준다. 앞 절반은 front 판, 뒤 절반은
back 판이다. 측면 판은 안 쓴다 — 한쪽 면만 보여줘서 반대쪽을 못 말한다.

## 두 단위로 낸다

    판 단위     원화가 그은 판 그대로. 조형·검사용이고 수가 많다
    재질 단위   흰 · 금 · 청회 · 검정으로 묶은 뒤 3D 로 이어진 덩이만 나눈다.
                **따로 뜨고 따로 칠할 실제 단위**다

재질 분류는 art3d 가 쓰는 규칙 그대로다 (`r-b>40 & r>130` 금 · `b-r>12` 청회 · 어두우면 검정).
새로 만들지 않는다.

두 단위 다 **3D 연결성으로 한 번 더 쪼갠다.** 2D 로 한 판이어도 3D 에서 두 덩이로 갈릴 수
있다(다리 사이를 건너는 판). 안 쪼개면 「한 부품」이 공중에 떨어져 두 조각인 채로 나간다 —
실측 63/208 이 그랬다.

## 안 하는 것

거울 대칭으로 짝을 묶지 않는다. 오메가몬은 검과 포가 좌우로 갈린 **비대칭** 물건이라
대칭을 가정하면 없는 것을 지어내는 것이다.
"""
import os
import sys
from collections import Counter

import numpy as np
import trimesh
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull as H
import win as W
from 계획 import _font

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
MIN_VOX = 200                                    # 이보다 작은 부품은 버린다. 출력도 못 한다
SRC = {"front": "omega_front_clean.png", "side": "omega_side.png", "back": "omega_back.png"}


def build():
    """정렬까지 끝난 마스크·깊이·라벨과 깎은 덩어리."""
    masks, deps, labs = {}, {}, {}
    for v, f in SRC.items():
        d = H.declutter(W.art_mask(os.path.join(H.IN7, f)))
        dep = H.load_depth(v, d) if H.DEPTH == "파이프" else np.ones(d.shape, np.float32)   # 타원 기본은 깊이맵을 안 쓴다 — 낡은 깊이맵 예외로 안 멈추게
        masks[v], deps[v], labs[v] = H.to_win(d, dep, H.load_labels(v, d))
    p = H.align(masks)
    masks = H._warp(masks, p)
    deps = {v: H._warp_one(a, v, p) for v, a in deps.items()}
    labs = {v: H._warp_one(a, v, p) for v, a in labs.items()}
    vox, axes = H.carve_default(masks, deps)         # 제품 기본 깎기 (09-15 타원 lam1.00)
    return vox, axes, labs


def material(v):
    """판 번호 -> 재질 (0 흰 · 1 금 · 2 청회 · 3 검정). **art3d 의 색상 규칙 그대로.**"""
    import json
    # 케이스 폴더를 뺀 옛 경로였다 — `hull.load_depth` 가 케이스별로 옮긴 뒤 이 줄만 남았다 (09-13 시계에서 걸림)
    j = json.load(open(os.path.join(OUT, "깊이", H.CASE, v, "art3d.json"), encoding="utf-8"))
    out = {}
    for r in j["regions"]:
        rr, gg, bb = r["rgb"]
        lum = (rr + gg + bb) / 3
        out[r["id"]] = 3 if lum < 90 else (1 if (rr - bb > 40 and rr > 130) else
                                           (2 if bb - rr > 12 else 0))
    return out


def split3d(part):
    """3D 로 안 이어진 조각은 다른 부품이다. 번호를 다시 매긴다."""
    out = np.zeros_like(part)
    n = 0
    for pid in np.unique(part[part > 0]):
        lab, k = ndimage.label(part == pid)
        for c in range(1, k + 1):
            n += 1
            out[lab == c] = n
    return out, n


def assign(vox, labs):
    """복셀마다 부품 번호. 가까운 쪽 껍질의 판을 준다."""
    u = W.U0 + (np.arange(H.N) + 0.5) / H.N * (W.U1 - W.U0)
    z = W.Z0 + (np.arange(H.N) + 0.5) / H.N * (W.Z1 - W.Z0)
    X2, Z2 = np.meshgrid(u, z, indexing="ij")
    def sample(v):
        sign = H.BACK_SIGN if v == "back" else W.VIEW_AXIS[v][1]
        py, px = W.topix(sign * X2, Z2)
        return np.rint(labs[v][py, px]).astype(np.int32)
    lo, hi = H.surfaces(vox)
    mid = (lo + hi) / 2.0
    j = np.arange(H.N)[None, :, None]
    front = j <= mid[:, None, :]
    ids = np.where(front, sample("front")[:, None, :], sample("back")[:, None, :] + 1000000)
    return np.where(vox, ids, 0)                 # 0 = 빈 곳. back 은 +1000000 로 겹침 방지


def main():
    os.makedirs(OUT, exist_ok=True)
    vox, axes, labs = build()
    part = assign(vox, labs)
    mats = {v: material(v) for v in ("front", "back")}
    ids, cnt = np.unique(part[part > 0], return_counts=True)
    small = {int(i) for i, c in zip(ids, cnt) if c < MIN_VOX}
    # **작은 부품은 버리지 않고 이웃에 붙인다.** 못 찍을 만큼 작은 조각이라도 부피는 진짜다 —
    # 버리면 덩어리에 구멍이 남는다. 제일 가까운 큰 부품으로 채운다 (라벨 0 채우기와 같은 수).
    if small:
        gap = np.isin(part, list(small)) & (part > 0)
        idx = ndimage.distance_transform_edt(gap | (part == 0), return_distances=False,
                                             return_indices=True)
        filled = part[tuple(idx)]
        part = np.where(gap, filled, part)
        part = np.where(vox, part, 0)
    part, _ = split3d(part)                      # 3D 로 떨어진 조각은 다른 부품
    ids, cnt = np.unique(part[part > 0], return_counts=True)
    keep = [(int(i), int(c)) for i, c in zip(ids, cnt)]
    keep.sort(key=lambda t: -t[1])
    dropped = 0
    print("  부품 후보 %d 개 -> %d 개 (복셀 %d 미만 %d 개는 버리지 않고 이웃에 붙였다)"
          % (len(ids) + len(small), len(keep), MIN_VOX, len(small)))

    scene, meshes = trimesh.Scene(), {}
    rng = np.random.default_rng(7)
    for pid, c in keep:
        m = part == pid
        V, F = H.mesh_from(m, axes)
        g = trimesh.Trimesh(V, F, process=True)
        if g.volume < 0:
            g.invert()
        col = (rng.integers(70, 235, 3).tolist() + [255])
        g.visual.face_colors = col
        name = "%s_%d" % ("back" if pid > 1000000 else "front", pid % 1000000)
        scene.add_geometry(g, node_name=name)
        meshes[pid] = (name, col)
    scene.export(os.path.join(OUT, "부품.glb"))

    # ── 자체검사: 자른 것이므로 부피 합이 원래와 같아야 한다 ──
    total = int(vox.sum())
    got = int(sum(c for _, c in keep)) + dropped
    assert got == total, "부품이 덩어리를 다 안 덮는다 (%d / %d) — 자르기가 아니라 짓고 있다" % (got, total)
    print("  복셀 %d 개가 부품 %d 개로 **빠짐없이** 갈렸다 (버린 것 없음)" % (total, len(keep)))

    # 부품마다 조각이 하나인가 — 둘이면 같은 판 번호가 두 군데 쓰인 것이다
    multi = 0
    for pid, _ in keep:
        if ndimage.label(part == pid)[1] > 1:
            multi += 1
    print("  조각이 둘 이상인 부품 %d / %d (같은 판 번호가 떨어진 두 곳에 쓰였다는 뜻)"
          % (multi, len(keep)))
    print("  -> out/부품.glb")

    # ── 재질 단위 ────────────────────────────────────────────
    raw = assign(vox, labs)
    mat = np.zeros_like(raw)
    for v, off, base in (("front", 0, 1), ("back", 1000000, 5)):
        m = (raw > 0) & ((raw >= 1000000) if off else (raw < 1000000))
        pid = raw - off
        look = np.vectorize(lambda k: mats[v].get(int(k), 0))
        u = np.unique(pid[m])
        tab = {int(k): base + look(k) for k in u}
        out = np.zeros_like(raw)
        for k, val in tab.items():
            out[m & (pid == k)] = val
        mat = np.where(m, out, mat)
    cls_of = mat.copy()                          # split3d 가 번호를 갈아치우기 전에 재질을 남긴다
    mat, nmat = split3d(mat)
    mids, mcnt = np.unique(mat[mat > 0], return_counts=True)
    big = [(int(i), int(c)) for i, c in zip(mids, mcnt) if c >= MIN_VOX]
    big.sort(key=lambda t: -t[1])
    print("\n  재질로 묶으면 %d 덩이 (복셀 %d 이상은 %d 덩이, 전체의 %.1f%%)"
          % (nmat, MIN_VOX, len(big), 100 * sum(c for _, c in big) / vox.sum()))
    sc2 = trimesh.Scene()
    MC = {1: (238, 238, 236), 2: (214, 178, 74), 3: (108, 132, 190), 4: (58, 58, 62),
          5: (238, 238, 236), 6: (214, 178, 74), 7: (108, 132, 190), 8: (58, 58, 62)}
    src_mat = {}
    for pid, c in big:
        m = mat == pid
        cls = int(np.bincount(cls_of[m]).argmax())
        V, F = H.mesh_from(m, axes)
        g = trimesh.Trimesh(V, F, process=True)
        if g.volume < 0:
            g.invert()
        col = MC.get(cls, (200, 200, 200))
        g.visual.face_colors = list(col) + [255]
        sc2.add_geometry(g, node_name="mat%d_%d" % (cls, pid))
        src_mat[pid] = col
    sc2.export(os.path.join(OUT, "재질부품.glb"))
    print("  -> out/재질부품.glb")
    return vox, part, keep, meshes, mat, big, src_mat


def sheet(part, keep, meshes, tag="부품", title="", az=(0, 30, 60), R=380):
    """부품을 색으로 칠해 본다. 앞면 껍질의 부품 번호를 그대로 색으로."""
    cmap = {pid: meshes[pid][1][:3] for pid, _ in keep}
    img = []
    for a in az:
        v = ndimage.rotate(part.astype(np.float32), a, axes=(0, 1), order=0,
                           reshape=False, prefilter=False)
        v = np.rint(v).astype(np.int64)
        occ = v > 0
        first = np.where(occ, np.arange(v.shape[1])[None, :, None], v.shape[1] + 1).argmin(1)
        idx = np.take_along_axis(v, first[:, None, :], 1)[:, 0, :]
        hit = occ.any(1)
        rgb = np.full(idx.shape + (3,), 255, np.uint8)
        for pid, c in cmap.items():
            rgb[(idx == pid) & hit] = c
        rgb[hit & ~np.isin(idx, list(cmap))] = (215, 215, 215)
        img.append(Image.fromarray(np.rot90(rgb)).resize((R, R), Image.NEAREST))
    sh = Image.new("RGB", (len(az) * (R + 14) + 14, R + 84), "white")
    d = ImageDraw.Draw(sh)
    d.text((14, 12), title, font=_font(19), fill=(20, 20, 20))
    d.text((14, 38), "지은 게 아니라 잰 덩어리를 자른 것. 부피 합이 원래와 같다",
           font=_font(12), fill=(120, 120, 120))
    for i, im in enumerate(img):
        sh.paste(im, (14 + i * (R + 14), 62))
    sh.save(os.path.join(OUT, "%s.png" % tag))
    print("  -> out/%s.png" % tag)


if __name__ == "__main__":
    vox, part, keep, meshes, mat, big, mcol = main()
    sheet(part, keep, meshes, tag="부품", title="판으로 가른 부품 %d 개" % len(keep))
    sheet(mat, big, {p: (None, list(c) + [255]) for p, c in mcol.items()},
          tag="재질부품", title="재질로 묶은 덩이 %d 개 — 따로 뜨고 따로 칠할 단위" % len(big))
