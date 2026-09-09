# -*- coding: utf-8 -*-
"""**정규 3시점이 아닌 데서 본다.** 이진 hull 과 깊이 깎기를 나란히.

    python 각도.py        ->  out/각도.png

원화가 정면·측면·후면뿐이라 그 셋은 잘 맞을 수밖에 없다. 파이프라인이 진짜 형태를 만들었는지는
**아무도 안 그린 각도**에서만 드러난다. 45도에서 이진 hull 은 상자 무더기로 보인다 —
`voxel[x,y,z] = F[z,x] & B[z,x] & S[z,y]` 라 단면이 축정렬 직사각형밖에 못 되기 때문이다.

메시를 안 그리고 **복셀을 돌려서** 그린다. 화가 알고리즘은 면을 깊이로 정렬하다 가로줄
아티팩트를 만들어서, 무엇이 진짜 계단이고 무엇이 렌더 탓인지 못 가른다.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull as H
import win as W
from 계획 import _font

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
AZ = (0, 25, 45, 65, 90)


def shot(vox, az, R=340):
    """복셀을 z 축으로 az 도 돌려 깊이로 그린다. 명암은 깊이 기울기에서 온다."""
    v = ndimage.rotate(vox.astype(np.float32), az, axes=(0, 1), order=0,
                       reshape=False, prefilter=False) > 0.5
    d = np.where(v, np.arange(v.shape[1])[None, :, None], v.shape[1] + 1).min(1)   # (x, z) 앞면
    hit = d <= v.shape[1]
    d = np.where(hit, d, np.nan).astype(np.float32)
    flat = np.nan_to_num(d, nan=float(np.nanmax(d)) if hit.any() else 0.0)
    # **명암용으로만** 살짝 흐린다. 복셀 격자가 깊이를 256단으로 끊어 실제로 계단이 지는데,
    # 기울기를 그대로 쓰면 그 계단이 화면을 덮어 형태가 안 보인다. 기하는 안 건드린다.
    flat = ndimage.gaussian_filter(flat, 1.6)
    gy, gx = np.gradient(flat)
    n = np.stack([-gx, -gy, np.ones_like(d) * 2.2], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9
    L = np.array([-0.45, 0.35, 0.82]); L /= np.linalg.norm(L)
    sh = np.clip(0.20 + 0.80 * (n @ L), 0, 1)
    img = np.where(hit, 40 + 200 * sh, 255).astype(np.uint8)
    img = np.rot90(img)                                    # (x, z) -> 화면 (행=z 위)
    return Image.fromarray(img).resize((R, R), Image.LANCZOS)


def main():
    src = {"front": "omega_front_clean.png", "side": "omega_side.png", "back": "omega_back.png"}
    masks, deps = {}, {}
    for v, f in src.items():
        d = H.declutter(W.art_mask(os.path.join(H.IN7, f)))
        masks[v], deps[v] = H.to_win(d, H.load_depth(v, d))
    p = H.align(masks)
    masks = H._warp(masks, p)
    deps = {v: H._warp_one(a, v, p) for v, a in deps.items()}

    plain, _ = H.carve(masks)
    deep, _ = H.carve_depth(masks, deps)
    rows = [("이진 hull — 실루엣 세 장만", plain), ("깊이 깎기 — 판 분할 + 크리스 인플레이션", deep)]

    R = 340
    sheet = Image.new("RGB", (len(AZ) * (R + 12) + 12, 2 * (R + 52) + 84), "white")
    d = ImageDraw.Draw(sheet)
    d.text((14, 12), "아무도 안 그린 각도에서 — 위 이진 hull · 아래 깊이 깎기", font=_font(20),
           fill=(20, 20, 20))
    for r, (label, vox) in enumerate(rows):
        y = 74 + r * (R + 52)
        d.text((14, y - 22), "%s      단면 형태값 %.2f 칸" % (label, H.box_score(vox)),
               font=_font(13), fill=(90, 90, 90))
        for i, az in enumerate(AZ):
            x = 12 + i * (R + 12)
            sheet.paste(shot(vox, az, R), (x, y))
            if r == 1:
                d.text((x + R // 2 - 16, y + R + 6), "%d°" % az, font=_font(13), fill=(120, 120, 120))
    sheet.save(os.path.join(OUT, "각도.png"))
    print("-> out/각도.png")


if __name__ == "__main__":
    main()
