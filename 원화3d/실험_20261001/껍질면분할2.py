# -*- coding: utf-8 -*-
"""껍질 면분할 다시 — 영역 키우기 (10-02 사용자 「그러면 다시 분할해」).
1 판(껍질면분할.py · 이웃 삼각형 사이 각 ≥ 10° 에서 자름)이 실패한 까닭: 칸 사이 꺾임은 17~31°(중앙값)인데 몇 화소에 걸쳐 둥글게 퍼져
삼각형 하나하나 사이 각은 2~3° → 못 자르고 큰 면 하나로 뭉침.
2 판: 면 법선을 2 고리 이웃 평균으로 다듬고 → 씨앗(가장 평평한 곳)에서 이웃 면을 붙여 나가되 「지금 영역 평균 법선」과 τ 이상 벌어지면 안 붙임(꺾임이 퍼져도 쌓이면 끊김)
   A = 3D 모양만 · B = A + 그 장의 먹선 칸 경계를 벽으로(같은 그림이라 위치를 믿는다 · 3D 로 평평한 경계 10~28 % 보충)
   작은 조각(전체 넓이 × 0.004 미만)은 가장 길게 맞닿은 이웃에.
잰다: 먹선 칸과 겹침(면분할.채점 · 칸은 정답 아님) + 눈으로 시트.
출력 out/오메가몬2/지표/각도데이터/면2A_<n>.ply · 면2B_<n>.ply · 면분할2.json"""
import os, sys, json, heapq, numpy as np, trimesh, scipy.sparse as sp
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "오메가몬", "지표")); from 면분할 import 채점
O = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; 타우 = 14.0; 작은비 = 0.004

def 키우기(m, 벽=None, tau=타우):
    nF = len(m.faces); adj = m.face_adjacency; A = sp.coo_matrix((np.ones(len(adj)), (adj[:, 0], adj[:, 1])), shape=(nF, nF)).tocsr(); A = (A + A.T).tocsr()
    if 벽 is not None:   # 벽 = 칸이 다른 이웃 면 쌍은 끊는다
        a, b = A.nonzero(); keep = 벽[a] == 벽[b]; A = sp.coo_matrix((np.ones(keep.sum()), (a[keep], b[keep])), shape=(nF, nF)).tocsr()
    n = m.face_normals.copy(); S = A + sp.eye(nF)
    for _ in range(2): n = S @ n; n /= np.linalg.norm(n, axis=1, keepdims=True)          # 2 고리 평균(계단 잡음 제거)
    curv = np.asarray(np.abs(S @ n - n * np.asarray(S.sum(1))).sum(1)).ravel()           # 평평한 곳 = 씨앗 먼저
    lab = -np.ones(nF, int); cos_t = np.cos(np.radians(tau)); area = m.area_faces; k = 0
    for s in np.argsort(curv):
        if lab[s] >= 0: continue
        lab[s] = k; sumn = n[s] * area[s]; stack = [s]
        while stack:
            f = stack.pop(); mean = sumn / np.linalg.norm(sumn)
            for g in A.indices[A.indptr[f]:A.indptr[f + 1]]:
                if lab[g] < 0 and n[g] @ mean >= cos_t: lab[g] = k; sumn = sumn + n[g] * area[g]; stack.append(g)
        k += 1
    # 작은 조각 → 가장 길게 맞닿은 이웃
    tot = area.sum()
    for _ in range(10):
        pa = np.bincount(lab, weights=area); small = pa < 작은비 * tot
        if not small[lab].any(): break
        a, b = lab[adj[:, 0]], lab[adj[:, 1]]; cr = a != b; w = sp.coo_matrix((np.ones(cr.sum()), (a[cr], b[cr])), shape=(lab.max() + 1,) * 2).tocsr(); w = w + w.T
        tgt = np.arange(lab.max() + 1)
        for q in np.nonzero(small)[0]:
            row = w.getrow(q)
            if row.nnz: tgt[q] = row.indices[np.argmax(row.data)]
        for _ in range(8): tgt = tgt[tgt]
        _, lab = np.unique(tgt[lab], return_inverse=True)
    return lab

def 저장(m, lab, path, seed=7):
    pal = np.random.RandomState(seed).randint(60, 240, (lab.max() + 1, 3)); fc = np.c_[pal[lab], np.full(len(lab), 255)].astype(np.uint8)
    c = trimesh.Trimesh(m.vertices[m.faces].reshape(-1, 3), np.arange(3 * len(m.faces)).reshape(-1, 3), process=False); c.visual.vertex_colors = np.repeat(fc, 3, axis=0); c.export(path)

if __name__ == "__main__":
    결과 = {}
    for n in "123456":
        m = trimesh.load(os.path.join(O, f"판_{n}.ply"), process=False)
        z = np.load(os.path.join(O, f"{n}.npz")); L = z["라벨"]; ys, xs = np.nonzero(L > 0); y0, x0 = ys.min(), xs.min()
        mm = np.load(os.path.join(O, f"판_{n}_Z.npz"))["m"]; py, px = np.nonzero(mm); 칸 = L[np.clip(y0 + 2 * py, 0, L.shape[0] - 1), np.clip(x0 + 2 * px, 0, L.shape[1] - 1)]
        gt = 칸[m.faces[:, 0]]; r = {}
        for 판, 벽 in (("A", None), ("B", gt)):
            lab = 키우기(m, 벽); 저장(m, lab, os.path.join(O, f"면2{판}_{n}.ply")); s = 채점(lab, gt, m.area_faces)
            r[판] = {"면": int(lab.max() + 1), "칸과 겹침": s["평균IoU"], "쪼갬": s["쪼갬"], "뭉침": s["뭉침"]}
        결과[n] = {"먹선 칸": int(L.max()), **r}; print(n, 결과[n])
    json.dump(결과, open(os.path.join(O, "면분할2.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
