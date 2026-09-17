# -*- coding: utf-8 -*-
"""**은둔자 공식 삼면도로 3판 파이프라인을 끝까지** (2026-09-17). 계획 `claudedocs/plan_은둔자삼면_20260917.md`.

    python 은둔자삼면.py 깎기        A 지금 기본 · B 생성∩hull -> out/은둔자삼면_{A,B}.glb · 정제 입력(원좌표) -> 스크래치 h3/
    (DetailGen3D 를 imggen venv 에서 두 번 — 정면 판 C · 빈 이미지 C0)
    python 은둔자삼면.py 합침그림    C · C0 를 창 좌표로 되돌려 재고 명암 그림 -> out/은둔자삼면_명암.png · out/기록/은둔자삼면_<때>.json

정답 메시가 없다 — 판정은 원화 3판 일치 · 눈으로만 하고 「관찰」 등급이다.
"""
import json
import os
import sys
import time

import numpy as np
import trimesh

HERE = r"G:\art2real\원화3d"
for d in ("", "실험_20260913", "실험_20260915", "실험_20260916"):
    sys.path.insert(0, os.path.join(HERE, d))
os.chdir(HERE)
import hull as H
import win as W
import 표면 as SF
import 앨리어싱 as AL
import 깊이색 as DC
import 폴리싱 as PL
import 생성3D as G3
from 생성깎기 import sil_fit, voxelize
from 조각생성 import trim

CASE = "은둔자"
H.CASES[CASE] = {"src": {v: v + ".png" for v in W.VIEWS}, "dir": os.path.join("out", "은둔자_자료", "삼면"), "back_sign": +1}
S = r"C:\Users\zesky\AppData\Local\Temp\claude\G--art2real\612c5d2a-3321-47b1-8ebf-c897df4a0801\scratchpad\h3"
GEN = os.path.join(S, "hermit_front.glb")


def build():
    src, base = H.CASES[CASE]["src"], H.art_dir(CASE)
    masks = {v: H.to_win(H.declutter(W.art_mask(os.path.join(base, f)))) for v, f in src.items()}
    bs = H.CASES[CASE]["back_sign"]
    masks = H._warp(masks, H.align(masks, back_sign=bs))
    plain, axes = H.carve(masks, back_sign=bs)
    deps = {v: np.ones((W.RES, W.RES), np.float32) for v in W.VIEWS}
    base_vox, _ = H.carve_default(masks, deps, back_sign=bs)
    return masks, bs, plain, base_vox, axes


def orient_raw(V0, masks):
    """`생성3D.orient` 와 같은 선택 — 그런데 **돌린 값(k, mir)도 돌려준다.** 정제기에 넣을 때 원좌표로 되돌려야 해서."""
    sc, V, yaw, mir = G3.orient(V0, masks)
    k = yaw // 90
    c, s = np.cos(k * np.pi / 2), np.sin(k * np.pi / 2)
    R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    return V, R, mir


def win_to_raw(V, R, mir):
    """창 좌표 -> TripoSG 원좌표 (y 위). `to_world("xyz")` · 회전 · 반전을 거꾸로 (정규화는 정제기가 bbox 로 다시 하니 안 되돌린다)."""
    Wd = (V * np.array([mir, 1, 1])) @ R                     # R 은 직교 — (V @ R.T) 의 역은 @ R
    return np.stack([Wd[:, 0], Wd[:, 2], Wd[:, 1]], 1)       # (x가로, y깊이, z위) -> (x, y위, z깊이)


def raw_to_win(V, R, mir):
    return (W.to_world(V, "xyz") @ R.T) * np.array([mir, 1, 1])


def to_mesh(vox, axes):
    m = trimesh.Trimesh(*H.mesh_from(vox, axes), process=True)
    if m.volume < 0:
        m.invert()
    return m


def rec(name, vox, masks, bs, axes, plain):
    r = sil_fit(vox, masks, bs, axes)
    r.update({"조각": SF.pieces(vox), "hull밖": round(float((vox & ~plain).sum() / max(vox.sum(), 1)), 4)})
    print("  %-10s 못덮음 f%.2f s%.2f · 넘침 f%.2f s%.2f · 조각 %d · hull밖 %.2f%%"
          % (name, 100 * r["못덮음_front"], 100 * r["못덮음_side"], 100 * r["넘침_front"], 100 * r["넘침_side"], r["조각"], 100 * r["hull밖"]), flush=True)
    return r


def carve():
    masks, bs, plain, A, axes = build()
    # 부스러기를 먼저 턴다 — 118 덩이 중 부피 있는 건 1 개인데 부스러기가 가로 bbox 를 0.91 -> 1.44 로 늘려
    # 3판맞춤이 몸을 가로로 눌렀다 (정면 못덮음 44%, 09-17 실측)
    g = trim(trimesh.load(GEN, force="mesh"))
    V, R, mir = orient_raw(g.vertices, masks)
    V = G3.fit_to_art(V, masks)
    gen = voxelize(trimesh.Trimesh(V, np.asarray(g.faces), process=False), axes)
    B = gen & plain
    out = {"A 지금 기본": rec("A 지금기본", A, masks, bs, axes, plain), "생성(깎기 전)": rec("생성", gen, masks, bs, axes, plain),
           "B 생성∩hull": rec("B 생성∩hull", B, masks, bs, axes, plain)}
    for tag, vox in (("A", A), ("B", B)):
        to_mesh(vox, axes).export(os.path.join(HERE, "out", "은둔자삼면_%s.glb" % tag))
    mb = to_mesh(B, axes)
    raw = trimesh.Trimesh(win_to_raw(np.asarray(mb.vertices), R, mir), np.asarray(mb.faces), process=False)
    raw.export(os.path.join(S, "B_raw.glb"))
    np.save(os.path.join(S, "orient.npy"), np.r_[R.ravel(), mir])
    json.dump(out, open(os.path.join(S, "carve.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  정제 입력 -> %s (원좌표 · 회전 %s · 반전 %+d)" % (os.path.join(S, "B_raw.glb"), np.round(R[0, :2], 2), mir))


def back_from_dg(path, raw_in, R, mir):
    m = trimesh.load(path, force="mesh")
    c, s = raw_in.bounding_box.centroid, 1.9 / max(raw_in.bounding_box.extents)
    V = np.asarray(m.vertices) / s + c                        # DetailGen3D 정규화(중심 · 최대변 1.9)를 거꾸로
    return trimesh.Trimesh(raw_to_win(V, R, mir), np.asarray(m.faces), process=True)


def merge_figure():
    masks, bs, plain, A, axes = build()
    o = np.load(os.path.join(S, "orient.npy")); R, mir = o[:9].reshape(3, 3), float(o[9])
    raw_in = trimesh.load(os.path.join(S, "A_raw.glb"), force="mesh")        # 사후: B 가 배관에서 떨어져 A 를 정제했다
    res = json.load(open(os.path.join(S, "carve.json"), encoding="utf-8"))
    meshes = {"A 지금 기본": trimesh.load(os.path.join(HERE, "out", "은둔자삼면_A.glb"), force="mesh"),
              "B 생성∩hull": trimesh.load(os.path.join(HERE, "out", "은둔자삼면_B.glb"), force="mesh")}
    for tag, sub in (("C′ A 정제", "dgA_front"), ("C′0 대조(빈 이미지)", "dgA_blank")):
        m = back_from_dg(os.path.join(S, sub, "A_raw.glb"), raw_in, R, mir)
        m.export(os.path.join(HERE, "out", "은둔자삼면_%s.glb" % sub))
        meshes[tag] = m
        vox = voxelize(m, axes)
        res[tag] = rec(tag, vox, masks, bs, axes, plain)
    res["때"] = time.strftime("%Y-%m-%d %H:%M")
    q = os.path.join(HERE, "out", "기록", "은둔자삼면_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump(res, open(q, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ref = meshes["A 지금 기본"]
    azs = (0, 45, 90, 180)
    fr = {az: AL.frame_of(ref, az) for az in azs}
    rows = [(n, [PL.shaded(m, az, fr[az], 380) for az in azs]) for n, m in meshes.items()]
    DC.grid(rows, ["정면", "45도", "옆", "뒤"],
            "은둔자 — 공식 삼면도(정면 · 옆 · 뒤)로 3판 파이프라인 끝까지",
            "A 3판 hull 타원 · B TripoSG(정면 판) ∩ hull (배관 실패) · C′ A 를 DetailGen3D 로 정제 · C′0 같은 정제에 빈 이미지 (면 법선 명암 · 같은 틀)",
            os.path.join(HERE, "out", "은둔자삼면_명암.png"))
    print("  -> %s" % q)


if __name__ == "__main__":
    a = sys.argv[1:] or ["깎기"]
    if a[0] == "깎기":
        carve()
    elif a[0] == "합침그림":
        merge_figure()
