# -*- coding: utf-8 -*-
"""**앨리어싱을 한 칸 안에서 편다** — 오메가몬 깎은 복셀에 ITK 구속 레벨셋(Whitaker 2000)을 건다.

    python 앨리어싱.py     -> out/앨리어싱_그림.png · out/앨리어싱_<판본>.glb · out/기록/앨리어싱_<날짜>.json

근거 `claudedocs/research_앨리어싱_20260913.md` 권고 2.

## 판본

    기준      지금 hull.py 그대로 (파이프 lam0.20 깎기 -> 0/1 복셀 -> 마칭큐브 0.5)
    ITK       같은 복셀 -> sitk.AntiAliasBinary **기본값** (MaximumRMSError 0.07 · 반복 1000) -> 수준 0 면.
              표면을 원래 0/1 경계에서 한 칸 안에 묶고 곡률 흐름으로 편다
    가우시안   **대조군** — 같은 복셀의 부호거리장을 σ 1 칸으로 흐린 면. 움직임에 상한이 없다
              (09-11 에 실루엣을 먹어 탈락한 `SMOOTH_OUT` 과 같은 종류)

셋 다 같은 위생을 건다 — 제일 큰 덩어리만 · 뒤집힌 법선 바로잡기 (`hull.main` 과 같다).

## 판정 — 돌리기 전에 적는다 (2026-09-13 밤)

ITK 가 셋을 다 지켜야 「통과」:

    되받아 재기   세 판 모두 원화를 못 덮은 비율 < 6% (hull.py assert 문턱 THRESH 그대로)
    가는 곳       원화 실루엣에서 **폭 약 12 화소 미만인 곳**(지름 13 원판으로 열면 사라지는 화소 — 칼 · 뿔 · 가시)을
                 덮는 비율이 기준보다 1%p 넘게 안 떨어진다 (세 판 모두)
    hull 상한     결과 칸 중 이진 hull 밖이 2% 이하

**결(가로 줄 · 계단)은 숫자로 안 잰다.** 결 지표는 09-11 에 두 번 죽었다

## ITK국소 — ITK 결과를 보고 더한 판본. 따로 적고 건다 (2026-09-13 밤)

ITK(전역)는 실루엣 · hull 상한은 지켰지만 옆 판 가는 곳 79.2% -> 65.7% 로 **가시를 먹었다.** 그래서 **두꺼운 곳만** 편다:

    두께     칸마다 이웃 7³ 안에서 내접구 반지름의 최댓값 (거리변환 -> 최댓값 필터)
    섞기     반지름 ≤ 2 칸 (키 150mm 에 지름 약 2.8mm — 뿔 · 가시 급) 은 원래 면 그대로,
            ≥ 4 칸은 ITK 면, 사이는 직선으로 섞는다 (둘 다 ±4 칸으로 자른 부호거리)
    판정     위와 같은 셋. 문턱(2 · 4 · 7)은 돌리기 전에 정했다 (`계단 거칠기` 가 정답을 hull 보다 거칠게 잼).
꼭짓점 법선 명암 그림으로 보고 「관찰」로만 적는다. 면마다 명암은 칸보다 작은 삼각형 방향 차를 줄무늬로 키운다 (09-11).
"""
import json
import os
import sys
import time

import cv2
import numpy as np
import trimesh
from scipy import ndimage

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
os.chdir(HERE)
import hull as H
import win as W

THIN_R = 6                       # 가는 곳: 지름 2·6+1 원판으로 열면 사라지는 화소
THIN_DROP = 0.01
OUTSIDE = 0.02
SIGMA = 1.0
VARIANTS = ("기준", "ITK", "ITK국소", "가우시안")
TH_LO, TH_HI, TH_WIN = 2.0, 4.0, 7                # ITK국소: 반지름 문턱 (칸) · 이웃 창


def build():
    """`hull.main` 과 같은 순서로 오메가몬 마스크 · 이진 hull · 깎은 복셀."""
    case = H.CASE
    src, base = H.CASES[case]["src"], H.art_dir(case)
    masks, deps = {}, {}
    for v, f in src.items():
        d = H.declutter(W.art_mask(os.path.join(base, f)))
        masks[v], deps[v] = H.to_win(d, H.load_depth(v, d, case=case))
    bs = H.CASES[case]["back_sign"] or H.pick_back_sign(masks)
    p = H.align(masks, back_sign=bs)
    masks = H._warp(masks, p)
    deps = {v: H._warp_one(a, v, p) for v, a in deps.items()}
    plain, _ = H.carve(masks, back_sign=bs)
    vox, axes = H.carve_depth(masks, deps, back_sign=bs)
    return masks, plain, vox, axes, bs, deps


def clean(V, F):
    mesh = trimesh.Trimesh(V, F, process=True)
    parts = mesh.split(only_watertight=False)
    if len(parts) > 1:
        mesh = max(parts, key=lambda q: abs(q.volume))
    if mesh.volume < 0:
        mesh.invert()
    return mesh


def variant(name, vox, axes):
    """-> (메시, 칸 점유). 점유는 hull 상한 검사에 쓴다."""
    if name == "기준":
        return clean(*H.mesh_from(vox, axes)), vox
    if name in ("ITK", "ITK국소"):
        import SimpleITK as sitk
        img = sitk.GetImageFromArray(vox.astype(np.uint8))       # 3D 는 정수만 받는다 (float32 · float64 둘 다 거절 — 09-13 탐침)
        f = sitk.GetArrayFromImage(sitk.AntiAliasBinary(img)).astype(np.float32)
        edt = ndimage.distance_transform_edt(vox)
        inner = np.unravel_index(edt.argmax(), vox.shape)
        if f[inner] < 0:                                         # 안쪽이 + 가 되게 (mesh_from_field 규약)
            f = -f
        if name == "ITK국소":                                     # 두꺼운 곳만 ITK, 가는 곳은 원래 면 (docstring)
            th = ndimage.maximum_filter(edt, size=TH_WIN)
            w = np.clip((th - TH_LO) / (TH_HI - TH_LO), 0, 1).astype(np.float32)
            f = w * np.clip(f, -4, 4) + (1 - w) * np.clip(H.sdf_of(vox), -4, 4)
        return clean(*H.mesh_from_field(f, axes)), f > 0
    f = ndimage.gaussian_filter(H.sdf_of(vox), SIGMA)
    return clean(*H.mesh_from_field(f, axes)), f > 0


def reproject(mesh, masks, bs):
    V, F = np.asarray(mesh.vertices), np.asarray(mesh.faces)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * THIN_R + 1,) * 2)
    out = {}
    for v in W.VIEWS:
        s = np.asarray(W.silhouette(V, F, v, bs if v == "back" else None)).astype(bool)
        a = masks[v].astype(bool)
        thin = a & ~cv2.morphologyEx(a.astype(np.uint8), cv2.MORPH_OPEN, k).astype(bool)
        out[v] = {"iou": W.iou(a, s), "miss": float((a & ~s).sum() / max(a.sum(), 1)),
                  "thin": float((thin & s).sum() / max(thin.sum(), 1)), "thin_px": int(thin.sum())}
    return out


def render(mesh, az, frame, S=420):
    """꼭짓점 법선 명암 (면마다 세 꼭짓점 명암 평균). 카메라는 돌린 뒤 -y 쪽에서 +y 를 본다."""
    a = np.radians(az)
    c, s = np.cos(a), np.sin(a)
    rot = lambda X: np.stack([c * X[:, 0] - s * X[:, 1], s * X[:, 0] + c * X[:, 1], X[:, 2]], 1)
    V, N, F = rot(np.asarray(mesh.vertices)), rot(np.asarray(mesh.vertex_normals)), np.asarray(mesh.faces)
    L = np.array([-0.45, -1.0, 0.75])
    L /= np.linalg.norm(L)
    fs = (0.2 + 0.8 * np.clip(N @ L, 0, 1))[F].mean(1)
    (x0, z0), span = frame
    P = np.round(np.stack([(V[:, 0] - x0) / span * S, (1 - (V[:, 2] - z0) / span) * S], 1) * 4).astype(np.int32)[F]
    img = np.full((S, S), 250, np.uint8)
    for i in np.argsort(V[F][:, :, 1].mean(1))[::-1]:
        cv2.fillConvexPoly(img, P[i], int(255 * fs[i]), shift=2)
    return img


def frame_of(mesh, az):
    a = np.radians(az)
    c, s = np.cos(a), np.sin(a)
    V = np.asarray(mesh.vertices)
    x = c * V[:, 0] - s * V[:, 1]
    lo, hi = np.array([x.min(), V[:, 2].min()]), np.array([x.max(), V[:, 2].max()])
    span = max(hi - lo) * 1.04
    return ((lo + hi) / 2 - span / 2), span


def figure(meshes, res):
    from PIL import Image, ImageDraw
    from 계획 import _font
    views = [("옆 (az −90)", -90), ("45도", 45)]
    frames = {az: frame_of(meshes["기준"], az) for _, az in views}
    S, Z, G, LW, TOP = 420, 420, 10, 170, 110
    cols = [n for n, _ in views] + ["옆 가슴 확대"]
    im = Image.new("RGB", (LW + len(cols) * (S + G), TOP + len(VARIANTS) * (S + 60)), "white")
    d = ImageDraw.Draw(im)
    f1, f2, f3 = _font(26), _font(17), _font(14)
    d.text((20, 16), "오메가몬 hull — 앨리어싱 (꼭짓점 법선 명암)", fill=(20, 20, 20), font=f1)
    d.text((20, 56), "기준 = 지금 hull.py · ITK = 한 칸 안에 묶은 곡률 흐름 (기본값) · 가우시안 = σ1 흐림 (대조군, 움직임 상한 없음)",
           fill=(90, 90, 90), font=f3)
    for j, n in enumerate(cols):
        d.text((LW + j * (S + G), TOP - 24), n, fill=(40, 40, 40), font=f2)
    for i, name in enumerate(VARIANTS):
        y0 = TOP + i * (S + 60)
        side = render(meshes[name], -90, frames[-90], S)
        tiles = [side, render(meshes[name], 45, frames[45], S)]
        big = render(meshes[name], -90, frames[-90], S * 3)
        tiles.append(big[int(S * 0.9):int(S * 0.9) + Z, int(S * 1.05):int(S * 1.05) + Z])
        for j, t in enumerate(tiles):
            im.paste(Image.fromarray(t).convert("RGB"), (LW + j * (S + G), y0))
        r = res[name]
        d.text((20, y0 + 10), name, fill=(20, 20, 20), font=f2)
        d.text((20, y0 + 36), "못 덮음 " + " · ".join("%.1f" % (100 * r["재기"][v]["miss"]) for v in W.VIEWS) + "%",
               fill=(60, 60, 60), font=f3)
        d.text((20, y0 + 56), "가는 곳 " + " · ".join("%.1f" % (100 * r["재기"][v]["thin"]) for v in W.VIEWS) + "%",
               fill=(60, 60, 60), font=f3)
        d.text((20, y0 + 76), "hull 밖 %.2f%%" % (100 * r["hull밖"]), fill=(60, 60, 60), font=f3)
        d.text((20, y0 + 96), "%.0f초" % r["초"], fill=(120, 120, 120), font=f3)
    p = os.path.join(HERE, "out", "앨리어싱_그림.png")
    im.save(p)
    print("  -> %s" % os.path.relpath(p, HERE))


def main():
    t0 = time.time()
    masks, plain, vox, axes, bs, _ = build()
    print("  복셀 준비 %.0f초 · 깎은 칸 %d" % (time.time() - t0, vox.sum()), flush=True)
    meshes, res = {}, {}
    for name in VARIANTS:
        t = time.time()
        mesh, occ = variant(name, vox, axes)
        sec = time.time() - t
        meshes[name] = mesh
        mesh.export(os.path.join(HERE, "out", "앨리어싱_%s.glb" % name))
        res[name] = {"재기": reproject(mesh, masks, bs), "hull밖": float((occ & ~plain).sum() / max(occ.sum(), 1)),
                     "부피": float(mesh.volume), "면": int(len(mesh.faces)), "닫힘": bool(mesh.is_watertight), "초": sec}
        r = res[name]
        print("  %-5s %4.0f초 · 면 %d · 부피 %.4f · 닫힘 %s · hull 밖 %.2f%%" % (
            name, sec, r["면"], r["부피"], r["닫힘"], 100 * r["hull밖"]), flush=True)
        for v in W.VIEWS:
            q = r["재기"][v]
            print("        %-6s IoU %.3f · 못 덮음 %.2f%% · 가는 곳 덮음 %.1f%% (%d 화소)" % (
                v, q["iou"], 100 * q["miss"], 100 * q["thin"], q["thin_px"]))
    b = res["기준"]
    verdict = {}
    for name in ("ITK", "ITK국소", "가우시안"):
        r = res[name]
        ok = {"되받아 재기": all(r["재기"][v]["miss"] < H.THRESH for v in W.VIEWS),
              "가는 곳": all(r["재기"][v]["thin"] >= b["재기"][v]["thin"] - THIN_DROP for v in W.VIEWS),
              "hull 상한": r["hull밖"] <= OUTSIDE}
        verdict[name] = {**ok, "통과": all(ok.values())}
        print("  판정 %-5s %s · **%s**" % (name, " · ".join("%s %s" % (k, "O" if x else "X") for k, x in ok.items()),
                                        "통과" if all(ok.values()) else "짐"))
    os.makedirs(os.path.join(HERE, "out", "기록"), exist_ok=True)
    p = os.path.join(HERE, "out", "기록", "앨리어싱_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"때": time.strftime("%Y-%m-%d %H:%M"), "판정": verdict, "결과": res}, open(p, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("  기록 -> %s" % os.path.relpath(p, HERE))
    # 명암 그림(figure)은 뺐다 — 렌더러가 명암을 틀리게 칠했다. 결은 `깊이색.py` 로 본다


if __name__ == "__main__":
    main()
