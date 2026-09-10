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


def depth(vox, az):
    """복셀을 z 축으로 az 도 돌려 **앞면 깊이맵**을 뽑는다 -> (깊이, 맞은 곳).

    칠하기와 나눠 둔 이유는 **여러 장을 같은 눈금으로** 칠하려면 눈금을 밖에서
    정해야 하기 때문이다 (`라벨.py` 가 정답·A·B 셋을 한 눈금으로 칠한다)."""
    v = ndimage.rotate(vox.astype(np.float32), az, axes=(0, 1), order=0,
                       reshape=False, prefilter=False) > 0.5
    d = np.where(v, np.arange(v.shape[1])[None, :, None], v.shape[1] + 1).min(1)   # (x, z) 앞면
    hit = d <= v.shape[1]
    return d.astype(np.float32), hit


# 멀다 -> 가깝다. 무지개가 아니라 밝기가 같이 오르는 순서라 흑백으로 봐도 순서가 남는다
STOPS = ((0.00, (46, 32, 120)), (0.28, (28, 130, 200)), (0.52, (40, 175, 130)),
         (0.78, (232, 190, 62)), (1.00, (205, 45, 40)))


def paint(d, hit, R=340, span=None):
    """깊이맵 -> 그림. `span=(lo, hi)` 를 주면 **그 눈금으로 색을 칠한다.**

    회색 음영은 깊이 기울기에서 오는데, 정지된 회색 한 장은 깊이차가 잘 안 읽힌다.
    색은 깊이를 **절대값으로** 준다 — 세 장이 같은 눈금이면 어느 쪽이 카메라 쪽으로
    뚱뚱하게 나왔는지가 바로 보인다."""
    flat = np.where(hit, d, d[hit].mean() if hit.any() else 0.0).astype(np.float32)
    # **명암용으로만** 살짝 흐린다. 복셀 격자가 깊이를 256단으로 끊어 실제로 계단이 지는데,
    # 기울기를 그대로 쓰면 그 계단이 화면을 덮어 형태가 안 보인다. 기하는 안 건드린다.
    flat = ndimage.gaussian_filter(flat, 1.6)
    gy, gx = np.gradient(flat)
    n = np.stack([-gx, -gy, np.ones_like(flat) * 2.2], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9
    L = np.array([-0.45, 0.35, 0.82]); L /= np.linalg.norm(L)
    sh = np.clip(0.20 + 0.80 * (n @ L), 0, 1)
    if span is None:
        img = np.where(hit, 40 + 200 * sh, 255).astype(np.uint8)[..., None].repeat(3, -1)
    else:
        lo, hi = span
        t = 1.0 - np.clip((flat - lo) / max(hi - lo, 1e-6), 0, 1)      # 1 = 카메라 쪽
        xp = [s[0] for s in STOPS]
        rgb = np.stack([np.interp(t, xp, [s[1][c] for s in STOPS]) for c in range(3)], -1)
        rgb *= (0.72 + 0.28 * sh)[..., None]              # 형태가 남게 음영을 얹는다
        img = np.where(hit[..., None], np.clip(rgb, 0, 255), 255).astype(np.uint8)
    img = np.rot90(img)                                    # (x, z) -> 화면 (행=z 위)
    return Image.fromarray(img).resize((R, R), Image.LANCZOS)


def bar(w, h, flip=False):
    """색 눈금 띠. 왼쪽이 멀고 오른쪽이 가깝다."""
    t = np.linspace(1, 0, w) if flip else np.linspace(0, 1, w)
    xp = [s[0] for s in STOPS]
    rgb = np.stack([np.interp(t, xp, [s[1][c] for s in STOPS]) for c in range(3)], -1)
    return Image.fromarray(np.tile(rgb.astype(np.uint8)[None], (h, 1, 1)))


def shot(vox, az, R=340, span=None):
    """복셀을 z 축으로 az 도 돌려 그린다."""
    return paint(*depth(vox, az), R=R, span=span)


def main(case=None, 한각=None):
    src = H.CASES[case]["src"] if case else         {"front": "omega_front_clean.png", "side": "omega_side.png", "back": "omega_back.png"}
    base = H.art_dir(case) if case else H.IN7
    masks, deps = {}, {}
    for v, f in src.items():
        d = H.declutter(W.art_mask(os.path.join(base, f)))
        masks[v], deps[v] = H.to_win(d, H.load_depth(v, d, case=case))
    p = H.align(masks)
    masks = H._warp(masks, p)
    deps = {v: H._warp_one(a, v, p) for v, a in deps.items()}

    plain, _ = H.carve(masks)
    deep, _ = H.carve_depth(masks, deps)
    rows = [("이진 hull — 실루엣 세 장만", plain), ("깊이 깎기 — 판 분할 + 크리스 인플레이션", deep)]

    if 한각 is not None:
        # 각도 하나만 크게. 만화 한 쪽이 한 각도를 통째로 쓰는 자리가 있다(1권 6화).
        R = 900
        one = Image.new("RGB", (R + 24, R + 64), "white")
        d1 = ImageDraw.Draw(one)
        d1.paste = None
        one.paste(shot(deep, 한각, R), (12, 12))
        d1.text((14, R + 26), "%s  %d°   단면 형태값 %.2f 칸" % (case or "오메가몬", 한각,
                H.box_score(deep)), font=_font(20), fill=(60, 60, 60))
        nm = f"각도_{case}_{한각}.png" if case else f"각도_{한각}.png"
        one.save(os.path.join(OUT, nm))
        print(f"-> out/{nm}")
        return

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
    name = "각도.png" if not case else f"각도_{case}.png"
    sheet.save(os.path.join(OUT, name))
    print(f"-> out/{name}")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("-")]
    # python 각도.py 무진1997 --각 45   -> 그 각도만 크게 한 장
    한각 = int(sys.argv[sys.argv.index("--각") + 1]) if "--각" in sys.argv else None
    main(a[0] if a else None, 한각)
