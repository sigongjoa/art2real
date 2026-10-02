# -*- coding: utf-8 -*-
"""면 방향 지도 → 높이 적분 → 접힌 판 (10-02 사용자 「하고 이미지 보여줘」).
입력: 면스무딩_전부(원화 그림자로 기울인 면 48 개)를 정면 반 해상도로 찍은 면 방향 · 부품 번호 / 부조_Z(칸 깊이 · 색 규칙)
풀기(희소 최소제곱):
  같은 부품 안 이웃(면 안 · 꺾임 선) : 높이 차 = 면 방향 기울기(두 화소 평균) · 무게 1   — 꺾임 선에서 이어짐
  다른 부품 이웃(가림 선)             : 높이 차 = 칸 깊이 차를 ±4 로 자른 값 · 무게 0.3  — 단(띄움)을 허용
  모든 화소                           : 부조 깊이 쪽으로 무게 0.02 (전체 높이만 잡음)
앞면 = 푼 높이 · 뒤 = 앞면에서 6 단위 껍질 + 투구 돔(소체 자리). 판정: 정면 그림자 · 먹선(면정보자) · 옆 실루엣 IoU(투구돔.py 방식) · 가시(앞면 깊이 범위)
출력 out/오메가몬2/지표/부조/접힌판.ply · 접힌판.json · 접힌판_시트.png(렌더는 접힌판_렌더)"""
import os, glob, json, numpy as np, cv2, trimesh, scipy.sparse as sp
from scipy.sparse.linalg import lsqr
from skimage import measure
import 면정보자 as M
O = os.path.join(M.K, "부조")
ms = [trimesh.load(f, process=False) for f in sorted(glob.glob(os.path.join(O, "면스무딩_전부", "*.ply")))]
names = [os.path.basename(f).rsplit("_", 1)[0] for f in sorted(glob.glob(os.path.join(O, "면스무딩_전부", "*.ply")))]   # 면 → 부품 이름
dep, nrm, face = M.찍기(ms); H, W = dep.shape; hit = ~np.isnan(dep) & M.head
pid = np.full((H, W), -1); uniq = sorted(set(names));
for i, n in enumerate(names): pid[face == i] = uniq.index(n)
# 화면 법선: x 오른 · y 위 · z 보는 쪽 ← 블렌더(x, −y 앞, z 위)
nx, ny, nz = nrm[..., 0], nrm[..., 2], -nrm[..., 1]; nz = np.where(np.abs(nz) < 0.2, 0.2, nz)
px = M.k * M.s_                                                               # 화소당 머리 단위
gx = -nx / nz * px; gy = ny / nz * px                                          # 오른쪽 한 칸 · 아래쪽 한 칸 갈 때 높이(보는 쪽 +) 변화
z = np.load(os.path.join(O, "부조_Z.npz")); Zc = z["Z"][::M.s_, ::M.s_][:H, :W]
idx = -np.ones((H, W), int); idx[hit] = np.arange(hit.sum()); n = hit.sum(); rows, cols, vals, rhs, wts = [], [], [], [], []
def eq(a, b, target, w):
    r = len(rhs); rows.extend([r, r]); cols.extend([idx[a], idx[b]]); vals.extend([w, -w]); rhs.append(w * target)
for dy, dx in ((0, 1), (1, 0)):
    A = hit[: H - dy, : W - dx] & hit[dy:, dx:]
    for (y, x) in zip(*np.nonzero(A)):
        p, q = (y, x), (y + dy, x + dx)
        if pid[p] == pid[q]:
            g = (gx[p] + gx[q]) / 2 if dx else (gy[p] + gy[q]) / 2; eq(q, p, g, 1.0)            # z_q − z_p = 기울기
        else:
            t = np.nan_to_num(Zc[q] - Zc[p]); eq(q, p, float(np.clip(t, -4, 4)), 0.3)
for (y, x) in zip(*np.nonzero(hit)):
    r = len(rhs); rows.append(r); cols.append(idx[y, x]); vals.append(0.02); rhs.append(0.02 * float(np.nan_to_num(Zc[y, x])))
Amat = sp.csr_matrix((vals, (rows, cols)), shape=(len(rhs), n)); sol = lsqr(Amat, np.array(rhs), atol=1e-8, btol=1e-8, iter_lim=20000)[0]
Zs = np.full((H, W), np.nan); Zs[hit] = sol
# 앞면 껍질 6 단위 → 복셀 → 메시(부조와 같은 블렌더 틀)
zz = np.arange(np.nanmin(Zs) - 7, np.nanmax(Zs) + 1, 0.5); V = np.zeros((W, H, len(zz)), bool)
for x in range(W):
    c = Zs[:, x]; ok = ~np.isnan(c); V[x, ok, :] = (zz[None, :] <= c[ok, None]) & (zz[None, :] >= c[ok, None] - 6)
v, f, _, _ = measure.marching_cubes(np.pad(V, 1).astype(np.float32), 0.5); v -= 1
X = (v[:, 0] * M.s_ + M.x0 - M.Lf.shape[1] / 2) * M.k; Zu = -(v[:, 1] * M.s_ + M.y0) * M.k; Dz = zz[0] + v[:, 2] * 0.5
mesh = trimesh.Trimesh(np.c_[X, -Dz, Zu], f); trimesh.smoothing.filter_taubin(mesh, iterations=5)
art = cv2.imdecode(np.fromfile(M.ART, np.uint8), 1)[M.y0:M.y1, M.x0:M.x1]
ci = np.clip((v[:, 0] * M.s_).astype(int), 0, art.shape[1] - 1); cj = np.clip((v[:, 1] * M.s_).astype(int), 0, art.shape[0] - 1)
col = (255 * (art[cj, ci][:, ::-1] / 255.0) ** 0.55).astype(np.uint8); mesh.visual.vertex_colors = np.c_[col, np.full(len(col), 255)].astype(np.uint8)
mesh.export(os.path.join(O, "접힌판.ply"))
# 판정
r_front, vis = M.재기([mesh])
import importlib.util
spec = importlib.util.spec_from_file_location("투구돔", os.path.join(os.path.dirname(os.path.abspath(__file__)), "투구돔.py"))
dome = trimesh.load(os.path.join(O, "투구돔.ply"), process=False)
def 실루엣(meshes, nn=400):
    pts = np.vstack([m.vertices for m in meshes]); lo = np.array([pts[:, 1].min(), pts[:, 2].min()]); sc = (nn - 1) / max(np.ptp(pts[:, 1]), np.ptp(pts[:, 2])); img = np.zeros((nn, nn), np.uint8)
    for m in meshes:
        T = ((m.vertices[:, [1, 2]] - lo) * sc).astype(np.int32)[m.faces]; T[:, :, 1] = nn - 1 - T[:, :, 1]
        for t_ in T: cv2.fillConvexPoly(img, t_, 1)
    za = dome.vertices[:, 2].max(); r0 = int(nn - 1 - (za - pts[:, 2].min()) * sc); img[:max(0, r0)] = 0; return img
def 틀(m):
    ys_, xs_ = np.nonzero(m); m = m[ys_.min():ys_.max() + 1, xs_.min():xs_.max() + 1]; h = 200; w = max(1, int(m.shape[1] * h / m.shape[0])); m = cv2.resize(m, (w, h), interpolation=cv2.INTER_NEAREST); c_ = np.zeros((h, 260), np.uint8); c_[:, :min(w, 260)] = m[:, :260]; return c_ > 0
Ls = np.load(os.path.join(M.K, "선파츠_옆.npz"))["라벨"]; side = 틀(cv2.morphologyEx((Ls > 0).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)))
A_ = 틀(실루엣([mesh, dome])); iou_side = float((A_ & side).sum() / (A_ | side).sum())
결과 = {**r_front, "옆실루엣IoU(돔 포함)": round(iou_side, 3), "앞면깊이범위": round(float(np.nanmax(Zs) - np.nanmin(Zs)), 1), "풀이잔차": round(float(np.linalg.norm(Amat @ sol - np.array(rhs)) / np.sqrt(len(rhs))), 3)}
json.dump(결과, open(os.path.join(O, "접힌판.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
hm = np.full((H, W, 3), 255, np.uint8); a = (Zs - np.nanpercentile(Zs, 2)) / (np.nanpercentile(Zs, 98) - np.nanpercentile(Zs, 2)); hm[hit] = cv2.applyColorMap((np.clip(a[hit], 0, 1) * 255).astype(np.uint8).reshape(-1, 1), cv2.COLORMAP_JET).reshape(-1, 3)
cv2.imencode(".png", cv2.resize(np.hstack([M.원화그림(), vis, hm]), None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST))[1].tofile(os.path.join(O, "접힌판_정면.png"))
print(결과)
