# -*- coding: utf-8 -*-
"""데칼 — 원화의 작은 색 무늬(파란 번개)를 얇은 판으로 오려 겉 바로 앞에 (10-04 모양 13 바퀴 · 와타나베 「밀도를 올릴수록 멋있다」).
면 칠(칠투영)은 큰 면 전체가 물들어 얼룩이 됐다 → 무늬 윤곽만 다각형으로 오려(eps 1) 그 자리 모델 겉(z-버퍼) 0.4 앞에.
python 데칼.py <입력 ply> <출력 ply>"""
import os, sys, numpy as np, cv2, trimesh
from scipy.spatial import Delaunay
from scipy import ndimage
A = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
art = cv2.imdecode(np.fromfile(os.path.join(A, "판_1_원화.png"), np.uint8), 1); H, W = art.shape[:2]; hsv = cv2.cvtColor(art, cv2.COLOR_BGR2HSV)
m1 = np.load(os.path.join(A, "판_1_Z.npz"))["m"]; cu = (np.nonzero(m1)[1].min() + np.nonzero(m1)[1].max()) / 2
src, dst = sys.argv[1], sys.argv[2]; m = trimesh.load(os.path.join(B, src), process=False)
zb = np.full((H, W), np.inf); P2 = np.c_[m.vertices[:, 0] + cu, -m.vertices[:, 2]]; dz = m.vertices[:, 1]
for f in np.argsort(-dz[m.faces].mean(1)):
    mk = np.zeros((H, W), np.uint8); cv2.fillPoly(mk, [np.round(P2[m.faces[f]]).astype(np.int32)], 1); zb[mk > 0] = dz[m.faces[f]].mean()
_e = ~np.isfinite(zb); _, (iy, ix) = ndimage.distance_transform_edt(_e, return_indices=True); zb = zb[iy, ix]
파랑 = ((hsv[:, :, 0] >= 95) & (hsv[:, :, 0] <= 130) & (hsv[:, :, 1] > 90) & (m1 > 0)).astype(np.uint8)
파랑 = cv2.morphologyEx(파랑, cv2.MORPH_CLOSE, np.ones((2, 2), np.uint8))
import json
번개 = [np.array(v, float) for k, v in json.load(open(os.path.join(A, "특징점.json"), encoding="utf-8"))["1"].items() if k.startswith("번개")]   # 모양 13 2 판: 푸른 기 장면이라 뿔 그늘 · 눈 아래까지 파랑 → 번개 특징점 15 화소 안 덩어리만
cs, _ = cv2.findContours(파랑, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); VV = []; n = 0
cs = [c for c in cs if min(np.hypot(*(c.reshape(-1, 2) - b).T).min() for b in 번개) < 15]
for c in cs:
    if cv2.contourArea(c) < 6: continue
    poly = cv2.approxPolyDP(c, 1.0, True).reshape(-1, 2).astype(float)
    if len(poly) < 3: continue
    tri = Delaunay(poly); n += 1
    for t in tri.simplices:
        if cv2.pointPolygonTest(poly.astype(np.float32), tuple(poly[t].mean(0)), False) < 0: continue
        v3 = np.array([[x - cu, zb[int(np.clip(round(r), 0, H - 1)), int(np.clip(round(x), 0, W - 1))] - 0.4, -r] for x, r in poly[t]])
        if np.cross(v3[1] - v3[0], v3[2] - v3[0])[1] > 0: v3 = v3[::-1]
        VV.append(v3)
D = np.array(VV).reshape(-1, 3); DC = np.tile([50, 100, 215, 255], (len(D), 1))
V = np.r_[m.vertices[m.faces].reshape(-1, 3), D]; C = np.r_[m.visual.vertex_colors[m.faces].reshape(-1, 4), DC]
trimesh.Trimesh(V, np.arange(len(V)).reshape(-1, 3), vertex_colors=C.astype(np.uint8), process=False).export(os.path.join(B, dst), encoding="ascii")
print({"무늬": n, "데칼 삼각형": len(VV)})
