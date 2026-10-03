# -*- coding: utf-8 -*-
"""깎기(스컬핑) 1 판 (10-03 사용자 「여전히 개판인 거 보이지 · 더 깎아 봐 · 스컬핑을 하라고」).
덩어리를 손으로 상상해 깎지 않는다 — 깎는 칼은 전부 원화에서:
  ① 덩어리 = 블록아웃 B 도형(투구 타원체 · 부리 쐐기 · 볼날개 · 뿔 · 안테나)의 합 — 위에서 본 둥긂 · 부피
  ② 윤곽 칼 = 정면 · 옆 두 장 실루엣(도면헐 B) — 원화 윤곽 밖은 깎음
  ③ 앞면 칼 = 정면 접힌 판(판_1_Z · 셀 그림자로 세운 면들 · 「3d 는 잘 만드네」의 그 껍질) — 정면에서 보이는 면의 각진 판 모양을 앞면에 새김
       껍질 깊이 → 머리 깊이: 눈 = 0 · 배율 a 는 껍질의 「눈 → 턱 끝」 깊이 차가 블록아웃 B 의 같은 차와 같게(지어낸 값 없음)
       앞면 = max(덩어리 앞면, 껍질 앞면) — 껍질보다 앞에 있는 덩어리만 깎는다(더하지 않음)
색 = 정면 원화를 앞에서 비춰 칠함(정면에서 안 보이는 면은 회색). 출력 out/오메가몬2/블렌더/깎기1.ply · 깎기1_비교.png(렌더는 bp3c)"""
import os, json, numpy as np, trimesh, cv2
from scipy.spatial import ConvexHull
from skimage import measure
os.environ["PAIR"] = "B"
G = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "도형블록아웃.py")}
exec(open(G["__file__"], encoding="utf-8").read(), G)
O, B, f, cen, rad, cu = G["O"], G["B"], G["f"], G["cen"], G["rad"], G["cu"]
st = 1.5; xs = np.arange(-130, 130, st); ds = np.arange(-130, 170, st); zs = np.arange(-310, 0, st)
GX, GD, GZ = np.meshgrid(xs, ds, zs, indexing="ij"); P = np.c_[GX.ravel(), GD.ravel(), GZ.ravel()]
# ① 덩어리
def 안_볼록(m, P, 여유=0.0):
    h = ConvexHull(m.vertices); A, b = h.equations[:, :3], h.equations[:, 3]; return np.all(P @ A.T + b <= 여유, axis=1)
V = (((P - cen) / (rad * 1.06)) ** 2).sum(1) <= 1.0
for m in [G["beak"], G["horn"]] + G["wings"] + G["ants"]: V |= 안_볼록(m, P, 2.0)
# ② 윤곽 칼(도면헐 B 와 같은 투영)
m1 = np.load(os.path.join(O, "판_1_Z.npz"))["m"]; m2 = np.load(os.path.join(O, "판_2_Z.npz"))["m"]
k, t, c, xm = G["k"], G["t"], G["c"], G["xm"]; ex, ey = G["ex"], G["ey"]; ct, s_ = np.cos(t), np.sin(t)
A = np.array([[k * ct, -k * s_], [k * s_, k * ct]]); Ai = np.linalg.inv(A); b0 = np.array([-k * (ex * ct - ey * s_), -k * xm * s_ + c])
fx = np.round(P[:, 0] + cu).astype(int); fy = np.round(-P[:, 2]).astype(int); ok = (fx >= 0) & (fx < m1.shape[1]) & (fy >= 0) & (fy < m1.shape[0])
f_in = np.zeros(len(P), bool); f_in[ok] = m1[fy[ok], fx[ok]]
sxy = (Ai @ np.stack([P[:, 1] - b0[0], -P[:, 2] - b0[1]])).T; sx, sy = np.round(sxy[:, 0]).astype(int), np.round(sxy[:, 1]).astype(int)
ok2 = (sx >= 0) & (sx < m2.shape[1]) & (sy >= 0) & (sy < m2.shape[0]); s_in = np.zeros(len(P), bool); s_in[ok2] = m2[sy[ok2], sx[ok2]]
s_in |= ~ok2   # 옆 그림 밖(뿔 끝 · 안테나 끝 잘림)은 모름 → 깎지 않음
V &= f_in & s_in
# ③ 앞면 칼: 정면 접힌 판
Z1 = np.load(os.path.join(O, "판_1_Z.npz"))["Z"]; eye = [(f["눈/왼"][0] + f["눈/오른"][0]) / 2, (f["눈/왼"][1] + f["눈/오른"][1]) / 2]
def zat(x, y):
    q = Z1[max(0, int(y) - 3):int(y) + 4, max(0, int(x) - 3):int(x) + 4]; return float(np.nanmedian(q))
z_eye, z_chin = zat(*eye), zat(*f["턱 끝"])
# 1 판: 껍질 깊이를 통째로 쓰니(배율 a) 껍질은 턱이 눈보다 46 뒤(정면 한 장은 부리 돌출을 모른다) → 부리 · 뿔이 다 깎여 나감.
# 2 판: 껍질의 큰 깊이는 버리고 **잔 꺾임(높은 주파수)만** — 껍질 − 가우스 흐림(σ 10) = 면 단차 · 홈 → 덩어리 앞면에서 그만큼만 판다(더하지 않음).
from scipy import ndimage
Zf = np.where(np.isfinite(Z1), Z1, np.nanmean(Z1)); rel = Zf - ndimage.gaussian_filter(Zf, 10)          # + = 보는 쪽으로 나옴
Vg0 = V.reshape(GX.shape); has = Vg0.any(1); first = np.where(has, Vg0.argmax(1), -1)                  # (x, z) 마다 덩어리 앞면 칸
dep = np.full(len(P), 0.0); fin = ok & f_in; dep[fin] = np.clip(-rel[fy[fin], fx[fin]], 0, None) * 1.5    # 들어간 곳만(+ 깊이) · 배율 1.5(가정)
ix = np.searchsorted(xs, P[:, 0]).clip(0, len(xs) - 1); iz = np.searchsorted(zs, P[:, 2]).clip(0, len(zs) - 1); fr = first[ix, iz]
front = np.where(fr >= 0, ds[fr.clip(0)] + dep, -1e9); a = 1.5
V &= ~(P[:, 1] < front)      # 껍질보다 앞에 있는 덩어리는 깎음
Vg = V.reshape(GX.shape); vt, fc, _, _ = measure.marching_cubes(np.pad(Vg, 1).astype(np.float32), 0.5); vt = (vt - 1) * st + np.array([xs[0], ds[0], zs[0]])
mesh = trimesh.Trimesh(vt, fc); trimesh.smoothing.filter_taubin(mesh, iterations=6)
art = cv2.imdecode(np.fromfile(os.path.join(O, "판_1_원화.png"), np.uint8), 1)[:, :, ::-1]
vx = np.clip(np.round(mesh.vertices[:, 0] + cu).astype(int), 0, art.shape[1] - 1); vy = np.clip(np.round(-mesh.vertices[:, 2]).astype(int), 0, art.shape[0] - 1)
col = art[vy, vx].astype(float); nf = mesh.vertex_normals[:, 1] < -0.25          # 앞(−y)을 보는 면만 원화 색
col = np.where(nf[:, None], np.clip(col * 1.25, 0, 255), 175); mesh.visual.vertex_colors = np.c_[col.astype(np.uint8), np.full(len(col), 255)].astype(np.uint8)
mesh.export(os.path.join(B, "깎기1.ply"), encoding="ascii")
r = {"복셀": int(V.sum()), "잔 꺾임 배율": a, "껍질 눈 · 턱 깊이": [round(z_eye, 1), round(z_chin, 1)]}
json.dump(r, open(os.path.join(B, "깎기1.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(r)
