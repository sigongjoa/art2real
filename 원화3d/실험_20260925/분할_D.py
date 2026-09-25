# -*- coding: utf-8 -*-
"""방식 D — Chopper 식 재귀 평면 절단(BSP) + 패널라인 · 대칭 비용 (2026-09-25).

    python 분할_D.py <판본>        (D1 D2 D3 · 가중은 아래 판본표)
  -> out/분할후보/D<n>_BSP.../lab.npy  ·  채점은 채점.py 로

몸 칸(106k)을 점 목록으로 두고, 부품 하나를 평면 하나로 둘로 자르는 걸 되풀이한다(빔 서치).
  후보 평면  법선: 세 축 + yz · xz · xy 평면 안 15° 간격 · 위치: 1 칸 간격(반 칸 어긋나게)
  비용       wa·절단면 넓이/V^(2/3)  (잘록한 곳)
           + wl·겉에 드러난 절단선 중 패널라인 밖 길이/V^(1/3)
           + wb·(1-4·fA·fB)        (끝만 얇게 깎기 벌점)
           - wv·V/전체              (큰 부품부터)
  대칭       부품이 제 거울과 겹치면(자기 대칭) 법선 x 성분 0 인 평면 또는 x=축i 평면만.
           거울 짝 부품이 있으면 거울 평면으로 짝도 같이 자른다. 둘 다 아니면(팔) 자유.
  자른 뒤    면 6 이웃 연결 조각으로 나누고, 0.3% 미만 조각은 가장 넓게 닿은 부품에 붙인다."""
import os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
from scipy import ndimage, sparse
from scipy.sparse import csgraph
sys.path[:0] = [r"G:\art2real\원화3d\실험_20260925"]
import 채점 as C

판본표 = {  # wa 넓이 · wl 선 밖 · wb 끝깎기 · wv 큰 부품 · 목표 부품 수 · 빔
    "D1": dict(wa=1.0, wl=0.5, wb=0.6, wv=4.0, 목표=30, 빔=4),
    "D2": dict(wa=0.5, wl=2.0, wb=0.6, wv=4.0, 목표=30, 빔=4),   # 패널라인을 더 무겁게
    "D3": dict(wa=1.5, wl=0.3, wb=0.3, wv=6.0, 목표=24, 빔=4),   # 잘록한 곳 · 적은 부품
}

O, a = C.O, C.축i
V = np.argwhere(O)                       # N×3 칸 좌표
N = len(V)
idx = -np.ones(O.shape, np.int64); idx[tuple(V.T)] = np.arange(N)
mj = np.round(2 * a - V[:, 0]).astype(int)
mi = np.where((mj >= 0) & (mj < O.shape[0]), idx[np.clip(mj, 0, O.shape[0] - 1), V[:, 1], V[:, 2]], -1)
겉 = (O & ~ndimage.binary_erosion(O))[tuple(V.T)]
# 채점과 같은 겉(깊이 첫·끝 칸) 위 패널라인
선 = {"front": C._열(C.I["선앞"], 1), "back": C._열(C.I["선뒤"], C.bs)}
for v in 선: 선[v] = ndimage.binary_dilation(선[v], iterations=2)
앞 = np.argmax(O, 1); 뒤 = O.shape[1] - 1 - np.argmax(O[:, ::-1], 1)
x, y, zz = V.T
선위 = ((y == 앞[x, zz]) & 선["front"][x, zz]) | ((y == 뒤[x, zz]) & 선["back"][x, zz])
최소조각 = int(0.003 * N)
E0, E1 = [], []
for ax in range(3):
    dv = np.zeros(3, int); dv[ax] = 1; W2 = V + dv; ok = W2[:, ax] < O.shape[ax]
    j = np.full(N, -1); j[ok] = idx[tuple(W2[ok].T)]; ok = j >= 0
    E0.append(np.nonzero(ok)[0]); E1.append(j[ok])
E0, E1 = np.concatenate(E0), np.concatenate(E1); 최소자름 = int(0.004 * N)


def _법선들():
    t = np.deg2rad(np.arange(0, 180, 15)); c, s = np.cos(t), np.sin(t); z0 = np.zeros_like(t)
    yz = np.stack([z0, s, c], 1); xz = np.stack([s, z0, c], 1); xy = np.stack([c, s, z0], 1)
    n = np.unique(np.round(np.concatenate([yz, xz, xy]), 6), axis=0)
    return n, n[np.abs(n[:, 0]) < 1e-6]


자유법선, 대칭법선 = _법선들()


def 후보(pts, 법선, w, 고정=None):
    """pts 칸 번호들을 자르는 평면 후보 → [(비용, n, d)] (비용 오름차순)."""
    P = V[pts].astype(np.float64); n0 = len(pts); 낼 = []
    su, sl = 겉[pts], 선위[pts]
    쌍 = [(n, None) for n in 법선] + ([고정] if 고정 is not None else [])
    for n, dd in 쌍:
        s = P @ n
        if dd is None:
            lo, hi = np.floor(s.min()) + 0.5, np.ceil(s.max()) - 0.5
            if hi <= lo: continue
            d = np.arange(lo, hi + 1e-9, 1.0)
        else:
            d = np.array([dd])
        so = np.sort(s); cA = np.searchsorted(so, d)
        area = np.searchsorted(so, d + 0.5) - np.searchsorted(so, d - 0.5)
        ss, sl_ = np.sort(s[su]), np.sort(s[su & ~sl])
        밖 = np.searchsorted(sl_, d + 0.5) - np.searchsorted(sl_, d - 0.5)
        fA = cA / n0; ok = (cA >= 최소자름) & (n0 - cA >= 최소자름)
        cost = w["wa"] * area / n0 ** (2 / 3) + w["wl"] * 밖 / n0 ** (1 / 3) + w["wb"] * (1 - 4 * fA * (1 - fA))
        for k in np.nonzero(ok)[0]: 낼.append((float(cost[k]), n, float(d[k])))
    낼.sort(key=lambda t: t[0]); return 낼


def 거울평면(n, d):
    return np.array([-n[0], n[1], n[2]]), d - 2 * a * n[0]


def 성질(L, p):
    """자기 대칭이면 ('자기',), 거울 짝이 있으면 ('짝', q), 아니면 ('자유',)."""
    pts = np.nonzero(L == p)[0]; m = mi[pts]; m = m[m >= 0]
    if len(m) == 0: return ("자유",)
    q = np.bincount(L[m])
    top = int(np.argmax(q)); 겹 = q[top]; 크q = (L == top).sum()
    iou = 겹 / (len(pts) + 크q - 겹)
    if iou < 0.5: return ("자유",)
    return ("자기",) if top == p else ("짝", top)


def 조각정리(L, 바뀐):
    """바뀐 부품들을 6 이웃 조각으로 나누고, 작은 조각은 가장 넓게 닿은 이웃 부품에 붙인다."""
    L = L.copy()
    같 = L[E0] == L[E1]
    k, cc = csgraph.connected_components(sparse.coo_matrix((np.ones(같.sum()), (E0[같], E1[같])), shape=(N, N)), directed=False)
    # 부품마다 가장 큰 조각은 제 번호 · 나머지는 새 번호
    크 = np.bincount(cc, minlength=k); 대표 = np.zeros(L.max() + 1, np.int64) - 1
    첫 = np.unique(cc, return_index=True)[1]; 부 = L[첫]
    순 = np.lexsort((-크, 부)); 새 = L.max() + 1; 번 = np.zeros(k, np.int64)
    앞부 = -1
    for c in 순:
        if 부[c] != 앞부: 번[c] = 부[c]; 앞부 = 부[c]
        else: 번[c] = 새; 새 += 1
    L = 번[cc]
    외톨 = set()
    while True:
        크 = np.bincount(L)
        작 = [p for p in np.nonzero((크 > 0) & (크 < 최소조각))[0] if p not in 외톨]
        if not 작: break
        p = 작[0]; a0, a1 = L[E0], L[E1]
        이웃 = np.concatenate([a1[(a0 == p) & (a1 != p)], a0[(a1 == p) & (a0 != p)]])
        if len(이웃) == 0: 외톨.add(p); continue
        L[L == p] = np.bincount(이웃).argmax()
    u, L2 = np.unique(L, return_inverse=True)
    return (L2 + 1).astype(np.int32)


def 펼치기(L, w, 넓이=3):
    """상태 하나에서 다음 수 후보들 → [(점수, 새 L, 설명)]."""
    수 = []
    for p in range(1, L.max() + 1):
        pts = np.nonzero(L == p)[0]
        if len(pts) < 2 * 최소자름: continue
        성 = 성질(L, p)
        if 성[0] == "자기":
            cs = 후보(pts, 대칭법선, w, 고정=(np.array([1.0, 0, 0]), a + 0.5))[:넓이]
            cs = [(c, n, d, None) for c, n, d in cs]
        elif 성[0] == "짝":
            q = 성[1]; qpts = np.nonzero(L == q)[0]; cs = []
            for c, n, d in 후보(pts, 자유법선, w)[:12]:
                n2, d2 = 거울평면(n, d); c2 = 후보(qpts, [], w, 고정=(n2, d2))
                if c2: cs.append((c + c2[0][0], n, d, (q, n2, d2)))
            cs.sort(key=lambda t: t[0]); cs = cs[:넓이]
        else:
            cs = [(c, n, d, None) for c, n, d in 후보(pts, 자유법선, w)[:넓이]]
        크 = len(pts) / N
        for c, n, d, 짝 in cs:
            수.append((c - w["wv"] * 크 * (2 if 짝 else 1), p, n, d, 짝))
    수.sort(key=lambda t: t[0])
    낼 = []
    for sc, p, n, d, 짝 in 수[:넓이 * 2]:
        L2 = L.copy(); 새 = L2.max() + 1
        pts = np.nonzero(L == p)[0]; L2[pts[V[pts] @ n >= d]] = 새; 바뀐 = [p, 새]
        if 짝:
            q, n2, d2 = 짝; qp = np.nonzero(L == q)[0]; L2[qp[V[qp] @ n2 >= d2]] = 새 + 1; 바뀐 += [q, 새 + 1]
        낼.append((sc, 조각정리(L2, 바뀐), "p%d n=(%.2f,%.2f,%.2f) d=%.1f%s" % (p, *n, d, " +짝" if 짝 else "")))
    return 낼


def 돌리기(이름, w):
    T0 = time.time()
    빔 = [(0.0, np.ones(N, np.int32), [])]
    while True:
        자식 = []
        for 누, L, 기록 in 빔:
            if L.max() >= w["목표"]: 자식.append((누, L, 기록)); continue
            for sc, L2, 설명 in 펼치기(L, w):
                if L2.max() > w["목표"] + 4: continue
                자식.append((누 + sc, L2, 기록 + [설명]))
        # 같은 결과 빼기
        본 = set(); 새빔 = []
        for t in sorted(자식, key=lambda t: t[0]):
            h = hash(t[1].tobytes())
            if h in 본: continue
            본.add(h); 새빔.append(t)
        빔 = 새빔[:w["빔"]]
        print("  [%4.0f s] 부품 %s · 누적 %.2f" % (time.time() - T0, [int(b[1].max()) for b in 빔], 빔[0][0]), flush=True)
        if all(b[1].max() >= w["목표"] for b in 빔): break
    누, L, 기록 = min(빔, key=lambda t: t[0])
    for s in 기록: print("   ", s)
    lab = np.zeros(O.shape, np.int32); lab[tuple(V.T)] = L
    D = os.path.join(C.D, 이름); os.makedirs(D, exist_ok=True)
    np.save(os.path.join(D, "lab.npy"), lab)
    print("%s 부품 %d · %.0f s" % (이름, L.max(), time.time() - T0), flush=True)


if __name__ == "__main__":
    # 거울 평면 자가 확인: 거울 평면을 두 번 거울하면 제자리
    n, d = np.array([0.6, 0.0, 0.8]), 123.5; n2, d2 = 거울평면(*거울평면(n, d)); assert np.allclose(n, n2) and np.isclose(d, d2)
    for 판 in sys.argv[1:]:
        돌리기(판 + "_BSP", 판본표[판])
