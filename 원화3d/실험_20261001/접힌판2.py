# -*- coding: utf-8 -*-
"""접힌 판 2 — 빈 곳 없애기 (10-02 사용자 「빈 부분이 왜 생긴 거지?」 → 먹선 화소를 면에서 빼고 · 윤곽을 단순화해 머리의 20.6 % 가 빔).
바뀐 점: ① 면 방향 지도를 화소 단위로 바로 만든다(면 메시 · 윤곽 단순화 없음 · 칸 경계 그대로)
         ② 먹선 화소는 가장 가까운 면에 넣는다(먹선 = 두 면이 만나는 모서리)  ③ 껍질 뒤를 둘레 5×5 의 가장 깊은 뒤까지 내려 단에 옆벽
면 나누기 · 면 방향은 면스무딩.py 와 같다(부품 안 먹선 + 원화 그림자 경계 · 깊이 평면 → 밝은 면 n·L ≥ 0.55 · 그림자 면 ≤ 0.25).
적분 · 판정은 접힌판.py 와 같다. 출력 out/오메가몬2/지표/부조/접힌판2.ply · 접힌판2.json · 접힌판2_정면.png"""
import os, json, numpy as np, cv2, trimesh, scipy.sparse as sp
from scipy.sparse.linalg import lsqr
from scipy import ndimage
from skimage import measure
import 면정보자 as M
O = os.path.join(M.K, "부조")
z = np.load(os.path.join(O, "부조_Z.npz")); Z = z["Z"]; Lc = z["Lf"]; x0, y0, x1, y1 = [int(a) for a in z["자르기"]]; k = float(z["k"]); Wf = M.Lf.shape[1]
그래프 = json.load(open(os.path.join(M.K, "연결그래프", "그래프.json"), encoding="utf-8"))
sv = cv2.imdecode(np.fromfile(os.path.join(M.G_, "그림자찾기.png"), np.uint8), 1); SH = (sv[:, :, 2] > 120) & (sv[:, :, 1] < 100)
Lum = cv2.cvtColor(cv2.imdecode(np.fromfile(M.ART, np.uint8), 1)[y0:y1, x0:x1], cv2.COLOR_BGR2LAB)[:, :, 0]
INK = cv2.dilate((cv2.morphologyEx(Lum, cv2.MORPH_BLACKHAT, np.ones((7, 7), np.uint8)) > 28).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
L_b = M.L_b
def bx(px): return (px + x0 - Wf / 2) * k
def bz(py): return -py * k
def 돌림(n, 밝음):
    n = n / np.linalg.norm(n); lo, hi = (0.55, 1.0) if 밝음 else (-1.0, 0.25); d = n @ L_b
    if lo <= d <= hi: return n
    up = d < lo; target = lo if up else hi; best = n
    for a in np.linspace(0, 3, 301):
        q = n + (a if up else -a) * L_b; q /= np.linalg.norm(q)
        if q[1] > -0.15: break
        best = q
        if (q @ L_b >= target) if up else (q @ L_b <= target): break
    return best
H, W = Lc.shape; FACE = np.full((H, W), -1); 법선 = []; 부품 = []
for p in 그래프["부품"]:
    m = cv2.morphologyEx(np.isin(Lc, p["칸"]).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) > 0
    if m.sum() < 20: continue
    inner = m & INK & (cv2.erode(m.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0)
    n_lab, lab = cv2.connectedComponents((m & ~inner).astype(np.uint8)); 면들 = []
    for i in range(1, n_lab):
        r = lab == i
        for 밝음 in (True, False):
            q = r & (~SH if 밝음 else SH)
            if q.sum() >= 15: 면들.append((q, 밝음))
    if not 면들: 면들 = [(m, not SH[m].mean() > 0.5)]
    for q, 밝음 in 면들:
        ys, xs = np.nonzero(q); zz = Z[ys, xs]; ok = ~np.isnan(zz)
        if ok.sum() < 5: continue
        a_, b_, c_ = np.linalg.lstsq(np.c_[bx(xs[ok]), bz(ys[ok]), np.ones(ok.sum())], zz[ok], rcond=None)[0]
        n0 = np.array([a_, -1.0, b_]); FACE[q & (FACE < 0)] = len(법선); 법선.append(돌림(n0, 밝음)); 부품.append(p["이름"])
    # 이 부품 안에서 아직 빈 화소(먹선 · 작은 조각) → 가장 가까운 면
    hole = m & (FACE < 0)
    if hole.any():
        own = np.isin(FACE, [i for i, nm in enumerate(부품) if nm == p["이름"]])
        if own.any():
            _, (iy, ix) = ndimage.distance_transform_edt(~own, return_indices=True); FACE[hole] = FACE[iy[hole], ix[hole]]
# 머리 안 남은 빈 화소(칸 밖 먹선 벽) → 가장 가까운 면
head = ndimage.binary_closing(Lc > 0, np.ones((7, 7))) | (Lc > 0)
if (head & (FACE < 0)).any():
    _, (iy, ix) = ndimage.distance_transform_edt(FACE < 0, return_indices=True); hole = head & (FACE < 0); FACE[hole] = FACE[iy[hole], ix[hole]]
print("면", len(법선), "· 머리 화소 덮음", f"{(head & (FACE >= 0)).sum() / head.sum():.1%}")
# 반 해상도로 내려 적분(접힌판.py 와 같은 식)
s_ = M.s_; F = FACE[::s_, ::s_]; hit = (F >= 0) & head[::s_, ::s_]; Hh, Ww = F.shape
N_ = np.array(법선); nb = np.zeros((Hh, Ww, 3)); nb[hit] = N_[F[hit]]
nx, ny, nz = nb[..., 0], nb[..., 2], -nb[..., 1]; nz = np.where(np.abs(nz) < 0.2, 0.2, nz); px = k * s_
gx = -nx / nz * px; gy = ny / nz * px; pid = np.full((Hh, Ww), -1); un = sorted(set(부품)); pid[hit] = [un.index(부품[f]) for f in F[hit]]
Zc = Z[::s_, ::s_]; idx = -np.ones((Hh, Ww), int); idx[hit] = np.arange(hit.sum()); n = int(hit.sum()); R, C, Vv, B = [], [], [], []
def eq(a, b, t, w): r = len(B); R.extend([r, r]); C.extend([idx[a], idx[b]]); Vv.extend([w, -w]); B.append(w * t)
for dy, dx in ((0, 1), (1, 0)):
    A = hit[: Hh - dy, : Ww - dx] & hit[dy:, dx:]
    for (y, x) in zip(*np.nonzero(A)):
        p_, q_ = (y, x), (y + dy, x + dx)
        if pid[p_] == pid[q_]: eq(q_, p_, (gx[p_] + gx[q_]) / 2 if dx else (gy[p_] + gy[q_]) / 2, 1.0)
        else: eq(q_, p_, float(np.clip(np.nan_to_num(Zc[q_] - Zc[p_]), -4, 4)), 0.3)
for (y, x) in zip(*np.nonzero(hit)): r = len(B); R.append(r); C.append(idx[y, x]); Vv.append(0.02); B.append(0.02 * float(np.nan_to_num(Zc[y, x])))
Am = sp.csr_matrix((Vv, (R, C)), shape=(len(B), n)); sol = lsqr(Am, np.array(B), atol=1e-8, btol=1e-8, iter_lim=20000)[0]
Zs = np.full((Hh, Ww), np.nan); Zs[hit] = sol
back = ndimage.minimum_filter(np.where(hit, Zs - 6, np.inf), size=5); back = np.where(hit, np.minimum(back, Zs - 6), np.nan)   # 단에 옆벽
zz = np.arange(np.nanmin(back) - 1, np.nanmax(Zs) + 1, 0.5); V = np.zeros((Ww, Hh, len(zz)), bool)
for x in range(Ww):
    c = Zs[:, x]; b = back[:, x]; ok = ~np.isnan(c); V[x, ok, :] = (zz[None, :] <= c[ok, None]) & (zz[None, :] >= b[ok, None])
v, f, _, _ = measure.marching_cubes(np.pad(V, 1).astype(np.float32), 0.5); v -= 1
X = (v[:, 0] * s_ + x0 - Wf / 2) * k; Zu = -(v[:, 1] * s_ + y0) * k; Dz = zz[0] + v[:, 2] * 0.5
mesh = trimesh.Trimesh(np.c_[X, -Dz, Zu], f); trimesh.smoothing.filter_taubin(mesh, iterations=5)
art = cv2.imdecode(np.fromfile(M.ART, np.uint8), 1)[y0:y1, x0:x1]; ci = np.clip((v[:, 0] * s_).astype(int), 0, art.shape[1] - 1); cj = np.clip((v[:, 1] * s_).astype(int), 0, art.shape[0] - 1)
col = (255 * (art[cj, ci][:, ::-1] / 255.0) ** 0.55).astype(np.uint8); mesh.visual.vertex_colors = np.c_[col, np.full(len(col), 255)].astype(np.uint8)
mesh.export(os.path.join(O, "접힌판2.ply"))
r_front, vis = M.재기([mesh])
결과 = {**r_front, "면": len(법선), "머리덮음": round(float((head & (FACE >= 0)).sum() / head.sum()), 3), "앞면깊이범위": round(float(np.nanmax(Zs) - np.nanmin(Zs)), 1)}
json.dump(결과, open(os.path.join(O, "접힌판2.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
hm = np.full((Hh, Ww, 3), 255, np.uint8); a = (Zs - np.nanpercentile(Zs, 2)) / (np.nanpercentile(Zs, 98) - np.nanpercentile(Zs, 2)); hm[hit] = cv2.applyColorMap((np.clip(a[hit], 0, 1) * 255).astype(np.uint8).reshape(-1, 1), cv2.COLORMAP_JET).reshape(-1, 3)
Hm = min(vis.shape[0], hm.shape[0]); Wm = min(vis.shape[1], hm.shape[1])
cv2.imencode(".png", cv2.resize(np.hstack([M.원화그림()[:Hm, :Wm], vis[:Hm, :Wm], hm[:Hm, :Wm]]), None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST))[1].tofile(os.path.join(O, "접힌판2_정면.png"))
print(결과)
