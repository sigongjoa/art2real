# -*- coding: utf-8 -*-
"""**부품 비교판** — 실제 키트 부품과 우리 부품을 «같은 배율»로 나란히 (2026-09-24).

    python 부품비교판.py      -> out/부품비교판.png

둘 다 전고 125mm(1/144) 로 맞추고 같은 화소/mm 로 그린다. 사진이 아니라 렌더라 크기가 정확히 비교된다.
"""
import os, sys
import numpy as np, trimesh, cv2
from PIL import Image, ImageDraw, ImageFont

sys.path[:0] = [r"G:\art2real\원화3d", r"G:\art2real\원화3d\실험_20260924"]
import hull as H
from 부품판 import 그리기

화소당mm = 0.55
전고 = 125.0
F = lambda s: ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", s)
R = (trimesh.transformations.rotation_matrix(np.radians(26), [0, 0, 1])[:3, :3]
     @ trimesh.transformations.rotation_matrix(np.radians(-74), [1, 0, 0])[:3, :3])
import 부품판 as PP
PP.화소당mm = 화소당mm


def 부품들(디, 배율맞춤=True):
    ms = []
    for f in sorted(os.listdir(디)):
        if not f.lower().endswith(".stl"): continue
        m = trimesh.load(os.path.join(디, f), force="mesh"); m.merge_vertices()
        if m.volume <= 0: continue
        ms.append(m)
    if 배율맞춤:
        모두 = trimesh.util.concatenate([m.copy() for m in ms])
        b = 전고 / float(모두.extents.max())
        for m in ms: m.apply_scale(b)
    return ms


def 판(ms, 폭, 제목, 부제):
    """부품을 큰 것부터 왼쪽 위에 채워 넣는다(단순 선반 배치)."""
    타 = sorted((그리기(m, R, 255) for m in ms), key=lambda im: -im.shape[0])
    선반, 줄, w = [], [], 0
    for im in 타:
        if w + im.shape[1] + 10 > 폭 - 8 and 줄:
            선반.append(줄); 줄, w = [], 0
        줄.append(im); w += im.shape[1] + 10
    if 줄: 선반.append(줄)
    높 = sum(max(im.shape[0] for im in r) + 12 for r in 선반) + 52
    판 = np.full((높, 폭, 3), 255, np.uint8)
    y = 46
    for r in 선반:
        x, h = 4, max(im.shape[0] for im in r)
        for im in r:
            판[y + h - im.shape[0]:y + h, x:x + im.shape[1]] = im
            x += im.shape[1] + 10
        y += h + 12
    p = Image.fromarray(판); d = ImageDraw.Draw(p)
    d.text((6, 4), 제목, fill=(20, 20, 20), font=F(19))
    d.text((6, 26), 부제, fill=(110, 110, 110), font=F(14))
    return np.asarray(p)


def main():
    키 = 부품들(os.path.join(H.OUT, "키트정답", "680191"))
    우 = 부품들(os.path.join(H.OUT, "출력", "mech_Mech_4UvIHxnoSR"), 배율맞춤=False)
    폭 = 900
    A = 판(키, 폭, "실제 키트 부품 %d 개" % len(키),
          "Printables 680191 (조립 좌표 확인 · 닿음 51) · 전고 125mm 로 맞춤 · 합계 %.0f cm³" % (sum(m.volume for m in 키) / 1000))
    B = 판(우, 폭, "우리 부품 %d 개" % len(우),
          "원화 3면 → 타원 → 제약분할 · 전고 125mm · 합계 %.0f cm³" % (sum(m.volume for m in 우) / 1000))
    h = max(A.shape[0], B.shape[0])
    캔 = np.full((h + 40, 폭 * 2 + 12, 3), 255, np.uint8)
    캔[40:40 + A.shape[0], :폭] = A
    캔[40:40 + B.shape[0], 폭 + 12:] = B
    캔[40:, 폭 + 4:폭 + 8] = 210
    p = Image.fromarray(캔); d = ImageDraw.Draw(p)
    자 = int(10 / 화소당mm)
    d.line([(10, 26), (10 + 자, 26)], fill=(0, 0, 0), width=3)
    d.text((10, 6), "10 mm", fill=(0, 0, 0), font=F(15))
    d.text((10 + 자 + 20, 6), "같은 배율 · 같은 각도로 그린 것 (사진 아님)", fill=(110, 110, 110), font=F(15))
    out = os.path.join(H.OUT, "부품비교판.png")
    cv2.imencode(".png", np.asarray(p)[:, :, ::-1])[1].tofile(out)
    print(out, np.asarray(p).shape)


if __name__ == "__main__":
    main()
