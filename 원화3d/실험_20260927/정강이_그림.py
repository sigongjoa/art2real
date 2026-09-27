# -*- coding: utf-8 -*-
"""정강이 모델을 실물 사진과 나란히 (2026-09-27).  python 정강이_그림.py -> out/키트/EG_RX78/정강이/정강이_실물대조.png"""
import sys, os, numpy as np, trimesh
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260925")
import 디테일대조 as DD
from scipy.spatial.transform import Rotation as Rot
from PIL import Image
D = r"G:\art2real\원화3d\out\키트\EG_RX78"
tm = trimesh.load(os.path.join(D, "정강이", "정강이.stl"))
def 그림(R, W=420, Hh=620, 빛=(-0.5, 0.45, 0.74), 색=(0.86, 0.9, 0.88)):
    V = tm.vertices @ R.T; N = tm.face_normals @ R.T
    cx_, cz_ = (V[:, 0].min() + V[:, 0].max()) / 2, (V[:, 1].min() + V[:, 1].max()) / 2; s = 66.0 / Hh
    Wb = max(W, Hh) + 2
    zb, tid = DD.래스터(V - [cx_, cz_, 0], tm.faces, W / 2, Hh / 2, s, Wb)
    zb, tid = zb[:Hh, :W], tid[:Hh, :W]
    img = np.ones((Hh, W, 3)) * 0.9; A = tid >= 0; Lt = np.array(빛, float); Lt /= np.linalg.norm(Lt)
    img[A] = np.array(색) * (np.clip(N[tid[A]] @ Lt, 0, 1) * 0.75 + 0.25)[:, None]
    nb = np.zeros((Hh, W, 3)); nb[A] = N[tid[A]]; z = np.where(A, zb, 0.0); 선 = np.zeros((Hh, W), bool)
    for ax in (0, 1):
        선 |= A & np.roll(A, 1, ax) & ((np.abs(z - np.roll(z, 1, ax)) > 0.3) | ((nb * np.roll(nb, 1, ax)).sum(-1) < np.cos(np.radians(20))))
    img[선] *= 0.55
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)
# 모델 좌표: x = 두께(겉쪽 +) · y = u · z = v.  옆(겉면)에서: 화면 X = y, Y = z, 깊이 = x
옆 = np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]], float)
비 = 옆 @ Rot.from_euler("z", 35, degrees=True).as_matrix()
앞 = 옆 @ Rot.from_euler("z", 90, degrees=True).as_matrix()
속 = 옆 @ Rot.from_euler("z", 180, degrees=True).as_matrix()
j1 = Image.open(os.path.join(D, "d_egx01_j1.jpg")).convert("RGB")
ph = j1.crop((615, 495, 715, 660)).resize((376, 620), Image.LANCZOS); ph2 = j1.crop((495, 495, 590, 662)).resize((353, 620), Image.LANCZOS)
tiles = [np.array(ph), 그림(옆), 그림(비), 그림(앞), 그림(속), np.array(ph2)]
Wt = sum(t.shape[1] for t in tiles); can = np.full((620, Wt, 3), 255, np.uint8); x = 0
for t in tiles: can[:, x:x + t.shape[1]] = t; x += t.shape[1]
Image.fromarray(can).save(os.path.join(D, "정강이", "정강이_실물대조.png")); print("ok")
