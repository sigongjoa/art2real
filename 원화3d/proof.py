# -*- coding: utf-8 -*-
"""셋팅 증명 그림. **창이 실제로 무엇을 하는지** 한 장으로 본다.

    python proof.py        ->  out/proof_win.png

위 두 줄은 `win.py` 의 공유 배율, 아래 한 줄은 옛 방식(시점마다 bbox 로 재정규화)이다.
아래 줄에서 측면이 정면만큼 넓어지는 게 보이면 그게 「크기부터 다르다」를 지운 자리다.
"""
import os
import sys

import cv2
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

import win as W

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
T7 = os.path.join(W.__file__, "..", "..", "트레일", "trail7_part3d", "out")
T7 = os.path.normpath(T7)
CELL, BAND = 300, 34

def _font(sz):
    for f in ("C:/Windows/Fonts/malgun.ttf", "C:/Windows/Fonts/gulim.ttc"):
        try: return ImageFont.truetype(f, sz)
        except Exception: pass
    return ImageFont.load_default()

F1, F2 = _font(13), _font(11)


def load(path):
    s = trimesh.load(path)
    g = list(s.geometry.values()) if isinstance(s, trimesh.Scene) else [s]
    V = np.vstack([np.asarray(m.vertices) for m in g])
    F, o = [], 0
    for m in g:
        F.append(np.asarray(m.faces) + o); o += len(m.vertices)
    return V, np.vstack(F)


def refit(m):
    """옛 방식 — 실루엣 bbox 로 잘라 높이를 꽉 채운다. 시점마다 배율이 달라진다."""
    ys, xs = np.where(m)
    if len(ys) == 0:
        return m
    c = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    s = (W.RES - 2) / c.shape[0]
    w = max(1, int(round(c.shape[1] * s)))
    r = cv2.resize(c.astype(np.uint8), (min(w, W.RES), W.RES - 2),
                   interpolation=cv2.INTER_NEAREST).astype(bool)
    out = np.zeros((W.RES, W.RES), bool)
    x0 = max(0, (W.RES - r.shape[1]) // 2)
    out[1:W.RES - 1, x0:x0 + r.shape[1]] = r
    return out


def cell(m, label, ground=True):
    """마스크 한 장 -> 라벨 붙은 칸. 창 테두리와 z=0 접지선을 같이 그린다."""
    img = np.full(m.shape + (3,), 255, np.uint8)
    img[m] = (60, 90, 170)
    im = Image.fromarray(img).resize((CELL, CELL), Image.NEAREST)
    d = ImageDraw.Draw(im)
    if ground:                                   # z=0 접지선
        y = int((W.Z1 - 0.0) / (W.Z1 - W.Z0) * CELL)
        d.line([(0, y), (CELL, y)], fill=(220, 80, 80), width=1)
        x = int((0.0 - W.U0) / (W.U1 - W.U0) * CELL)
        d.line([(x, 0), (x, CELL)], fill=(230, 200, 200), width=1)
    d.rectangle([0, 0, CELL - 1, CELL - 1], outline=(170, 170, 170))
    out = Image.new("RGB", (CELL, CELL + BAND), "white")
    out.paste(im, (0, BAND))
    ImageDraw.Draw(out).text((6, 3), label, fill=(0, 0, 0), font=F1)
    ImageDraw.Draw(out).text((6, 19), "{:,} 화소".format(int(m.sum())), fill=(110, 110, 110), font=F2)
    return out


def row(path, axes, name, old=False):
    V, F = load(path)
    Wc = W.normalize(W.to_world(V, axes))
    cells = []
    for v in W.VIEWS:
        m = W.silhouette(Wc, F, v)
        if old:
            m = refit(m)
        cells.append(cell(m, "%s · %s%s" % (name, v, "  [옛 방식]" if old else ""), not old))
    return cells


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    rows = [
        row(os.path.join(T7, "omega6t.glb"), "xyz", "전신 (PartCrafter)"),
        row(os.path.join(T7, "op_front.glb"), "xzy", "견갑 (OmniPart)"),
        row(os.path.join(T7, "op_front.glb"), "xzy", "견갑", old=True),
    ]
    w = CELL * 3
    sheet = Image.new("RGB", (w, (CELL + BAND) * len(rows)), "white")
    for i, r in enumerate(rows):
        for j, c in enumerate(r):
            sheet.paste(c, (j * CELL, i * (CELL + BAND)))
    p = os.path.join(OUT, "proof_win.png")
    sheet.save(p)
    print("->", p)
