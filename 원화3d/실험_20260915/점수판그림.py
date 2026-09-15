# -*- coding: utf-8 -*-
"""**점수판을 모양으로** — 정답(GT) · 옛 기본(파이프 lam0.20) · 새 기본(타원 lam1.00) 세 칸 (2026-09-15).

    python 점수판그림.py [케이스...]   -> out/점수판그림.png  (기본: 가장 오른 셋 · 가장 떨어진 셋)

같은 각도(앞 · 오른쪽 · 위) · 같은 틀 · 자르지 않음 · 세 칸 같은 회색. 사용자: 「GT 랑 옛날 거 지금 거 이렇게 비교해야지」.
처음 판은 겹침 색칠(회색 · 빨강 · 보라)로 두 칸만 그렸다.
"""
import json
import os
import sys

import cv2
import numpy as np
import trimesh
from PIL import Image, ImageDraw

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "실험_20260915"))
os.chdir(HERE)
import hull as H
import 대조 as C
import 오라클 as O
import 정답 as J
import 속채움그림 as SC
from 속채움그림 import S, basis, paint
from 계획 import _font

SHAPE = (170, 170, 170)                              # 세 칸 모두 같은 회색 — 색이 아니라 모양을 본다
FRONT_VIEW = np.array([0.8, 1.0, 0.45])              # 앞(+y) · 오른쪽 · 위에서. 자르지 않는다

PROG = os.path.join(HERE, "out", "기록", "점수판_진행.jsonl")


def picks(rows, k=3):
    d = sorted(rows.values(), key=lambda r: r["새"][1] - r["옛"][1])
    return [r["case"] for r in d[::-1][:k]] + [r["case"] for r in d[:k]]


def shapes(c):
    """정답 · 옛 기본 · 새 기본을 자르지 않고 같은 틀 · 같은 각도로. 정답은 원래 메시의 복셀 (속 채우지 않음)."""
    truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
    T, ot = J.grid(truth)
    _, old, axes, _ = O.build(c, truth, H.LAM, "파이프")
    _, new, axes2, _ = C.build(c)
    _, ora, axes3, _ = O.build(c, truth, 1.00, "오라클")      # 천장 — 정답 깊이를 넣었을 때. 여기서도 틀린 곳은 3판의 한계
    Go, oo = J.grid(O.C.to_mesh(old, axes))
    Gn, on = J.grid(O.C.to_mesh(new, axes2))
    Gc, oc = J.grid(O.C.to_mesh(ora, axes3))
    lo = np.minimum.reduce([ot, oo, on, oc])
    hi = np.maximum.reduce([ot + T.shape, oo + Go.shape, on + Gn.shape, oc + Gc.shape])

    def put(g, o):
        a = np.zeros(hi - lo + 2, bool)
        a[tuple(slice(o[i] - lo[i] + 1, o[i] - lo[i] + 1 + g.shape[i]) for i in range(3))] = g
        return a
    grids = [put(T, ot), put(Go, oo), put(Gn, on), put(Gc, oc)]
    SC.VIEW = FRONT_VIEW
    r, u, _ = basis()
    pts = np.argwhere(np.logical_or.reduce(grids))
    X, Y = pts @ r, pts @ u
    span = max(X.max() - X.min(), Y.max() - Y.min()) * 1.06
    frame = (((X.max() + X.min()) / 2 - span / 2, (Y.max() + Y.min()) / 2 - span / 2), span)
    return [paint([(g, SHAPE)], frame) for g in grids]


def main(cases):
    rows = {r["case"]: r for r in map(json.loads, open(PROG, encoding="utf-8"))}
    cases = cases or picks(rows)
    G, TOP, LW = 18, 140, 250
    im = Image.new("RGB", (LW + 4 * (S + G) + 30, TOP + len(cases) * (S + G) + 20), "white")
    d = ImageDraw.Draw(im)
    d.text((24, 16), "정답 · 옛 기본(파이프 lam 0.20) · 새 기본(타원 lam 1.00) · 천장(정답 깊이)", font=_font(30), fill=(20, 20, 20))
    d.text((24, 58), "같은 각도 · 같은 크기 · 자르지 않음 · 위 셋 = 점수가 가장 오른 장 · 아래 셋 = 가장 떨어진 장 · 숫자는 속 채운 정답 IoU",
           font=_font(18), fill=(90, 90, 90))
    d.text((24, 84), "천장에서도 틀린 곳 = 3판의 한계 · 천장은 맞는데 새 기본만 틀린 곳 = 다음 개선 대상", font=_font(18), fill=(40, 110, 200))
    for k, name in enumerate(("정답 (GT)", "옛 기본", "새 기본", "천장")):
        d.text((LW + k * (S + G) + S // 2 - 50, TOP - 34), name, font=_font(22), fill=(30, 30, 30))
    for i, c in enumerate(cases):
        y = TOP + i * (S + G)
        for k, t in enumerate(shapes(c)):
            im.paste(Image.fromarray(cv2.cvtColor(t, cv2.COLOR_BGR2RGB)), (LW + k * (S + G), y))
        r = rows[c]
        dv = r["새"][1] - r["옛"][1]
        d.text((24, y + S // 2 - 40), c[:24], font=_font(18), fill=(30, 30, 30))
        d.text((24, y + S // 2 - 12), "%.3f → %.3f" % (r["옛"][1], r["새"][1]), font=_font(22), fill=(30, 30, 30))
        d.text((24, y + S // 2 + 20), "%+.3f" % dv, font=_font(26), fill=(40, 120, 60) if dv > 0 else (200, 50, 50))
        print("  %s" % c, flush=True)
    p = os.path.join(HERE, "out", "점수판그림.png")
    im.save(p)
    print("  -> %s" % p)


if __name__ == "__main__":
    main(sys.argv[1:])
