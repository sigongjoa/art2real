# -*- coding: utf-8 -*-
"""**부품판** — 우리 부품을 키트 부품도처럼 늘어놓는다 (2026-09-24).

    python 부품판.py [폴더] [출력.png]

dalong 의 키트 부품도(흰 바탕에 부품을 늘어놓은 사진)와 같은 틀로 우리 부품을 그려
나란히 놓고 볼 수 있게 한다. 눈금자를 함께 그려 크기를 속이지 않는다.
"""
import os, sys
import numpy as np, trimesh, cv2
from PIL import Image, ImageDraw, ImageFont

디 = sys.argv[1] if len(sys.argv) > 1 else r"G:\art2real\원화3d\out\출력\mech_Mech_4UvIHxnoSR"
낼곳 = sys.argv[2] if len(sys.argv) > 2 else r"G:\art2real\원화3d\out\부품판.png"
화소당mm = 0.25                      # 1 화소 = 0.25mm -> 125mm 부품이 500 화소
여백 = 26


def 그리기(m, R, 배경):
    """화가 알고리즘. 실제 mm 를 그대로 화소로 옮긴다(부품끼리 크기가 비교된다)."""
    v = np.asarray(m.vertices) @ R.T
    tri = v[np.asarray(m.faces)]
    fn = np.asarray(m.face_normals) @ R.T
    L = np.array([0.3, -0.62, 0.72]); L /= np.linalg.norm(L)
    sh = np.clip(fn @ L, 0, 1) * 0.62 + 0.3
    x0, z0 = v[:, 0].min(), v[:, 2].min()
    w = int((v[:, 0].max() - x0) / 화소당mm) + 2
    h = int((v[:, 2].max() - z0) / 화소당mm) + 2
    im = np.full((h, w, 3), 배경, np.uint8)
    pts = np.stack([(tri[:, :, 0] - x0) / 화소당mm, h - (tri[:, :, 2] - z0) / 화소당mm], -1).astype(np.int32)
    for i in np.argsort(tri[:, :, 1].mean(1))[::-1]:
        c = int(200 * sh[i])
        cv2.fillConvexPoly(im, pts[i], (c, c - 6, c - 14))
    return im


def main():
    fs = sorted(f for f in os.listdir(디) if f.lower().endswith(".stl"))
    R = (trimesh.transformations.rotation_matrix(np.radians(26), [0, 0, 1])[:3, :3]
         @ trimesh.transformations.rotation_matrix(np.radians(-74), [1, 0, 0])[:3, :3])
    칸 = []
    for f in fs:
        m = trimesh.load(os.path.join(디, f), force="mesh")
        칸.append((f, 그리기(m, R, 255), m.extents, abs(m.volume)))
    열 = 3
    셀w = max(c[1].shape[1] for c in 칸) + 여백
    셀h = max(c[1].shape[0] for c in 칸) + 여백 + 18
    행 = (len(칸) + 열 - 1) // 열
    판 = np.full((행 * 셀h + 46, 열 * 셀w, 3), 255, np.uint8)
    pim = Image.fromarray(판); d = ImageDraw.Draw(pim)
    F = lambda s: ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", s)
    for k, (f, im, e, V) in enumerate(칸):
        r, c = divmod(k, 열)
        y = r * 셀h + 40 + (셀h - 18 - im.shape[0]) // 2
        x = c * 셀w + (셀w - im.shape[1]) // 2
        pim.paste(Image.fromarray(im), (x, y))
        d.text((c * 셀w + 8, r * 셀h + 40 + 셀h - 34),
               "%s   %.0f×%.0f×%.0f mm   %.0f cm³" % (f[:-4], e[0], e[1], e[2], V / 1000),
               fill=(70, 70, 70), font=F(13))
    # 눈금자 10mm
    자 = int(10 / 화소당mm)
    d.line([(14, 26), (14 + 자, 26)], fill=(0, 0, 0), width=3)
    d.text((14, 6), "10 mm", fill=(0, 0, 0), font=F(14))
    d.text((14 + 자 + 16, 6), "%s · 부품 %d · 전고 125mm(1/144)" % (os.path.basename(디), len(칸)),
           fill=(110, 110, 110), font=F(14))
    cv2.imencode(".png", np.asarray(pim)[:, :, ::-1])[1].tofile(낼곳)
    print(낼곳, np.asarray(pim).shape)


if __name__ == "__main__":
    main()
