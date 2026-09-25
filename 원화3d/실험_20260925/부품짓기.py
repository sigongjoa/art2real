# -*- coding: utf-8 -*-
"""**부품짓기** — 분할 라벨을 실제 출력 부품 메시로 바꾼다 (2026-09-25).

    python 부품짓기.py [판본=A4] [틈=0.20]
      -> out/출력/오메가몬_<판본>키트/부품NN.stl (출력용 · 바닥에 눕힘) · _조립/부품NN.stl (조립 좌표) · 키트.json

  ① 짝마다 경계 면(칸 사이 면 중점)에 평면을 맞춘다. 한 평면으로 안 맞으면(L 자) 평면 여럿으로 나눈다.
  ② 부품 k = 몸 메시 ∩ D_k(라벨 k 를 3 칸 부풀린 영역 · 이웃 아닌 부품 칸은 뺀다) − 뒤 차례 이웃 j 쪽 반공간(이음면 근처만)
     − 앞 차례 부품들. **차례대로 빼므로 겹침은 0 이 정의상 보장**되고, 이음면은 반공간이 자른 평면 그대로다.
     L 자 짝은 「반공간 교집합」 쪽(볼록한 쪽)이 먼저 잘라야 오목한 쪽을 파먹지 않는다 → 차례 제약.
  ③ 짝마다 이음면 단면(manifold slice 둘의 교집합)의 2D 거리변환 최대 1~2 곳에 다보 — 핀(작은 부품) · 구멍(큰 부품).
     핀 둘레 벽 1mm · 구멍 바닥 벽 0.8mm 가 안 남으면 생략. 핀은 이음면 법선 방향.
좌표: 격자 색인 × 칸mm (등방 · 창 0.00625 단위). 조립 좌표 = 이 mm 좌표 그대로."""
import base64, graphlib, json, os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np, trimesh, manifold3d as M
from PIL import Image, ImageDraw
from scipy import ndimage
from skimage.measure import marching_cubes

D = r"G:\art2real\원화3d\out"
전고 = 125.0
핀r, 핀길이, 벽, 바닥벽 = 0.9, 2.5, 1.0, 0.8     # mm
부풀림, 이음근처, 인라이어 = 3, 4, 0.9             # 칸


def 만(v, f):
    m = M.Manifold(M.Mesh(vert_properties=np.asarray(v, np.float32), tri_verts=np.asarray(f, np.uint32)))
    assert m.status() == M.Error.NoError, m.status()
    return m if m.volume() > 0 else 만(v, np.asarray(f)[:, ::-1])


def 트(m):
    g = m.to_mesh(); return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False)


def 칸메시(mask, 칸):
    """bool 칸 영역 → 닫힌 메시 (mm). bbox 로 잘라 계산."""
    idx = np.argwhere(mask); lo = idx.min(0) - 1; hi = idx.max(0) + 2
    f = np.pad(mask[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]], 1).astype(np.float32)
    v, fc, _, _ = marching_cubes(f, 0.5)
    return 만((v - 1 + lo) * 칸, fc)


def 회전(n):
    """R @ n = +z."""
    n = n / np.linalg.norm(n); z = np.array([0, 0, 1.0]); v = np.cross(n, z); s = np.linalg.norm(v); c = n @ z
    if s < 1e-9: return np.eye(3) if c > 0 else np.diag([1, -1, -1.0])
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / s ** 2)


def 옮김(m, R, t):   # p -> R p + t
    return m.transform(np.c_[R, t])


def 평면틀(n, c):
    """평면 좌표 → 세계: p = Rᵀ q + c (q 의 z = 평면에서 n 방향 거리)."""
    R = 회전(n); return R.T, c


def 반공간(n, c, L=400.0):   # {p : n·(p−c) >= 0}
    Rt, c = 평면틀(n, c)
    return 옮김(M.Manifold.cube([2 * L, 2 * L, L]).translate([-L, -L, 0]), Rt, c)


def 상자겹침(a, b, e=0.5):
    a, b = np.asarray(a).reshape(2, 3) if np.size(a) == 6 else a, np.asarray(b).reshape(2, 3) if np.size(b) == 6 else b
    return bool(np.all(a[0] - e <= b[1]) and np.all(b[0] - e <= a[1]))


def 거리(s, P):
    """면까지 부호 거리 (색인 단위). 평면: n·(p−c) · 원통: 축에서 반지름 거리 − r (밖이 +)."""
    if s["종류"] == "평면": return (P - s["c"]) @ s["n"]
    q = P - s["c"]; return np.linalg.norm(q - np.outer(q @ s["a"], s["a"]), axis=1) - s["r"]


def 저쪽(s, 부, 칸, 틈):
    """부품 쪽에서 본 이웃 쪽 영역 (mm manifold). 부 = +1 이면 작은 번호 부품 기준."""
    σ = 부 * s["σ"]
    if s["종류"] == "평면": return 반공간(부 * s["n"], s["c"] * 칸)
    t0, t1 = s["t"]; R = 회전(s["a"]).T
    def 통(r): return 옮김(M.Manifold.cylinder((t1 - t0) * 칸, r, r, 96).translate([0, 0, t0 * 칸]), R, s["c"] * 칸)
    if σ < 0: return 통(s["r"] * 칸 + 틈)                  # 이웃이 원통 안 → 바깥 부품은 틈만큼 넓게 판다
    return M.Manifold.cube([1000, 1000, 1000], center=True) - 통(s["r"] * 칸)


def 일관(n, ax):
    """평면 법선이 칸 면 방향과 맞나 — 기운 평면의 계단은 면 축 몫이 |n| 몫과 같다.
    한 줄로 늘어선 면(일직선)은 SVD 가 엉뚱한 법선을 준다(A4 (3,18): z 면 21 개에 y 법선) — 그걸 거른다."""
    f = np.bincount(ax, minlength=3) / max(len(ax), 1); e = np.abs(n) / np.abs(n).sum()
    return np.abs(f - e).max() < 0.35


def 평면들(P, ax):
    """면 중점 P(색인) 을 평면 여럿으로 — 후보 = 남은 점 SVD · 축 평면(면 축의 좌표 최빈값). 인라이어 최대부터."""
    남 = np.ones(len(P), bool); 낼 = []
    while 남.sum() >= max(3, 0.05 * len(P)) or (not 낼 and 남.any()):
        Q = P[남]; 후 = []
        if len(Q) >= 3:
            c = Q.mean(0); 후.append((np.linalg.svd(Q - c, full_matrices=False)[2][-1], c))
        for a in np.unique(ax[남]):
            vals, cnt = np.unique(P[남 & (ax == a), a], return_counts=True)
            n = np.zeros(3); n[a] = 1; c = Q.mean(0).copy(); c[a] = vals[cnt.argmax()]; 후.append((n, c))
        최 = None
        for n, c in 후[::-1]:                       # 축 평면이 먼저 (같은 수면 축 평면)
            for _ in range(3):   # 인라이어로 다시 맞추기 (축 평면은 축 유지)
                inl = 남 & (np.abs((P - c) @ n) < 인라이어)
                if inl.sum() < 3 or np.count_nonzero(np.abs(n) > 0.999): break
                c = P[inl].mean(0); n = np.linalg.svd(P[inl] - c, full_matrices=False)[2][-1]
            inl = 남 & (np.abs((P - c) @ n) < 인라이어)
            if not 일관(n, ax[inl]): continue
            if 최 is None or inl.sum() > 최[2].sum(): 최 = (n / np.linalg.norm(n), c, inl)
        if 최 is None: break
        if 최[2].sum() == 0: break
        낼.append(최); 남 &= ~최[2]
    return 낼, 남.sum()


def 단면(m, Rt, c, z):
    """부품 m 을 평면틀로 옮겨 높이 z 에서 자른 CrossSection."""
    return 옮김(m, Rt.T, -Rt.T @ c).slice(z)


def 래스터(cs, 해=0.1):
    polys = cs.to_polygons()
    if not polys: return None
    allp = np.concatenate(polys); lo = allp.min(0) - 1; hi = allp.max(0) + 1
    W, H = np.ceil((hi - lo) / 해).astype(int) + 1
    acc = np.zeros((H, W), bool)
    for p in polys:
        im = Image.new("1", (W, H)); ImageDraw.Draw(im).polygon([tuple(x) for x in (p - lo) / 해], fill=1)
        acc ^= np.array(im)
    return acc, lo, 해


def 두께(tm, n=1500):
    """겉에서 안쪽 광선 → 다음 면까지 (벽 두께). 1 분위 · 0.8mm 미만 면적 몫."""
    pts, fid = tm.sample(n, return_index=True); nrm = tm.face_normals[fid]; e = 1e-3
    loc, ray, _ = tm.ray.intersects_location(pts - nrm * e, -nrm, multiple_hits=False)
    if len(ray) < 20: return None, None
    d = np.linalg.norm(loc - (pts - nrm * e)[ray], axis=1) + e
    return float(np.quantile(d, 0.01)), float(np.mean(d < 0.8))


def main():
    판 = sys.argv[1] if len(sys.argv) > 1 else "A4"
    틈 = float(sys.argv[2]) if len(sys.argv) > 2 else 0.20
    t0 = time.time()
    I = np.load(os.path.join(D, "분할후보", "입력.npz")); g = I["g"]
    lab = np.load(os.path.join(D, "분할후보", 판, "lab.npy")).astype(np.int32); n = int(lab.max()); N = lab.shape[0]

    # ── 몸: 연속 장 0 등위면 · 떠 있는 부스러기는 버린다
    v, f, _, _ = marching_cubes(np.pad(g, 2, constant_values=float(g.min())), 0.0); v -= 2
    칸 = 전고 / float(np.ptp(v[:, 2]))
    몸0 = 만(v * 칸, f); 조 = sorted(몸0.decompose(), key=lambda m: -m.volume())
    몸 = M.Manifold.batch_boolean([m for m in 조 if m.volume() > 1.0], M.OpType.Add)
    print("칸 %.3f mm · 몸 %.1f cm³ · 부스러기 %d 개 %.2f mm³ 버림" % (칸, 몸.volume() / 1000, sum(m.volume() <= 1 for m in 조),
          sum(m.volume() for m in 조 if m.volume() <= 1)), flush=True)

    # ── 짝과 평면
    면 = {}
    for a in range(3):
        a0 = np.take(lab, range(N - 1), axis=a); a1 = np.take(lab, range(1, N), axis=a)
        s = (a0 != a1) & (a0 > 0) & (a1 > 0); idx = np.argwhere(s)
        for p, x, y in zip(idx, a0[s], a1[s]):
            k, j = (x, y) if x < y else (y, x); lo_is_k = x < y
            면.setdefault((int(k), int(j)), []).append((*p, a, 1 if lo_is_k else -1))   # 부호: k 칸이 낮은 쪽이면 +1
    # 분할 에이전트의 평면.json 이 있으면 그 면(칸 >= 10 줄만 · 평면 또는 소켓 원통)을 쓰고, 인라이어는 거리로 다시 가른다.
    # 받은 면에 안 붙는 점(원통 짝의 마개 면 등)과 json 이 없는 짝은 직접 평면을 맞춘다.
    jf = os.path.join(D, "분할후보", 판, "평면.json"); 받은 = {}
    if os.path.exists(jf):
        for x in json.load(open(jf, encoding="utf-8")):
            if x["칸"] < 10: continue
            if "원통" in x:
                o = x["원통"]; a_ = np.array(o["축"], float)
                s = {"종류": "원통", "c": np.array(o["점"], float), "a": a_ / np.linalg.norm(a_), "r": float(o["반지름"]), "t": tuple(o["t"])}
            else:
                nn = np.array(x["법선"], float); s = {"종류": "평면", "n": nn / np.linalg.norm(nn), "c": np.array(x["점"], float)}
            받은.setdefault(tuple(sorted(x["짝"])), []).append(s)
    짝 = {}
    for (k, j), rows in 면.items():
        R_ = np.array(rows); P = R_[:, :3].astype(float); ax = R_[:, 3]; P[np.arange(len(P)), ax] += 0.5
        kc = P.copy(); kc[np.arange(len(P)), ax] -= 0.5 * R_[:, 4]          # k 칸 중심
        ss = [dict(s) for s in 받은.get((k, j), [])]
        if ss:
            d = np.stack([np.abs(거리(s, P)) for s in ss], 1); 가 = d.argmin(1)
            for i, s in enumerate(ss): s["inl"] = (가 == i) & (d.min(1) < 인라이어 + 0.3)
            ss = [s for s in ss if s["inl"].any() and (s["종류"] != "평면" or 일관(s["n"], ax[s["inl"]]))]
        남점 = ~np.logical_or.reduce([s["inl"] for s in ss]) if ss else np.ones(len(P), bool)
        if 남점.sum() >= (max(10, 0.05 * len(P)) if ss else 1):
            ps, _ = 평면들(P[남점], ax[남점]); w = np.nonzero(남점)[0]
            for nn, c, inl in ps:
                full = np.zeros(len(P), bool); full[w[inl]] = True; ss.append({"종류": "평면", "n": nn, "c": c, "inl": full})
        for s in ss:   # 거의 축인 평면은 축으로 · 칸 경계(반 정수)로 붙인다 — 같은 컷이 짝마다 0.1° 씩 달리 맞춰지면
            if s["종류"] == "평면" and np.abs(s["n"]).max() > 0.995:   # 짝 사이에 얇은 쐐기 틈이 생긴다 (E13 머리·가슴·어깨 사이 123 mm³)
                a_ = int(np.abs(s["n"]).argmax()); n_ = np.zeros(3); n_[a_] = np.sign(s["n"][a_]); s["n"] = n_
                s["c"] = s["c"].copy(); s["c"][a_] = np.floor(s["c"][a_]) + 0.5
        for s in ss:   # 부호: k 칸 쪽이 음수가 되게 (σ·거리 < 0 이 k)
            i_ = s["inl"]; s["σ"] = -1.0 if np.sum(거리(s, kc[i_]) - 거리(s, P[i_])) > 0 else 1.0   # 면 → k 칸 방향만 본다 (면 자리 잡음은 뺀다)
            if s["종류"] == "평면": s["n"] = s["σ"] * s["n"]; s["σ"] = 1.0
            s["rms"] = float(np.sqrt(np.mean(거리(s, P[s["inl"]]) ** 2)))
        버 = int(len(P) - sum(s["inl"].sum() for s in ss))
        짝[(k, j)] = {"P": P, "ax": ax, "kc": kc, "평면": ss, "버림": 버}
    이웃 = {k: set() for k in range(1, n + 1)}
    for k, j in 짝: 이웃[k].add(j); 이웃[j].add(k)

    # ── 이음 근처 N (칸 · bbox 안에서만 거리변환) · 차례 제약
    def 근처(P, inl):
        m = np.zeros(lab.shape, bool)
        for d in (0, 1):   # 면 양쪽 칸
            qq = np.clip(np.floor(P[inl] - 0.5 + d).astype(int), 0, N - 1); m[tuple(qq.T)] = True
        idx = np.argwhere(m); lo = np.maximum(idx.min(0) - 이음근처 - 1, 0); hi = np.minimum(idx.max(0) + 이음근처 + 2, N)
        sl = tuple(slice(l, h) for l, h in zip(lo, hi)); o = np.zeros_like(m)
        o[sl] = ndimage.distance_transform_edt(~m[sl]) <= 이음근처; return o
    제약 = {k: set() for k in range(1, n + 1)}
    for (k, j), s in 짝.items():
        for p in s["평면"]: p["N"] = 근처(s["P"], p["inl"])
        if len(s["평면"]) < 2: continue
        U = np.logical_or.reduce([p["N"] for p in s["평면"]]) & ((lab == k) | (lab == j))
        q = np.argwhere(U) + 0.5; isk = lab[U] == k
        S = np.stack([p["σ"] * 거리(p, q) < 0 for p in s["평면"]], 1)   # k 쪽
        교, 합 = np.mean(S.all(1) == isk), np.mean(S.any(1) == isk)
        먼저, 뒤 = (k, j) if 교 >= 합 else (j, k)
        제약[뒤].add(먼저); s["볼록"] = 먼저
        print("  꺾인 짝 %s: 면 %s · 교집합 %.3f 합집합 %.3f → %d 가 먼저" % ((k, j), [p["종류"] for p in s["평면"]], 교, 합, 먼저), flush=True)
    print("면 · 차례 %.0fs" % (time.time() - t0), flush=True)
    차례 = list(graphlib.TopologicalSorter(제약).static_order()); 몇째 = {k: i for i, k in enumerate(차례)}

    # ── 부품 짓기 (차례대로 · 앞 부품을 뺀다 → 겹침 0)
    _부 = {}
    def 부풂(j, r):
        if (j, r) not in _부:
            idx = np.argwhere(lab == j); lo = np.maximum(idx.min(0) - r - 1, 0); hi = np.minimum(idx.max(0) + r + 2, N)
            sl = tuple(slice(l, h) for l, h in zip(lo, hi)); o = np.zeros(lab.shape, bool)
            o[sl] = ndimage.distance_transform_edt(lab[sl] != j) <= r; _부[(j, r)] = o
        return _부[(j, r)]
    부품 = {}; 살핌 = int(os.environ.get("DBG", "0"))      # DBG=라벨 이면 그 부품의 자름을 하나씩 찍는다
    for k in 차례:
        idx = np.argwhere(lab == k); lo = np.maximum(idx.min(0) - 부풀림 - 1, 0); hi = np.minimum(idx.max(0) + 부풀림 + 2, N)
        sl = tuple(slice(l, h) for l, h in zip(lo, hi)); Dk = np.zeros(lab.shape, bool)
        Dk[sl] = ndimage.distance_transform_edt(lab[sl] != k) <= 부풀림
        Dk &= ~((lab > 0) & ~np.isin(lab, list(이웃[k] | {k})))
        R = 몸 ^ 칸메시(Dk, 칸)
        자름 = []
        for j in 이웃[k]:
            s = 짝[(min(k, j), max(k, j))]; 부 = 1.0 if k < j else -1.0   # 면 부호는 작은 번호 기준
            if s.get("볼록", k) != k: continue      # 꺾인 짝의 오목한 쪽은 자르지 않고 볼록한 쪽(먼저 지은 것)을 빼기만 한다
            for p in s["평면"]:
                # 이웃 j 칸에서 2 칸 안쪽만 자른다 — 평면을 이음면 밖으로 늘리면 k 가 셋째 부품과 맞닿은 (높이가 다른) 면까지 파먹어
                # 아무도 안 가지는 얇은 판 틈이 생긴다 (E13 머리뒤·가슴뒤·가슴판 z=148.5/149.5 계단)
                자름.append(저쪽(p, 부, 칸, 틈) ^ 칸메시(p["N"] & 부풂(j, 2), 칸))
                if 살핌 == k: print("    [%d] 짝 %d %s 인라이어 %d · 떼는 부피 %.1f mm³ · 그중 라벨 칸 안 %.1f" % (k, j, p["종류"], p["inl"].sum(), (R ^ 자름[-1]).volume(), (칸메시(lab == k, 칸) ^ 자름[-1]).volume()), flush=True)
        if 자름: R = R - M.Manifold.batch_boolean(자름, M.OpType.Add)
        if 살핌 == k: print("    [%d] 몸∩D %.1f → 자른 뒤 %.1f" % (k, (몸 ^ 칸메시(Dk, 칸)).volume(), R.volume()), flush=True)
        if 부품:   # 앞 부품 중 상자가 겹치는 것만 뺀다 (전체 합집합을 들고 다니면 부품마다 두 배씩 느려졌다)
            bb = R.bounding_box(); 앞 = [m for m in 부품.values() if 상자겹침(bb, m.bounding_box())]
            if 앞: R = R - M.Manifold.batch_boolean(앞, M.OpType.Add)
        R = M.Manifold(R.to_mesh()); 부품[k] = R
        print("  부품 %2d  %.2f cm³  자름 %d  %.0fs" % (k, R.volume() / 1000, len(자름), time.time() - t0), flush=True)
    # 틈 · 부스러기: 부품마다 가장 큰 덩어리만 남기고(큰 덩어리가 여럿이면 둔다) 나머지와 몸−합 틈 조각을
    # **가장 넓게 맞닿은 부품**(조각 정점이 그 부품 겉 위에 있는 몫)에 붙인다 → 틈 0 · 겹침 0 · 한 덩어리.
    남 = 몸 - M.Manifold.batch_boolean(list(부품.values()), M.OpType.Add)
    떼 = []
    for k in list(부품):
        조 = sorted(부품[k].decompose(), key=lambda m: -m.volume())
        if len(조) > 1:
            남길 = [m for m in 조 if m.volume() >= 0.2 * 조[0].volume()]
            부품[k] = M.Manifold.batch_boolean(남길, M.OpType.Add) if len(남길) > 1 else 조[0]
            떼 += [m for m in 조 if m.volume() < 0.2 * 조[0].volume()]
    남조 = sorted(남.decompose() + 떼, key=lambda m: -m.volume())
    print("남은 틈 %.3f mm³ + 뗀 부스러기 %.3f mm³ (%d 조각) · %.0fs" % (남.volume(), sum(m.volume() for m in 떼), len(남조), time.time() - t0), flush=True)
    부트 = {k: 트(m) for k, m in 부품.items()}; 부상 = {k: np.asarray(m.bounding_box()).reshape(2, 3) for k, m in 부품.items()}
    몫들 = {k: [] for k in 부품}; 붙임, 외톨 = [], 0.0
    잔 = 0.0
    for m in 남조:
        if m.volume() < 0.02: 잔 += m.volume(); continue     # 0.3mm 정육면체보다 작은 틈 — 노즐이 못 본다 (속 빈 금으로 남는다)
        v = np.asarray(m.to_mesh().vert_properties)[:, :3]; lo, hi = v.min(0), v.max(0)
        최 = (0.0, None)
        for k, b in 부상.items():
            if np.any(lo > b[1] + 0.01) or np.any(hi < b[0] - 0.01): continue
            d = 부트[k].nearest.on_surface(v)[1]; c = float(np.mean(d < 1e-3))
            if c > 최[0]: 최 = (c, k)
        if 최[1] is None: 외톨 += m.volume(); continue
        몫들[최[1]].append(m)
        if m.volume() > 1: 붙임.append((최[1], round(m.volume(), 2), round(최[0], 2)))
    for k, ms in 몫들.items():
        if ms: 부품[k] = M.Manifold(M.Manifold.batch_boolean([부품[k]] + ms, M.OpType.Add).to_mesh())
    print("  붙임 (1 mm³ 넘는 것: 부품 · 부피 · 맞닿은 몫) %s · 맞닿은 부품 없는 조각 %.3f mm³ · 0.02 미만 버림 %.3f mm³ · %.0fs" % (붙임, 외톨, 잔, time.time() - t0), flush=True)

    # ── 짝 검사 · 다보
    핀, 구멍, 다보표 = {k: [] for k in 부품}, {k: [] for k in 부품}, []
    겹합 = 0.0
    for (k, j), s in sorted(짝.items()):
        겹 = (부품[k] ^ 부품[j]).volume(); 겹합 += 겹
        평 = [q for q in s["평면"] if q["종류"] == "평면"]
        if not 평:
            다보표.append({"짝": [k, j], "평면": 0, "면": [q["종류"] for q in s["평면"]], "겹침mm3": round(겹, 4), "다보": [], "비고": "소켓(원통) 이음 — 다보 없음"}); continue
        p = max(평, key=lambda p: p["inl"].sum())
        nn, c = p["n"], p["c"] * 칸; Rt, _ = 평면틀(nn, c)
        cs = 단면(부품[k], Rt, c, -0.02) ^ 단면(부품[j], Rt, c, 0.02)
        넓이 = cs.area(); 줄 = {"짝": [k, j], "평면": len(평), "면": [q["종류"] for q in s["평면"]], "맞춤rms칸": [round(q["rms"], 3) for q in s["평면"]],
                               "법선": [round(float(x), 3) for x in nn], "이음넓이mm2": round(넓이, 1), "겹침mm3": round(겹, 4), "다보": []}
        r = 래스터(cs) if 넓이 > 1 else None
        if r is not None:
            acc, lo, 해 = r; E = ndimage.distance_transform_edt(acc) * 해; 후, 박 = [], []
            while len(후) < 8:      # 후보: 2D 거리변환 극대 (서로 3mm 떨어진) — 가장 두꺼운 곳부터
                y, x = np.unravel_index(E.argmax(), E.shape)
                if E[y, x] < 핀r + 틈 + 벽: break
                후.append(np.array([x * 해 + lo[0], y * 해 + lo[1]]))
                yy, xx = np.ogrid[:E.shape[0], :E.shape[1]]; E[(yy - y) ** 2 + (xx - x) ** 2 < (3 / 해) ** 2] = 0
            작은쪽 = k if 부품[k].volume() < 부품[j].volume() else j
            for q in 후:
                if len(박) >= 2: break
                if any(np.linalg.norm(q - b_) < 8 for b_ in 박): continue
                def 기둥(r_, z0, z1): return 옮김(M.Manifold.cylinder(z1 - z0, r_, r_, 32).translate([q[0], q[1], z0]), Rt, c)
                깊이 = 핀길이 + 0.3; 최 = None
                for 수 in (작은쪽, j if 작은쪽 == k else k):     # 핀은 작은 부품 쪽이 먼저 · 안 들어가면 바꿔 본다
                    암 = j if 수 == k else k; sgn = 1 if 수 == k else -1   # 평면틀 z: k 는 z<0 쪽
                    wall = 기둥(핀r + 틈 + 벽, 0, 깊이 + 바닥벽) if sgn > 0 else 기둥(핀r + 틈 + 벽, -깊이 - 바닥벽, 0)
                    root = 기둥(핀r + 벽, -1.0, 0) if sgn > 0 else 기둥(핀r + 벽, 0, 1.0)
                    샘 = (wall - 부품[암]).volume() / wall.volume() + (root - 부품[수]).volume() / root.volume()
                    if 최 is None or 샘 < 최[0]: 최 = (샘, 수, 암, sgn)
                    if 샘 < 0.01: break
                샘, 수, 암, sgn = 최; ok = 샘 < 0.01
                if ok:
                    핀[수].append(기둥(핀r, -1.0, 핀길이) if sgn > 0 else 기둥(핀r, -핀길이, 1.0))
                    # 구멍은 이음면 밖으로 0.5 부터 — 면과 같은 높이에서 시작하면 두께 0 막이 남아 구멍이 속 빈 방이 된다
                    구멍[암].append(기둥(핀r + 틈, -0.5, 깊이) if sgn > 0 else 기둥(핀r + 틈, -깊이, 0.5))
                    p.setdefault("핀쪽", set()).add(수); 박.append(q)
                줄["다보"].append({"자리mm": [round(float(x), 2) for x in (Rt @ np.r_[q, 0] + c)], "핀": 수, "구멍": 암, "벽새는몫": round(샘, 4), "박음": ok})
            줄["다보"] = [d for d in 줄["다보"] if d["박음"]] or 줄["다보"][:1]
        다보표.append(줄)
    쓰레기 = 0.0
    for k in 부품:
        if 핀[k]: 부품[k] = 부품[k] + M.Manifold.batch_boolean(핀[k], M.OpType.Add)
        if 구멍[k]: 부품[k] = 부품[k] - M.Manifold.batch_boolean(구멍[k], M.OpType.Add)
        조 = 부품[k].decompose(); 남길 = [m for m in 조 if m.volume() >= 0.05]   # 부피 0 에 가까운 껍질(맞닿은 면 불리언 찌꺼기)은 버린다
        쓰레기 += sum(abs(m.volume()) for m in 조 if m.volume() < 0.05)
        if len(남길) < len(조): 부품[k] = M.Manifold.batch_boolean(남길, M.OpType.Add) if len(남길) > 1 else 남길[0]

    # ── 내보내기 · 검사
    out = os.path.join(D, "출력", "오메가몬_%s키트" % 판); os.makedirs(os.path.join(out, "_조립"), exist_ok=True)
    for dd in (out, os.path.join(out, "_조립")):
        for fn in os.listdir(dd):
            if fn.endswith(".stl"): os.remove(os.path.join(dd, fn))
    줄들, 보기 = [], []
    몸중심 = 트(몸).centroid
    nf = os.path.join(D, "분할후보", 판, "이름.json")
    이름표 = {int(a): b for a, b in json.load(open(nf, encoding="utf-8")).items()} if os.path.exists(nf) else {}
    # 앞/뒤: 이름.json 을 그대로 쓴다. 확인 — E13 은 「앞」 라벨의 y 가 더 크다(1 머리앞 106.6 · 18 머리뒤 97.3):
    # 공통입력.py 의 「선앞 = +y 쪽 겉」과 맞다. 보기 좌표는 (−x, z, y) 로 앞(+y)이 카메라(+Z) 쪽.
    줄기 = lambda s: s[:-1] if s[-1:] in ("앞", "뒤") else s
    블록들 = list(dict.fromkeys(줄기(이름표.get(k, "부품%02d" % k)) for k in sorted(부품)))
    색표 = ["#e8590c", "#1c7ed6", "#2f9e44", "#ae3ec9", "#f59f00", "#0c8599", "#d6336c", "#5c940d", "#6741d9", "#868e96"]
    for i, k in enumerate(sorted(부품)):
        # (simplify(1e-3) 로 짧은 모서리를 접어 봤다 → 스스로 닿는 곳이 정확히 붙어 STL 열린 부품이 2 → 16 으로 늘었다. 안 쓴다)
        m = 부품[k]; 조각수 = len(m.decompose()); tm = 트(m)
        이름 = "부품%02d" % k
        tm.export(os.path.join(out, "_조립", 이름 + ".stl"))
        # 출력 방향: 바닥에 닿는 면적이 가장 넓은 쪽을 아래로 (후보 = 이음 평면 법선 ± · 축 여섯). 핀이 난 면은 핀 끝만 닿아 저절로 밀린다.
        # (09-25 첫 판: 넓은 이음면이 없는 부품을 조립 방향 그대로 두었더니 바닥 면적 0 → OrcaSlicer 가 5 개를 거부)
        후보 = [np.eye(3)[a_] * s_ for a_ in range(3) for s_ in (1, -1)]
        for j in 이웃[k]:
            for p in 짝[(min(k, j), max(k, j))]["평면"]:
                if p["종류"] == "평면": 후보 += [p["n"], -p["n"]]
        def 바닥(d):   # (그 방향으로 가장 넓은 평면 한 장의 넓이, 그 면 밖으로 튀어나온 턱 mm)
            fc = tm.face_normals @ d > 0.999
            if not fc.any(): return 0.0, 9.0
            lv = np.round(tm.triangles_center[fc] @ d, 2); a_ = tm.area_faces[fc]
            u, inv = np.unique(lv, return_inverse=True); s_ = np.bincount(inv, a_); i_ = s_.argmax()
            return float(s_[i_]), float((tm.vertices @ d).max() - u[i_])
        # 턱 0.5mm 넘는 방향은 뺀다 — 이음면 밖으로 라벨 계단이 남은 곳이 있어 평면이 바닥에 안 닿는다
        아래 = max(후보, key=lambda d: 바닥(d)[0] if 바닥(d)[1] < 0.5 else -바닥(d)[1]); 바닥mm2, 턱 = 바닥(아래)
        pm = tm.copy(); T = np.eye(4); T[:3, :3] = 회전(-아래); pm.apply_transform(T)
        pm.apply_translation(-pm.bounds[0]); pm.export(os.path.join(out, 이름 + ".stl"))
        stl닫힘 = all(trimesh.load(os.path.join(d_, 이름 + ".stl")).is_watertight for d_ in (out, os.path.join(out, "_조립")))
        t1, 얇몫 = 두께(tm)
        줄 = {"부품": 이름, "이름": 이름표.get(k, ""), "라벨": k, "차례": 몇째[k], "부피cm3": round(m.volume() / 1000, 3), "치수mm": [round(float(x), 1) for x in tm.extents],
              "짝": sorted(이웃[k]), "핀": len(핀[k]), "구멍": len(구멍[k]), "닫힘": bool(tm.is_watertight), "STL닫힘(다시 읽어서)": stl닫힘, "manifold": str(m.status()).split(".")[-1],
              "조각수": 조각수, "종류(genus)": m.genus(), "바닥면적mm2": round(바닥mm2, 1), "바닥 턱mm": round(턱, 2),
              "벽1분위mm": None if t1 is None else round(t1, 2), "0.8mm미만몫": None if 얇몫 is None else round(얇몫, 3)}
        줄들.append(줄)
        # 보기 (위 +y · 앞 +z) = (x, z, −y) · 벌림 = 이웃 평면 법선의 반대(이웃에서 멀어지는 쪽) 합
        vm = tm.copy(); vm.apply_translation(-몸중심); vv = vm.vertices[:, [0, 2, 1]] * [-1, 1, 1]
        b = np.zeros(3)
        for j in 이웃[k]:
            s = 짝[(min(k, j), max(k, j))]; 부 = 1 if k < j else -1
            for p in s["평면"]:
                if p["종류"] == "평면": b -= 부 * p["n"] * p["inl"].sum()
        b = b[[0, 2, 1]] * [-1, 1, 1]; b = (b / np.linalg.norm(b)).round(3).tolist() if np.linalg.norm(b) > 0 else None
        블 = 줄기(이름표.get(k, 이름)); 쪽 = 이름표.get(k, "")[-1:] if 이름표.get(k, "")[-1:] in ("앞", "뒤") else ""
        보기.append({"부품": 블, "조각": (블 + " " + 쪽) if 쪽 else 블, "블록": 블, "종류": "반쪽" if 쪽 else "통", "벌림": b,
                   "색": 색표[블록들.index(블) % len(색표)],
                   "치수": 줄["치수mm"], "닫힘": 줄["닫힘"], "부피": round(m.volume() / 1000, 2),
                   "v": base64.b64encode(vv.astype(np.float32).tobytes()).decode(),
                   "f": base64.b64encode(tm.faces.astype(np.uint32).tobytes()).decode()})
        print("  %s %-8s %6.2f cm³  %s  닫힘 %s 조각 %d  핀 %d 구멍 %d  벽1%% %s" % (이름, 줄["이름"], 줄["부피cm3"], 줄["치수mm"], 줄["닫힘"], 조각수,
              줄["핀"], 줄["구멍"], 줄["벽1분위mm"]), flush=True)
    합 = sum(m.volume() for m in 부품.values())
    다보박음 = sum(d["박음"] for x in 다보표 for d in x["다보"])
    요약 = {"판본": 판, "전고mm": 전고, "칸mm": round(칸, 4), "틈mm(한쪽)": 틈, "핀지름mm": 2 * 핀r, "핀길이mm": 핀길이,
          "부품": len(부품), "닫힌 부품": sum(x["닫힘"] and x["manifold"] == "NoError" for x in 줄들), "STL 닫힌 부품": sum(x["STL닫힘(다시 읽어서)"] for x in 줄들),
          "한 조각 부품": sum(x["조각수"] == 1 for x in 줄들),
          "짝": len(짝), "L자 짝": sum(len(s["평면"]) > 1 for s in 짝.values()),
          "몸 부피cm3": round(몸.volume() / 1000, 3), "부품 합cm3": round(합 / 1000, 3),
          "틈(몸−합, 다보 전)mm3": round(남.volume(), 3), "틈·부스러기 붙임(부품,mm3,맞닿은몫)": 붙임, "맞닿은 부품 없는 조각mm3": round(외톨, 3), "0.02mm3 미만 틈 버림mm3": round(잔, 3), "짝 겹침 합mm3(다보 전)": round(겹합, 4), "0.05mm3 미만 찌꺼기 껍질 버림mm3": round(쓰레기, 3),
          "다보 박음": 다보박음, "다보 생략 짝": [x["짝"] for x in 다보표 if not any(d["박음"] for d in x["다보"])],
          "가장 얇은 벽 1분위mm": min(x["벽1분위mm"] for x in 줄들 if x["벽1분위mm"] is not None),
          "PLA g(1.24)": round(합 / 1000 * 1.24, 1), "걸린 초": round(time.time() - t0), "짝표": 다보표, "부품표": 줄들}
    json.dump(요약, open(os.path.join(out, "키트.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    t = open(r"G:\art2real\원화3d\설계\부품속.src.html", encoding="utf-8").read()
    t = t.replace("부품 속 — 오메가몬", "부품 — 오메가몬 %s 키트" % 판).replace(
        "색 = 블록 · 회색 = 관절 부품(볼 · 폴리캡 · 플러그) · 반쪽은 속이 빈 컵(벽 1.2 mm)이고 속 기둥(보스) 두 개 — 한쪽 보스에 핀, 다른 쪽에 구멍 · 전고 125 mm",
        "색 = 블록 · 이음면 = 정확한 평면(소켓은 원통) · 짝마다 다보 핀 Ø%.1f×%.1f mm / 구멍 틈 한쪽 %.2f mm · 속 찬 부품 · 전고 125 mm" % (2 * 핀r, 핀길이, 틈)).replace("__DATA__", json.dumps(보기, ensure_ascii=False))
    open(os.path.join(D, "부품속_%s키트.html" % 판), "w", encoding="utf-8").write(t)
    print({k: v for k, v in 요약.items() if k not in ("짝표", "부품표")})
    print(out)


if __name__ == "__main__":
    main()
