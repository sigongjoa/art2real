# -*- coding: utf-8 -*-
"""B — 겉면 위 닫힌 고리로 가르기 (Easy Mesh Cutting · 선 스냅 계열, 2026-09-25).

    python 분할_B.py B1 [B2 ...]

  1 몸.ply 정점에 앞 · 뒤 패널라인을 정사영 (앞 판은 앞에서 보이는 정점만, 옆면은 비움)
  2 2D 선 뼈대의 끝점마다 메시 모서리 그래프 Dijkstra 로 다른 선까지 잇는다
     비용 = 길이 × (1 + 2·평평함) + 축에서 벗어난 성분 (수평/수직 이음 선호) · 옆면을 돌아 뒷선과 만난다
  3 선 + 이음 = 벽 → 벽 아닌 정점의 연결 성분 = 부품 겉 · 작은 겉은 가장 길게 닿은 이웃에
  4 부피 칸 = 가장 가까운 겉 정점의 부품 → 맞닿은 짝마다 겉 경계 고리에 평면을 맞춰 그 평면으로 다시 가름
  5 대칭 구역(다리 전체 · 몸통 |dx|≤20, 팔 · 무기 제외)은 왼쪽을 거울로 복사 → out/분할후보/<이름>/lab.npy
판본: B1 선만 · B2 선 + 색 경계 · B3 B1 에 합치기 문턱 올림"""
import os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np, trimesh
from scipy import ndimage, sparse
from scipy.sparse import csgraph
from scipy.spatial import cKDTree
from skimage.morphology import skeletonize

sys.path[:0] = [r"G:\art2real\원화3d"]
import win as W

T0 = time.time()
def 찍(s): print("  [%4.0f s] %s" % (time.time() - T0, s), flush=True)

D = r"G:\art2real\원화3d\out\분할후보"
I = np.load(os.path.join(D, "입력.npz"))
O, ux, uy, z, 축i, bs = I["O"], I["ux"], I["uy"], I["z"], float(I["축i"]), float(I["bs"])
d = ux[1] - ux[0]
PX = W.RES / (W.U1 - W.U0) * d          # 격자 한 칸 = 5.3 px


def 판좌표(V, sign):
    col = (sign * V[:, 0] - W.U0) / (W.U1 - W.U0) * W.RES - 0.5
    row = (W.Z1 - V[:, 2]) / (W.Z1 - W.Z0) * W.RES - 0.5
    return np.stack([row, col], 1)


def 색경계(색):
    """원화 색을 8 단계로 묶어 바뀌는 자리 — B2 에서 선에 더한다. 흰/회색 음영 차이는 무시(채도 낮은 건 한 무리)."""
    c = np.asarray(색, np.float32); mx, mn = c.max(-1), c.min(-1)
    hue = np.round(np.arctan2(np.sqrt(3) * (c[..., 1] - c[..., 2]), 2 * c[..., 0] - c[..., 1] - c[..., 2]) / (np.pi / 4)) % 8
    q = np.where(mx - mn < 0.18, np.where(mx < 0.35, 9, 8), hue).astype(int)   # 8 = 흰·회 · 9 = 검정
    q = ndimage.median_filter(q, 7)
    e = np.zeros(q.shape, bool)
    e[1:] |= q[1:] != q[:-1]; e[:, 1:] |= q[:, 1:] != q[:, :-1]
    return skeletonize(ndimage.binary_dilation(e) & (mx > 0.02))


def 끝점(선):
    """2D 뼈대 끝점과 끝에서 안쪽으로 8 px 뒤 점 → (끝, 방향[row, col])."""
    sk = skeletonize(선)
    nb = ndimage.convolve(sk.astype(int), np.ones((3, 3), int), mode="constant") - 1
    낼 = []
    for r, c in np.argwhere(sk & (nb == 1)):
        p, prev = (r, c), None; 길 = [p]
        for _ in range(8):
            r0, c0 = p; nxt = None
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    q = (r0 + dr, c0 + dc)
                    if q != p and q != prev and 0 <= q[0] < sk.shape[0] and 0 <= q[1] < sk.shape[1] and sk[q] and q not in 길:
                        nxt = q; break
                if nxt: break
            if nxt is None: break
            prev, p = p, nxt; 길.append(p)
        if len(길) >= 4:
            v = np.array([r, c], float) - np.array(길[-1], float); 낼.append(((r, c), v / np.linalg.norm(v)))
    return 낼


def main(이름):
    색도 = 이름 == "B2"; 합문 = 0.012 if 이름 == "B3" else 0.006
    M = trimesh.load(os.path.join(D, "몸.ply"), process=False)
    V, Fc, N = np.asarray(M.vertices), np.asarray(M.faces), np.asarray(M.vertex_normals)
    gi = (V - [ux[0], uy[0], z[0]]) / d
    ix = np.clip(np.round(gi[:, 0]).astype(int), 0, 191); iz = np.clip(np.round(gi[:, 2]).astype(int), 0, 191)
    has = O.any(1); 앞 = np.where(has, O.shape[1] - 1 - np.argmax(O[:, ::-1], 1), -1); 뒤 = np.where(has, np.argmax(O, 1), 999)
    # +y 가 앞 (공통입력: 앞 판 = +y 쪽 겉)
    보 = {"front": (N[:, 1] > 0.15) & (gi[:, 1] >= 앞[ix, iz] - 2.0), "back": (N[:, 1] < -0.15) & (gi[:, 1] <= 뒤[ix, iz] + 2.0)}
    선판 = {"front": I["선앞"].copy(), "back": I["선뒤"].copy()}
    if 색도:
        선판["front"] |= 색경계(I["색앞"]); 선판["back"] |= 색경계(I["색뒤"])
    sign = {"front": 1.0, "back": bs}
    # 테두리(실루엣 1.3 칸 안쪽 띠)의 선은 지운다 — 외곽선이 앞 가장자리를 막아 T 자로 끝나면 옆면을 돌 끝점이 안 생긴다
    rr, cc = np.mgrid[0:W.RES, 0:W.RES]; 실거 = {}
    for v in 선판:
        xg = ((sign[v] * ((cc + 0.5) / W.RES * (W.U1 - W.U0) + W.U0)) - ux[0]) / d
        zg = ((W.Z1 - (rr + 0.5) / W.RES * (W.Z1 - W.Z0)) - z[0]) / d
        실 = ndimage.map_coordinates(has.astype(np.float32), [xg, zg], order=0, mode="constant") > 0
        선판[v] &= ndimage.binary_erosion(실, iterations=int(1.3 * PX)); 실거[v] = ndimage.distance_transform_edt(실)
    E = np.asarray(M.edges_unique); nV = len(V)
    u, v2 = np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]]
    선id = np.full(nV, -1); 끊 = np.zeros(len(E), bool); 끝들 = []; off = 0
    for v in ("front", "back"):
        sk = skeletonize(선판[v]); lc, nl = ndimage.label(sk, np.ones((3, 3)))
        거, (ri, ci) = ndimage.distance_transform_edt(~sk, return_indices=True)
        rc = 판좌표(V, sign[v]); r0 = np.clip(np.round(rc[:, 0]).astype(int), 0, W.RES - 1); c0 = np.clip(np.round(rc[:, 1]).astype(int), 0, W.RES - 1)
        tag = 보[v] & (거[r0, c0] < 0.6 * PX)
        선id[tag] = off + lc[ri[r0, c0], ci[r0, c0]][tag]
        # 선을 가로지르는 모서리를 끊는다 (두 끝이 이 판에서 보일 때 · 모서리를 10 점으로 훑음)
        굵 = ndimage.binary_dilation(sk)
        ev = 보[v][E[:, 0]] & 보[v][E[:, 1]]
        for t in np.linspace(0, 1, 10):
            p = rc[E[ev, 0]] * (1 - t) + rc[E[ev, 1]] * t
            끊[np.nonzero(ev)[0]] |= ndimage.map_coordinates(굵.astype(np.float32), p.T, order=0, mode="constant") > 0
        idx = np.nonzero(보[v])[0]; tr = cKDTree(rc[idx])
        for (r, c), dv in 끝점(선판[v]):
            dd, j = tr.query([r, c])
            if dd < 0.8 * PX:
                # 판 방향(row, col) → 메시 방향(x, z): col 은 sign·x, row 는 -z
                끝들.append((idx[j], np.array([sign[v] * dv[1], 0, -dv[0]]), off + lc[r, c], v == "front", 실거[v][r, c] < 2.3 * PX))
        off += nl + 1
        if v == "front": 앞끝 = off
    표 = 선id >= 0
    찍("선 정점 %d · 끊은 모서리 %d · 끝점 %d" % (표.sum(), 끊.sum(), len(끝들)))

    dv3 = V[E[:, 1]] - V[E[:, 0]]; L = np.linalg.norm(dv3, axis=1)
    주름 = 1 - (N[E[:, 0]] * N[E[:, 1]]).sum(1)
    둘째 = np.sort(np.abs(dv3), 1)[:, 1]
    w = L * (1 + np.exp(-주름 / 0.05)) + 1.0 * 둘째 + 1e-9
    # 방향 그래프: 선 정점 → 선 정점 은 막는다 (이음은 선을 벗어나 빈 겉을 지나 다른 선에 닿아야)
    ww = np.r_[w, w]; k2 = ~(표[u] & 표[v2])
    G = sparse.coo_matrix((ww[k2], (u[k2], v2[k2])), shape=(nV, nV)).tocsr()
    섬 = np.zeros(nV, bool); 이음 = [0, 0]
    선앞쪽 = (선id >= 0) & (선id < 앞끝)
    for 테 in (False, True):          # 안쪽 끝점: 가까운 다른 선 · 테두리 끝점: 옆면을 돌아 반대 판의 선
        무리 = [e for e in 끝들 if e[4] == 테]; 한 = (90 if 테 else 40) * d
        for s0 in range(0, len(무리), 150):
            ch = [e[0] for e in 무리[s0:s0 + 150]]
            dist, pred = csgraph.dijkstra(G, indices=ch, limit=한, return_predecessors=True)
            for k, s in enumerate(ch):
                _, dvec, 제, 앞판, _ = 무리[s0 + k]
                cand = 표 & (선id != 제) & np.isfinite(dist[k])
                if 테: cand &= ~선앞쪽 if 앞판 else 선앞쪽
                cand = np.nonzero(cand)[0]
                if len(cand) == 0: continue
                t = V[cand] - V[s]; tn = np.linalg.norm(t, axis=1) + 1e-9
                cos = (t[:, 0] * dvec[0] + t[:, 2] * dvec[2]) / tn
                if 테: cos = np.maximum(cos, 0.3)
                ok = cos > 0.2
                if not ok.any(): continue
                sc = dist[k, cand] * (1 + 1.0 * (1 - cos)); sc[~ok] = np.inf
                p = pred[k, cand[np.argmin(sc)]]
                while p != s and p >= 0: 섬[p] = True; p = pred[k, p]
                섬[s] = True; 이음[테] += 1
    찍("이음 안 %d · 옆 돌기 %d" % tuple(이음))
    # 이음 정점은 섬으로 떼어 벽이 되게 · 선 모서리는 끊는다
    막 = np.r_[끊, 끊] | 섬[u] | 섬[v2]
    Afree = sparse.coo_matrix((np.ones((~막).sum()), (u[~막], v2[~막])), shape=(nV, nV)).tocsr()
    A = sparse.coo_matrix((np.ones(len(u)), (u, v2)), shape=(nV, nV)).tocsr()
    _, lab = csgraph.connected_components(Afree, directed=False)
    크0 = np.bincount(lab); lab = np.where(크0[lab] < 3, -1, lab)     # 떨어진 섬 정점
    if os.environ.get("B_DBG"):
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(16, 12))
        for a, sg in zip(ax, (1, -1)):
            o = np.argsort(sg * V[:, 1]); cl = np.where(lab[o] < 0, 0, 1 + lab[o] % 9)
            a.scatter(sg * V[o, 0], V[o, 2], c=cl, s=2, cmap="tab10", vmin=0, vmax=9); a.set_aspect("equal")
            m = 표[o]; a.scatter(sg * V[o][m, 0], V[o][m, 2], c="k", s=1)
            m = 섬[o]; a.scatter(sg * V[o][m, 0], V[o][m, 2], c="r", s=3)
            for e in 끝들:
                if (sg * V[e[0], 1] > 0): a.plot(sg * V[e[0], 0], V[e[0], 2], "g^", ms=3)
        fig.savefig(os.environ["B_DBG"], dpi=70, bbox_inches="tight")
        top = np.argsort(np.bincount(lab[lab >= 0]))[::-1][:8]; R = np.full(nV, -1)
        for i2, k in enumerate(top): R[lab == k] = i2
        fig, ax = plt.subplots(1, 4, figsize=(20, 8))
        for a, (i, j, ax2, sg) in zip(ax, ((0, 2, 1, 1), (0, 2, 1, -1), (1, 2, 0, 1), (1, 2, 0, -1))):
            o = np.argsort(sg * V[:, ax2]); a.scatter(V[o, i], V[o, j], c=np.where(R[o] >= 0, R[o], 9), s=2, cmap="tab10", vmin=0, vmax=9); a.set_aspect("equal")
        fig.savefig(os.environ["B_DBG"].replace(".png", "_허벅지.png"), dpi=60, bbox_inches="tight")
    for _ in range(30):
        m = lab < 0
        if not m.any(): break
        r, c = A[m].nonzero(); 후 = lab[c]; rows = np.nonzero(m)[0][r]
        ok = 후 >= 0; lab[rows[ok]] = 후[ok]
    _, lab = np.unique(lab, return_inverse=True)
    # 넓이 (정점 둘레 면 넓이 1/3)
    va = np.zeros(nV); np.add.at(va, Fc.ravel(), np.repeat(M.area_faces / 3, 3))
    찍("겉 조각 %d" % (lab.max() + 1))

    def 겉합치기(lab, 몫):
        외 = set()
        while True:
            ar = np.bincount(lab, va); 작 = [k for k in np.argsort(ar) if 0 < ar[k] < 몫 * va.sum() and k not in 외]
            if not 작: return np.unique(lab, return_inverse=True)[1]
            k = 작[0]; m = lab == k
            r, c = A[m].nonzero(); nb = lab[c]; nb = nb[nb != k]
            if len(nb) == 0: 외.add(k); continue   # 외딴 섬은 그대로 둔다
            lab[m] = np.bincount(nb).argmax()
    lab = 겉합치기(lab, 합문)
    찍("합친 겉 %d" % (lab.max() + 1))

    # 부피: 가장 가까운 겉 정점
    vox = np.argwhere(O); tr = cKDTree(gi)
    _, j = tr.query(vox, workers=2); vl = lab[j]
    # 맞닿은 짝마다 겉 경계 고리에 평면
    r, c = A.nonzero(); 다름 = lab[r] != lab[c]; r, c = r[다름], c[다름]
    짝 = {}
    for a, b, i in zip(lab[r], lab[c], r):
        짝.setdefault((min(a, b), max(a, b)), set()).add(i)
    순 = sorted(짝.items(), key=lambda kv: len(kv[1]))
    바꿈 = 0
    for (a, b), pts in 순:
        P = gi[list(pts)]
        if len(P) < 12: continue
        cc = P.mean(0); _, s, vt = np.linalg.svd(P - cc, full_matrices=False); n = vt[-1]
        if s[-1] / np.sqrt(len(P)) > 2.0: continue            # 고리가 평면이 아니면 두고 본다
        R = np.linalg.norm(P - cc, axis=1).max() + 1
        m = ((vl == a) | (vl == b)) & (np.linalg.norm(vox - cc, axis=1) < R) & (np.abs((vox - cc) @ n) < 0.5 * R)
        if m.sum() < 10: continue
        sd = (vox[m] - cc) @ n
        ma = vl[m] == a
        if ma.all() or (~ma).all(): continue
        a쪽 = np.sign(sd[ma].mean()) if abs(sd[ma].mean()) > 1e-6 else 1
        new = np.where(sd * a쪽 >= 0, a, b); 바꿈 += (new != vl[m]).sum(); vl[m] = new
    찍("평면 가르기 %d 칸 바뀜" % 바꿈)
    L3 = np.zeros(O.shape, np.int32); L3[tuple(vox.T)] = vl + 1

    # 대칭: 다리(z<88)는 |dx|≤36, 위는 |dx|≤20 — 구역 경계로 먼저 자르고 왼쪽을 거울로
    X = np.arange(192)[:, None, None]; Zk = np.arange(192)[None, None, :]
    dx = X - 축i
    구 = np.where(Zk < 88, np.abs(dx) <= 36, np.abs(dx) <= 20) & O
    L3 = np.where(O, L3 * 2 + 구, 0)
    L3 = 부피합치기(연결정리(L3, O), 0.004)          # 합치기를 거울보다 먼저 — 뒤에 하면 좌우가 또 어긋난다
    j = np.round(2 * 축i - np.arange(192)).astype(int)
    왼 = L3.copy()
    # 가운데를 넘는 부품(머리 · 가슴 · 허리)만 한 번호로 — 가랑이에 살짝 닿은 허벅지는 좌우 따로
    좌수 = np.bincount(L3[(dx < 0) & 구], minlength=L3.max() + 1); 우수 = np.bincount(L3[(dx > 0) & 구], minlength=L3.max() + 1)
    중앙 = set(np.nonzero(np.minimum(좌수, 우수) >= 0.2 * (좌수 + 우수 + 1))[0]) - {0}
    off = L3.max() + 1
    mir = np.zeros_like(L3); ok = (j >= 0) & (j < 192); mir[ok] = 왼[j[ok]]
    오른 = (dx > 0) & 구
    vals = mir[오른]; 표중 = np.isin(vals, list(중앙))
    vals = np.where((vals == 0) | 표중, vals, vals + off)
    L3[오른] = vals
    팔 = (dx > 0) & O & ~구; L3[팔] += 2 * off                 # 오른팔 번호가 왼쪽 번호와 겹치지 않게
    # 오른쪽 구역인데 거울 칸이 몸 밖 → 가까운 칸 번호
    빈 = O & (L3 == 0)
    if 빈.any():
        ii = ndimage.distance_transform_edt(~(L3 > 0), return_distances=False, return_indices=True)
        L3 = np.where(빈, L3[tuple(ii)], L3)
    # 오른쪽 구역 바깥(팔)에 남은 번호가 구역 안 번호와 겹치지 않게: 구역 밖 칸은 이미 *2+0 짝수, 구역 안은 홀수(+off 도 구분)
    # 부품마다 연결 성분 — 가장 큰 것만 두고 조각은 이웃에
    L3 = 부피합치기(연결정리(L3, O), 0.0015)        # 거울에서 생긴 부스러기만
    _, inv = np.unique(L3, return_inverse=True); L3 = inv.reshape(O.shape).astype(np.int32)
    os.makedirs(os.path.join(D, 이름), exist_ok=True)
    np.save(os.path.join(D, 이름, "lab.npy"), L3)
    찍("%s 부품 %d 저장" % (이름, L3.max()))


def 연결정리(L3, O):
    out = L3.copy(); st = ndimage.generate_binary_structure(3, 1)
    for k in np.unique(L3):
        if k == 0: continue
        m = L3 == k; cl, n = ndimage.label(m, st)
        if n > 1:
            big = np.bincount(cl.ravel())[1:].argmax() + 1
            out[m & (cl != big)] = 0
    빈 = O & (out == 0)
    ii = ndimage.distance_transform_edt(~(out > 0), return_distances=False, return_indices=True)
    return np.where(빈, out[tuple(ii)], out)


def 부피합치기(lab, 몫):
    lab = lab.copy(); 전 = (lab > 0).sum()
    while True:
        크 = np.bincount(lab.ravel()); 크[0] = 0
        작 = [k for k in np.argsort(크) if 0 < 크[k] < 몫 * 전]
        if not 작: return lab
        k = 작[0]; M = lab == k
        테 = ndimage.binary_dilation(M) & ~M & (lab > 0)
        if not 테.any(): lab[M] = 0; continue
        lab[M] = np.bincount(lab[테]).argmax()


if __name__ == "__main__":
    for 이름 in sys.argv[1:] or ["B1"]: main(이름)
