# -*- coding: utf-8 -*-
"""마스크를 한 덩어리로 짓고 분할선으로 판을 나눈다 (10-03 사용자 「붙어 있어야 하지 않아? 안 붙어 있는데 뭐 어떻게 하는데?」).
지금까지: 판마다 따로 지어 따로 놓음 → 판끼리 · 얼굴과 안 붙음(그리고 장끼리 이름 짝이 틀려 판이 빔).
이번: ① 마스크 전체 = 정면 마스크 칸 전부 ∩ 옆 마스크 칸 전부(두 장 분할 · 맞춘 카메라 B) — 한 덩어리라 붙어 있음은 구성상 보장
      ② 판 나누기 = 정면 분할선으로만(복셀마다 정면 화소의 칸 → 판 이름) — 장끼리 이름 짝이 필요 없음(분할선 = 겹 경계 · 메모 layers-not-one-volume)
      ③ 마스크 뒷면은 속머리에 닿을 때까지(빈틈 없음) — 속머리 = 디테일 1 판의 검은 타원체
바탕(투구 · 속머리 · 뿔 · 안테나 · 눈 · 볼날개)은 디테일 1 판 그대로, 옛 계단 쐐기는 뺌.
출력 out/오메가몬2/블렌더/마스크한장.ply · 마스크한장_단계.png"""
import os, json, numpy as np, cv2, trimesh
from skimage import measure
G = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "디테일1.py")}
exec(open(G["__file__"], encoding="utf-8").read(), G)
GG = G["G"]; O, B, cu = GG["O"], G["B"], GG["cu"]
k, t_, c_, xm, ex, ey = GG["k"], GG["t"], GG["c"], GG["xm"], GG["ex"], GG["ey"]
ct, st = np.cos(t_), np.sin(t_); Ai = np.linalg.inv(np.array([[k * ct, -k * st], [k * st, k * ct]])); b0 = np.array([-k * (ex * ct - ey * st), -k * xm * st + c_])
대응 = json.load(open(os.path.join(O, "부품ID.json"), encoding="utf-8"))["대응표"]
def 칸지도(n):
    z = np.load(os.path.join(O, f"{n}.npz")); L = z["라벨"]; ys, xs = np.nonzero(L > 0); y0, x0_ = ys.min(), xs.min()
    m = np.load(os.path.join(O, f"판_{n}_Z.npz"))["m"]; H, W = m.shape; py, px = np.mgrid[0:H, 0:W]
    return L[np.clip(y0 + 2 * py, 0, L.shape[0] - 1), np.clip(x0_ + 2 * px, 0, L.shape[1] - 1)] * m
C1, C2 = 칸지도("1"), 칸지도("2")
마스크칸 = lambda n: [c for e in 대응[n] if e.get("부품") == "H02 마스크" for c in e["칸"]]
F = np.isin(C1, 마스크칸("1")); S = cv2.dilate(np.isin(C2, 마스크칸("2")).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
판이름 = {c: e.get("표면", "?") for e in 대응["1"] if e.get("부품") == "H02 마스크" for c in e["칸"]}
st_ = 1.0; xs = np.arange(-130, 130, st_); ds = np.arange(-160, 140, st_); zs = np.arange(-330, -140, st_)
GX, GD, GZ = np.meshgrid(xs, ds, zs, indexing="ij")
fx = np.round(GX + cu).astype(int); fy = np.round(-GZ).astype(int); sxy = np.einsum("ij,j...->i...", Ai, np.stack([GD - b0[0], -GZ - b0[1]]))
sx, sy = np.round(sxy[0]).astype(int), np.round(sxy[1]).astype(int)
ok1 = (fx >= 0) & (fx < F.shape[1]) & (fy >= 0) & (fy < F.shape[0]); ok2 = (sx >= 0) & (sx < S.shape[1]) & (sy >= 0) & (sy < S.shape[0])
V = np.zeros(GX.shape, bool); both = ok1 & ok2; V[both] = F[fy[both], fx[both]] & S[sy[both], sx[both]]
# ③ 속머리까지 메움: (x, z) 마다 마스크 앞면부터 속머리 겉면까지 채움
ic, ir = G["ic"], G["ir"]; inside_inner = (((np.stack([GX, GD, GZ], -1) - ic) / ir) ** 2).sum(-1) <= 1.0
has = V.any(1); first = np.where(has, V.argmax(1), 0)
idx = np.arange(len(ds))[None, :, None]; fill = has[:, None, :] & (idx >= first[:, None, :]) & (F[np.clip(fy, 0, F.shape[0] - 1), np.clip(fx, 0, F.shape[1] - 1)] & ok1)
# 속머리 겉면을 지나면 멈춤(속머리 안은 비움 — 속머리 자체가 덩어리)
m2h = np.load(os.path.join(O, "판_2_Z.npz"))["m"]; 옆머리 = np.zeros(GX.shape, bool); 옆머리[ok2] = m2h[sy[ok2], sx[ok2]]
reached = np.cumsum(inside_inner & fill, axis=1) > 0; V = (V | (fill & 옆머리)) & ~reached   # 1 판: 메움이 옆 머리 실루엣을 안 따라 뒤로 상자처럼 늘어남 → 옆 머리 안에서만 메움
결과 = {"마스크 복셀": int(V.sum())}
vt, fc, _, _ = measure.marching_cubes(np.pad(V, 1).astype(np.float32), 0.5); vt = (vt - 1) * st_ + np.array([xs[0], ds[0], zs[0]])
mm = trimesh.Trimesh(vt, fc); trimesh.smoothing.filter_taubin(mm, iterations=4)
# ② 판 나누기: 꼭짓점마다 정면 화소의 칸 → 판 → 색
색 = {"코판": (235, 90, 90), "미늘2": (90, 210, 90), "턱판": (90, 130, 235), "볼판": (220, 200, 90)}
vx = np.clip(np.round(mm.vertices[:, 0] + cu).astype(int), 0, C1.shape[1] - 1); vy = np.clip(np.round(-mm.vertices[:, 2]).astype(int), 0, C1.shape[0] - 1)
cell = C1[vy, vx]; nm = [판이름.get(int(c), "?") for c in cell]
from collections import Counter; 결과["판별 꼭짓점"] = dict(Counter(nm))
mm.visual.vertex_colors = np.c_[np.array([색.get(n, (200, 200, 205)) for n in nm], np.uint8), np.full(len(nm), 255)].astype(np.uint8)
# 바탕: 디테일 1 판에서 옛 계단 쐐기 빼고
bb = G["beak"].bounds; base = [p for p in G["parts"] if not (np.all(p.bounds[0] >= bb[0] - 3) and np.all(p.bounds[1] <= bb[1] + 3))]
allm = trimesh.util.concatenate(base + [mm]); allm = trimesh.Trimesh(allm.vertices, allm.faces, vertex_colors=allm.visual.vertex_colors, process=False)
allm.export(os.path.join(B, "마스크한장.ply"), encoding="ascii")
# 붙음 검사: 마스크 덩어리가 한 조각인가 · 속머리에 닿는가
결과["마스크 조각 수"] = int(len(mm.split(only_watertight=False)))
d_in = np.abs(np.linalg.norm((mm.vertices - ic) / ir, axis=1) - 1.0); 결과["속머리에 닿은 꼭짓점 비"] = round(float((d_in < 0.05).mean()), 3)
json.dump(결과, open(os.path.join(B, "마스크한장.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(결과)
