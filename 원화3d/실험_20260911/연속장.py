# -*- coding: utf-8 -*-
"""**단위 큐브가 0/1 이 아니라 거리를 갖게** — 연속장 hull · 연속장 깎기. -> out/연속장_<케이스>.png

    python 연속장.py 케이스

지금 파이프라인은 연속값을 두 군데서 버린다:
    실루엣   1024² 마스크(칸당 4화소)를 `keep &= m[py, px]` 로 0/1 로 자른다
    깎기     jf · jb 는 소수인데 `j >= jf` 정수 비교로 0/1 로 자른다
그러면 마칭큐브는 큐브 모서리의 **정가운데**에서만 면을 자를 수 있어 표면이 반 칸 단위로 놓인다 = 계단.

연속장:
    hull 장  = 판마다 2D 부호거리(1024² 에서, 칸 단위) 를 기둥으로 밀어 **최솟값**
    깎기 장  = min(j − jf + ½, jb + ½ − j)   (½ 는 불 0.5 면과 같은 자리에 두려고)
    결과     = min(hull 장, 깎기 장) 의 수준 0 을 마칭큐브
잰다: 정답 IoU · 원화 마스크 대비 실루엣 IoU (판마다) · 45도 그림."""
import os
import sys

import numpy as np
import trimesh
from PIL import Image, ImageDraw
from scipy import ndimage

SCR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCR)
import 벤치smooth as BS
import 벤치그림 as RG
from 계획 import _font

O, H, W = BS.O, BS.O.H, BS.O.W
PX = W.RES / (W.Z1 - W.Z0) * (W.U1 - W.U0) / H.N    # 칸 하나가 몇 화소인가 (창 가로 1.2 = 256칸)


def prepare(case, truth, which):
    """`오라클.build` 와 같은 순서로 정렬된 마스크·깊이까지 (build 는 마스크를 안 돌려준다)."""
    src, base = H.CASES[case]["src"], H.art_dir(case)
    bs = H.CASES[case]["back_sign"]
    masks, deps = {}, {}
    for v, f in src.items():
        d = H.declutter(W.art_mask(os.path.join(base, f)))
        dep = H.load_depth(v, d, case=case) if which == "파이프" else O.oracle_depth(truth, v)
        masks[v], deps[v] = H.to_win(d, dep)
    p = H.align(masks, back_sign=bs)
    return H._warp(masks, p), {v: H._warp_one(a, v, p) for v, a in deps.items()}, bs


def hull_field(masks, bs):
    """판마다 2D 부호거리(칸) 를 기둥으로 — `hull.carve` 와 같은 표본화, 교집합은 최솟값."""
    u = W.U0 + (np.arange(H.N) + 0.5) / H.N * (W.U1 - W.U0)
    z = W.Z0 + (np.arange(H.N) + 0.5) / H.N * (W.Z1 - W.Z0)
    X, Y, Z = np.meshgrid(u, u, z, indexing="ij")
    F = np.full(X.shape, np.inf, np.float32)
    for v, m in masks.items():
        m = m.astype(bool)
        d2 = (ndimage.distance_transform_edt(m) - ndimage.distance_transform_edt(~m)) / PX
        a, sign = W.VIEW_AXIS[v]
        py, px = W.topix((bs if v == "back" else sign) * (X if a == 0 else Y), Z)
        F = np.minimum(F, d2[py, px].astype(np.float32))
    return F, (u, u, z)


def main():
    case = sys.argv[1]
    O.H.register_sheets()
    truth = trimesh.load(os.path.join(O.OUT, "시트", case, "truth.glb"), force="mesh")
    T, ot = O.J.grid(truth)

    def iou(m):
        G, og = O.J.grid(m)
        A, B = O.J.common(T, ot, G, og)
        return float((A & B).sum() / max((A | B).sum(), 1))

    out, meshes = {}, {}
    for which, lam in (("파이프", None), ("오라클", 0.50)):
        masks, deps, bs = prepare(case, truth, which)
        plain, axes = H.carve(masks, back_sign=bs)
        Fh, _ = hull_field(masks, bs)
        if lam is None:                                  # 이진 hull 두 판
            vers = {"이진 · 0/1": O.C.to_mesh(plain, axes), "이진 · 연속장": BS.mesh(Fh, axes)}
        else:
            deep, _ = H.carve_depth(masks, deps, lam=lam, back_sign=bs)
            # 깎기 장 — carve_depth 의 jf · jb 를 다시 뽑는다 (소수 그대로)
            n = H.N
            j = np.arange(n, dtype=np.float32)[None, :, None]
            on = plain.any(1)
            lo = np.where(plain, np.arange(n)[None, :, None], n).min(1).astype(np.float32)
            hi = np.where(plain, np.arange(n)[None, :, None], -1).max(1).astype(np.float32)
            D = np.maximum(hi - lo, 0.0)
            u, _, z = axes
            X2, Z2 = np.meshgrid(u, z, indexing="ij")

            def sample(v):
                py, px = W.topix((bs if v == "back" else W.VIEW_AXIS[v][1]) * X2, Z2)
                return deps[v][py, px]

            def norm(h):
                top = np.where(on, h, 0.0).max(0, keepdims=True)
                return np.where(on, h / np.maximum(top, 1e-6), 0.0)
            jf = lo + (1.0 - norm(sample("front"))) * lam * D
            jb = hi - (1.0 - norm(sample("back"))) * lam * D
            Fc = np.minimum(j - jf[:, None, :] + 0.5, jb[:, None, :] + 0.5 - j)
            Fc = np.where(on[:, None, :], Fc, np.inf).astype(np.float32)
            vers = {"오라클0.50 · 0/1": O.C.to_mesh(deep, axes), "오라클0.50 · 연속장": BS.mesh(np.minimum(Fh, Fc), axes)}
        for k, m in vers.items():
            sil = []
            for v in W.VIEWS:
                s = W.silhouette(np.asarray(m.vertices), np.asarray(m.faces), v, bs if v == "back" else None)
                sil.append(W.iou(masks[v], s))
            out[k] = (iou(m), sil)
            meshes[k] = m
            print("  %-18s 정답 IoU %.4f · 원화 실루엣 IoU  정면 %.4f · 측면 %.4f · 후면 %.4f"
                  % (k, out[k][0], *sil), flush=True)
    R = RG.rot(np.asarray(meshes["이진 · 0/1"].vertices))
    lo_, hi_ = R.min(0), R.max(0)
    span = max(hi_[0] - lo_[0], hi_[2] - lo_[2]) * 1.04
    frame = ((lo_[0] + hi_[0]) / 2 - span / 2, (lo_[2] + hi_[2]) / 2 - span / 2), span
    S, G, TOP = 400, 12, 80
    names = ["이진 · 0/1", "이진 · 연속장", "오라클0.50 · 0/1", "오라클0.50 · 연속장"]
    tint = [RG.TINT["이진 hull"], RG.TINT["이진 hull"], RG.TINT["오라클0.50"], RG.TINT["오라클0.50"]]
    im = Image.new("RGB", (5 * (S + G) + G, TOP + S + 60), "white")
    d = ImageDraw.Draw(im)
    d.text((G, 14), "%s — 단위 큐브에 0/1 대신 거리를: 연속장 (45도 · 같은 렌더러)" % case, fill=(20, 20, 20), font=_font(22))
    d.text((G + 0 * (S + G), TOP - 22), "정답", fill=(40, 40, 40), font=_font(15))
    im.paste(Image.fromarray(RG.render(truth, frame, S, RG.TINT["정답"])), (G, TOP))
    for c, (k, tn) in enumerate(zip(names, tint), 1):
        x0 = G + c * (S + G)
        d.text((x0, TOP - 22), k, fill=(40, 40, 40), font=_font(15))
        im.paste(Image.fromarray(RG.render(meshes[k], frame, S, tn)), (x0, TOP))
        x, sil = out[k]
        d.text((x0, TOP + S + 6), "정답 IoU %.4f" % x, fill=(40, 40, 40), font=_font(13))
        d.text((x0, TOP + S + 26), "실루엣 IoU  %.3f · %.3f · %.3f" % tuple(sil), fill=(90, 90, 90), font=_font(13))
    p = os.path.join(RG.HERE, "out", "연속장_%s.png" % case)
    im.save(p)
    print("  ->", p)


if __name__ == "__main__":
    main()
