# -*- coding: utf-8 -*-
"""**결과 그림** — 실제 키트 · 우리 덩어리 · 우리 껍질을 같은 배율로 (2026-09-24).

    python 결과그림.py   -> out/결과_껍질.png

위: 부품을 늘어놓은 것. 아래: 같은 평면으로 자른 단면. 숫자는 그림에 붙인다.
"""
import os, sys
import numpy as np, trimesh, cv2
from PIL import Image, ImageDraw, ImageFont
from shapely.affinity import scale as sc, translate as tr

sys.path[:0] = [r"G:\art2real\원화3d", r"G:\art2real\원화3d\실험_20260924"]
import hull as H
import 부품판 as PP

화소당mm = 0.55
PP.화소당mm = 화소당mm
단면mm = 0.50
F = lambda s: ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", s)
R = (trimesh.transformations.rotation_matrix(np.radians(26), [0, 0, 1])[:3, :3]
     @ trimesh.transformations.rotation_matrix(np.radians(-74), [1, 0, 0])[:3, :3])
전고 = 125.0


def 읽기(디, 배율맞춤):
    ms = []
    for f in sorted(os.listdir(디)):
        if not f.lower().endswith(".stl"): continue
        m = trimesh.load(os.path.join(디, f), force="mesh"); m.merge_vertices()
        if abs(m.volume) > 0: ms.append(m)
    if 배율맞춤:
        모두 = trimesh.util.concatenate([m.copy() for m in ms])
        b = 전고 / float(모두.extents.max())
        for m in ms: m.apply_scale(b)
    return ms


def 선반(ms, 폭):
    타 = sorted((PP.그리기(m, R, 255) for m in ms), key=lambda im: -im.shape[0])
    줄들, 줄, w = [], [], 0
    for im in 타:
        if w + im.shape[1] + 9 > 폭 - 8 and 줄:
            줄들.append(줄); 줄, w = [], 0
        줄.append(im); w += im.shape[1] + 9
    if 줄: 줄들.append(줄)
    h = sum(max(i.shape[0] for i in r) + 10 for r in 줄들) + 6
    판 = np.full((h, 폭, 3), 255, np.uint8); y = 4
    for r in 줄들:
        x, hh = 4, max(i.shape[0] for i in r)
        for im in r:
            판[y + hh - im.shape[0]:y + hh, x:x + im.shape[1]] = im; x += im.shape[1] + 9
        y += hh + 10
    return 판


def 단면(m, 폭, 높이, 색):
    o = m.bounds[0] + (m.bounds[1] - m.bounds[0]) * np.array([0.5, 0.5, 0.5])
    s = m.section(plane_origin=o, plane_normal=[0, 0, 1])
    im = np.full((높이, 폭, 3), 255, np.uint8)
    if s is None: return im
    p, _ = s.to_planar()
    폴 = list(p.polygons_full)
    if not 폴: return im
    pts = np.vstack([np.array(g.exterior.coords) for g in 폴])
    lo = pts.min(0)
    cx, cy = 폭 / 2, 높이 / 2
    mid = (pts.max(0) + lo) / 2
    for g in 폴:
        g2 = tr(sc(g, 1 / 단면mm, 1 / 단면mm, origin=(0, 0)), cx - mid[0] / 단면mm, cy - mid[1] / 단면mm)
        cv2.fillPoly(im, [np.array(g2.exterior.coords).astype(np.int32)], 색)
        for hh in g2.interiors:
            cv2.fillPoly(im, [np.array(hh.coords).astype(np.int32)], (255, 255, 255))
    return im


def main():
    c = "mech_Mech_4UvIHxnoSR"
    열 = [
        ("실제 키트 부품 19 개", "게이트 통과 0.70 · 플라스틱 약 40 g · 사출",
         읽기(os.path.join(H.OUT, "키트정답", "680191"), True), (60, 130, 90)),
        ("우리 · 지금 6 개", "게이트 통과 0.00 · 297 g · 36시간 53분",
         읽기(os.path.join(H.OUT, "출력", c), False), (170, 80, 60)),
        ("우리 · 속 비움 1.2mm 6 개", "게이트 통과 1.00 · 129 g · 19시간 15분",
         읽기(os.path.join(H.OUT, "출력", c + "_껍질1.2"), False), (60, 100, 175)),
    ]
    폭 = 620
    위 = [선반(ms, 폭) for _, _, ms, _ in 열]
    hi = max(p.shape[0] for p in 위)
    단면높 = 232
    # 단면은 셋 다 «가장 큰 부품»으로
    큰 = [max(ms, key=lambda m: abs(m.volume)) for _, _, ms, _ in 열]
    아래 = [단면(m, 폭, 단면높, 색) for m, (_, _, _, 색) in zip(큰, 열)]
    H0, 머리, 띠 = 44, 52, 30
    캔 = np.full((H0 + 머리 + hi + 띠 + 단면높 + 16, 폭 * 3 + 24, 3), 255, np.uint8)
    for i in range(3):
        x = i * (폭 + 12)
        캔[H0 + 머리:H0 + 머리 + 위[i].shape[0], x:x + 폭] = 위[i]
        캔[H0 + 머리 + hi + 띠:H0 + 머리 + hi + 띠 + 단면높, x:x + 폭] = 아래[i]
    p = Image.fromarray(캔); d = ImageDraw.Draw(p)
    for i, (제, 부, _, 색) in enumerate(열):
        x = i * (폭 + 12) + 6
        d.text((x, H0 + 6), 제, fill=색, font=F(20))
        d.text((x, H0 + 32), 부, fill=(100, 100, 100), font=F(14))
        d.text((x, H0 + 머리 + hi + 8), "가장 큰 부품의 단면 (같은 배율)", fill=(120, 120, 120), font=F(13))
    자 = int(10 / 화소당mm)
    d.line([(12, 30), (12 + 자, 30)], fill=(0, 0, 0), width=3)
    d.text((12, 8), "10 mm", fill=(0, 0, 0), font=F(15))
    d.text((12 + 자 + 20, 8), "셋 다 전고 125mm(1/144) 로 맞추고 같은 배율 · 같은 각도로 그린 것", fill=(110, 110, 110), font=F(15))
    out = os.path.join(H.OUT, "결과_껍질.png")
    cv2.imencode(".png", np.asarray(p)[:, :, ::-1])[1].tofile(out)
    print(out, np.asarray(p).shape)


if __name__ == "__main__":
    main()
