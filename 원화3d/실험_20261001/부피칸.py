# -*- coding: utf-8 -*-
"""부품 부피 칸 채우기 (10-02 사용자 「TripoSG 랑 분할한 칸으로 부피도 안다 · 해봐야 알지」).
TripoSG 머리(h_remesh · 머리 단위: x 오른 · y 아래 · z 앞)를 0.5 단위 복셀로 채우고, 정면 칸(연결그래프 30 부품)을 같은 틀에 겹친다.
  앞면 깊이 = 그 기둥에서 가장 앞 복셀 · 턱 = 맞닿은 두 부품의 경계 양쪽 앞면 깊이 차(중앙) → 3D 앞뒤 · 띄움
  두께 = 그 부품이 앞에 선 이웃들과의 턱 중 최대(1 ~ 8 단위로 자름 · 없으면 2) · 부피 조각 = 앞면에서 두께만큼 · 나머지 = 코어
2D 덮음(볼록성)과 3D 턱 부호가 맞는지 대조. 출력 out/오메가몬2/지표/부피칸/{부피칸.json, 그래프_부피.json(지온.py), part_*.obj, 코어.obj}"""
import os, sys, json, numpy as np, trimesh
from skimage import measure
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 지온 as G
K = r"G:\art2real\원화3d\out\오메가몬2\지표"; O = os.path.join(K, "부피칸")
L = np.load(os.path.join(K, "선파츠_정면.npz"))["라벨"]; ys, xs = np.nonzero(L > 0); top, bot = ys.min(), ys.max(); k = 100 / (bot - top)
그래프 = json.load(open(os.path.join(K, "연결그래프", "그래프.json"), encoding="utf-8"))
부품 = 그래프["부품"]; 이름 = [p["이름"] for p in 부품]
dome = np.isin(L, [n for p in 부품 if p["이름"].startswith("투구 돔") for n in p["칸"]]); dx_ = np.nonzero(dome)[1]; cx = (dx_.min() + dx_.max()) / 2

m = trimesh.load(os.path.join(O, "h_remesh.obj"), process=False); u = 0.5
vg = m.voxelized(u).fill(); V = vg.matrix; T = vg.transform        # V[i,j,l] ↔ 점 = T @ (i,j,l,1)
lo = T[:3, 3]; nx, ny, nz = V.shape
X = lo[0] + np.arange(nx) * u; Y = lo[1] + np.arange(ny) * u; Z = lo[2] + np.arange(nz) * u
# 앞면 깊이 지도(z 가 앞) · 칸 번호 지도(같은 격자)
has = V.any(2); zi = np.where(has, nz - 1 - np.argmax(V[:, :, ::-1], 2), -1); Zf = np.where(has, Z[np.clip(zi, 0, nz - 1)], np.nan)
PX = np.clip(np.round(X[:, None] / k + cx).astype(int), 0, L.shape[1] - 1); PY = np.clip(np.round(Y[None, :] / k + top).astype(int), 0, L.shape[0] - 1)
cell = L[PY.T, PX.T].T if False else L[np.broadcast_to(PY, (nx, ny)), np.broadcast_to(PX, (nx, ny))]
c2p = {n: i for i, p in enumerate(부품) for n in p["칸"]}; Pm = np.vectorize(lambda c: c2p.get(int(c), -1))(cell); Pm[~has] = -1
# 턱: 격자 이웃(오른 · 아래)이 다른 부품인 쌍
턱 = {}
for dxy in ((1, 0), (0, 1)):
    a = Pm[: nx - dxy[0], : ny - dxy[1]]; b = Pm[dxy[0]:, dxy[1]:]; za = Zf[: nx - dxy[0], : ny - dxy[1]]; zb = Zf[dxy[0]:, dxy[1]:]
    ok = (a >= 0) & (b >= 0) & (a != b)
    for i, j, d in zip(a[ok], b[ok], (za - zb)[ok]):
        key = (min(i, j), max(i, j)); 턱.setdefault(key, []).append(d if i < j else -d)
step = {key: float(np.median(v)) for key, v in 턱.items() if len(v) >= 3}
# 2D 덮음과 대조
대조 = []; 맞음 = 0; 확실 = 0
for e in 그래프["덮음"]:
    if not e["확실"]: continue
    i, j = 이름.index(e["앞"]), 이름.index(e["뒤"]); key = (min(i, j), max(i, j))
    if key not in step: continue
    d3 = step[key] if i < j else -step[key]; 확실 += 1; 맞음 += d3 > 0; 대조.append((e["앞"], e["뒤"], round(d3, 1)))
# 부피 칸 · 조각
부피 = {}; 조각 = np.full(V.shape, -1, np.int16)
for i, p in enumerate(부품):
    mk = Pm == i
    if not mk.any(): 부피[p["이름"]] = None; continue
    zf = Zf[mk]; front = [step[(min(i, j), max(i, j))] * (1 if i < j else -1) for j in range(len(부품)) if (min(i, j), max(i, j)) in step]
    proud = [d for d in front if d > 0]; 두께 = float(np.clip(max(proud) if proud else 2.0, 1.0, 8.0))
    부피[p["이름"]] = {"앞면깊이": round(float(np.median(zf)), 1), "앞면범위": [round(float(zf.min()), 1), round(float(zf.max()), 1)], "두께": round(두께, 1),
                     "띄움최대": round(float(max(proud)), 1) if proud else 0.0, "넓이": round(float(mk.sum() * u * u), 1)}
    ii, jj = np.nonzero(mk)
    for a_, b_ in zip(ii, jj):
        if zi[a_, b_] < 0: continue
        l0 = max(0, zi[a_, b_] - int(round(두께 / u)) + 1); seg = V[a_, b_, l0: zi[a_, b_] + 1]; 조각[a_, b_, l0: zi[a_, b_] + 1][seg] = i
코어 = V & (조각 < 0)
def 메시(mask, name):
    if mask.sum() < 4: return
    vv, ff, _, _ = measure.marching_cubes(np.pad(mask, 1).astype(np.float32), 0.5)
    vv = (vv - 1) * u + lo; mm = trimesh.Trimesh(np.c_[vv[:, 0], -vv[:, 2], -vv[:, 1]], ff)   # M(x, y아래, z앞) → 블렌더(x, -z, -y)
    trimesh.smoothing.filter_taubin(mm, iterations=8); mm.export(os.path.join(O, name + ".obj"))
for f in os.listdir(O):
    if f.startswith("part_"): os.remove(os.path.join(O, f))
for i, p in enumerate(부품): 메시(조각 == i, f"part_{i:02d}")
메시(코어, "코어")
# 지온 그래프에 담기
g = G.그래프()
for i, p in enumerate(부품):
    nm, side = p["이름"].split("/"); g.더하기(G.부품(nm, side, p["층"], None, "정면", [G.관찰("정면", p["칸"])], 부피=부피[p["이름"]] or {}))
g.저장(os.path.join(O, "그래프_부피.json"))
json.dump({"부피": 부피, "턱": {f"{이름[a]}|{이름[b]}": round(v, 1) for (a, b), v in step.items()}, "덮음대조": {"확실": 확실, "3D와같음": int(맞음), "목록": 대조},
           "복셀": [nx, ny, nz], "코어복셀": int(코어.sum()), "부품복셀": int((조각 >= 0).sum())}, open(os.path.join(O, "부피칸.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("복셀", V.shape, "코어", int(코어.sum()), "부품", int((조각 >= 0).sum()), "· 2D 덮음 vs 3D 턱:", 맞음, "/", 확실)
for n, v in 부피.items(): print(n, v)
