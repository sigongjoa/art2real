# -*- coding: utf-8 -*-
"""**판정기가 실제로 뭘 겹쳐 봤나**를 그림으로 뽑는다. 숫자에 속지 않으려고 먼저 본다.

    python view.py 견갑             # case 이름 일부로 거른다
    python view.py                  # 전부

    빨강 = 원화만 · 초록 = 모델만 · 회색 = 겹침

trail7 이 `judge_view.py` 로 배운 것과 같은 이유다 — cfg12 판이 cfg7.5 보다 IoU 가
높았는데 형태가 나아서가 아니었다. 다른 건 하나, **시점마다 뽑는다.** 낙차가
「형태가 틀려서」인지 「원화 3판이 서로 안 맞아서」인지는 그림에서만 갈린다.

아무것도 안 고친다. `judge.py` 의 투영과 `judge_stand.art_mask` 를 그대로 부른다.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

import judge as Jd
from judge import J

OUT = os.path.join(Jd.HERE, "out")
BAND = 22                                     # 위쪽 라벨 띠


def panel(art, mesh, label):
    rgb = np.full(art.shape + (3,), 255, np.uint8)
    rgb[art & ~mesh] = (215, 60, 60)          # 원화만 — 모델이 못 채운 곳
    rgb[mesh & ~art] = (60, 165, 60)          # 모델만 — 원화 밖으로 나간 곳
    rgb[art & mesh] = (170, 170, 170)         # 겹침
    im = Image.new("RGB", (rgb.shape[1], rgb.shape[0] + BAND), "white")
    im.paste(Image.fromarray(rgb), (0, BAND))
    ImageDraw.Draw(im).text((4, 5), label, fill=(0, 0, 0))
    return im


def sheet(row):
    mesh_path = os.path.join(Jd.ROOT, row["mesh"])
    if not os.path.exists(mesh_path):
        return None
    import trimesh
    sc = trimesh.load(mesh_path)
    parts = list(sc.geometry.values()) if isinstance(sc, trimesh.Scene) else [sc]
    V = np.vstack([np.asarray(p.vertices) for p in parts])
    ax = (tuple("xyz".index(c) for c in row["axes"])
          if row.get("axes", "auto") != "auto" else J.axes(V))

    panels = []
    for v in Jd.VIEWS:
        png = row.get("art_" + v, "")
        if not png or not os.path.exists(os.path.join(Jd.ROOT, png)):
            continue
        A = J.art_mask(os.path.join(Jd.ROOT, png))
        M = Jd.mesh_mask(parts, ax, v)
        iou = float((M & A).sum()) / max(int((M | A).sum()), 1)
        panels.append(panel(A, M, "%s  IoU %.3f" % (v, iou)))
    if not panels:
        return None
    w = sum(p.width for p in panels)
    im = Image.new("RGB", (w, panels[0].height), "white")
    x = 0
    for p in panels:
        im.paste(p, (x, 0)); x += p.width
    return im


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    pick = [a for a in sys.argv[1:] if not a.startswith("-")]
    for row in Jd.read_cases():
        if pick and not any(p in row["case"] or p in row["model"] for p in pick):
            continue
        im = sheet(row)
        if im is None:
            print("  건너뜀 %s / %s" % (row["case"], row["model"])); continue
        f = os.path.join(OUT, "%s_%s.png" % (row["case"], row["model"].replace(".", "")))
        im.save(f)
        print("  %s" % os.path.basename(f))
