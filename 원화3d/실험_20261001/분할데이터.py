# -*- coding: utf-8 -*-
"""분할 학습 확인용 데이터 (2026-10-05) — 사람이 나눈 출력용 모델(조립 위치) → 점 + 「자르는 자리(경계)」 정답
모델마다: 부품 표면에서 점 → 바깥에 보이는 점만(다른 부품 속 · 맞닿아 숨은 면 빼기) → 경계 = 다른 부품 표면이 1.5 mm 안
조립 확인: 부품의 맞닿음 비율(다른 부품 표면 0.5 mm 안에 점이 1 % 넘는 부품의 비율) — 경계상자 판별은 틀렸음
python 분할데이터.py → out/레퍼런스/사람분할/_학습/<폴더>.npz {xyz(mm) · n · 경계 · 부품} · 확인.json"""
import os, sys, glob, json, numpy as np, trimesh
from scipy.spatial import cKDTree
R = "G:/art2real/원화3d/out/레퍼런스/사람분할/"; O = R + "_학습/"; os.makedirs(O, exist_ok=True)
# 한눈 그림에서 조립 위치로 보인 것(눈 판정) — 맞닿음 숫자로 한 번 더 거른다
후보 = [1, 3, 8, 9, 14, 16, 20, 21, 22, 26, 30, 32, 33, 38, 40, 41, 42, 48]
ds = sorted(glob.glob(R + "*/")); ds = [d for d in ds if not os.path.basename(d[:-1]).startswith("_")]
rng = np.random.default_rng(0); 확인 = {}
# 10-05 메모리 부족으로 죽음 → 모델 하나씩(인자) · 150 MB 넘는 모델 건너뜀 · 광선 대신 「맞닿아 숨은 면」만 뺌
하나 = int(sys.argv[1]) if len(sys.argv) > 1 else None
for k in ([하나] if 하나 else 후보):
    d = ds[k - 1]; name = os.path.basename(d[:-1])
    fs = [f for f in glob.glob(d + "*") if f.lower().endswith((".stl", ".obj"))]
    if os.path.exists(O + name + ".npz"): continue
    if sum(os.path.getsize(f) for f in fs) > 150e6: print(name, "150 MB 넘음 · 건너뜀"); continue
    parts = []
    for f in fs:
        try:
            m = trimesh.load(f, force="mesh")
            if len(m.faces) >= 20: parts.append(m)
        except Exception: pass
    if len(parts) < 3: 확인[name] = {"부품": len(parts), "판정": "부품 적음"}; continue
    if len(parts) > 150: parts = sorted(parts, key=lambda m: -m.area)[:150]
    tot = sum(p.area for p in parts); N = 30000
    P, Nn, I = [], [], []
    for i, p in enumerate(parts):
        k_ = max(30, int(N * p.area / tot)); pts, fi = trimesh.sample.sample_surface(p, k_, seed=i)
        P.append(pts); Nn.append(p.face_normals[fi]); I.append(np.full(len(pts), i))
    P, Nn, I = np.vstack(P), np.vstack(Nn), np.concatenate(I)
    P = P * (200.0 / np.ptp(P, 0).max())   # 모델마다 단위가 달라(Stray 15 mm 등) 긴 변 200 mm 로 맞춤 — 경계 1.5 mm 기준을 같게
    tr = cKDTree(P)
    # 다른 부품까지 최근접 거리
    dd = np.full(len(P), np.inf)
    for i in range(len(parts)):
        o = I != i
        if o.sum() == 0: continue
        t = cKDTree(P[o]); m = I == i; dd[m] = t.query(P[m], k=1)[0]
    닿음 = np.array([np.mean(dd[I == i] < 0.5) > 0.01 for i in range(len(parts))]).mean()
    # 맞닿아 숨은 면 빼기: 다른 부품 표면이 0.3 mm 안이고 그쪽 법선이 반대(마주 봄)면 숨은 면
    vis = np.ones(len(P), bool)
    for i in range(len(parts)):
        o = np.where(I != i)[0]; m = np.where(I == i)[0]
        if len(o) == 0: continue
        dist, j = cKDTree(P[o]).query(P[m], k=1); 마주 = (Nn[m] * Nn[o[j]]).sum(1) < -0.5
        vis[m[(dist < 0.3) & 마주]] = False
    경계 = (dd < 1.5) & vis
    확인[name] = {"부품": len(parts), "맞닿음비율": round(float(닿음), 2), "점": int(len(P)), "바깥": int(vis.sum()), "경계비율": round(float(경계[vis].mean()), 3),
                 "크기mm": np.round(np.ptp(P, 0), 1).tolist(), "판정": "조립" if 닿음 >= 0.5 else "흩어짐"}
    print(name, 확인[name], flush=True)
    if 닿음 >= 0.5: np.savez_compressed(O + name + ".npz", xyz=P[vis].astype(np.float32), n=Nn[vis].astype(np.float32), 경계=경계[vis], 부품=I[vis])
old = json.load(open(O + "확인.json", encoding="utf-8")) if os.path.exists(O + "확인.json") else {}
old.update(확인); json.dump(old, open(O + "확인.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
