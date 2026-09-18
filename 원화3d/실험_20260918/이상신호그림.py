# -*- coding: utf-8 -*-
"""이상 신호 접촉지 — 28장을 **이상 점수 순위대로** 줄 세워 명암으로 본다 (2026-09-18).

    python 이상신호.py 그림   -> out/이상신호.png

판정은 사람 눈이다 — 위쪽이 정말 더 이상한가. 히트맵이 아니라 명암으로 본다 (09-16 사용자 지적).
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
import 대조 as C
import 앨리어싱 as AL
from 계획 import _font
from 생성깎기 import variants as gen_variants
from 폴리싱 import shaded
from 이상신호 import ranked

S, GAP, TOP, COLS = 300, 10, 128, 7


def main():
    H.register_sheets()
    order = ranked()
    rowsn = (len(order) + COLS - 1) // COLS
    im = Image.new("RGB", (20 + COLS * (S + GAP), TOP + rowsn * (S + 56) + 20), "white")
    d = ImageDraw.Draw(im)
    d.text((24, 14), "이상 신호로 줄 세운 28장 — 위줄이 정말 더 이상한가", font=_font(30), fill=(20, 20, 20))
    d.text((24, 56), "판본 = 생성∩hull+보충 (TripoSG 한 판 + 원화 실루엣으로 깎기) · 45도 · 면 법선 명암 · 같은 빛",
           font=_font(17), fill=(90, 90, 90))
    d.text((24, 80), "이상 점수 = 못덮음 · 가는곳 · 조각 · 찢김 · 실루엣 다섯의 순위 평균 (가중치 없음) · 클수록 이상",
           font=_font(17), fill=(90, 90, 90))
    d.text((24, 104), "아래 줄 = 점수 | 조각 수 · 찢김 · 가는곳", font=_font(16), fill=(120, 120, 120))

    for i, (case, sc, sig) in enumerate(order):
        r, c = divmod(i, COLS)
        x, y = 20 + c * (S + GAP), TOP + r * (S + 56)
        vs, plain, axes, masks, bs = gen_variants(case)
        mesh = C.to_mesh(vs["생성∩hull+보충"], axes)
        fr = AL.frame_of(mesh, 45)
        t = shaded(mesh, 45, fr, S)
        im.paste(Image.fromarray(np.asarray(t)[:, :, ::-1] if t.ndim == 3 else t), (x, y))
        d.text((x + 2, y + S + 2), case[:30], font=_font(14), fill=(40, 40, 40))
        d.text((x + 2, y + S + 20), "%.1f | 조각 %d · 찢김 %.3f · 가는곳 %.2f"
               % (sc, sig["조각"], sig["찢김"], sig["가는곳"]), font=_font(14), fill=(110, 110, 110))
        print("  %2d %s" % (i + 1, case), flush=True)
    p = os.path.join(HERE, "out", "이상신호.png")
    im.save(p)
    print("  -> %s" % p)
    pairs(order)


def pairs(order, k=7):
    """위 k 장 · 아래 k 장을 **정답 옆에** 둔다 — 「이상」인지 「원래 그런 모양」인지는 정답이 있어야 갈린다."""
    import trimesh
    sel = order[:k] + order[-k:]
    im = Image.new("RGB", (20 + k * (2 * S + 6 + GAP), 150 + 2 * (S + 76)), "white")
    d = ImageDraw.Draw(im)
    d.text((24, 14), "위 7장(이상 점수 높음) · 아래 7장(낮음) — 왼쪽이 정답, 오른쪽이 판본", font=_font(30), fill=(20, 20, 20))
    d.text((24, 56), "정답과 나란히 놓아야 「이상한 것」과 「원래 그런 모양」이 갈린다 (궤짝 · 모자는 납작한 게 맞다)",
           font=_font(17), fill=(90, 90, 90))
    for i, (case, sc, sig) in enumerate(sel):
        r, c = divmod(i, k)
        x, y = 20 + c * (2 * S + 6 + GAP), 150 + r * (S + 76)
        vs, plain, axes, masks, bs = gen_variants(case)
        mesh = C.to_mesh(vs["생성∩hull+보충"], axes)
        truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
        fr = AL.frame_of(truth, 45)
        for j, m in enumerate((truth, mesh)):
            t = shaded(m, 45, fr, S)
            im.paste(Image.fromarray(np.asarray(t)[:, :, ::-1] if t.ndim == 3 else t), (x + j * (S + 6), y))
        d.text((x + 2, y + S + 2), "%s" % case[:40], font=_font(15), fill=(40, 40, 40))
        d.text((x + 2, y + S + 22), "이상 점수 %.1f | 조각 %d · 찢김 %.3f · 가는곳 %.2f"
               % (sc, sig["조각"], sig["찢김"], sig["가는곳"]), font=_font(15), fill=(110, 110, 110))
        print("  짝 %s" % case, flush=True)
    q = os.path.join(HERE, "out", "이상신호_짝.png")
    im.save(q)
    print("  -> %s" % q)


if __name__ == "__main__":
    main()
