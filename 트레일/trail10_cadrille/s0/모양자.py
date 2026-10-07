# -*- coding: utf-8 -*-
"""모양 자 묶음 (10-07 · claudedocs/research_CAD역설계메트릭_20261007.md)
IoU 하나로는 구멍을 메운 코드가 통과한다(정제 비교 그림) → 논문들이 쓰는 자를 같이 잰다.
  iou      부피 겹침 · 128³ 격자(64³ 은 긴 변 1.5 % 아래 구멍을 못 본다)
  cd       Chamfer 거리(표면 점 양방향 평균 거리 · 같은 좌표 [-1,1] 상자)
  b0 · 구멍  덩어리 수 · 관통 구멍 수(오일러 지표 χ = 2·b0 − 2·g 에서 g) — 위상이 원본과 같은지
  edge_f1  날카로운 모서리(이면각 30° 이상) 위 점끼리 F1 · 거리 문턱 = 상자 크기의 2 %
pred · gt 는 같은 좌표계 메시(역산수확.채점과 같은 규약: gt 는 [-1,1] 상자, 코드 메시는 /100)."""
import numpy as np, trimesh

def _occ(m, g):
    import open3d as o3d
    s = o3d.t.geometry.RaycastingScene(); s.add_triangles(o3d.core.Tensor(m.vertices.astype(np.float32)), o3d.core.Tensor(m.faces.astype(np.uint32)))
    return s.compute_occupancy(o3d.core.Tensor(g.astype(np.float32))).numpy() > 0.5

def _위상(m):
    b0 = len(m.split(only_watertight=False)); chi = m.euler_number
    return b0, int(round((2 * b0 - chi) / 2))

def _모서리점(m, n=3000, deg=30):
    if len(m.face_adjacency) == 0: return np.zeros((0, 3))
    e = m.face_adjacency_edges[m.face_adjacency_angles > np.radians(deg)]
    if len(e) == 0: return np.zeros((0, 3))
    a, b = m.vertices[e[:, 0]], m.vertices[e[:, 1]]; L = np.linalg.norm(b - a, axis=1); p = L / L.sum()
    k = np.random.default_rng(0).choice(len(e), n, p=p); t = np.random.default_rng(1).random((n, 1))
    return a[k] + (b[k] - a[k]) * t

def _가까움(a, b):
    from scipy.spatial import cKDTree
    return cKDTree(b).query(a)[0]

def 재기(pred, gt, n=128, tau=0.04):
    g = (np.indices((n, n, n)).reshape(3, -1).T + 0.5) / n * 2 - 1
    ia = _occ(gt, g) if gt.is_watertight else np.zeros(len(g), bool); ib = _occ(pred, g) if pred.is_watertight else np.zeros(len(g), bool)
    u = (ia | ib).sum(); iou = float((ia & ib).sum() / u) if u else 0.0
    pa = trimesh.sample.sample_surface_even(gt, 8192, seed=0)[0]; pb = trimesh.sample.sample_surface_even(pred, 8192, seed=0)[0]
    cd = float((_가까움(pa, pb).mean() + _가까움(pb, pa).mean()) / 2)
    ea, eb = _모서리점(gt), _모서리점(pred)
    if len(ea) == 0 and len(eb) == 0: ef = 1.0
    elif len(ea) == 0 or len(eb) == 0: ef = 0.0
    else:
        P = (_가까움(eb, ea) < tau).mean(); Rc = (_가까움(ea, eb) < tau).mean(); ef = float(2 * P * Rc / (P + Rc)) if P + Rc else 0.0
    (a0, ag), (b0_, bg) = _위상(gt), _위상(pred)
    return {"iou": round(iou, 3), "cd": round(cd, 4), "edge_f1": round(ef, 3), "b0": [a0, b0_], "구멍": [ag, bg], "위상같음": a0 == b0_ and ag == bg}

def _깊이(occ, ax, flip):   # 한 방향에서 본 첫 표면까지 깊이(칸) · 빈 곳은 -1
    o = np.flip(occ, ax) if flip else occ; hit = o.any(ax); d = np.argmax(o, axis=ax).astype(float); d[~hit] = -1; return d

def _거친위상(occ, k=4, frac=0.01):   # 128³ → 32³ (작은 디테일은 투머치) · 부스러기(<1 %) 무시 · 덩어리 b0 · 관통 구멍 b1
    from scipy import ndimage
    from skimage.measure import euler_number
    n = occ.shape[0] // k; c = occ[:n * k, :n * k, :n * k].reshape(n, k, n, k, n, k).mean((1, 3, 5)) >= 0.5
    lab, m = ndimage.label(c, structure=np.ones((3, 3, 3)))
    if m == 0: return 0, 0
    sz = ndimage.sum(c, lab, range(1, m + 1)); keep = np.isin(lab, 1 + np.flatnonzero(sz >= frac * c.sum())); b0 = int((sz >= frac * c.sum()).sum())
    bg, nb = ndimage.label(~np.pad(keep, 1)); b2 = nb - 1
    chi = euler_number(keep, connectivity=3); return b0, int(b0 + b2 - chi)

def 재기2(pred, gt, n=128, tol=2):
    """10-07 사용자 기준(cad-part-match-criterion): 겉보기 = 6 방향 깊이 지도 일치(가장 나쁜 쪽) · 연결 = 거친 격자 덩어리 · 구멍 수."""
    g = (np.indices((n, n, n)).reshape(3, -1).T + 0.5) / n * 2 - 1
    A = (_occ(gt, g) if gt.is_watertight else np.zeros(len(g), bool)).reshape(n, n, n); B = (_occ(pred, g) if pred.is_watertight else np.zeros(len(g), bool)).reshape(n, n, n)
    u = (A | B).sum(); iou = float((A & B).sum() / u) if u else 0.0
    views = []
    for ax in range(3):
        for fl in (False, True):
            da, db = _깊이(A, ax, fl), _깊이(B, ax, fl); m = (da >= 0) | (db >= 0)
            views.append(float(((da >= 0) & (db >= 0) & (np.abs(da - db) <= tol))[m].mean()) if m.any() else 1.0)
    ta, tb = _거친위상(A), _거친위상(B)
    return {"iou": round(iou, 3), "겉보기": round(min(views), 3), "겉보기평균": round(float(np.mean(views)), 3), "연결": [list(ta), list(tb)], "연결같음": ta == tb}

if __name__ == "__main__":   # 자기 검사: 구멍 뚫린 상자와 꽉 찬 상자 — IoU 는 높아도 위상이 달라야 한다
    box = trimesh.creation.cylinder(0.8, 0.6, sections=64); ring = trimesh.creation.annulus(0.15, 0.8, 0.6, sections=64)   # 꽉 찬 원반 대 링
    r = 재기(box, ring); print(r)
    assert r["iou"] > 0.9 and not r["위상같음"], "구멍을 못 잡음"
    r2 = 재기(ring, ring); assert r2["위상같음"] and r2["iou"] > 0.99 and r2["edge_f1"] > 0.95; print("ok", r2)
