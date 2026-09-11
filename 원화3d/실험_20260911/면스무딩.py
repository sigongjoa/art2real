# -*- coding: utf-8 -*-
"""**실루엣을 안 건드리는 스무딩** 시험 — `hull.ZSMOOTH` (앞·뒷면 깊이를 z 로만 민다).

    python 면스무딩.py 케이스

σ 0 · 2 · 4 마다 판본(파이프0.20 · 파이프0.50 · 타원0.50 · 오라클0.50)을 다시 깎고 잰다:
    IoU      제 부피 대조군(hull 을 그 부피까지 매끈하게 민 것) 대비 — lam4 와 같은 대조군
    찢김     앞면이 위아래 이웃 줄끼리 >3칸 튄 쌍 · 조각 50칸↑ · 실루엣 손실 (정면·측면 중 큰 쪽)
이 스무딩은 결과만 바꾸고 hull 은 그대로라 대조군은 σ 와 무관하다 (대조군의 부피만 판본 따라 바뀐다).
-> out/면스무딩_<케이스>.png (45도)"""
import os
import sys

import numpy as np
import trimesh
from PIL import Image, ImageDraw

SCR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCR)
import 벤치smooth as BS                                # cwd 를 원화3d 로 · O 를 부른다
import 벤치그림 as RG
from 계획 import _font

O, H = BS.O, BS.O.H
VERS = [("파이프", 0.20), ("파이프", 0.50), ("타원", 0.50), ("오라클", 0.50)]
SIG = (0, 2, 4)


def main():
    case = sys.argv[1]
    O.H.register_sheets()
    truth = trimesh.load(os.path.join(O.OUT, "시트", case, "truth.glb"), force="mesh")
    T, ot = O.J.grid(truth)

    def iou(m):
        G, og = O.J.grid(m)
        A, B = O.J.common(T, ot, G, og)
        return float((A & B).sum() / max((A | B).sum(), 1))

    res, meshes = {}, {}
    plain = axes = keep = None
    curve = None
    print("  %s   (대조 = 제 부피 · 찢김 위아래 >3칸 · 조각 50칸↑ · 실루엣 손실)" % case)
    for s in SIG:
        H.ZSMOOTH = float(s)
        for which, l in VERS:
            pl, v, ax, _ = O.build(case, truth, l, which)
            if plain is None:
                plain, axes = pl, ax
                keep = H.sdf_of(plain)
                vh = BS.mesh(keep, axes).volume
                ts, vs = [0.0], [1.0]
                while vs[-1] > 0.55 and ts[-1] < 12:
                    ts.append(ts[-1] + 0.25)
                    vs.append(BS.mesh(keep - ts[-1], axes, False).volume / vh)
                curve = (ts, vs, vh)
            k = "%s%.2f" % (which, l)
            m = BS.mesh(H.sdf_of(v), axes)
            ts, vs, vh = curve
            rv = m.volume / vh
            t = float(np.interp(rv, vs[::-1], ts[::-1]))
            ci = iou(BS.mesh(keep - t, axes))
            x = iou(m)
            res[(k, s)] = (x, x - ci, BS.tear(v), BS.pieces(v), BS.sil_loss(v, plain), rv)
            meshes[(k, s)] = m
            print("    σ%d %-11s IoU %.4f (대조 %+.4f) · 찢김 %5.1f%% · 조각 %2d · 실루엣 손실 %.2f%% · 부피 %.3f"
                  % (s, k, x, x - ci, 100 * res[(k, s)][2], res[(k, s)][3], 100 * res[(k, s)][4], rv), flush=True)
    H.ZSMOOTH = 0.0
    # 그림 — 줄 = 판본, 칸 = σ
    R = RG.rot(np.asarray(BS.mesh(keep, axes).vertices))
    lo, hi = R.min(0), R.max(0)
    span = max(hi[0] - lo[0], hi[2] - lo[2]) * 1.04
    frame = ((lo[0] + hi[0]) / 2 - span / 2, (lo[2] + hi[2]) / 2 - span / 2), span
    S, G, LW, TOP = 260, 10, 140, 80
    tint = {"파이프0.20": RG.TINT["파이프0.20"], "파이프0.50": RG.TINT["파이프0.50"],
            "타원0.50": RG.TINT["타원0.50"], "오라클0.50": RG.TINT["오라클0.50"]}
    names = ["%s%.2f" % v for v in VERS]
    im = Image.new("RGB", (LW + (len(SIG) + 1) * (S + G) + G, TOP + len(names) * (S + 30)), "white")
    d = ImageDraw.Draw(im)
    f1, f2, f3 = _font(22), _font(15), _font(12)
    d.text((16, 12), "%s — 면 스무딩 (앞·뒷면 깊이를 높이 방향으로만) σ 0·2·4 · 45도" % case, fill=(20, 20, 20), font=f1)
    d.text((16, 44), "실루엣을 원리적으로 안 건드린다 — 기둥을 안 지우고, hull 밖으로 안 나가고, 높이마다 제일 앞·뒤를 지킨다",
           fill=(90, 90, 90), font=f3)
    d.text((LW + G, TOP - 22), "정답", fill=(40, 40, 40), font=f2)
    for c, s in enumerate(SIG):
        d.text((LW + G + (c + 1) * (S + G), TOP - 22), "σ %d" % s, fill=(40, 40, 40), font=f2)
    im.paste(Image.fromarray(RG.render(truth, frame, S, RG.TINT["정답"])), (LW + G, TOP))
    for i, k in enumerate(names):
        y0 = TOP + i * (S + 30)
        d.text((12, y0 + S // 2), k, fill=(20, 20, 20), font=f2)
        for c, s in enumerate(SIG):
            x0 = LW + G + (c + 1) * (S + G)
            im.paste(Image.fromarray(RG.render(meshes[(k, s)], frame, S, tint[k])), (x0, y0))
            x, dv, tr, pc, sl, _ = res[(k, s)]
            d.text((x0, y0 + S + 4), "IoU %.4f (%+.4f) · 찢김 %.0f%% · 조각 %d · 실루엣 −%.1f%%" % (x, dv, 100 * tr, pc, 100 * sl),
                   font=f3, fill=(30, 130, 70) if dv > 0 else (190, 60, 40))
    p = os.path.join(RG.HERE, "out", "면스무딩_%s.png" % case)
    im.save(p)
    print("  ->", p)


if __name__ == "__main__":
    main()
