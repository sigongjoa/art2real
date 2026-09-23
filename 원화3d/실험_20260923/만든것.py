# -*- coding: utf-8 -*-
"""**만들어진 것** — 판 다섯이 실제로 어떤 모양인지 케이스마다 한 줄로 본다 (2026-09-23).

    python 만든것.py [각도]    -> out/만든것.png
사용자(09-23): 「나는 지표가 아니라 그림을 원해 — 만들어진 거」.
"""
import os, sys
import numpy as np
import cv2
from scipy import ndimage
import trimesh
from PIL import Image, ImageDraw, ImageFont

sys.path[:0] = [r"G:\art2real\원화3d", r"G:\art2real\원화3d\실험_20260921", r"G:\art2real\원화3d\실험_20260922", r"G:\art2real\원화3d\실험_20260923"]
import hull as H
import win as W
import 정답 as JD
import 부품분할 as BB
import 면자르기 as MJ
import 도면벤치_천장 as DC
import 지표 as Z
import 색대응 as CC
import 최소표면 as MS
import 깊이칸 as K
import 깊이추정 as GC

F = lambda s: ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", s)
크기 = 210


def 셰이딩(m, yaw=32, pitch=-72, 색=(224, 224, 224)):
    v = np.asarray(m.vertices); v = v - v.mean(0)
    R = (trimesh.transformations.rotation_matrix(np.radians(yaw), [0, 0, 1])[:3, :3]
         @ trimesh.transformations.rotation_matrix(np.radians(pitch), [1, 0, 0])[:3, :3])
    p = v @ R.T
    fn = np.asarray(m.face_normals) @ R.T
    tri = p[np.asarray(m.faces)]
    sc = 크기 * 0.40 / max(np.abs(p[:, [0, 2]]).max(), 1e-9)
    pts = np.stack([tri[:, :, 0] * sc + 크기 / 2, -tri[:, :, 2] * sc + 크기 / 2], -1).astype(np.int32)
    order = np.argsort(tri[:, :, 1].mean(1))[::-1]
    L = np.array([0.35, -0.6, 0.72]); L = L / np.linalg.norm(L)
    sh = np.clip(fn @ L, 0, 1) * 0.72 + 0.28
    im = np.full((크기, 크기, 3), 255, np.uint8)
    for i in order:
        c = tuple(int(x * sh[i]) for x in 색)
        cv2.fillConvexPoly(im, pts[i], c)
    return im


def 한줄(c):
    raw, masks, bs, p = BB.판(c)
    g, ax = H.field_default(masks, back_sign=bs, n=BB.N)
    gh, _ = H.field_hull(masks, back_sign=bs, n=BB.N)
    ux, uy, z = [np.asarray(a) for a in ax]
    O = g > 0
    tm = trimesh.load(os.path.join(H.OUT, "시트", c, "truth.glb"), force="mesh")
    A, o = JD.grid(tm, 봉합=1)
    T = DC.우리격자로(A.astype(np.int32), np.asarray(o), ux, uy, z) > 0
    격, _ = CC.판색(c, raw, masks, p, bs)
    _, 부위, _ = MJ.부위(O); 부위 = BB.채우기(부위, O)
    값 = {l: K.숫자읽기(부위, T, l) for l in np.unique(부위) if l}
    값 = {l: v for l, v in 값.items() if v}
    판 = [("hull", gh > 0, (205, 205, 205)), ("타원(지금)", O, (205, 190, 165)),
         ("색 대응", CC.깎기(O, 격, 6), (175, 205, 185)), ("최소표면", MS.되돌림(O, 1.6, 6), (195, 195, 215)),
         ("깊이칸(신탁)", K.조이기(O, 부위, 값, "D2"), (215, 195, 160))]
    타 = []
    앞 = masks["front"] > 0.5
    im = np.full(앞.shape + (3,), 255, np.uint8); im[앞] = (90, 90, 90)
    타.append(("원화 앞", cv2.resize(im, (크기, 크기), interpolation=cv2.INTER_AREA)))
    for 이름, V, col in 판:
        타.append((이름, 셰이딩(Z.메시로(V, (ux, uy, z)), 색=col)))
    타.append(("정답", 셰이딩(tm, 색=(170, 170, 170))))
    return 타


def main(각도=32):
    케이스 = [GC.케이스들[i] for i in (0, 4, 5, 6, 7, 9)]
    줄들, 이름줄 = [], None
    for c in 케이스:
        타 = 한줄(c)
        이름줄 = [n for n, _ in 타]
        row = np.hstack([t for _, t in 타])
        band = np.full((22, row.shape[1], 3), 255, np.uint8)
        pim = Image.fromarray(np.vstack([band, row]))
        ImageDraw.Draw(pim).text((5, 3), c[:34], fill=(80, 80, 80), font=F(14))
        줄들.append(np.asarray(pim))
        print("  ", c, flush=True)
    머리 = Image.fromarray(np.full((30, 줄들[0].shape[1], 3), 255, np.uint8))
    d = ImageDraw.Draw(머리)
    for i, n in enumerate(이름줄):
        d.text((i * 크기 + 6, 6), n, fill=(25, 25, 25), font=F(15))
    out = np.vstack([np.asarray(머리)] + 줄들)
    p = os.path.join(H.OUT, "만든것.png")
    cv2.imencode(".png", out[:, :, ::-1])[1].tofile(p)
    print(p, out.shape)


if __name__ == "__main__":
    main()
