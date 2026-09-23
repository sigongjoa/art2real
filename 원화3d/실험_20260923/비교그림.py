# -*- coding: utf-8 -*-
"""**비포 애프터** — 오늘 시험한 판들을 같은 각도에서 3D 로 렌더해 나란히 놓는다 (2026-09-23).

    python 비교그림.py [케이스]   -> out/비교_<케이스>.png
복셀을 돌려 첫 닿는 깊이를 구하고 그 기울기로 음영을 준다(GL 없이 numpy 만).
"""
import os, sys
import numpy as np
from scipy import ndimage
import cv2
import trimesh

sys.path[:0] = [r"G:\art2real\원화3d", r"G:\art2real\원화3d\실험_20260921", r"G:\art2real\원화3d\실험_20260922", r"G:\art2real\원화3d\실험_20260923"]
import hull as H
import 정답 as JD
import 부품분할 as BB
import 면자르기 as MJ
import 도면벤치_천장 as DC
import 부피벤치 as PB
import 색대응 as CC
import 깊이칸 as K


def 그려(V, yaw, 색=(210, 205, 195), 크기=300):
    """복셀을 yaw 만큼 돌려 정면에서 본 음영 그림."""
    R = ndimage.rotate(V.astype(np.float32), yaw, axes=(0, 1), order=0, reshape=True) > 0.5
    있 = R.any(axis=1)
    깊 = np.where(있, np.argmax(R, axis=1).astype(np.float32), np.nan)          # (x, z)
    img = np.full(깊.shape + (3,), 255, np.uint8)
    d = np.nan_to_num(깊, nan=np.nanmax(깊) if 있.any() else 0)
    gy, gx = np.gradient(ndimage.gaussian_filter(d, 1.0))
    n = np.dstack([-gx, -gy, np.ones_like(d) * 2.0])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    L = np.array([0.35, -0.5, 0.79]); L = L / np.linalg.norm(L)
    램 = np.clip((n * L).sum(2), 0, 1) * 0.75 + 0.25
    깊정 = 1 - np.clip((d - np.nanmin(d[있])) / max(np.ptp(d[있]), 1), 0, 1) * 0.35 if 있.any() else 1
    for k in range(3):
        img[..., k] = np.where(있, np.clip(색[k] * 램 * 깊정, 0, 255), 255)
    img = np.rot90(img)
    h = 크기; w = max(int(img.shape[1] * h / img.shape[0]), 1)
    return cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)


def 글(im, s, 크기=19):
    from PIL import Image, ImageDraw, ImageFont
    band = np.full((30, im.shape[1], 3), 255, np.uint8)
    im = np.vstack([band, im])
    p = Image.fromarray(im)
    ImageDraw.Draw(p).text((6, 5), s, fill=(35, 35, 35), font=ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 크기))
    return np.asarray(p)


def main(c="mech_Mech_4UvIHxnoSR"):
    raw, masks, bs, p = BB.판(c)
    g, ax = H.field_default(masks, back_sign=bs, n=BB.N)
    ux, uy, z = [np.asarray(a) for a in ax]
    O = g > 0
    tm = trimesh.load(os.path.join(H.OUT, "시트", c, "truth.glb"), force="mesh")
    A, o = JD.grid(tm, 봉합=1)
    T = DC.우리격자로(A.astype(np.int32), np.asarray(o), ux, uy, z) > 0
    격, _ = CC.판색(c, raw, masks, p, bs)
    _, 부위, _ = MJ.부위(O); 부위 = BB.채우기(부위, O)
    값 = {l: K.숫자읽기(부위, T, l) for l in np.unique(부위) if l}
    값 = {l: v for l, v in 값.items() if v}
    판들 = [("지금 (타원 장)", O, (150, 175, 205)),
          ("색 대응 겉6", CC.깎기(O, 격, 6), (150, 195, 175)),
          ("사람 깊이 칸 12", K.조이기(O, 부위, 값, "D2"), (215, 185, 140)),
          ("정답", T, (170, 170, 170))]
    줄 = []
    for 이름, V, col in 판들:
        r = PB.재기(V, T)
        타 = [그려(V, yaw, col) for yaw in (0, 40, 90)]
        h = max(t.shape[0] for t in 타)
        타 = [np.vstack([t, np.full((h - t.shape[0], t.shape[1], 3), 255, np.uint8)]) for t in 타]
        줄.append(글(np.hstack(타), "%s — IoU %.3f · 정밀 %.3f · 재현 %.3f" % (이름, r["IoU"], r["정밀도"], r["재현율"])))
    w = max(r.shape[1] for r in 줄)
    줄 = [np.hstack([r, np.full((r.shape[0], w - r.shape[1], 3), 255, np.uint8)]) for r in 줄]
    out = np.vstack(줄)
    pth = os.path.join(H.OUT, "비교_%s.png" % c)
    cv2.imencode(".png", out[:, :, ::-1])[1].tofile(pth)
    print(pth, out.shape)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "mech_Mech_4UvIHxnoSR")
