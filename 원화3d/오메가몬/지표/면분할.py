# -*- coding: utf-8 -*-
"""꺾인 모서리 분할(공용) — 실험_20261001/트리포_먹선분할.py 의 나누기를 메시 인자로 뺐다.
오목만=True(기본): **오목하게 꺾인 변에서만 자른다**(Hoffman & Richards 최소 규칙 — 부품 경계는 오목한 곳) → 자른 변을 뺀 면 연결 성분 = 조각. 볼록한 각(상자 모서리)은 한 부품 안에 남는다.
  k = 0 이면 변만 자르고(정확한 메시 · 로우폴리), k ≥ 1 이면 잘린 변의 양쪽 면을 k 고리 벽으로 두껍게(끊긴 선이 있는 생성 메시용) 뒤 이웃으로 번짐.
작은 조각(전체 면적 × 작은비 미만)은 가장 길게 맞닿은 이웃에."""
import numpy as np, scipy.sparse as sp
from scipy.sparse.csgraph import connected_components


def 나누기(m, 문턱=30, k=0, 작은비=0.004, 오목만=True):
    adj = m.face_adjacency; ang = np.degrees(m.face_adjacency_angles); nF = len(m.faces); area = m.area_faces; tot = area.sum()
    FA = sp.coo_matrix((np.ones(len(adj)), (adj[:, 0], adj[:, 1])), shape=(nF, nF)).tocsr(); FA = FA + FA.T
    e = ang >= 문턱
    if 오목만: e &= ~m.face_adjacency_convex
    wall = np.zeros(nF, bool)
    if k > 0:
        wall[adj[e, 0]] = True; wall[adj[e, 1]] = True
        for _ in range(k - 1): wall = wall | (FA @ wall.astype(float) > 0)
    keep = ~e & ~wall[adj[:, 0]] & ~wall[adj[:, 1]]
    _, lab = connected_components(sp.coo_matrix((np.ones(keep.sum()), (adj[keep, 0], adj[keep, 1])), shape=(nF, nF)), directed=False)
    lab = lab.astype(np.int64); lab[wall] = -1
    for _ in range(400):
        if not (lab < 0).any(): break
        la, lb = lab[adj[:, 0]], lab[adj[:, 1]]; s1 = (la < 0) & (lb >= 0); lab[adj[s1, 0]] = lb[s1]; s2 = (lb < 0) & (la >= 0); lab[adj[s2, 1]] = la[s2]
    lab[lab < 0] = 0; _, lab = np.unique(lab, return_inverse=True)
    for _ in range(10):
        pa = np.bincount(lab, weights=area); small = pa < 작은비 * tot
        if not small[lab].any(): break
        a, b = lab[adj[:, 0]], lab[adj[:, 1]]; cr = a != b
        w = sp.coo_matrix((np.ones(cr.sum()), (a[cr], b[cr])), shape=(lab.max() + 1,) * 2).tocsr(); w = w + w.T; tgt = np.arange(lab.max() + 1)
        for s_ in np.nonzero(small)[0]:
            row = w.getrow(s_)
            if row.nnz: tgt[s_] = row.indices[np.argmax(row.data)]
        for _ in range(6): tgt = tgt[tgt]
        _, lab = np.unique(tgt[lab], return_inverse=True)
    cut = np.zeros(nF, bool); cut[adj[e, 0]] = True; cut[adj[e, 1]] = True
    return lab, cut


def 채점(lab, gt, area, 최소비=0.005):
    """정답 부품마다 가장 많이 겹친 조각과의 면적 IoU. 덮인(안 보이는) 부품은 뺀다(보이는 면적 < 전체 × 최소비)."""
    tot = area.sum(); G = [g for g in np.unique(gt) if area[gt == g].sum() >= 최소비 * tot]
    iou = {}; 쪼갬 = 0
    for g in G:
        gm = gt == g; ov = np.bincount(lab[gm], weights=area[gm], minlength=lab.max() + 1); s = int(np.argmax(ov))
        iou[int(g)] = float(ov[s] / (area[gm].sum() + area[lab == s].sum() - ov[s]))
        if (ov > 0.2 * area[gm].sum()).sum() >= 2: 쪼갬 += 1
    뭉침 = 0
    for s in np.unique(lab):
        sm = lab == s; ov = np.bincount(gt[sm], weights=area[sm])
        if (ov > 0.2 * area[sm].sum()).sum() >= 2: 뭉침 += 1
    return {"정답부품": len(G), "조각": int(len(np.unique(lab))), "평균IoU": round(float(np.mean(list(iou.values()))), 3), "쪼갬": 쪼갬, "뭉침": 뭉침, "부품별": iou}


if __name__ == "__main__":   # 자체 검사: 상자 둘을 붙인 합집합 → 문턱 30 이면 조각 ≥ 2 이고 정답 IoU 높음
    import trimesh
    a = trimesh.creation.box((2, 2, 2)); b = trimesh.creation.box((1, 1, 1)); b.apply_translation((0, 0, 1.5))
    u = trimesh.boolean.union([a, b], engine="manifold"); gt = (u.triangles_center[:, 2] > 1.0001).astype(int)
    lab, _ = 나누기(u, 30, 0, 0.0)   # 오목 변 = 작은 상자 밑 둘레
    r = 채점(lab, gt, u.area_faces); assert r["조각"] == 2 and r["평균IoU"] > 0.95, r; print("ok", {k: v for k, v in r.items() if k != "부품별"})
