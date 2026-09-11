# -*- coding: utf-8 -*-
"""**깨짐을 크게 보고, 잰다.** -> out/깨짐_<케이스>.png + 거칠기 표

    python 깨짐.py <벤치lam4.jsonl> 케이스

그림: 정답 · 이진 · 대조군 · 파이프0.50 · 타원0.50 · 오라클0.50 을 520px 로 (45도, 같은 렌더러).

거칠기: 앞면(정면에서 처음 맞는 칸)의 y 를 (x, z) 마다 뽑아 **이웃끼리 몇 칸 튀나**를 잰다.
    위아래  = 같은 x 에서 z 줄끼리       좌우 = 같은 z 에서 x 칸끼리
    찢김    = 위아래로 3칸 넘게 튄 쌍의 비율
정답보다 위아래만 유독 크면 「높이마다 따로 처리해서 가로로 찢어진다」가 선다."""
import json
import os
import sys

import numpy as np
import trimesh
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 벤치그림 as RG
from 계획 import _font

O, B, W = RG.O, RG.B, RG.O.W


def front_index(vox):
    """(x, z) 마다 앞면 칸 번호. 물건이 없으면 nan."""
    n = vox.shape[1]
    jf = np.where(vox, np.arange(n)[None, :, None], n).min(1).astype(float)
    jf[jf >= n] = np.nan
    return jf


def rough(jf):
    dz = np.abs(np.diff(jf, axis=1)); dx = np.abs(np.diff(jf, axis=0))
    dz, dx = dz[np.isfinite(dz)], dx[np.isfinite(dx)]
    return dz.mean(), dx.mean(), (dz > 3).mean()


def main():
    rows = {json.loads(l)["case"]: json.loads(l) for l in open(sys.argv[1], encoding="utf-8")}
    case = sys.argv[2]
    r = rows[case]
    O.H.register_sheets()
    truth = trimesh.load(os.path.join(O.OUT, "시트", case, "truth.glb"), force="mesh")
    plain, p20, axes, _ = O.build(case, truth, 0.20, "파이프")
    vox = {"이진": plain, "파이프0.50": O.build(case, truth, 0.50, "파이프")[1],
           "타원0.50": O.build(case, truth, 0.50, "타원")[1], "오라클0.50": O.build(case, truth, 0.50, "오라클")[1]}
    sdf = (ndimage.distance_transform_edt(plain) - ndimage.distance_transform_edt(~plain)).astype(np.float32)
    ctrl = B.sdf_mesh(sdf, axes, r["t"]["파이프0.50"])
    # 대조군의 칸 판 — 수준 t 보다 안쪽
    vox["대조군"] = sdf > r["t"]["파이프0.50"]
    # 정답의 앞면 — 오라클 깊이 이미지를 복셀 중심에서 읽어 칸 번호로 되돌린다
    u, _, z = axes
    X2, Z2 = np.meshgrid(u, z, indexing="ij")
    py, px = W.topix(X2, Z2)
    hf = O.oracle_depth(truth, "front")[py, px]
    y = np.asarray(truth.vertices)[:, 1]
    yt = y.max() - hf * (y.max() - y.min())
    jt = (yt - u[0]) / (u[1] - u[0])
    jt[~plain.any(1)] = np.nan
    print("  %s  거칠기 (앞면 · 칸)      위아래   좌우    찢김(위아래 >3칸)" % case)
    for name, jf in [("정답", jt)] + [(k, front_index(vox[k])) for k in ("이진", "대조군", "파이프0.50", "타원0.50", "오라클0.50")]:
        a, b, c = rough(jf)
        print("    %-10s              %6.2f  %6.2f   %5.1f%%" % (name, a, b, 100 * c))
    meshes = {"정답": truth, "이진": O.C.to_mesh(plain, axes), "대조군": ctrl,
              **{k: O.C.to_mesh(vox[k], axes) for k in ("파이프0.50", "타원0.50", "오라클0.50")}}
    R = RG.rot(np.asarray(meshes["이진"].vertices))
    lo, hi = R.min(0), R.max(0)
    span = max(hi[0] - lo[0], hi[2] - lo[2]) * 1.04
    frame = ((lo[0] + hi[0]) / 2 - span / 2, (lo[2] + hi[2]) / 2 - span / 2), span
    S, G = 520, 12
    names = ["정답", "이진", "대조군", "파이프0.50", "타원0.50", "오라클0.50"]
    tint = {"정답": RG.TINT["정답"], "이진": RG.TINT["이진 hull"], "대조군": RG.TINT["대조군"],
            "파이프0.50": RG.TINT["파이프0.50"], "타원0.50": RG.TINT["타원0.50"], "오라클0.50": RG.TINT["오라클0.50"]}
    im = Image.new("RGB", (3 * (S + G) + G, 2 * (S + 40) + 70), "white")
    d = ImageDraw.Draw(im)
    f1, f2 = _font(24), _font(16)
    d.text((G, 16), "%s — 45도 · 깨짐 확대" % case, fill=(20, 20, 20), font=f1)
    for i, k in enumerate(names):
        x0, y0 = G + (i % 3) * (S + G), 70 + (i // 3) * (S + 40)
        im.paste(Image.fromarray(RG.render(meshes[k], frame, S, tint[k])), (x0, y0))
        lab = k if k == "정답" else "%s  IoU %.4f" % (k, r["128"]["균일@파이프0.50" if k == "대조군" else k])
        d.text((x0, y0 + S + 6), lab, fill=(40, 40, 40), font=f2)
    p = os.path.join(RG.HERE, "out", "깨짐_%s.png" % case)
    im.save(p)
    print("  ->", p)


if __name__ == "__main__":
    main()
