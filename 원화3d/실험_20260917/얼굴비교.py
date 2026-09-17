# -*- coding: utf-8 -*-
"""**은둔자 얼굴만 잘라 원화와 나란히** (2026-09-17). 방향 잡기용 관찰 그림 — 점수 없음.

    python 얼굴비교.py      -> out/은둔자_얼굴비교.png

윗줄은 나무위키 그림 1장(TripoSG 입력), 아랫줄은 공식 삼면도 정면. 원화 칸에는 **그 파이프라인이 실제로 본 화소**를 그대로 키워 넣는다.
메시는 머리 상자 안 면만 떼서 같은 방향(원화와 같은 시점)에서 명암으로 그린다.
"""
import os
import sys

import cv2
import numpy as np
import trimesh
from PIL import Image, ImageDraw

HERE = r"G:\art2real\원화3d"
for d in ("", "실험_20260913", "실험_20260916"):
    sys.path.insert(0, os.path.join(HERE, d))
os.chdir(HERE)
import 폴리싱 as PL
from 계획 import _font

S = r"C:\Users\zesky\AppData\Local\Temp\claude\G--art2real\612c5d2a-3321-47b1-8ebf-c897df4a0801\scratchpad"
T = 400
# 머리 상자 (정규화 z 위 좌표 · 09-17 탐침): (x0, x1, z0, z1, az)
BOX_NAMU = (-0.07, 0.15, 0.845, 1.005, 180)            # 이 메시는 az 180 이 입력 판 시점
BOX_3 = (-0.075, 0.075, 0.875, 1.0, 0)


def load(path):
    m = trimesh.load(path, force="mesh")
    if m.bounds[1, 2] > 1.5 or m.bounds[0, 2] < -0.1:   # 정제기 원좌표(y 위 · 키 1.9) -> 정규화 z 위
        V = np.asarray(m.vertices)
        y0, h = V[:, 1].min(), np.ptp(V[:, 1])
        m = trimesh.Trimesh(np.stack([V[:, 0] / h, V[:, 2] / h, (V[:, 1] - y0) / h], 1), m.faces, process=False)
    return m


def face(m, box, tint=None):
    x0, x1, z0, z1, az = box
    c = m.triangles_center
    keep = (c[:, 2] > z0 - 0.03) & (c[:, 0] > x0 - 0.05) & (c[:, 0] < x1 + 0.05)
    sub = m.submesh([np.nonzero(keep)[0]], append=True)
    t = None if tint is None else tint[keep]
    a = np.radians(az)
    V = sub.vertices[(sub.vertices[:, 2] > z0) & (sub.vertices[:, 0] > x0) & (sub.vertices[:, 0] < x1)]
    X = np.cos(a) * V[:, 0] - np.sin(a) * V[:, 1]              # 화면 가로 (`깊이색.project` 와 같은 식)
    span = max(x1 - x0, z1 - z0)
    return PL.shaded(sub, az, (((X.min() + X.max()) / 2 - span / 2, z1 - span), span), T, tint=t)


def art(path, box, interp):
    a = cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_UNCHANGED)
    if a.shape[2] == 4:
        al = a[:, :, 3:] / 255.0
        a = (a[:, :, :3] * al + 255 * (1 - al)).astype(np.uint8)
    y0, y1, x0, x1 = box
    c = a[y0:y1, x0:x1]
    return cv2.cvtColor(cv2.resize(c, (T, T), interpolation=interp), cv2.COLOR_BGR2RGB), c.shape[0]


def main():
    namu_art, n1 = art(os.path.join(S, "dg_head", "face.png"), (0, 220, 0, 220), cv2.INTER_CUBIC)
    tri_art, n3 = art(os.path.join("out", "은둔자_자료", "삼면", "front.png"), (8, 66, 80, 138), cv2.INTER_NEAREST)
    rows = [
        ("나무위키 그림 1장 → TripoSG", [
            ("원화 (정제기에 준 얼굴 크롭 %d화소)" % n1, namu_art),
            ("TripoSG 원출력", face(load("out/은둔자.glb"), BOX_NAMU)),
            ("+ DetailGen3D 머리 정제", face(load("out/은둔자_머리정제.glb"), BOX_NAMU)),
            ("+ 포스터 얼굴로 정제", face(load(os.path.join(S, "dg_head", "merged_poster.glb")), BOX_NAMU)),
        ]),
        ("공식 삼면도 → 3판", [
            ("원화 (정면 판 머리 %d화소)" % n3, tri_art),
            ("A 3판 hull (지금 기본)", face(load("out/은둔자삼면_A.glb"), BOX_3)),
            ("B TripoSG ∩ hull", face(load("out/은둔자삼면_B.glb"), BOX_3)),
            ("C′ A 를 DetailGen3D 정제", face(load("out/은둔자삼면_dgA_front.glb"), BOX_3)),
        ]),
    ]
    G, LW, TOP, CAP = 10, 170, 80, 30
    im = Image.new("RGB", (LW + 4 * (T + G), TOP + len(rows) * (T + CAP + G)), "white")
    d = ImageDraw.Draw(im)
    d.text((16, 14), "은둔자 얼굴 — 원화 vs 우리가 만든 메시 (같은 시점 · 머리만)", fill="black", font=_font(26))
    d.text((16, 50), "원화 칸은 파이프라인이 실제로 받은 화소를 키운 것 · 메시는 면 법선 명암", fill=(90, 90, 90), font=_font(15))
    for r, (name, tiles) in enumerate(rows):
        y = TOP + r * (T + CAP + G)
        d.text((12, y + T // 2), name, fill="black", font=_font(16))
        for i, (cap, tile) in enumerate(tiles):
            x = LW + i * (T + G)
            d.text((x, y + 4), cap, fill="black", font=_font(16))
            im.paste(Image.fromarray(tile), (x, y + CAP))
    q = os.path.join("out", "은둔자_얼굴비교.png")
    im.save(q)
    print(" ->", q)


if __name__ == "__main__":
    main()
