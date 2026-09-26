# -*- coding: utf-8 -*-
"""manifold → 출력용 STL 메시 (디자인_머리어깨.py 에서 옮김 · 색분할.py 도 쓴다)."""
import numpy as np, trimesh
def A(*v): return np.array(v, float)

def 부채나누기(m, 양=0.03):
    """manifold 메시 → 출력용 trimesh: 정점마다 면 부채(모서리로 이어진 면 무리)가 둘 이상이면 부채별로 정점을 복제하고,
    복제된 정점과 같은 자리에 겹친 정점을 제 면들의 무게중심 쪽·안쪽으로 양 만큼 밀어 STL 병합 뒤에도 2-manifold 가 되게 한다."""
    t = m.to_mesh(); V = np.asarray(t.vert_properties)[:, :3].astype(np.float64).copy(); F = np.asarray(t.tri_verts).astype(np.int64).copy()
    nV = len(V); inc = [[] for _ in range(nV)]
    for fi in range(len(F)):
        for k in range(3): inc[F[fi, k]].append(fi)
    moved = np.zeros(nV, bool); addV = []; addM = []
    for v in range(nV):
        fs = inc[v]
        if len(fs) < 2: continue
        parent = {fi: fi for fi in fs}
        def find(x):
            while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
            return x
        by_nb = {}
        for fi in fs:
            for w in F[fi]:
                if w != v: by_nb.setdefault(w, []).append(fi)
        for lst in by_nb.values():
            for fi in lst[1:]: parent[find(fi)] = find(lst[0])
        groups = {}
        for fi in fs: groups.setdefault(find(fi), []).append(fi)
        if len(groups) <= 1: continue
        moved[v] = True
        for gi, (_, lst) in enumerate(groups.items()):
            if gi == 0: continue
            nv = nV + len(addV); addV.append(V[v].copy()); addM.append(True)
            for fi in lst: F[fi][F[fi] == v] = nv
    if addV: V = np.vstack([V, np.array(addV)]); moved = np.concatenate([moved, np.array(addM)])
    key = np.round(V / 1e-4).astype(np.int64); _, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
    dup = (cnt[inv.ravel()] > 1) | moved
    tm = trimesh.Trimesh(V, F, process=False)
    VN = np.zeros_like(V); np.add.at(VN, F.ravel(), np.repeat(tm.face_normals, 3, 0)); VN /= np.linalg.norm(VN, axis=1, keepdims=True) + 1e-12
    FC = np.zeros_like(V); np.add.at(FC, F.ravel(), np.repeat(tm.triangles_center, 3, 0))
    FC = FC / np.maximum(np.bincount(F.ravel(), minlength=len(V)), 1)[:, None] - V; FC /= np.linalg.norm(FC, axis=1, keepdims=True) + 1e-12
    V2 = V.copy(); V2[dup] += 양 * (FC[dup] - VN[dup])
    order = np.argsort(inv.ravel(), kind="stable"); rank = np.zeros(len(V), int); seen = {}
    for i in order:
        g = int(inv.ravel()[i]); rank[i] = seen.get(g, 0); seen[g] = rank[i] + 1
    tang = np.cross(VN, A(0.3, 0.5, 0.8)); tang /= np.linalg.norm(tang, axis=1, keepdims=True) + 1e-12
    V2[dup] += (0.5 * 양 * rank[dup])[:, None] * tang[dup]        # 무리 안 k 번째는 접선으로 k·양/2 더
    return trimesh.Trimesh(V2, F, process=False)
