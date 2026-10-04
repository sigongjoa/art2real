# -*- coding: utf-8 -*-
"""겹 — 소체(덩어리)는 판(갑주) 뒤에 (10-04 「ㄱㄱ」 · 위키 규칙 「갑주는 소체 위에 짓는다 · 갑주 ∩ 소체 = 0」).
3 바퀴 덩어리판은 덩어리 앞면이 행마다 옆 실루엣 가장 앞(= 부리 끝 깊이)까지 와서 정면 판(V 부리 · 투구 각)을 덮어 돌덩이가 됐다.
→ 덩어리 = 정면 ∩ 옆(B2 와 같음 · 모서리 깎음 c0.5 · 범위 고르게 · 높이 흐림) 에서 **판 뒤만** 남긴다:
   정면 판(6B 의 앞을 보는 면)을 (x, 행) z-버퍼로 그려, 판이 있는 열은 판 깊이 + 두께 t 보다 뒤만 덩어리 · 판이 없는 열은 그대로
   판은 6B 원래 깊이 그대로(끌어내지 않음) + 안테나(노랑) 면 · 옆벽은 버림
t = 3 화소(판 두께 · 가정). 출력 out/오메가몬2/블렌더/겹_소체.ply · 겹.ply"""
import os, json, numpy as np, cv2, trimesh, contextlib, io
from scipy import ndimage
from skimage import measure
A = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
K = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "기준선.py")}
with contextlib.redirect_stdout(io.StringIO()): exec(open(K["__file__"], encoding="utf-8").read(), K)
m1 = np.load(os.path.join(A, "판_1_Z.npz"))["m"]; H, W = m1.shape; cu = (np.nonzero(m1)[1].min() + np.nonzero(m1)[1].max()) / 2
m2 = np.load(os.path.join(A, "판_2_Z.npz"))["m"]; D0, D1 = -200, 200; ND = D1 - D0
k_, t_ = K["k"], K["t"]; ct, st_ = np.cos(t_), np.sin(t_)
M = np.array([[k_ * ct, -k_ * st_, -k_ * K["ex"] * ct + k_ * K["ey"] * st_ - D0], [k_ * st_, k_ * ct, K["c"] - k_ * K["xm"] * st_]], np.float32)
S2 = (cv2.warpAffine(m2.astype(np.uint8) * 255, M, (ND, H), flags=cv2.INTER_LINEAR) > 127)
F1 = m1.astype(bool)
판 = trimesh.load(os.path.join(B, "저폴리머리6B.ply"), process=False)
vc = 판.visual.vertex_colors[판.faces][:, 0, :3].astype(int); 노랑 = (vc[:, 0] > 150) & (vc[:, 2] < 120)
앞윤곽 = {k: np.array(v, np.float32) for k, v in json.load(open(os.path.join(B, "저폴리눈_앞윤곽.json"), encoding="utf-8")).items()}
눈판 = np.zeros((H, W), np.uint8)
for P_ in 앞윤곽.values(): cv2.fillPoly(눈판, [np.round(P_).astype(np.int32)], 1)
_c = 판.triangles_center; _px = np.clip(np.round(_c[:, 0] + cu).astype(int), 0, W - 1); _pr = np.clip(np.round(-_c[:, 2]).astype(int), 0, H - 1)
눈면 = (눈판[_pr, _px] > 0) & (_c[:, 1] > -30) if os.environ.get("EYE") == "1" else np.zeros(len(판.faces), bool)   # 디테일 모양 1: 눈구멍 옆벽 · 바닥 · 눈알은 방향 상관없이 남김(앞면 거르기로 옆벽이 빠져 눈구멍이 묻혔다)
앞면 = (판.face_normals[:, 1] < -0.3) | 노랑 | 눈면; sub = 판.submesh([np.nonzero(앞면)[0]], append=True)
# 판 z-버퍼 (x, 행) → 가장 앞 깊이
zb = np.full((H, W), np.inf); P2 = np.c_[sub.vertices[:, 0] + cu, -sub.vertices[:, 2]]; dz = sub.vertices[:, 1]
for f in np.argsort(-dz[sub.faces].mean(1)):   # 먼 면 먼저 → 가까운 면이 덮음
    if 노랑[np.nonzero(앞면)[0][f]]: continue   # 안테나는 가는 막대라 덩어리를 깎지 않음
    m_ = np.zeros((H, W), np.uint8); cv2.fillPoly(m_, [np.round(P2[sub.faces[f]]).astype(np.int32)], 1); zb[m_ > 0] = dz[sub.faces[f]].mean()
# 자가개선 1 바퀴: 판이 안 덮은 열(70 %)에서 덩어리가 옆 실루엣 맨 앞(부리 끝)까지 나와 입 높이에 상자가 튐
#   → 정면 마스크 안의 빈 열은 가장 가까운 판 열의 깊이를 물려받음(거리변환 최근접) — 덩어리가 이웃 판보다 앞에 못 나옴
_빈 = ~np.isfinite(zb); _, (iy, ix) = ndimage.distance_transform_edt(_빈, return_indices=True)
zb_막 = np.where(F1, zb[iy, ix], np.inf); zb_판 = zb.copy(); zb = zb_막
t = 3.0; st = 2; xg, dg, rg = np.arange(0, W, st), np.arange(D0, D1, st), np.arange(0, H, st)
범위 = np.full((len(rg), 4), np.nan)
for k, r in enumerate(rg):
    fx = F1[r, xg]; sd = S2[r, dg - D0]
    if fx.any() and sd.any(): xi = np.nonzero(fx)[0]; di = np.nonzero(sd)[0]; 범위[k] = (xi.min(), xi.max(), di.min(), di.max())
ok_ = ~np.isnan(범위[:, 0]); 범위[ok_] = ndimage.gaussian_filter1d(범위[ok_], 3, axis=0, mode="nearest")
V = np.zeros((len(xg), len(dg), len(rg)), bool); c = 0.5
for k, r in enumerate(rg):
    fx = F1[r, xg]; sd = S2[r, dg - D0]
    if not fx.any() or not sd.any(): continue
    v = fx[:, None] & sd[None, :]; x0, x1, d0, d1 = 범위[k]
    u = np.abs((np.arange(len(xg))[:, None] - (x0 + x1) / 2) / max(1, (x1 - x0) / 2)); w = np.abs((np.arange(len(dg))[None, :] - (d0 + d1) / 2) / max(1, (d1 - d0) / 2))
    v &= (u + w) <= 2 - c
    v &= dg[None, :] >= (zb[r, xg] + t)[:, None]   # 판 뒤만(판 없는 열은 inf → 아래 줄에서 풀어 줌)
    V[:, :, k] = v
if os.environ.get("EYE") == "1":   # 소체를 눈 윤곽 안 · 바닥(+4) 앞쪽까지 파냄 — 창 깊이 17 은 잰 값
    ex_ = 눈판[np.ix_(rg, xg)].T.astype(bool); V[ex_[:, None, :] & (dg[None, :, None] < 4)] = False
vol = ndimage.gaussian_filter(V.astype(float), (1.0, 1.0, 2.0))
verts, faces, _, _ = measure.marching_cubes(vol, 0.5)
hull = trimesh.Trimesh(np.c_[verts[:, 0] * st - cu, verts[:, 1] * st + D0, -verts[:, 2] * st], faces, process=False); hull.fix_normals()
hull = hull.simplify_quadric_decimation(face_count=int(os.environ.get("NF", "6000")))   # 자가개선 3 바퀴: NF 로 면 수(저폴리 모양 언어)
소체색 = [150, 154, 168, 255] if os.environ.get("HULLCOL", "gray") == "gray" else [226, 228, 240, 255]   # 자가개선 2 바퀴: 원화 갑주는 한 흰색
hull.visual.vertex_colors = np.tile(소체색, (len(hull.vertices), 1)).astype(np.uint8)   # 소체는 회색(갑주와 구분)
hull.export(os.path.join(B, "겹" + os.environ.get("TAG", "2") + "_소체.ply"), encoding="ascii")
allm = trimesh.util.concatenate([hull, sub])
trimesh.Trimesh(allm.vertices, allm.faces, vertex_colors=allm.visual.vertex_colors, process=False).export(os.path.join(B, "겹" + os.environ.get("TAG", "2") + ".ply"), encoding="ascii")
# 갑주 ∩ 소체 검사: 판 꼭짓점이 소체 안에 든 비율
inside = hull.contains(sub.vertices) if hull.is_watertight else None
print({"판 면": len(sub.faces), "소체 면": len(hull.faces), "판 덮은 열 비율": round(float(np.isfinite(zb_판).mean()), 3), "판 꼭짓점 중 소체 안": None if inside is None else round(float(inside.mean()), 3)})
