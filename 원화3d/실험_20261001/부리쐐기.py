# -*- coding: utf-8 -*-
"""부리 쐐기 — 창 모듈 앞에 얹는 따로 된 덩어리 (10-04 「ㄱㄱ」 · 얼굴 모듈 실패 → 부리는 쐐기).
옆에서 칸 이름은 안 쓴다(이름 짝이 계속 틀렸다) — 기하로만 고른다:
  옆 윤곽 = 옆 머리 마스크 중 「창 입구(−17)보다 앞」 · 높이 L6 ~ L2 (B 맞춤으로 정면 층에 맞춤) = 주둥이 단면
  정면 윤곽 = 정면 마스크 칸(부품ID H02) ∪ 코판 능선(두 창 사이 · 축 B'~B · L6~L4) · 창(앞 윤곽)은 뺌
  쐐기 = 정면 윤곽 ∩ 옆 윤곽(두 장 헐 · 깊이 −130 ~ −17)
창 모듈 3 판(창모듈2.ply)과 합쳐 얼굴로. 출력 out/오메가몬2/블렌더/부리쐐기.ply · 부리쐐기_비교.png"""
import os, json, numpy as np, cv2, trimesh
from skimage import measure
G = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "창모듈2.py")}; exec(open(G["__file__"], encoding="utf-8").read(), G)
O, B, m, H, W, px, py, cell, 층, 축, cu, D, 앞 = [G[k] for k in ("O", "B", "m", "H", "W", "px", "py", "cell", "층", "축", "cu", "D", "앞")]
K = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "기준선.py")}; exec(open(K["__file__"], encoding="utf-8").read(), K)
k, t, c, xm, ex, ey = [K[q] for q in ("k", "t", "c", "xm", "ex", "ey")]; ct, st = np.cos(t), np.sin(t)
Ai = np.linalg.inv(np.array([[k * ct, -k * st], [k * st, k * ct]])); b0 = np.array([-k * (ex * ct - ey * st), -k * xm * st + c])
대응 = json.load(open(os.path.join(O, "부품ID.json"), encoding="utf-8"))["대응표"]["1"]
L6, L4, L2 = 층["L6 처마"], 층["L4 코판 끝"], 층["L2 턱 끝"]
정면 = np.isin(cell, [c_ for e in 대응 if e.get("부품") == "H02 마스크" for c_ in e["칸"]])
xb1, xb2 = sorted([축["B' 눈구멍 안 L"], 축["B 눈구멍 안 R"]]); 정면 |= m & (px >= xb1) & (px <= xb2) & (py >= L6) & (py <= L4)
정면 = (cv2.morphologyEx(정면.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)) > 0) & ~앞 & (py >= L6) & (py <= L2 + 3)
m2 = np.load(os.path.join(O, "판_2_Z.npz"))["m"]
st_ = 1.0; xs = np.arange(-120, 120, st_); ds = np.arange(-135, -16, st_); zs = np.arange(-(L2 + 6), -(L6 - 2), st_)
GX, GD, GZ = np.meshgrid(xs, ds, zs, indexing="ij")
fx = np.round(GX + cu).astype(int); fy = np.round(-GZ).astype(int); ok1 = (fx >= 0) & (fx < W) & (fy >= 0) & (fy < H)
q = np.einsum("ij,j...->i...", Ai, np.stack([GD - b0[0], -GZ - b0[1]])); sx, sy = np.round(q[0]).astype(int), np.round(q[1]).astype(int)
ok2 = (sx >= 0) & (sx < m2.shape[1]) & (sy >= 0) & (sy < m2.shape[0])
V = np.zeros(GX.shape, bool); both = ok1 & ok2; V[both] = 정면[fy[both], fx[both]] & m2[sy[both], sx[both]]
vt, fc, _, _ = measure.marching_cubes(np.pad(V, 1).astype(np.float32), 0.5); vt = (vt - 1) * st_ + np.array([xs[0], ds[0], zs[0]])
w = trimesh.Trimesh(vt, fc); trimesh.smoothing.filter_taubin(w, iterations=6); w.visual.vertex_colors = np.tile([232, 234, 244, 255], (len(w.vertices), 1)).astype(np.uint8)
창 = trimesh.load(os.path.join(B, "창모듈2.ply"), process=False)
allm = trimesh.util.concatenate([창, w]); allm = trimesh.Trimesh(allm.vertices, allm.faces, vertex_colors=allm.visual.vertex_colors, process=False)
allm.export(os.path.join(B, "부리쐐기.ply"), encoding="ascii")
print({"쐐기 복셀": int(V.sum()), "깊이 범위": [round(float(vt[:, 1].min()), 1), round(float(vt[:, 1].max()), 1)], "조각": len(w.split(only_watertight=False))})
