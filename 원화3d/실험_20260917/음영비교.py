# -*- coding: utf-8 -*-
"""**은둔자 — 원화 그대로 vs SDXL 음영 몸 + 원화 얼굴** (2026-09-17). 관찰 그림 — 점수 없음.

    python 음영비교.py    -> out/은둔자_음영비교.png

음영 판: SDXL img2img 0.50 (씨앗 5) · 머리 창(1696 판 y150..450 x780..990)만 원화로 되돌림 — SDXL 이 55화소 얼굴을 광대 얼굴로 바꿨다.
TripoSG 는 두 입력에서 앞 방향을 다르게 잡았다 (원화 az 180 · 음영 az 90) — 머리 상자는 그 시점의 화면 좌표로 적는다.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = r"G:\art2real\원화3d"
for d in ("실험_20260913", "실험_20260916", "실험_20260917"):
    sys.path.insert(0, os.path.join(HERE, d))
os.chdir(HERE)
import 폴리싱 as PL
import 얼굴비교 as FC
from 조각생성 import trim
from 계획 import _font

S = r"C:\Users\zesky\AppData\Local\Temp\claude\G--art2real\612c5d2a-3321-47b1-8ebf-c897df4a0801\scratchpad"
T = 360
ROWS = [  # 이름 · 입력 그림 · 메시 · 앞 az · 머리 상자(화면 X0, X1, z0, z1)
    ("원화 그대로", os.path.join(S, "hermit", "hermit_prep.png"), "out/은둔자.glb", 180, (-0.15, 0.07, 0.845, 1.005)),
    ("SDXL 음영 몸 + 원화 얼굴", os.path.join(S, "hermit_sdxl", "comp_view_full.png"), os.path.join(S, "hermit_sdxl", "tri", "comp_rgba.glb"), 90, (-0.09, 0.13, 0.80, 1.0)),
]


def screen_x(V, az):
    a = np.radians(az)
    return np.cos(a) * V[:, 0] - np.sin(a) * V[:, 1]


def view(m, az, box=None, sel=None):
    V = m.vertices
    if box is None:
        X = screen_x(V, az)
        span = max(np.ptp(X), np.ptp(V[:, 2])) * 1.03
        return PL.shaded(m, az, (((X.min() + X.max()) / 2 - span / 2, (V[:, 2].min() + V[:, 2].max()) / 2 - span / 2), span), T)
    x0, x1, z0, z1 = box
    span = max(x1 - x0, z1 - z0)
    X = screen_x(V[sel], az)
    return PL.shaded(m, az, (((X.min() + X.max()) / 2 - span / 2, z1 - span), span), T)


def main():
    comp = np.array(Image.open(os.path.join(S, "hermit_sdxl", "comp_rgba.png")))
    a = comp[..., 3:] / 255.0
    Image.fromarray((comp[..., :3] * a + 255 * (1 - a)).astype(np.uint8)).save(ROWS[1][1])
    cols = ["입력 그림", "전신 · 입력 시점", "전신 · 옆", "머리 · 입력 시점", "머리 · 45도"]
    G, LW, TOP, CAP = 10, 190, 80, 28
    im = Image.new("RGB", (LW + len(cols) * (T + G), TOP + CAP + len(ROWS) * (T + G)), "white")
    d = ImageDraw.Draw(im)
    d.text((16, 14), "은둔자 — 음영을 입혀 TripoSG 에 넣으면", fill="black", font=_font(26))
    d.text((16, 50), "음영 판 = SDXL img2img 0.50 몸 + 원화 머리 (SDXL 이 55화소 얼굴을 광대 얼굴로 바꿔서) · 면 법선 명암", fill=(90, 90, 90), font=_font(15))
    for c, name in enumerate(cols):
        d.text((LW + c * (T + G), TOP), name, fill="black", font=_font(16))
    for r, (name, img, path, az, box) in enumerate(ROWS):
        y = TOP + CAP + r * (T + G)
        d.text((12, y + T // 2), name, fill="black", font=_font(16))
        m = trim(FC.load(path))
        V = m.vertices
        X = screen_x(V, az)
        sel = (X > box[0]) & (X < box[1]) & (V[:, 2] > box[2])
        c = m.triangles_center
        Xc = screen_x(c, az)
        head = m.submesh([np.nonzero((Xc > box[0] - 0.05) & (Xc < box[1] + 0.05) & (c[:, 2] > box[2] - 0.03))[0]], append=True)
        hs = (screen_x(head.vertices, az) > box[0]) & (screen_x(head.vertices, az) < box[1]) & (head.vertices[:, 2] > box[2])
        tiles = [np.array(Image.open(img).convert("RGB").resize((T, T))), view(m, az), view(m, az + 90),
                 view(head, az, box, hs), view(head, az + 45, box, hs)]
        for k, t in enumerate(tiles):
            im.paste(Image.fromarray(t), (LW + k * (T + G), y))
        e = m.bounding_box.extents
        print("  %s 면 %d · 가로 %.2f 깊이 %.2f (높이 1)" % (name, len(m.faces), *sorted(e[:2])[::-1]), flush=True)
    q = os.path.join("out", "은둔자_음영비교.png")
    im.save(q)
    print(" ->", q)


if __name__ == "__main__":
    main()
