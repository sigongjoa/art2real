# -*- coding: utf-8 -*-
"""분할 데이터 2판 (2026-10-05) — 1판은 「다른 부품 1.5 mm 안」이라 겹친 판 덩어리가 경계로 찍혔다(학습 전도 F1 0.70).
고침: ① 보이는 겉면만 — open3d 광선 추적으로 점마다 15 방향(법선 쪽 반구) 중 하나라도 빠져나가면 보임
      ② 경계 = 보이는 점 중 1.2 mm 안의 보이는 이웃에 다른 부품이 있는 점(사람이 자른 이음 「선」)
python 분할데이터2.py <후보 번호> → _학습2/<폴더>.npz {xyz · n · 경계 · 부품} · 확인.json 누적"""
import os, sys, glob, json, numpy as np, trimesh, open3d as o3d
from scipy.spatial import cKDTree
R = "G:/art2real/원화3d/out/레퍼런스/사람분할/"; O = R + "_학습2/"; os.makedirs(O, exist_ok=True)
ds = sorted(d for d in glob.glob(R + "*/") if not os.path.basename(d[:-1]).startswith("_"))
k = int(sys.argv[1]); d = ds[k - 1]; name = os.path.basename(d[:-1])
fs = [f for f in glob.glob(d + "*") if f.lower().endswith((".stl", ".obj"))]
if os.path.exists(O + name + ".npz") or sum(os.path.getsize(f) for f in fs) > 150e6: sys.exit()
parts = []
for f in fs:
    try:
        m = trimesh.load(f, force="mesh")
        if len(m.faces) >= 20: parts.append(m)
    except Exception: pass
if len(parts) > 150: parts = sorted(parts, key=lambda m: -m.area)[:150]
allv = np.vstack([p.vertices for p in parts]); s = 200.0 / np.ptp(allv, 0).max()
for p in parts: p.apply_scale(s)
tot = sum(p.area for p in parts); P, Nn, I = [], [], []
for i, p in enumerate(parts):
    pts, fi = trimesh.sample.sample_surface(p, max(30, int(40000 * p.area / tot)), seed=i); P.append(pts); Nn.append(p.face_normals[fi]); I.append(np.full(len(pts), i))
P, Nn, I = np.vstack(P), np.vstack(Nn), np.concatenate(I)
sc = o3d.t.geometry.RaycastingScene()
for p in parts: sc.add_triangles(o3d.t.geometry.TriangleMesh.from_legacy(o3d.geometry.TriangleMesh(o3d.utility.Vector3dVector(p.vertices), o3d.utility.Vector3iVector(p.faces))))
rng = np.random.default_rng(0); D = rng.normal(size=(15, 3)); D /= np.linalg.norm(D, axis=1, keepdims=True)
vis = np.zeros(len(P), bool)
for j in range(16):
    dv = Nn if j == 0 else np.where(((Nn @ D[j - 1]) > 0)[:, None], D[j - 1][None], -D[j - 1][None])   # 법선 쪽 반구로 뒤집기
    todo = np.where(~vis)[0]
    if not len(todo): break
    rays = np.hstack([P[todo] + Nn[todo] * 0.2, dv[todo]]).astype(np.float32)
    t = sc.cast_rays(o3d.core.Tensor(rays))["t_hit"].numpy(); vis[todo[np.isinf(t)]] = True
V = np.where(vis)[0]; tv = cKDTree(P[V]); 경계 = np.zeros(len(V), bool)
for a, nb in enumerate(tv.query_ball_point(P[V], 1.2)): 경계[a] = np.any(I[V][nb] != I[V][a])
info = {"부품": len(parts), "점": int(len(P)), "보임": int(len(V)), "경계비율": round(float(경계.mean()), 3)}
np.savez_compressed(O + name + ".npz", xyz=P[V].astype(np.float32), n=Nn[V].astype(np.float32), 경계=경계, 부품=I[V])
old = json.load(open(O + "확인.json", encoding="utf-8")) if os.path.exists(O + "확인.json") else {}
old[name] = info; json.dump(old, open(O + "확인.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(name, info)
