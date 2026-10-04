# -*- coding: utf-8 -*-
"""덩어리(속) — 원형사 패널 10-04 권고 O5 ① · O3 · O5 ② (claudedocs/figure_panel_저폴리머리_20261004.md).
① 덩어리 = 정면 실루엣(판_1) ∩ 옆 실루엣(판_2 를 B 맞춤 T 로 (깊이, 행)에 옮김) — 두 장 헐 · 3/4 는 판정용으로 남김
   단면 두 판(O3 · 이토): c=0 상자 / c=0.5 모서리 깎음(행마다 정규화 |u|+|v| ≤ 2−c · 가정 · 사람이 고름)
   눈구멍: 정면 눈 앞 윤곽(저폴리눈_앞윤곽.json) 안은 겉에서 깊이 +4(눈 바닥)까지 파냄 — 창 깊이는 이미 잰 값
② 얹기: 저폴리머리6B 의 앞을 보는 면만(법선 y < −0.3 · 옆벽 버림), 덩어리 겉보다 뒤에 묻힌 꼭짓점만 겉 −0.5 로 끌어냄
출력 out/오메가몬2/블렌더/덩어리_c{0,05}.ply · 덩어리판_c{0,05}.ply"""
import os, sys, json, numpy as np, cv2, trimesh, contextlib, io
from scipy import ndimage
from skimage import measure
A = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
K = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "기준선.py")}
with contextlib.redirect_stdout(io.StringIO()): exec(open(K["__file__"], encoding="utf-8").read(), K)
T = K["T"]
m1 = np.load(os.path.join(A, "판_1_Z.npz"))["m"]; H, W = m1.shape; cu = (np.nonzero(m1)[1].min() + np.nonzero(m1)[1].max()) / 2
m2 = np.load(os.path.join(A, "판_2_Z.npz"))["m"]; ys, xs = np.nonzero(m2); dd, rr = T(xs.astype(float), ys.astype(float))
D0, D1 = -200, 200; ND = D1 - D0
S2 = np.zeros((H, ND), np.uint8); ok = (rr >= 0) & (rr < H) & (dd >= D0) & (dd < D1)
S2[np.round(rr[ok]).astype(int).clip(0, H - 1), np.round(dd[ok] - D0).astype(int).clip(0, ND - 1)] = 1
S2 = cv2.morphologyEx(S2, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
F1 = m1.astype(bool)
앞윤곽 = {k: np.array(v) for k, v in json.load(open(os.path.join(B, "저폴리눈_앞윤곽.json"), encoding="utf-8")).items()}
눈 = np.zeros((H, W), np.uint8)
for P in 앞윤곽.values(): cv2.fillPoly(눈, [P.round().astype(np.int32)], 1)
판 = trimesh.load(os.path.join(B, "저폴리머리6B.ply"), process=False)
st = 2   # 격자 2 화소
xg, dg, rg = np.arange(0, W, st), np.arange(D0, D1, st), np.arange(0, H, st)
for c in (0.0, 0.5):
    V = np.zeros((len(xg), len(dg), len(rg)), bool)
    for k, r in enumerate(rg):
        fx = F1[r, xg]; sd = S2[r, dg - D0].astype(bool)
        if not fx.any() or not sd.any(): continue
        X, Dd = np.meshgrid(fx, sd, indexing="ij"); v = X & Dd
        if c > 0:
            xi = np.nonzero(fx)[0]; di = np.nonzero(sd)[0]; x0, x1, d0, d1 = xi.min(), xi.max(), di.min(), di.max()
            u = np.abs((np.arange(len(xg))[:, None] - (x0 + x1) / 2) / max(1, (x1 - x0) / 2)); w = np.abs((np.arange(len(dg))[None, :] - (d0 + d1) / 2) / max(1, (d1 - d0) / 2))
            v &= (u + w) <= 2 - c
        V[:, :, k] = v
    # 눈구멍 파기: 정면 눈 윤곽 안 · 깊이 +4 앞쪽 전부
    ex = 눈[np.ix_(rg, xg)].T.astype(bool)   # (x, r)
    V[ex[:, None, :] & (dg[None, :, None] < 4)] = False
    vol = ndimage.gaussian_filter(V.astype(float), 1.0)
    verts, faces, _, _ = measure.marching_cubes(vol, 0.5)
    vx = verts[:, 0] * st - cu; vd = verts[:, 1] * st + D0; vr = verts[:, 2] * st
    hull = trimesh.Trimesh(np.c_[vx, vd, -vr], faces, process=False); hull.fix_normals()
    hull = hull.simplify_quadric_decimation(face_count=6000) if hasattr(hull, "simplify_quadric_decimation") else hull
    hull.visual.vertex_colors = np.tile([226, 228, 240, 255], (len(hull.vertices), 1)).astype(np.uint8)
    tag = "0" if c == 0 else "05"
    hull.export(os.path.join(B, f"덩어리_c{tag}.ply"), encoding="ascii")
    # ② 얹기
    앞면 = 판.face_normals[:, 1] < -0.3; sub = 판.submesh([np.nonzero(앞면)[0]], append=True)
    겉 = np.full((H, W), np.inf)   # 열마다 덩어리 가장 앞 깊이
    for k, r in enumerate(rg):
        for i, x in enumerate(xg):
            col = np.nonzero(V[i, :, k])[0]
            if len(col): 겉[r:r + st, x:x + st] = dg[col[0]]
    v = sub.vertices.copy(); px_ = np.clip(np.round(v[:, 0] + cu).astype(int), 0, W - 1); pr_ = np.clip(np.round(-v[:, 2]).astype(int), 0, H - 1)
    s = 겉[pr_, px_]; 묻힘 = np.isfinite(s) & (v[:, 1] > s + 0.5) & ~눈[pr_, px_].astype(bool)
    v[묻힘, 1] = s[묻힘] - 0.5; sub.vertices = v
    allm = trimesh.util.concatenate([hull, sub])
    trimesh.Trimesh(allm.vertices, allm.faces, vertex_colors=allm.visual.vertex_colors, process=False).export(os.path.join(B, f"덩어리판_c{tag}.ply"), encoding="ascii")
    print(c, {"덩어리 면": len(hull.faces), "얹은 판 면": len(sub.faces), "끌어낸 꼭짓점": int(묻힘.sum())})
