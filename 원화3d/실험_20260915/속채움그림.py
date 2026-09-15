# -*- coding: utf-8 -*-
"""**속채움 결과를 모양으로** — 케이스마다 반 자른 3D 두 칸 (2026-09-15).

    python 속채움그림.py [n]    아직 안 그린 장 n 개 (기본 1) -> out/속채움그림/<케이스>.png
    python 속채움그림.py 모음   -> out/속채움그림.png (속채움 배율 큰 순)

    왼쪽 · 정답      회색 원래 모델 · 파랑 층 채움으로 채운 속 · 주황 3판에서 안 보이는데 층 채움이 못 채운 곳
    오른쪽 · 원형    속 채운 정답 대 타원1.00 — 회색 겹침 · 빨강 원형이 넘친 곳 · 보라 원형이 모자란 곳

x 가운데에서 잘라 앞쪽 반만 남기고(+x 쪽을 지움), 절단면이 보이게 +x · 앞(+y) · 아래에서 본다. 격자 128 복셀 면.
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
import 오라클 as O
import 정답 as J
from 겉면채점 import bench_cases, bench_rows, fill_slices
from 계획 import _font

OUT = os.path.join(HERE, "out", "속채움그림")
S = 300
VIEW = np.array([1.0, 0.75, -0.45])                 # 물체에서 카메라 쪽. +x 절단면 · 앞 · 아래
LIGHT = np.array([0.35, 0.8, 0.5])
GRAY, BLUE, ORANGE = (175, 175, 175), (225, 145, 55), (40, 150, 245)            # BGR
OVERLAP, OVER, MISS = (185, 185, 185), (60, 60, 215), (175, 85, 160)


def basis():
    f = -VIEW / np.linalg.norm(VIEW)
    r = np.cross(f, [0, 0, 1.0])
    r /= np.linalg.norm(r)
    return r, np.cross(r, f), f


def unseen(T):
    """앞 · 뒤 · 옆 한쪽 광선이 처음 닿기 전 빈 칸만 보인다. 그 밖의 빈 칸."""
    hit = lambda ax, rev: (np.flip(np.cumsum(np.flip(T, ax), ax), ax) if rev else np.cumsum(T, ax)) > 0
    return ~T & hit(1, False) & hit(1, True) & hit(0, False)


def faces(mask, col):
    from skimage import measure
    if mask.sum() < 2:
        return None
    v, f, _, _ = measure.marching_cubes(np.pad(mask, 1).astype(np.uint8), 0.5)
    v -= 1
    r, u, fw = basis()
    T3 = v[f]
    n = np.cross(T3[:, 1] - T3[:, 0], T3[:, 2] - T3[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
    L = LIGHT / np.linalg.norm(LIGHT)
    shade = 0.42 + 0.58 * np.abs(n @ L)
    return (np.stack([v @ r, v @ u], 1)[f], (v @ fw)[f].mean(1), np.asarray(col, np.float32)[None] * shade[:, None])


def paint(layers, frame):
    parts = [p for p in (faces(m, c) for m, c in layers) if p is not None]
    img = np.full((S, S, 3), 255, np.uint8)
    if not parts:
        return img
    P = np.concatenate([p[0] for p in parts])
    D = np.concatenate([p[1] for p in parts])
    C = np.concatenate([p[2] for p in parts]).astype(np.int32)
    (x0, y0), span = frame
    Q = np.round(np.stack([(P[..., 0] - x0) / span * S, (1 - (P[..., 1] - y0) / span) * S], -1) * 4).astype(np.int32)
    for i in np.argsort(D)[::-1]:                                     # 먼 것부터
        cv2.fillConvexPoly(img, Q[i], C[i].tolist(), shift=2)
    return img


def one(c):
    truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
    T, ot = J.grid(truth)
    _, deep, axes, _ = O.build(c, truth, 1.00, "타원")
    G, og = J.grid(O.C.to_mesh(deep, axes))
    A, B = J.common(T, ot, G, og)
    A, B = np.pad(A, 1), np.pad(B, 1)
    F = fill_slices(A)
    U = unseen(A)
    xs = np.nonzero(A.any((1, 2)))[0]
    mid = (xs.min() + xs.max()) // 2
    for m in (A, B, F, U):
        m[mid + 1:] = False                                            # +x 반을 지운다 — 절단면이 보인다
    r, u, _ = basis()
    pts = np.argwhere(A | B | U)
    X, Y = pts @ r, pts @ u
    span = max(X.max() - X.min(), Y.max() - Y.min()) * 1.08
    frame = (((X.max() + X.min()) / 2 - span / 2, (Y.max() + Y.min()) / 2 - span / 2), span)
    left = paint([(A, GRAY), (F & ~A, BLUE), (U & ~F, ORANGE)], frame)
    right = paint([(B & F, OVERLAP), (B & ~F, OVER), (F & ~B, MISS)], frame)
    os.makedirs(OUT, exist_ok=True)
    cv2.imencode(".png", np.hstack([left, np.full((S, 6, 3), 255, np.uint8), right]))[1].tofile(os.path.join(OUT, c + ".png"))


def run(n):
    todo = [c for c in bench_cases() if c != "소체" and not os.path.exists(os.path.join(OUT, c + ".png"))]
    for c in todo[:n]:
        one(c)
        print("  %s" % c, flush=True)
    print("  남은 것 %d 장" % (len(todo) - min(n, len(todo))))


def sheet():
    rows = bench_rows()
    cases = sorted([c for c in bench_cases() if c != "소체"], key=lambda c: -rows[c]["속채움배"])
    COLS, CW, CH, TOP = 4, 2 * S + 6, S + 58, 150
    im = Image.new("RGB", (COLS * (CW + 24) + 24, TOP + ((len(cases) + COLS - 1) // COLS) * (CH + 18)), "white")
    d = ImageDraw.Draw(im)
    d.text((24, 18), "속 채운 정답 — 실물 28장 · 반 잘라 비스듬히 밑에서 · 속채움 배율 큰 순", font=_font(30), fill=(20, 20, 20))
    key = [((175, 175, 175), "원래 모델"), ((55, 145, 225), "채운 속"), ((245, 150, 40), "안 보이는데 못 채운 곳"),
           ((215, 60, 60), "원형이 넘친 곳"), ((160, 85, 175), "원형이 모자란 곳")]
    d.text((24, 66), "왼쪽 칸 · 정답", font=_font(20), fill=(90, 90, 90))
    d.text((24 + CW // 2 + 400, 66), "오른쪽 칸 · 속 채운 정답 대 지금 원형 (회색 = 겹침)", font=_font(20), fill=(90, 90, 90))
    x = 24
    for col, name in key:
        d.rectangle([x, 104, x + 18, 122], fill=col)
        d.text((x + 26, 100), name, font=_font(20), fill=(40, 40, 40))
        x += 60 + 13 * len(name) + 40
    for i, c in enumerate(cases):
        x, y = 24 + (i % COLS) * (CW + 24), TOP + (i // COLS) * (CH + 18)
        im.paste(Image.open(os.path.join(OUT, c + ".png")).convert("RGB"), (x, y))
        r = rows[c]
        a, b = r["타원1.00"]
        d.text((x, y + S + 6), c[:30], font=_font(18), fill=(30, 30, 30))
        d.text((x, y + S + 30), "속채움 %.2f배 · 지금 원형 %.3f → %.3f" % (r["속채움배"], a, b), font=_font(17),
               fill=(40, 110, 200) if b - a > 0.02 else (120, 120, 120))
    p = os.path.join(HERE, "out", "속채움그림.png")
    im.save(p)
    print("  -> %s" % p)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["모음"]:
        sheet()
    elif a and not a[0].isdigit():                   # 케이스 이름을 주면 그 장만 (다시) 그린다
        for c in a:
            one(c)
            print("  %s" % c)
    else:
        run(int(a[0]) if a else 1)
