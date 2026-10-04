# -*- coding: utf-8 -*-
"""레퍼런스 변형 2 단계 — 휘기 (10-04 「계속 해봐봐」).
정렬된 엑시아(엑시아_정렬.ply)를 원화 측정에 맞춰 줄(행)마다 휜다. 모양은 레퍼런스 것, 목표값만 원화:
  정면: 행마다 몸통(지름 25 원으로 열어 가시 · V 핀 · 뿔 · 안테나를 뗀 실루엣)의 가운데 · 반폭 → x' = c원화 + (x − c엑시아)·(w원화/w엑시아)
  옆:   행마다 뒤 끝(가장 뒤 깊이) → 눈 깊이 0 보다 뒤(y > 0)만 y' = y·(뒤원화/뒤엑시아) · 앞(부리 쪽)은 4 단계 몫이라 그대로
  배율은 행 방향 가우시안 σ 6 으로 고르게 · 0.6 ~ 1.6 으로 묶음 · 원화 몸통이 없는 행(뿔 위 · 턱 아래)은 가장 가까운 행 값
출력 out/오메가몬2/블렌더/엑시아_휨.ply"""
import os, numpy as np, cv2, trimesh, contextlib, io
from scipy import ndimage
A = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
K = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "기준선.py")}
with contextlib.redirect_stdout(io.StringIO()): exec(open(K["__file__"], encoding="utf-8").read(), K)
m1 = np.load(os.path.join(A, "판_1_Z.npz"))["m"]; H, W = m1.shape; cu = (np.nonzero(m1)[1].min() + np.nonzero(m1)[1].max()) / 2
m2 = np.load(os.path.join(A, "판_2_Z.npz"))["m"]; D0, ND = -200, 400; k_, t_ = K["k"], K["t"]; ct, st_ = np.cos(t_), np.sin(t_)
Ma = np.array([[k_ * ct, -k_ * st_, -k_ * K["ex"] * ct + k_ * K["ey"] * st_ - D0], [k_ * st_, k_ * ct, K["c"] - k_ * K["xm"] * st_]], np.float32)
S2 = cv2.warpAffine(m2.astype(np.uint8), Ma, (ND, H), flags=cv2.INTER_NEAREST)
me = trimesh.load(os.path.join(B, "엑시아_정렬.ply"), process=False); v = me.vertices.copy(); f = me.faces
def 실루엣(u, shape):
    img = np.zeros(shape, np.uint8); r = -v[:, 2]
    cv2.fillPoly(img, [np.round(np.c_[u[t], r[t]]).astype(np.int32) for t in f], 1); return img
몸 = lambda m: cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
Fa, Fe = 몸(m1), 몸(실루엣(v[:, 0] + cu, (H, W)))
Se = 몸(실루엣(v[:, 1] - D0, (H, ND)))
# 3 판: V 핀 · 가시 떼기(4 단계 「없는 부품 빼기」를 앞당김) — 면 중심이 정면 몸통 밖이거나 옆 몸통 밖이면 버림
cen = v[f].mean(1); rr_ = np.clip(np.round(-cen[:, 2]).astype(int), 0, H - 1)
안 = (Fe[rr_, np.clip(np.round(cen[:, 0] + cu).astype(int), 0, W - 1)] > 0) & (Se[rr_, np.clip(np.round(cen[:, 1] - D0).astype(int), 0, ND - 1)] > 0)
f = f[안]; print({"뗀 면": int((~안).sum())})
def 행값(mask, fn):
    out = np.full(H, np.nan)
    for r in range(H):
        xs = np.nonzero(mask[r])[0]
        if len(xs) > 2: out[r] = fn(xs)
    return out
ca, wa = 행값(Fa, lambda x: (x.min() + x.max()) / 2), 행값(Fa, lambda x: (x.max() - x.min()) / 2)
ce, we = 행값(Fe, lambda x: (x.min() + x.max()) / 2), 행값(Fe, lambda x: (x.max() - x.min()) / 2)
ba, be = 행값(S2, lambda x: x.max() + D0), 행값(Se, lambda x: x.max() + D0)   # 뒤 끝 깊이
def 채우고고르게(a, lo=None, hi=None):
    ok = np.isfinite(a)
    if ok.sum() < 3: return np.ones_like(a)
    a = np.interp(np.arange(H), np.nonzero(ok)[0], a[ok]); a = ndimage.gaussian_filter1d(a, 25)   # 2 판: σ 6 은 행마다 따로 놀아 녹은 듯 · V 핀이 1.6 배로 옆으로 늘어남
    return np.clip(a, lo, hi) if lo is not None else a
sx = 채우고고르게(wa / we, 0.8, 1.25); dc = 채우고고르게(ca - ce); 기준c = 채우고고르게(ce)
sy = 채우고고르게(np.where(be > 5, ba / be, np.nan), 0.8, 1.25)
r = np.clip(np.round(-v[:, 2]).astype(int), 0, H - 1)
x_img = v[:, 0] + cu
v[:, 0] = (기준c[r] + dc[r] + (x_img - 기준c[r]) * sx[r]) - cu
뒤 = v[:, 1] > 0; v[뒤, 1] = v[뒤, 1] * sy[r[뒤]]
trimesh.Trimesh(v, f, vertex_colors=me.visual.vertex_colors, process=False).export(os.path.join(B, "엑시아_휨3.ply"))
rows = slice(int(np.nanmin(np.nonzero(np.isfinite(wa))[0])), int(np.nanmax(np.nonzero(np.isfinite(wa))[0])))
print({"폭 배율 범위": [round(float(sx[rows].min()), 2), round(float(sx[rows].max()), 2)], "뒤 배율 범위": [round(float(sy[rows].min()), 2), round(float(sy[rows].max()), 2)], "가운데 옮김 최대": round(float(np.abs(dc[rows]).max()), 1)})
