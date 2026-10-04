# -*- coding: utf-8 -*-
"""저폴리 머리 나머지 (10-04 사용자 「나머지 부분도 해봐봐」).
부리 · 눈 밖의 정면 칸(투구 · 이마 · 볼날개 · 뿔 · 번개 …)을 칸 하나 = 평평한 면 몇 개로:
  꼭짓점 = 칸 먹선 다각형(먹선 가운데까지 넓힘) · 깊이 = 그 자리 창 모듈 벽(정면 접힌 판 상대 높이 − 17 · 이미 쓰던 잰 면)을 찍기만
  → 새 모양을 짓지 않고 계단 벽을 먹선 따라 납작면으로 다시 깎는 것
  이음: 꼭짓점이 앞서 놓인 꼭짓점(부리 판 · 눈구멍 앞 윤곽 · 먼저 지은 칸) 4 화소 안이면 그 자리 · 깊이로
  색: 원화 칸 평균이 채도 높으면(노랑 뿔 · 파랑 번개) 그 색, 아니면 흰 갑주색
출력 out/오메가몬2/블렌더/저폴리머리.ply"""
import os, json, numpy as np, cv2, trimesh
from scipy.spatial import Delaunay
A = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
z = np.load(os.path.join(A, "1.npz")); L = z["라벨"]; yy, xx = np.nonzero(L > 0); y0, x0 = yy.min(), xx.min()
m1 = np.load(os.path.join(A, "판_1_Z.npz"))["m"]; H, W = m1.shape; py, px = np.mgrid[0:H, 0:W]; cu = (np.nonzero(m1)[1].min() + np.nonzero(m1)[1].max()) / 2
C1 = L[np.clip(y0 + 2 * py, 0, L.shape[0] - 1), np.clip(x0 + 2 * px, 0, L.shape[1] - 1)] * m1
art = cv2.imdecode(np.fromfile(os.path.join(A, "판_1_원화.png"), np.uint8), 1); hsv = cv2.cvtColor(art, cv2.COLOR_BGR2HSV); rgb = art[:, :, ::-1]
창 = trimesh.load(os.path.join(B, "창모듈2.ply"), process=False); wv = 창.vertices
벽 = lambda x, y: float(wv[np.argmin((wv[:, 0] + cu - x) ** 2 + (-wv[:, 2] - y) ** 2), 1])
base = trimesh.load(os.path.join(B, "저폴리눈_벽없음.ply"), process=False)
앞윤곽 = {k: np.array(v) for k, v in json.load(open(os.path.join(B, "저폴리눈_앞윤곽.json"), encoding="utf-8")).items()}
안쪽 = lambda poly, p: cv2.pointPolygonTest(poly.astype(np.float32), (float(p[0]), float(p[1])), False) >= 0
부리칸 = {25, 26, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42}
pool = np.c_[base.vertices[:, 0] + cu, -base.vertices[:, 2]]; pool_d = base.vertices[:, 1].copy()   # 이음 후보(2D, 깊이)
parts = [base]; 기록 = []
ids, cnt = np.unique(C1[C1 > 0], return_counts=True)
for c in [int(i) for i, n in sorted(zip(ids, cnt), key=lambda t: -t[1]) if n >= 20]:
    if c in 부리칸: continue
    mk = cv2.dilate((C1 == c).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=2)
    yy_, xx_ = np.nonzero(C1 == c); cen = (xx_.mean(), yy_.mean())
    if any(안쪽(P, cen) for P in 앞윤곽.values()): continue          # 눈구멍 안 칸(눈동자 · 검은 칠)은 눈 모듈 몫
    cs, _ = cv2.findContours(mk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); poly = cv2.approxPolyDP(max(cs, key=cv2.contourArea), 2.0, True).reshape(-1, 2).astype(float)
    if len(poly) < 3: continue
    d = np.array([벽(x, y) for x, y in poly])
    for i in range(len(poly)):
        dist = np.hypot(*(pool - poly[i]).T); j = int(np.argmin(dist))
        if dist[j] < 4.0: poly[i] = pool[j]; d[i] = pool_d[j]
    tri = Delaunay(poly); fc = [t for t in tri.simplices if 안쪽(poly, poly[t].mean(0))]
    if not fc: continue
    me = trimesh.Trimesh(np.c_[poly[:, 0] - cu, d, -poly[:, 1]], np.array(fc), process=False)
    bad = me.face_normals[:, 1] > 0; me.faces[bad] = me.faces[bad][:, ::-1]
    hs = hsv[yy_, xx_].mean(0); col = rgb[yy_, xx_].mean(0) if hs[1] > 70 else np.array([232, 234, 244])
    me.visual.vertex_colors = np.tile(list(col.astype(int)) + [255], (len(poly), 1)).astype(np.uint8); parts.append(me)
    pool = np.r_[pool, poly]; pool_d = np.r_[pool_d, d]; 기록.append((c, len(poly), round(float(d.min()), 1), round(float(d.max()), 1)))
allm = trimesh.util.concatenate(parts)
trimesh.Trimesh(allm.vertices, allm.faces, vertex_colors=allm.visual.vertex_colors, process=False).export(os.path.join(B, "저폴리머리.ply"), encoding="ascii")
print({"칸": len(기록), "꼭짓점 합": sum(r[1] for r in 기록)}, 기록[:12])
