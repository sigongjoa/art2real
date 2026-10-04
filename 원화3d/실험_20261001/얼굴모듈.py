# -*- coding: utf-8 -*-
"""얼굴 모듈 = 창 모듈 3 판 + 부리(마스크 아래) (10-04 「ㄱㄱ」).
부리 깊이를 3/4 옆벽 폭으로 재려 했으나 3/4 는 부리가 망토 · 마우스 커서에 가리고 화면 아래로 잘림 · 판 윗면 폭 ÷ sin(내려다본 각)은 각이 5~15° 로 몰라 3 배가 흔들림 → 못 씀.
대신 건축의 「단면」: 옆 원화의 머리 앞 윤곽선 = 높이별 가장 앞 깊이(옆 원화를 B 맞춤으로 정면 층에 맞춤 · 눈 = 0 · 앞 −). 잰 단면을 그대로 씀.
  부리 영역 = 정면 마스크 칸(부품ID H02) 중 L5(눈) 아래 · 높이 행 r 의 앞면 깊이 = 단면(r) + (접힌 판 상대 높이(x, r) − 그 행의 가운데 값)  — 가로로는 접힌 판의 V 꺾임
  그 위(창 모듈 영역)는 창 모듈 3 판 그대로 · 두 영역이 같은 높이장이라 붙어 있음.
출력 out/오메가몬2/블렌더/얼굴모듈.ply · 얼굴모듈_비교.png · 얼굴모듈.json"""
import os, json, numpy as np, cv2, trimesh
from scipy import ndimage
G = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "창모듈2.py")}; exec(open(G["__file__"], encoding="utf-8").read(), G)
O, B, m, H, W, px, py, cell, 층, 축, rel, dep, 쓸, 안 = [G[k] for k in ("O", "B", "m", "H", "W", "px", "py", "cell", "층", "축", "rel", "dep", "쓸", "안")]
reveal, 위띠, cu = G["reveal"], G["위띠"], G["cu"]
K = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "기준선.py")}; exec(open(K["__file__"], encoding="utf-8").read(), K); T = K["T"]
# 단면: 옆 머리 마스크의 행마다 가장 앞(정면 행으로 옮김)
m2 = np.load(os.path.join(O, "판_2_Z.npz"))["m"]; ys2, xs2 = np.nonzero(m2); dd, rr = T(xs2.astype(float), ys2.astype(float))
rows = np.round(rr).astype(int); 단면 = np.full(H, np.nan)
for r_ in range(H):
    q = rows == r_
    if q.any(): 단면[r_] = dd[q].min()
ok = np.isfinite(단면); 단면 = np.interp(np.arange(H), np.nonzero(ok)[0], 단면[ok]); 단면 = ndimage.median_filter(단면, 7)
대응 = json.load(open(os.path.join(O, "부품ID.json"), encoding="utf-8"))["대응표"]["1"]
마스크칸 = [c for e in 대응 if e.get("부품") == "H02 마스크" for c in e["칸"]]
L5, L2 = 층["L5 눈"], 층["L2 턱 끝"]
부리 = np.isin(cell, 마스크칸) & (py > L5) & (py <= L2 + 2) & ~안
부리 = cv2.morphologyEx(부리.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) > 0
# 1 판: 부리만 단면 깊이(−90 안팎)로 두고 창 둘레 벽은 −17 그대로 → 부리가 얼굴 앞 70 에 떠 버림. 단면은 「행마다 가장 앞 = 코판 · 부리 능선」이고 −17 은 「창 입구」 — 둘 다 잰 값이라 한 행 안에서 이어야 한다.
# 2 판: 행마다 가로 무게 w = 접힌 판 상대 높이를 그 행의 [10 백분위, 가운데] 로 0~1 정규화 → 벽 깊이 = −D + (단면(r) + D) · w   (창 둘레 = −D · 가운데 능선 = 단면)
xa = 축["A 중심"]; 영역 = 쓸 | 부리; D_ = G["D"]
wall = np.full((H, W), np.nan)
for r_ in range(H):
    q = 영역[r_] & ~G["앞"][r_]
    if q.sum() < 3: continue
    rv = rel[r_, q]; lo = np.percentile(rv, 10); cmask = q & (np.abs(np.arange(W) - xa) < 6); hi = np.median(rel[r_, cmask]) if cmask.any() else rv.max()
    w = np.clip((rel[r_] - lo) / max(1e-3, hi - lo), 0, 1); wall[r_] = -D_ + (단면[r_] + D_) * w
wall = np.where(np.isfinite(wall), wall, -D_)
dep2 = wall.copy(); 앞_ = G["앞"]
d_in = ndimage.distance_transform_edt(~안); d_out = ndimage.distance_transform_edt(앞_); tt = d_in / np.maximum(1e-6, d_in + d_out)
rv_ = 앞_ & ~안; _, (iy, ix) = ndimage.distance_transform_edt(앞_, return_indices=True); 벽끝 = wall[iy, ix]
dep2[rv_] = (벽끝 * tt)[rv_]; dep2[안] = 0.0; dep2[위띠] -= 2.0
쓸2 = 쓸 | 부리
ys, xs = np.nonzero(쓸2); vid = -np.ones((H, W), int); vid[ys, xs] = np.arange(len(ys)); n = len(ys)
V = np.c_[xs - cu, dep2[ys, xs], -ys.astype(float)]
a, b, c, d = vid[:-1, :-1], vid[:-1, 1:], vid[1:, :-1], vid[1:, 1:]; ok = (a >= 0) & (b >= 0) & (c >= 0) & (d >= 0)
F = np.r_[np.c_[a[ok], b[ok], c[ok]], np.c_[b[ok], d[ok], c[ok]]]
col = np.full((n, 3), (225, 228, 238), np.uint8); col[안[ys, xs]] = (25, 25, 32); col[reveal[ys, xs]] = (240, 242, 250); col[부리[ys, xs]] = (215, 218, 230)
me = trimesh.Trimesh(V, F, process=False); trimesh.smoothing.filter_taubin(me, iterations=3); me.visual.vertex_colors = np.c_[col, np.full(n, 255)].astype(np.uint8)
parts = [me] + [p for p in G["parts"][1:]]
allm = trimesh.util.concatenate(parts); allm = trimesh.Trimesh(allm.vertices, allm.faces, vertex_colors=allm.visual.vertex_colors, process=False)
allm.export(os.path.join(B, "얼굴모듈.ply"), encoding="ascii")
r = {"단면 깊이(눈 = 0)": {nm: round(float(단면[int(v)]), 1) for nm, v in 층.items()}, "부리 화소": int(부리.sum())}
json.dump(r, open(os.path.join(B, "얼굴모듈.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(r)
