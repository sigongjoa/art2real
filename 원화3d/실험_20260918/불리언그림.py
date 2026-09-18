# -*- coding: utf-8 -*-
"""불리언 그림 — 복셀로 깎은 것과 메시로 깎은 것을 같은 자리로 확대해 나란히 (2026-09-18).

    python 불리언.py 그림 [케이스...]   -> out/불리언.png
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
import trimesh

import hull as H
import 대조 as C
import 앨리어싱 as AL
from 계획 import _font
from 폴리싱 import shaded
from 면 import dihedral
from 불리언 import boolean_hull, fitted, gen_build, voxelize, rows

CASES = ["sendagaya_shino", "wizard_WIzard_Gnome_dEuyzEgrF4"]
S = 420


def main(cases=None):
    H.register_sheets()
    cases = cases or CASES
    cols = ("정답 (사람이 만든 것)", "복셀로 깎기 (지금)", "메시 불리언으로 깎기")
    im = Image.new("RGB", (30 + 2 * len(cols) * (S + 8), 140 + len(cases) * (S + 60)), "white")
    d = ImageDraw.Draw(im)
    d.text((24, 14), "같은 것을 복셀로 깎느냐 메시로 깎느냐 — 면이 남는다", font=_font(30), fill=(20, 20, 20))
    d.text((24, 58), "둘 다 TripoSG 한 판을 원화 3판 실루엣으로 깎은 것이다. 왼쪽은 256³ 복셀에 다시 굽고, 오른쪽은 실루엣 윤곽으로 세운 기둥 셋과 메시 불리언.",
           font=_font(17), fill=(90, 90, 90))
    d.text((24, 82), "면 법선 명암 · 빛 하나 · 회색 한 가지 · 같은 틀. 숫자 = 계단(이웃 면 사이 30~60° 의 면적 몫)",
           font=_font(17), fill=(90, 90, 90))
    for i, n in enumerate(cols):
        d.text((30 + i * 2 * (S + 8) + 10, 112), n, font=_font(20), fill=(30, 30, 30))

    rs = rows()
    for r, case in enumerate(cases):
        y = 140 + r * (S + 60)
        masks, bs, plain, base, axes = gen_build(case)
        gen = fitted(case, masks)
        truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
        ms = [truth, C.to_mesh(voxelize(gen, axes) & plain, axes), boolean_hull(gen, masks, bs)]
        fr = AL.frame_of(ms[0], 45)
        (x0, z0), span = fr
        zoom = ((x0 + 0.30 * span, z0 + 0.52 * span), 0.30 * span)
        for i, m in enumerate(ms):
            for j, f in enumerate((fr, zoom)):
                t = shaded(m, 45, f, S)
                im.paste(Image.fromarray(np.asarray(t)[:, :, ::-1] if t.ndim == 3 else t),
                         (30 + (2 * i + j) * (S + 8), y))
            q = dihedral(m)
            d.text((30 + 2 * i * (S + 8) + 4, y + S + 4),
                   "%s · 계단 %.3f · 면 %d" % (case[:20], q["계단"], q["면"]), font=_font(17), fill=(60, 60, 60))
            print("  %s %d" % (case, i), flush=True)
    p = os.path.join(HERE, "out", "불리언.png")
    im.save(p)
    print("  -> %s" % p)


if __name__ == "__main__":
    main()
