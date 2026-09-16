# -*- coding: utf-8 -*-
"""**조각마다 생성해서 다시 합친다** (시험 C · 2026-09-16).

    python 조각생성.py 앉힘      조각 glb 를 제자리에 앉혀 합치고 잰다 -> out/기록/조각생성_<때>.json
    python 조각생성.py 그림      명암 · 깊이색 네 칸 -> out/조각생성_명암.png

계획 · 판정은 `claudedocs/plan_조각생성_20260916.md` 그대로. 조각 크롭은 `트레일/trail7_part3d/in/c0_mask.npy` (손으로 나눈 26 조각),
생성은 `run_triposg.py ... --no-rmbg` 로 미리 돌려 둔 것을 읽는다 (조각당 약 110초).

**08-30 이 잰 것이 이 시험의 근거다** — 전신을 넣으면 생성 격자 한 칸이 원본 3.61 화소라 얼굴 먹선(1.9 화소)이 사라지고,
조각으로 자르면 한 칸이 0.32~1.98 화소가 된다. 같은 모델 · 같은 원화인데 조각이 2~11배 촘촘하다.
"""
import glob
import json
import os
import sys
import time

import cv2
import numpy as np
import trimesh

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "실험_20260913"))
sys.path.insert(0, os.path.join(HERE, "실험_20260915"))
sys.path.insert(0, os.path.join(HERE, "실험_20260916"))
os.chdir(HERE)
import hull as H
import win as W
import 표면 as SF
import 앨리어싱 as AL
import 깊이색 as DC
import 생성3D as G3
import 폴리싱 as PL
from 생성깎기 import fill_gaps, voxelize

PARTS = r"C:\Users\zesky\AppData\Local\Temp\claude\G--art2real\612c5d2a-3321-47b1-8ebf-c897df4a0801\scratchpad\part_out"
LABELS = r"G:\art2real\트레일\trail7_part3d\in\c0_mask.npy"
CASE = "오메가몬"


def build():
    """전신 앞단 — 마스크 · 이진 hull · 지금 기본 · **조각 라벨을 정면 마스크와 같은 변환으로** 창에 앉힌다."""
    src, base = H.CASES[CASE]["src"], H.art_dir(CASE)
    lab = np.load(LABELS).astype(np.float32)
    masks, labw = {}, None
    for v, f in src.items():
        d = H.declutter(W.art_mask(os.path.join(base, f)))
        if v == "front":
            l = np.where(d, lab, 0.0).astype(np.float32)          # 지시선 뺀 자리는 라벨에서도 뺀다
            masks[v], labw = H.to_win(d, l)
        else:
            masks[v] = H.to_win(d)
    bs = H.CASES[CASE]["back_sign"] or H.pick_back_sign(masks)
    p = H.align(masks, back_sign=bs)
    masks = H._warp(masks, p)
    labw = H._warp_one(labw, "front", p)
    plain, axes = H.carve(masks, back_sign=bs)
    deps = {v: np.ones((W.RES, W.RES), np.float32) for v in W.VIEWS}
    vox, _ = H.carve_default(masks, deps, back_sign=bs)
    return masks, np.rint(labw).astype(np.int32), plain, vox, axes, bs


def region(plain, labw, i, axes):
    """조각 i 의 **3D 자리** — 그 조각 정면 화소의 광선 ∩ 이진 hull. 여기 밖으로는 못 나간다."""
    sel = labw == i
    if not sel.any():
        return None, None
    u, _, z = axes
    py, px = W.topix(W.VIEW_AXIS["front"][1] * u[:, None] * np.ones(len(z)), np.ones(len(u))[:, None] * z)
    col = sel[py, px]                                             # (x, z) — 칸 격자에서 본 조각 마스크
    return plain & col[:, None, :], col


def trim(mesh, frac=0.02):
    """**부스러기를 턴다.** 조각 생성물은 덩이가 19~77개로 나오고, 멀리 떨어진 부스러기 하나가 bbox 를
    두 배로 늘려 맞추기를 망친다 (머리: 전체 bbox z 1.84 · 제일 큰 덩이 0.23 — 2026-09-16 실측).
    제일 큰 덩이 부피의 frac 이상인 덩이만 남긴다 (뿔처럼 진짜로 떨어진 덩이를 지키려고 0 이 아니다)."""
    ps = mesh.split(only_watertight=False)
    if len(ps) <= 1:
        return mesh
    vs = np.array([abs(p.volume) for p in ps])
    keep = [p for p, v in zip(ps, vs) if v >= frac * vs.max()]
    return trimesh.util.concatenate(keep) if keep else mesh


def place(mesh, col, reg, axes, pmask):
    """조각 메시를 제자리에 앉힌다 (정답 안 봄). 4 방향 × 좌우 반전 중 **정면 실루엣이 조각 마스크와 가장 맞는** 것.
    x · z 는 조각의 정면 칸 범위 · y(깊이)는 그 자리 hull 의 깊이 범위로 늘인다 — 전신 `3판맞춤` 의 조각판."""
    u, uy, z = axes
    xs, zs = np.nonzero(col.any(1)), np.nonzero(col.any(0))
    ys = np.nonzero(reg.any((0, 2)))[0]
    if not len(xs[0]) or not len(zs[0]) or not len(ys):
        return None
    box = [(u[xs[0].min()], u[xs[0].max()]), (uy[ys.min()], uy[ys.max()]), (z[zs[0].min()], z[zs[0].max()])]
    base = W.to_world(np.asarray(mesh.vertices, np.float64), "xyz")
    best = None
    for k in range(4):
        c, s = np.cos(k * np.pi / 2), np.sin(k * np.pi / 2)
        R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        for mir in (1, -1):
            V = base @ R.T * np.array([mir, 1, 1])
            V = V.copy()
            for ax, (lo, hi) in enumerate(box):                   # 조각 상자에 늘여 넣는다
                a, b = V[:, ax].min(), V[:, ax].max()
                V[:, ax] = lo + (V[:, ax] - a) / max(b - a, 1e-9) * (hi - lo)
            sc = W.iou(G3.splat(V, "front"), pmask)
            if best is None or sc > best[0]:
                best = (sc, V, k * 90, mir)
    return best


def assemble():
    masks, labw, plain, vox, axes, bs = build()
    files = {int(os.path.basename(f)[:2]): f for f in glob.glob(os.path.join(PARTS, "*.glb"))}
    union = np.zeros_like(plain)
    rows = []
    for i in sorted(files):
        reg, col = region(plain, labw, i, axes)
        if reg is None or not reg.any():
            print("  %2d 자리 없음" % i, flush=True); continue
        g = trim(trimesh.load(files[i], force="mesh"))
        pm = labw == i
        got = place(g, col, reg, axes, pm)
        if got is None:
            print("  %2d 앉힐 수 없음" % i, flush=True); continue
        sc, V, yaw, mir = got
        v = voxelize(trimesh.Trimesh(V, np.asarray(g.faces), process=False), axes) & reg
        union |= v
        rows.append({"조각": os.path.basename(files[i])[:-4], "정렬": round(float(sc), 3), "회전": yaw, "반전": mir,
                     "칸": int(v.sum()), "자리": int(reg.sum()), "참": int(g.faces.shape[0])})
        print("  %-14s 정렬 %.3f (%3d°,%+d) · 칸 %6d / 자리 %6d" % (rows[-1]["조각"], sc, yaw, mir, v.sum(), reg.sum()), flush=True)
    return {"지금 기본": vox, "조각생성∩hull": union, "조각생성+보충": fill_gaps(union, vox, plain)}, masks, plain, axes, bs, rows


def measure(vs, masks, plain, axes, bs, rows):
    rec = {"case": CASE, "때": time.strftime("%Y-%m-%d %H:%M"), "조각": rows, "판본": {}}
    base = None
    for n, occ in vs.items():
        # **`AL.clean` 을 쓰지 않는다** — 제일 큰 덩이만 남기는 함수라 조각 29 덩이 중 28 개를 버린다
        # (그렇게 재서 못덮음 94% 가 나왔다 · 2026-09-16). 여기선 뒤집힌 것만 바로잡고 다 남긴다
        mesh = trimesh.Trimesh(*H.mesh_from(occ, axes), process=True)
        if mesh.volume < 0:
            mesh.invert()
        rp = AL.reproject(mesh, masks, bs)
        r = {"못덮음": {v: round(rp[v]["miss"], 4) for v in W.VIEWS},
             "가는곳": {v: round(rp[v]["thin"], 4) for v in W.VIEWS},
             "hull밖": round(float((occ & ~plain).sum() / max(occ.sum(), 1)), 4),
             "조각수": SF.pieces(occ), "면": len(mesh.faces)}
        if base is None:
            base, r["판정"] = r, "기준"
        else:                                                     # 계획 「판정」 — 가는 곳이 오르는 게 이 시험의 목적이다
            up = sum(r["가는곳"][v] > base["가는곳"][v] for v in W.VIEWS)
            r["판정"] = "통과" if (max(r["못덮음"].values()) < H.THRESH and up >= 2 and r["hull밖"] <= AL.OUTSIDE) else "짐"
        rec["판본"][n] = r
        mesh.export(os.path.join(HERE, "out", "조각생성_%s.glb" % n))
        print("  %-14s 못덮음 %s · 가는곳 %s · hull밖 %.2f%% · 덩이 %d · %s"
              % (n, " ".join("%.2f%%" % (100 * r["못덮음"][v]) for v in W.VIEWS),
                 " ".join("%.1f%%" % (100 * r["가는곳"][v]) for v in W.VIEWS),
                 100 * r["hull밖"], r["조각수"], r["판정"]), flush=True)
    q = os.path.join(HERE, "out", "기록", "조각생성_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump(rec, open(q, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  -> %s" % q)


def figure():
    names = ["지금 기본", "조각생성∩hull", "조각생성+보충"]
    ms = {n: trimesh.load(os.path.join(HERE, "out", "조각생성_%s.glb" % n), force="mesh") for n in names}
    ref = ms["지금 기본"]
    fr = {az: AL.frame_of(ref, az) for az in (-90, 0, 45)}
    (x0, z0), span = fr[0]
    zoom = ((x0 + 0.33 * span, z0 + 0.62 * span), 0.26 * span)     # 머리 · 가슴 확대 (디테일이 생겼나)
    rows = [(n, [PL.shaded(ms[n], az, fr[az], 400) for az in (0, -90, 45)] + [PL.shaded(ms[n], 0, zoom, 400)]) for n in names]
    for n, _ in rows:
        print("  %s 명암" % n, flush=True)
    DC.grid(rows, ["정면", "옆", "45도", "머리·가슴 확대"],
            "조각생성 — 오메가몬 · 조각 26개를 따로 생성해 hull 자리에 앉혀 합쳤다 (면 법선 명암)",
            "같은 열은 틀이 같다 · 조각 크롭은 생성 격자 한 칸이 원본 0.32~1.98 화소 (전신은 3.61) — 없던 디테일이 생겼는지 본다",
            os.path.join(HERE, "out", "조각생성_명암.png"))


if __name__ == "__main__":
    H.register_sheets()
    a = sys.argv[1:] or ["앉힘"]
    if a[0] == "앉힘":
        t0 = time.time()
        vs, masks, plain, axes, bs, rows = assemble()
        measure(vs, masks, plain, axes, bs, rows)
        print("  %.0f초" % (time.time() - t0))
    elif a[0] == "그림":
        figure()
