# -*- coding: utf-8 -*-
"""부조 옮기기 F4 (10-05 · F3 에서 부위 강체 변형으로는 정면 껍질 부조 차(중앙 12.6)가 안 줄어 — 차이는 부위 안쪽 표면)
python 부조옮기기.py <입력 판> <출력 판> [w=0.5]
  꼭짓점 y(깊이)만 움직임 · x · z 고정
  min ‖L y' − L y‖² + w Σ앞면 (y' − (껍질 깊이 + 어긋남))²   (L = 균일 라플라시안 · 앞면 = 법선 y < −0.3 · 껍질이 있는 곳)
  → 이웃 관계(모양)는 지키고 앞 표면 높낮이만 원화 한 장의 부조 쪽으로"""
import sys, numpy as np, trimesh, scipy.sparse as sp
from scipy.sparse.linalg import spsolve
B = "G:/art2real/원화3d/out/오메가몬2/블렌더/"; A = "G:/art2real/원화3d/out/오메가몬2/지표/각도데이터/"
src, dst = sys.argv[1], sys.argv[2]; W = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
m = trimesh.load(B + src + ".ply", process=False); m = trimesh.Trimesh(m.vertices, m.faces, process=False); V = m.vertices.copy(); n = len(V)
sh = trimesh.load(A + "판_1.ply", process=False); sv = sh.vertices * 3.009; sv[:, 0] -= 121.0; sh = trimesh.Trimesh(sv, sh.faces, process=False)
o = np.c_[V[:, 0], np.full(n, -800.0), V[:, 2]]
loc, ri, _ = sh.ray.intersects_location(o, np.tile([0, 1.0, 0], (n, 1)), multiple_hits=False)
D = np.full(n, np.nan); D[ri] = loc[:, 1]
fr = (m.vertex_normals[:, 1] < -0.3) & ~np.isnan(D)
# 앞면 중에서도 「가장 앞 겉」만(뒤쪽 면이 같은 x · z 에 걸리면 안 됨): 같은 x · z 로 쏜 광선의 첫 교차가 이 꼭짓점 근처
hit, hri, _ = m.ray.intersects_location(o, np.tile([0, 1.0, 0], (n, 1)), multiple_hits=False)
first = np.full(n, np.nan); first[hri] = hit[:, 1]; fr &= np.abs(V[:, 1] - first) < 2.0
OFF = np.median(V[fr, 1] - D[fr]); T = D + OFF
print("앞 겉 꼭짓점", fr.sum(), "어긋남", round(OFF, 1), "처음 차 중앙", round(np.median(np.abs(V[fr, 1] - T[fr])), 1))
e = m.edges_unique; r_ = np.r_[e[:, 0], e[:, 1]]; c_ = np.r_[e[:, 1], e[:, 0]]
Adj = sp.coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)).tocsr(); deg = np.asarray(Adj.sum(1)).ravel()
L = sp.diags(np.ones(n)) - sp.diags(1 / np.maximum(deg, 1)) @ Adj
Wd = sp.diags(fr.astype(float) * W)
Wa = sp.diags((~fr).astype(float) * 1.0)   # F4b: 앞 겉이 아닌 꼭짓점은 원래 깊이에 묶음 — 안 묶으니 머리 전체가 판으로 납작해졌다
M = (L.T @ L + Wd + Wa).tocsc(); rhs = L.T @ (L @ V[:, 1]) + Wd @ np.nan_to_num(T) + Wa @ V[:, 1]
y = spsolve(M, rhs)
print("끝 차 중앙", round(np.median(np.abs(y[fr] - T[fr])), 1), "움직임 최대", round(np.abs(y - V[:, 1]).max(), 1))
V[:, 1] = y; out = trimesh.Trimesh(V, m.faces, process=False)
out.visual.vertex_colors = np.tile([228, 232, 240, 255], (n, 1)).astype(np.uint8); out.export(B + dst + ".ply")
