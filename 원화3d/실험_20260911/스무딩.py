# -*- coding: utf-8 -*-
"""**스무딩을 넣으면 깨짐이 주나 — 그리고 대조군도 같이 민다.** -> out/스무딩_<케이스>.png + 표

    python 스무딩.py <벤치lam4.jsonl> 케이스

스무딩: 결과 복셀 -> 부호거리장 -> 가우시안(σ 칸) -> 0 보다 안쪽 **그리고 hull 안** (실루엣 밖으로
부풀면 원화에 없는 걸 지어내는 셈이라 막는다). 대조군에도 **같은 σ** 를 건다 — 안 그러면
스무딩이 올린 IoU 가 깊이맵 실력으로 읽힌다.

원인 한 줄: 오라클0.50 을 `carve_depth` 의 **높이별 정규화 없이** 다시 깎는다 (`정규화끔`).
이게 찢김을 없애면 스무딩보다 그걸 먼저 고쳐야 한다."""
import json
import os
import sys

import numpy as np
import trimesh
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 벤치그림 as RG
import 깨짐 as K
from 계획 import _font

O, W = RG.O, RG.O.W
SIG = (0, 1, 2)


def smooth(v, plain, s):
    if s == 0:
        return v
    d = ndimage.distance_transform_edt(v) - ndimage.distance_transform_edt(~v)
    return (ndimage.gaussian_filter(d.astype(np.float32), s) > 0) & plain


def carve_nonorm(plain, axes, deps, lam, bs):
    """`hull.carve_depth` 에서 **높이별 정규화만 뺀** 것. 나머지는 한 줄씩 같다."""
    u, _, z = axes
    X2, Z2 = np.meshgrid(u, z, indexing="ij")
    n = plain.shape[1]
    j = np.arange(n)[None, :, None]
    lo = np.where(plain, j, n).min(1).astype(np.float32)
    hi = np.where(plain, j, -1).max(1).astype(np.float32)
    D = np.maximum(hi - lo, 0.0)

    def sample(v):
        py, px = W.topix((bs if v == "back" else W.VIEW_AXIS[v][1]) * X2, Z2)
        return deps[v][py, px]
    jf = lo + (1.0 - sample("front")) * lam * D
    jb = hi - (1.0 - sample("back")) * lam * D
    return plain & (j >= jf[:, None, :]) & (j <= jb[:, None, :])


def pieces(v):
    lab, _ = ndimage.label(v, structure=np.ones((3, 3, 3)))
    s = np.bincount(lab.ravel())[1:]
    return int((s >= 50).sum())


def main():
    rows = {json.loads(l)["case"]: json.loads(l) for l in open(sys.argv[1], encoding="utf-8")}
    case = sys.argv[2]
    r = rows[case]
    O.H.register_sheets()
    truth = trimesh.load(os.path.join(O.OUT, "시트", case, "truth.glb"), force="mesh")
    T, ot = O.J.grid(truth)

    def iou(v, axes):
        G, og = O.J.grid(O.C.to_mesh(v, axes))
        A, B = O.J.common(T, ot, G, og)
        return float((A & B).sum() / max((A | B).sum(), 1))

    plain, _, axes, _ = O.build(case, truth, 0.20, "파이프")
    bs = O.H.CASES[case]["back_sign"]
    _, o50, _, od = O.build(case, truth, 0.50, "오라클")
    sdf = ndimage.distance_transform_edt(plain) - ndimage.distance_transform_edt(~plain)
    base = {"대조군": sdf > r["t"]["파이프0.50"], "파이프0.50": O.build(case, truth, 0.50, "파이프")[1],
            "타원0.50": O.build(case, truth, 0.50, "타원")[1], "오라클0.50": o50,
            "오라클·정규화끔": carve_nonorm(plain, axes, od, 0.50, bs)}
    res, vox = {}, {}
    print("  %s   (IoU 괄호 = 같은 σ 대조군 대비 · 찢김 = 위아래 >3칸 · 조각 = 50칸↑)" % case)
    for s in SIG:
        ctrl = smooth(base["대조군"], plain, s)
        ci = iou(ctrl, axes)
        for k, v in base.items():
            sv = ctrl if k == "대조군" else smooth(v, plain, s)
            x = ci if k == "대조군" else iou(sv, axes)
            tear = K.rough(K.front_index(sv))[2]
            res[(k, s)] = (x, x - ci, tear, pieces(sv))
            vox[(k, s)] = sv
            print("    σ%d %-14s IoU %.4f (%+.4f) · 찢김 %5.1f%% · 조각 %2d" % (s, k, x, x - ci, 100 * tear, pieces(sv)),
                  flush=True)
    # 그림 — 줄 = 판본, 칸 = σ
    names = list(base)
    R = RG.rot(np.asarray(O.C.to_mesh(plain, axes).vertices))
    lo, hi = R.min(0), R.max(0)
    span = max(hi[0] - lo[0], hi[2] - lo[2]) * 1.04
    frame = ((lo[0] + hi[0]) / 2 - span / 2, (lo[2] + hi[2]) / 2 - span / 2), span
    S, G, LW, TOP = 280, 10, 150, 80
    tint = {"대조군": RG.TINT["대조군"], "파이프0.50": RG.TINT["파이프0.50"], "타원0.50": RG.TINT["타원0.50"],
            "오라클0.50": RG.TINT["오라클0.50"], "오라클·정규화끔": (120, 200, 200)}
    im = Image.new("RGB", (LW + (len(SIG) + 1) * (S + G) + G, TOP + len(names) * (S + 30)), "white")
    d = ImageDraw.Draw(im)
    f1, f2, f3 = _font(22), _font(15), _font(13)
    d.text((16, 12), "%s — 스무딩 σ 0·1·2 (대조군도 같은 σ) · 45도" % case, fill=(20, 20, 20), font=f1)
    d.text((LW + G, TOP - 24), "정답", fill=(40, 40, 40), font=f2)
    for c, s in enumerate(SIG):
        d.text((LW + G + (c + 1) * (S + G), TOP - 24), "σ %d" % s, fill=(40, 40, 40), font=f2)
    im.paste(Image.fromarray(RG.render(truth, frame, S, RG.TINT["정답"])), (LW + G, TOP))
    for i, k in enumerate(names):
        y0 = TOP + i * (S + 30)
        d.text((12, y0 + S // 2), k, fill=(20, 20, 20), font=f2)
        for c, s in enumerate(SIG):
            x0 = LW + G + (c + 1) * (S + G)
            im.paste(Image.fromarray(RG.render(O.C.to_mesh(vox[(k, s)], axes), frame, S, tint[k])), (x0, y0))
            x, dv, tear, pc = res[(k, s)]
            txt = "IoU %.4f" % x + ("" if k == "대조군" else " (%+.4f)" % dv) + " · 찢김 %.0f%% · 조각 %d" % (100 * tear, pc)
            d.text((x0, y0 + S + 4), txt, font=f3,
                   fill=(60, 60, 60) if k == "대조군" else (30, 130, 70) if dv > 0 else (190, 60, 40))
    p = os.path.join(RG.HERE, "out", "스무딩_%s.png" % case)
    im.save(p)
    print("  ->", p)


if __name__ == "__main__":
    main()
