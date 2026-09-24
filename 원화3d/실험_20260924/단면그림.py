# -*- coding: utf-8 -*-
"""**단면 그림** — 속이 정말 비었나 (2026-09-24). 덩어리 대 껍질을 같은 평면으로 자른다."""
import os, sys
import numpy as np, trimesh, cv2
from PIL import Image, ImageDraw, ImageFont

sys.path[:0] = [r"G:\art2real\원화3d"]
import hull as H
F = lambda s: ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", s)
화소당mm = 0.28


def 단면(m, 높이몫=0.5):
    o = m.bounds[0] + (m.bounds[1] - m.bounds[0]) * np.array([0.5, 0.5, 높이몫])
    s = m.section(plane_origin=o, plane_normal=[0, 0, 1])
    if s is None: return None
    p, _ = s.to_planar()
    return p.polygons_full


def 칠(폴, 크기, 색=(40, 90, 170)):
    im = np.full((크기[1], 크기[0], 3), 255, np.uint8)
    for g in 폴:
        ext = np.array(g.exterior.coords)
        cv2.fillPoly(im, [ext.astype(np.int32)], 색)
        for h in g.interiors:
            cv2.fillPoly(im, [np.array(h.coords).astype(np.int32)], (255, 255, 255))
    return im


def main():
    c = "mech_Mech_4UvIHxnoSR"
    a = trimesh.load(os.path.join(H.OUT, "출력", c, "부품02.stl"), force="mesh")
    b = trimesh.load(os.path.join(H.OUT, "출력", c + "_껍질1.2", "부품02.stl"), force="mesh")
    폴들 = [단면(a), 단면(b)]
    모두 = [np.array(g.exterior.coords) for 폴 in 폴들 for g in 폴]
    lo = np.min([p.min(0) for p in 모두], 0); hi = np.max([p.max(0) for p in 모두], 0)
    w = int((hi[0] - lo[0]) / 화소당mm) + 20; h = int((hi[1] - lo[1]) / 화소당mm) + 20
    타 = []
    for 폴 in 폴들:
        이 = []
        for g in 폴:
            from shapely.affinity import scale as sc, translate as tr
            g2 = tr(sc(g, 1 / 화소당mm, 1 / 화소당mm, origin=(0, 0)),
                    -lo[0] / 화소당mm + 10, -lo[1] / 화소당mm + 10)
            이.append(g2)
        타.append(칠(이, (w, h)))
    판 = np.full((h + 44, w * 2 + 14, 3), 255, np.uint8)
    판[44:, :w] = 타[0]; 판[44:, w + 14:] = 타[1]
    p = Image.fromarray(판); d = ImageDraw.Draw(p)
    d.text((6, 4), "지금 (속 찬 덩어리) · 328 cm³", fill=(20, 20, 20), font=F(17))
    d.text((w + 20, 4), "껍질 1.2mm · 30 cm³", fill=(20, 20, 20), font=F(17))
    d.text((6, 25), "부품02 를 높이 한가운데에서 자른 단면 (같은 배율)", fill=(110, 110, 110), font=F(13))
    자 = int(10 / 화소당mm)
    d.line([(w * 2 - 자 - 10, h + 34), (w * 2 - 10, h + 34)], fill=(0, 0, 0), width=3)
    d.text((w * 2 - 자 - 10, h + 14), "10 mm", fill=(0, 0, 0), font=F(13))
    out = os.path.join(H.OUT, "단면_껍질.png")
    cv2.imencode(".png", np.asarray(p)[:, :, ::-1])[1].tofile(out)
    print(out, np.asarray(p).shape)


if __name__ == "__main__":
    main()
