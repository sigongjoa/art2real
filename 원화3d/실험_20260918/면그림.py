# -*- coding: utf-8 -*-
"""면 그림 — 정답 · TripoSG 생 · 우리 것을 **같은 자리로 확대해** 나란히 (2026-09-18).

    python 면.py 그림 [케이스...]   -> out/면.png
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
for d in ("실험_20260913", "실험_20260915", "실험_20260916", "실험_20260918"):
    sys.path.insert(0, os.path.join(HERE, d))
os.chdir(HERE)
import hull as H
import 앨리어싱 as AL
from 계획 import _font
from 폴리싱 import shaded
from 면 import VARS, dihedral, meshes, rows

CASES = ["sendagaya_shino", "knight_Warrior_RaWl2GJ0NZ"]
S = 420


def main(cases=None):
    H.register_sheets()
    cases = cases or CASES
    cols = ("정답 (사람이 만든 것)", "TripoSG 생", "생성∩hull+보충 (우리 것)")
    im = Image.new("RGB", (30 + 2 * len(cols) * (S + 8), 140 + len(cases) * (S + 60)), "white")
    d = ImageDraw.Draw(im)
    d.text((24, 14), "면이 어디서 사라지나 — 왼쪽이 전신, 오른쪽이 같은 자리 확대", font=_font(30), fill=(20, 20, 20))
    d.text((24, 58), "면 법선 명암 · 빛 하나 · 회색 한 가지. 면이 이어지면 명암이 이어지고, 격자 계단이면 줄무늬로 끊긴다",
           font=_font(17), fill=(90, 90, 90))
    d.text((24, 82), "숫자 = 이웃 면 사이 각의 면적 몫 — 계단(30~60°) 은 마칭큐브가 복셀 격자에서 만드는 각이다",
           font=_font(17), fill=(90, 90, 90))
    for i, n in enumerate(cols):
        d.text((30 + i * 2 * (S + 8) + 10, 112), n, font=_font(20), fill=(30, 30, 30))

    for r, case in enumerate(cases):
        y = 140 + r * (S + 60)
        ms = meshes(case)
        for i, n in enumerate(("정답", "TripoSG생", "생성∩hull+보충")):
            m = ms[n]
            if n == "TripoSG생":                                   # 생 메시는 y 가 위다 — 보기 위해서만 세운다
                import trimesh.transformations as TT
                m = m.copy()
                m.apply_transform(TT.rotation_matrix(np.radians(90), [1, 0, 0]))
            # **틀은 메시마다 제 것으로 잡는다** — TripoSG 원본은 창 좌표가 아니라 제 좌표계에 있다
            fr = AL.frame_of(m, 45)
            (x0, z0), span = fr
            zoom = ((x0 + 0.30 * span, z0 + 0.52 * span), 0.30 * span)     # 가슴 · 어깨께 (틀 비율로 같은 자리)
            for j, f in enumerate((fr, zoom)):
                t = shaded(m, 45, f, S)
                im.paste(Image.fromarray(np.asarray(t)[:, :, ::-1] if t.ndim == 3 else t),
                         (30 + (2 * i + j) * (S + 8), y))
            q = dihedral(m)
            d.text((30 + 2 * i * (S + 8) + 4, y + S + 4),
                   "%s · 계단 %.2f · 능선 %.2f · 면 %d" % (case[:18], q["계단"], q["능선"], q["면"]),
                   font=_font(17), fill=(60, 60, 60))
            print("  %s %s" % (case, n), flush=True)
    p = os.path.join(HERE, "out", "면.png")
    im.save(p)
    print("  -> %s" % p)


if __name__ == "__main__":
    main()
