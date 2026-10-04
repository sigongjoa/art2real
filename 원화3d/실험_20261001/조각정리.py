# -*- coding: utf-8 -*-
"""O12 조각 정리 (원형사 패널 조작 · 모토무라 「3D 처럼 보이나」 · 10-04 「전부다 해봐봐」).
덩어리판_c05_2 = 덩어리(앞 6000 면) + 얹은 정면 판. 얹은 판에서 「3D 냄새」 조각을 뺀다:
  ① 가는 조각: 삼각형 가장 짧은 높이 < 0.8 화소
  ② 거의 옆을 보는 면: 법선 y > −0.5 (앞을 덜 보는 면은 덩어리 겉에 비스듬히 꽂혀 어두운 쐐기로 보였다)
  ③ 덩어리 겉보다 2 이상 뒤(어차피 가려짐)
덩어리 면은 건드리지 않는다. 출력 out/오메가몬2/블렌더/덩어리판_c05_3.ply"""
import os, numpy as np, trimesh
B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
hull = trimesh.load(os.path.join(B, "덩어리_c05_2.ply"), process=False); nh = len(hull.faces)
allm = trimesh.load(os.path.join(B, "덩어리판_c05_2.ply"), process=False)
판 = allm.submesh([np.arange(nh, len(allm.faces))], append=True)
tri = 판.triangles; e = np.linalg.norm(tri[:, [1, 2, 0]] - tri, axis=2); 높이 = 2 * 판.area_faces / np.maximum(e.max(1), 1e-9)
가늘 = 높이 < 0.8; 옆 = 판.face_normals[:, 1] > -0.5
뒤 = np.zeros(len(판.faces), bool)
if len(판.faces):
    loc, idx_ray, idx_tri = hull.ray.intersects_location(판.triangles_center + np.array([0, -300, 0]), np.tile([0, 1, 0], (len(판.faces), 1)), multiple_hits=False)
    겉 = np.full(len(판.faces), np.inf); 겉[idx_ray] = loc[:, 1]; 뒤 = 판.triangles_center[:, 1] > 겉 + 2
keep = ~(가늘 | 뒤); 판.update_faces(keep); 판.remove_unreferenced_vertices()   # 2 판: 「옆을 봄」 기준은 안테나 · 부리 V 판(오메가몬다움의 핵심)까지 지워 뺌 — 가는 조각 · 가려진 면만
out = trimesh.util.concatenate([hull, 판])
trimesh.Trimesh(out.vertices, out.faces, vertex_colors=out.visual.vertex_colors, process=False).export(os.path.join(B, "덩어리판_c05_4.ply"), encoding="ascii")
print({"판 면": int(len(keep)), "가는": int(가늘.sum()), "옆을 봄": int(옆.sum()), "가려짐": int(뒤.sum()), "남김": int(keep.sum())})
