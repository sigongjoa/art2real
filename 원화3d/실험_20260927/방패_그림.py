# -*- coding: utf-8 -*-
"""방패 모델을 실물 사진 두 장과 같은 각도로 나란히 (2026-09-27).  python 방패_그림.py -> out/키트/EG_RX78/방패/방패_실물대조.png"""
import sys, os, numpy as np, trimesh
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260925")
import 디테일대조 as DD
from scipy.spatial.transform import Rotation as Rot
from PIL import Image
D = r"G:\art2real\원화3d\out\키트\EG_RX78"
tm = trimesh.load(os.path.join(D, "방패", "방패.stl"))
def 그림(R, W=560, 빛=(-0.55, 0.35, 0.76)):
    V = tm.vertices @ R.T; N = tm.face_normals @ R.T
    x0, x1 = V[:, 0].min() - 3, V[:, 0].max() + 3; z0, z1 = V[:, 1].min() - 3, V[:, 1].max() + 3; s = max(x1 - x0, z1 - z0) / W
    zb, tid = DD.래스터(V, tm.faces, -x0 / s, z1 / s, s, W)
    img = np.ones((W, W, 3)); A = tid >= 0; Lt = np.array(빛, float); Lt /= np.linalg.norm(Lt)
    img[A] = np.array([0.85, 0.2, 0.17]) * (np.clip(N[tid[A]] @ Lt, 0, 1) * 0.8 + 0.2)[:, None]
    nb = np.zeros((W, W, 3)); nb[A] = N[tid[A]]; z = np.where(A, zb, 0.0); 선 = np.zeros((W, W), bool)      # 모서리 선: 깊이 단차 > 0.25 mm · 법선 > 12°
    for d in ((0, 1), (1, 0)):
        선 |= A & np.roll(A, 1, d[1] if d[0] == 0 else 0) & ((np.abs(z - np.roll(z, 1, 1 if d[0] == 0 else 0)) > 0.25) | ((nb * np.roll(nb, 1, 1 if d[0] == 0 else 0)).sum(-1) < np.cos(np.radians(12))))
    img[선] = img[선] * 0.45
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)
눕 = Rot.from_euler("z", 90, degrees=True).as_matrix(); 비 = Rot.from_euler("x", -28, degrees=True).as_matrix() @ 눕
a = 그림(np.eye(3)); b = 그림(비)
ph = Image.open(os.path.join(D, "d_egx01_runner.jpg")).convert("RGB").crop((40, 50, 235, 140)).resize((560, 258), Image.LANCZOS)
j1 = Image.open(os.path.join(D, "d_egx01_j1.jpg")).convert("RGB").crop((800, 50, 940, 290)).resize((327, 560), Image.LANCZOS)
can = Image.new("RGB", (327 + 560 + 560, 560), "white")
can.paste(j1, (0, 0)); can.paste(Image.fromarray(a), (327, 0)); can.paste(ph, (327 + 560, 0)); bb = Image.fromarray(b); ys = np.nonzero((b < 250).any((1, 2)))[0]; can.paste(bb.crop((0, max(ys.min() - 10, 0), 560, min(ys.max() + 10, 560))).resize((560, 302)), (327 + 560, 258))
can.save(os.path.join(D, "방패", "방패_실물대조.png")); print("ok")
