# -*- coding: utf-8 -*-
"""오메가몬 PG 급(300 mm) 가동 키트 — **디자인 판** 외장 · 다리 블록 (2026-09-25).

    python 디자인_다리.py      -> out/출력/오메가몬_PG/디자인/다리/*.stl · 부품.json · 보기.png

몸 부피를 깎지 않는다. 원화 마스크(창 좌표 → mm)에서 높이마다 **정면 폭 · 옆 깊이 두 값만** 읽어
팔각 단면(모따기)을 만들고, 이웃 단면을 manifold hull 로 이은 **각진 로프트**로 부품을 새로 짓는다.
  · L 다리만 짓고 R 은 x 거울 (정확 대칭). 폭은 L 과 거울한 R 마스크의 평균.
  · 껍질 2.0 mm = 로프트 − 단면 안쪽 2 mm 오프셋 로프트 − 비움(뼈 · 관절 외피 · J2 부품 볼록 껍질 + 0.4, 움직이는 이웃은 쓸어서).
  · 앞뒤 반쪽 = 뼈 선을 품는 평면 · 다보 Ø2 / 구멍 Ø2.4 (한쪽 0.20) · 뼈 결합 = 반쪽마다 반달 갈비(뼈 + 0.10)가 뼈를 끼운다.
  · 패널라인 = 규칙(직선 · 45°) V 홈 폭 0.8 · 깊이 0.5 (두 계단 근사).
  · 가동: 무릎 뒤 파냄 · 무릎 장갑은 정강이에 핀 · 발목 · 발끝 힌지 둘레 원통 컷. 무릎 90/150 · 발목 ±30 · 고관절 앞차기 90 에서 교집합 부피를 잰다.
좌표 = 관절.json: mm · 원점 발바닥 중앙 · [x 좌우, y 깊이(작은 y 가 앞), z 높이]."""
import os, sys, json, time
os.environ.setdefault("OMP_NUM_THREADS", "4"); os.environ.setdefault("INK_W", "1")
import numpy as np, trimesh, manifold3d as M
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 장갑 as JG

ROOT = r"G:\art2real\원화3d"
OUT = os.path.join(ROOT, "out", "출력", "오메가몬_PG", "디자인", "다리"); os.makedirs(OUT, exist_ok=True)
캐시 = os.path.join(ROOT, "out", "출력", "오메가몬_PG", "_캐시"); os.makedirs(캐시, exist_ok=True)
두께, 비움틈, 결합틈, 끼움틈 = 2.0, 0.4, 0.20, 0.10
PLA = 1.24e-3                                   # g / mm³
t0 = time.time()
def 로그(*a): print("[%4.0fs]" % (time.time() - t0), *a, flush=True)
X, Y, Z = np.eye(3)
단 = JG.단; 관절 = JG.관절; 트 = JG.트
def 만(v, f): return JG.만(np.ascontiguousarray(v, np.float32), np.ascontiguousarray(f, np.uint32))
ADD = M.OpType.Add
def 합(ms): ms = [m for m in ms if m is not None and not m.is_empty()]; return M.Manifold.batch_boolean(ms, ADD) if ms else M.Manifold()
def 부피(m): return 0.0 if m.is_empty() else m.volume()
def 겹(a, b): return 부피(a ^ b)

# ════════ ① 원화 윤곽 (창 마스크 → mm 격자 0.5) ════════════════════════
def 윤곽():
    f = os.path.join(캐시, "다리윤곽.npz")
    if not os.path.exists(f):
        sys.path[:0] = [ROOT] + [ROOT + r"\실험_202609%02d" % d for d in (21, 22, 23, 24, 25)]
        import win as W, 부품분할 as BB
        _, masks, _, _ = BB.판("오메가몬")
        d = np.load(os.path.join(ROOT, "out", "분할후보", "입력.npz")); O = d["O"]; 축i = float(d["축i"])
        zs = np.nonzero(O.any((0, 1)))[0]; C = 300.0 / (zs[-1] - zs[0] + 1); y0 = np.argwhere(O[:, :, zs[0]:zs[0] + 2])[:, 1].mean()
        u = lambda v, i0: W.U0 + (v / C + i0 + 0.5) / 192 * (W.U1 - W.U0)
        zw = lambda z: W.Z0 + (z / C + zs[0]) / 192 * (W.Z1 - W.Z0)
        xs = np.arange(-90, 90.01, 0.5); ys = np.arange(-50, 70.01, 0.5); zz = np.arange(-5, 200.01, 0.5)
        def s(v, a, i0):
            A, G = np.meshgrid(a, zz, indexing="ij"); py, px = W.topix(u(A, i0), zw(G)); return masks[v][py, px]
        np.savez_compressed(f, F=s("front", xs, 축i), S=s("side", ys, y0), xs=xs, ys=ys, zz=zz)
    d = np.load(f); return d["F"], d["S"], d["xs"], d["ys"], d["zz"]
F정, F옆, AX, AY, AZ = 윤곽()

def _구간(row, a, seed):
    lab, n = ndimage.label(row); i = int(np.argmin(abs(a - seed))); c = lab[i]
    if c == 0:
        nz = np.nonzero(lab)[0]
        if len(nz) == 0: return None
        c = lab[nz[np.argmin(abs(nz - i))]]
    w = np.nonzero(lab == c)[0]; return a[w[0]], a[w[-1]]

def 폭(z, seed=-30.0, 쪽="L"):
    """정면 마스크 z 행에서 seed 를 품는 조각의 x 구간. 쪽 L = 그대로 · R = 거울 뒤 L 좌표로 · 평 = 평균."""
    k = int(np.argmin(abs(AZ - z)))
    if 쪽 == "평":
        a, b = 폭(z, seed, "L"), 폭(z, seed, "R"); return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    if 쪽 == "L": return _구간(F정[:, k], AX, seed)
    r = _구간(F정[:, k], AX, -seed); return (-r[1], -r[0])

def 깊이(z, seed=22.0):
    k = int(np.argmin(abs(AZ - z))); return _구간(F옆[:, k], AY, seed)

def 계열(z0, z1, seed=-30.0, 덮기=None):
    """z0..z1 (1 mm) 의 [z, x0, x1, y0, y1] 표 · 중앙값 3 으로 계단 잡음 빼기. 덮기(z, 행) 로 원화 밖 규칙을 덮는다."""
    zs = np.arange(z0, z1 + 0.01, 1.0); T = []
    for z in zs:
        a = 폭(z, seed, "평"); b = 깊이(z); T.append([z, a[0], a[1], b[0], b[1]])
    T = np.array(T); T[:, 1:] = ndimage.median_filter(T[:, 1:], size=(3, 1), mode="nearest")
    if 덮기: T = np.array([덮기(r[0], r.copy()) for r in T])
    return T

def RDP(T, tol):
    """네 곡선(x0 x1 y0 y1) 을 선형 보간이 tol 안에 들게 하는 최소 역."""
    keep = {0, len(T) - 1}
    def 나눔(i, j):
        if j - i < 2: return
        t = (T[i + 1:j, 0] - T[i, 0]) / (T[j, 0] - T[i, 0])
        L = T[i, 1:] + t[:, None] * (T[j, 1:] - T[i, 1:]); e = np.abs(T[i + 1:j, 1:] - L).max(1)
        k = int(np.argmax(e))
        if e[k] > tol: keep.add(i + 1 + k); 나눔(i, i + 1 + k); 나눔(i + 1 + k, j)
    나눔(0, len(T) - 1); return T[sorted(keep)]

# ════════ ② 단면 · 로프트 ════════════════════════════════════════
def 팔각(a0, a1, b0, b1, c앞, c뒤):
    """(a, b) 평면 팔각. b 가 작은 쪽 = 앞(모따기 c앞)."""
    w, d = a1 - a0, b1 - b0; cf = min(c앞, 0.49 * w, 0.49 * d); cb = min(c뒤, 0.49 * w, 0.49 * d)
    return [(a0 + cf, b0), (a1 - cf, b0), (a1, b0 + cf), (a1, b1 - cb), (a1 - cb, b1), (a0 + cb, b1), (a0, b1 - cb), (a0, b0 + cf)]

def 오프셋(p, d):
    if abs(d) < 1e-9: return np.array(p, float)
    ps = M.CrossSection([np.array(p, float)]).offset(d, M.JoinType.Miter, 2.0).to_polygons()
    return np.array(max(ps, key=len), float)

def 로프트(단면들, 축="z", d=0.0):
    """단면들 = [(s, 다각형 (a, b))]. 축 z: (a, b) = (x, y) · 축 y: (a, b) = (x, z)."""
    def 삼(p, s):
        p = np.asarray(p, float); c = np.full(len(p), s)
        return np.c_[p[:, 0], p[:, 1], c] if 축 == "z" else np.c_[p[:, 0], c, p[:, 1]]
    조각 = [M.Manifold.hull_points(np.r_[삼(오프셋(p0, d), s0), 삼(오프셋(p1, d), s1)])
          for (s0, p0), (s1, p1) in zip(단면들[:-1], 단면들[1:])]
    return 합(조각)

def 판(n, p):
    """n · (x − p) >= 0 인 반공간과 교집합할 때 쓰는 trim 인자."""
    n = 단(n); return n, float(n @ np.asarray(p, float))
def 자름(m, n, p): nn, o = 판(n, p); return m.trim_by_plane(tuple(nn), o)       # n 쪽을 남김
def 상자(lo, hi): lo = np.asarray(lo, float); return M.Manifold.cube(tuple(np.asarray(hi, float) - lo)).translate(tuple(lo))
def 원기둥(p0, p1, r, seg=32):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float); L = np.linalg.norm(p1 - p0)
    R = JG.PJ.회전(p1 - p0).T
    return M.Manifold.cylinder(L, r, r, seg).transform(np.c_[R, p0])

def 회전행렬(a, θ):
    a = 단(a); K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]]); t = np.radians(θ)
    return np.eye(3) + np.sin(t) * K + (1 - np.cos(t)) * K @ K
def 강체(R, p):                                  # p 둘레 R → 4×3
    p = np.asarray(p, float); return np.c_[R, p - R @ p]
def 합성(A, B):                                  # A ∘ B (B 먼저)
    return np.c_[A[:, :3] @ B[:, :3], A[:, :3] @ B[:, 3] + A[:, 3]]
def 놓(m, T): return m.transform(T)
def 쓸기(m, 틀들):
    """틀들(연속 자세) 사이를 짝마다 볼록 껍질로 이은 합 — 쓸린 부피의 겉 근사 (볼록 조각에 쓸 것)."""
    ps = [놓(m, T) for T in 틀들]
    return 합([M.Manifold.batch_hull([a, b]) for a, b in zip(ps[:-1], ps[1:])])
def 힌지틀(n, θ):
    j = 관절[n]; return 강체(회전행렬(j["축"], θ), j["피벗mm"])

# ── 관절 자세 (L) ──
P1 = np.array(관절["L무릎"]["피벗mm"]); P2 = np.array(관절["L무릎"]["외피"]["둘째축피벗mm"]); A무 = 단(관절["L무릎"]["축"])
def 무릎틀(θ):
    """이중힌지 θ = 두 축이 반씩. 자식 = R1(θ/2) ∘ R2(θ/2) (R2 는 원래 둘째 축 둘레)."""
    return 합성(강체(회전행렬(A무, θ / 2), P1), 강체(회전행렬(A무, θ / 2), P2))
def 링크틀(θ): return 강체(회전행렬(A무, θ / 2), P1)
_s = 무릎틀(30.0) @ np.r_[관절["L발목볼"]["피벗mm"], 1]
assert _s[1] > 관절["L발목볼"]["피벗mm"][1], "무릎 + 가 뒤로 접히는 쪽이어야"

# ════════ ③ 비움 (뼈 · 관절 외피 · J2 부품) ═══════════════════════════
다리관절 = ["L고관절", "L허벅지회전", "L무릎", "L발목볼", "L발목", "L발끝"]
다리뼈 = ["L허벅지위", "L허벅지", "L정강이", "L발목블록", "L발", "L발끝"]

def 뼈캡슐(n, 덧):
    return 합([JG.캡슐(a, b, ra + 덧, rb + 덧, 20) for a, b, ra, rb in JG.뼈선(n)])

def J2껍질():
    f = os.path.join(캐시, "다리J2.npz")
    if os.path.exists(f):
        d = np.load(f, allow_pickle=True); return {k: 만(v[0], v[1]) for k, v in d["m"].item().items()}
    저장 = JG.관절; JG.관절 = {k: v for k, v in 저장.items() if k in 다리관절}
    try: 놓인, _, _ = JG.관절짓기()
    finally: JG.관절 = 저장
    out = {}
    for (n, k), v in 놓인.items():
        h = JG.볼록덧(v["m"], 비움틈); g = h.to_mesh(); out["%s|%s" % (n, k)] = (np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts))
    np.savez(f, m=np.array(out, dtype=object)); return {k: 만(*v) for k, v in out.items()}

def 관절덩이(n, 덧=비움틈):
    """관절 n 의 외피 + J2 부품 볼록 껍질 (+덧)."""
    return 합([JG.외피메시(관절[n], 덧, 40)] + [m for k, m in J2.items() if k.split("|")[0] == n])

def 각들(lo, hi, 걸음=10.0):
    k = max(1, int(np.ceil((hi - lo) / 걸음))); return np.linspace(lo, hi, k + 1)

def 비움들():
    """부품(붙는 뼈)마다 뺄 곳. 같은 뼈 · 양끝 관절은 그대로, 관절 너머 이웃 뼈는 그 관절 범위로 쓸어서."""
    B = {n: 뼈캡슐(n, 비움틈) for n in 다리뼈}
    Jd = {n: 관절덩이(n) for n in 다리관절}
    회 = 관절["L허벅지회전"]
    회틀 = [강체(회전행렬(회["축"], a), 회["피벗mm"]) for a in 각들(-45, 45, 15)]
    링크 = [링크틀(θ) for θ in 각들(0, 150, 15)]
    발목 = [힌지틀("L발목", a) for a in 각들(-30, 30, 10)]
    발끝 = [힌지틀("L발끝", a) for a in 각들(-30, 20, 10)]
    볼 = 관절["L발목볼"]; bp = 볼["피벗mm"]
    볼틀 = [합성(강체(회전행렬(Y, b), bp), 강체(회전행렬(X, a), bp)) for a in (-10, 10) for b in (-25, 0, 25)]
    볼틀 = [볼틀[0], 볼틀[1], 볼틀[2], 볼틀[5], 볼틀[4], 볼틀[3], 볼틀[0]]
    무릎덩 = Jd["L무릎"]
    K = {}; KL = {}
    KL["허벅지"] = ([B["L허벅지"], Jd["L허벅지회전"], 쓸기(B["L허벅지위"], 회틀), 쓸기(Jd["L고관절"], 회틀),
                    무릎덩, 쓸기(JG.외피메시(관절["L무릎"], 비움틈, 40), 링크), 쓸기(뼈캡슐("L정강이", 비움틈), [무릎틀(θ) for θ in 각들(0, 150, 10)])])
    KL["정강이"] = ([B["L정강이"], Jd["L발목볼"], 무릎덩, 쓸기(B["L발목블록"], 볼틀), 쓸기(Jd["L발목"], 볼틀)])
    KL["발"] = ([B["L발"], Jd["L발목"], Jd["L발끝"], 쓸기(B["L발목블록"], 발목), 쓸기(Jd["L발목볼"], 발목)])
    KL["발끝"] = ([B["L발끝"], Jd["L발끝"], 쓸기(B["L발"], 발끝)])
    for k, v in KL.items(): K[k] = 합(v); K[k + "_뼈빼고"] = 합(v[1:])
    return K, B, Jd

# ════════ ④ 부품 모양 ═══════════════════════════════════════════
허벅지위, 허벅지아래 = 163.0, 126.0
허뒤컷 = ((0, -0.70, 0.714), (0, 27.0, 129.0))
정뒤컷 = ((0, -0.80, -0.60), (0, 38.0, 100.0))
정강이위, 정강이아래 = 116.0, 28.0
def 허벅지덮기(z, r):
    if z > 150: r[2] = min(r[2], -6.5 - 0.02 * (z - 150)); r[3] = max(r[3], 3.0)   # 가랑이 위 · 앞 스커트 밑은 원화에 선이 없다
    return r
def 정강이덮기(z, r):
    if z > 101: r[3] = max(r[3], 6.5 + (z - 101) * 0.25)                            # 무릎 장갑 뒤로 물린 앞면
    return r

def z단면(T, c앞, c뒤):
    return [(r[0], 팔각(r[1], r[2], r[3], r[4], c앞 * min(r[2] - r[1], r[4] - r[3]), c뒤 * min(r[2] - r[1], r[4] - r[3]))) for r in T]

def 허벅지모양():
    T = RDP(계열(허벅지아래, 허벅지위, -22, 허벅지덮기), 0.8)
    S = z단면(T, 0.30, 0.22)
    겉 = 로프트(S); 안 = 로프트(S, d=-두께)
    안 = 자름(자름(안, Z, [0, 0, 허벅지아래 + 두께]), -Z, [0, 0, 허벅지위 - 두께])
    컷 = []
    # 윗단 앞 모따기 (앞차기 90 에 스커트 · 골반과 덜 닿게) · 무릎 앞 아래 모따기 (무릎 장갑 끝이 앉을 자리) · 무릎 뒤 파냄
    컷.append(((0, 0.60, -0.80), (0, 5.0, 157.0)))              # 앞 윗단: y 작고 z 큰 모서리
    컷.append(((0, 0.55, 0.835), (0, 12.0, 128.5)))              # 앞 아랫단
    컷.append(허뒤컷)                                             # 뒤 아랫단 (무릎 뒤)
    for n, p in 컷: 겉 = 자름(겉, n, p); 안 = 자름(안, n, np.asarray(p) + 두께 * 단(n))
    return dict(겉=겉, 안=안, 단면=T, 갈안=로프트(S, d=-(두께 - 0.3)) ^ 겉)

def 정강이모양():
    T = RDP(계열(정강이아래, 정강이위, -30, 정강이덮기), 0.8)
    S = z단면(T, 0.42, 0.25)                  # 앞 모따기 크게 = 앞 능선
    겉 = 로프트(S); 안 = 로프트(S, d=-두께)
    안 = 자름(자름(안, Z, [0, 0, 정강이아래 + 두께]), -Z, [0, 0, 정강이위 - 두께])
    컷 = [정뒤컷]                                                 # 뒤 윗단 (무릎 150 에 허벅지 뒤와)
    for n, p in 컷: 겉 = 자름(겉, n, p); 안 = 자름(안, n, np.asarray(p) + 두께 * 단(n))
    pa = np.array(관절["L발목"]["피벗mm"])
    겉 = 겉 - (원기둥(pa - 40 * X, pa + 40 * X, 발원r + 0.5, 96) - 상자([-100, 14.0, 0], [0, 37.0, 60]))   # 앞 · 뒤 부채꼴만 (옆 나팔은 발이 돌아도 안 닿는다)
    return dict(겉=겉, 안=안, 단면=T, 갈안=로프트(S, d=-(두께 - 0.3)) ^ 겉)

def 무릎장갑모양(허, 정):
    cx = (폭(118, -30, "평")[0] + 폭(118, -30, "평")[1]) / 2
    rows = [(104.0, 10.5, 9.0, 17.0), (110.0, 11.0, 6.0, 15.5), (118.0, 10.8, 2.0, 13.5), (126.0, 10.0, 0.3, 12.5),
            (129.0, 6.5, 4.5, 12.5), (133.5, 0.8, 9.5, 12.5)]
    S = [(z, 팔각(cx - w, cx + w, y0, y1, 0.45 * min(2 * w, y1 - y0), 0.1)) for z, w, y0, y1 in rows]
    겉 = 로프트(S)
    안 = 로프트([(z, 팔각(cx - w + 두께, cx + w - 두께, y0 + 두께, y1 + 10, 0.45 * min(2 * w, y1 - y0), 0.1)) for z, w, y0, y1 in rows[:-1]])
    안 = 자름(안, Z, [0, 0, 104.0 + 1.2])
    m = 겉 - 안 - 로프트(허["S"], d=비움틈) - 정["겉"]
    return dict(겉=겉, 몸=m, cx=cx)

# 발: y 방향 로프트 · 단면 (x, z) — 윗선은 옆 마스크 앞선, 폭은 정면 z 22~26 에서
발x = (-61.0, -22.0)
발원r = 16.8
def 발모양():
    rows = [(-9.0, 0.0, 19.0), (-2.0, 0.0, 24.0), (4.0, 0.0, 26.0), (22.0, 0.0, 27.0), (40.0, 0.0, 26.0), (47.0, 0.5, 23.5), (49.5, 2.0, 19.0)]
    x0, x1 = 발x
    def 단(y, z0, z1, 좁=0.0):
        return 팔각(x0 + 좁, x1 - 좁, z0, z1, 1.2, 0.30 * (x1 - x0))   # b = z · 앞(작은 b) = 바닥 모따기 작게 · 위 모따기 크게
    S = [(y, 단(y, z0, z1, 1.5 if y > 45 else 0.0)) for y, z0, z1 in rows]
    겉 = 로프트(S, "y"); 안 = 로프트(S, "y", d=-두께)
    안 = 자름(자름(안, Y, [0, -9.0 + 두께, 0]), -Y, [0, 49.5 - 두께, 0])
    # 발목 힌지 둘레 원통: 정강이 아랫단이 ±30 에 안 닿게 발 윗면을 축 둘레 반지름 r 안으로
    j = 관절["L발목"]; p = np.array(j["피벗mm"])
    r = 발원r
    원 = 원기둥(p - 40 * X, p + 40 * X, r, 96)
    위 = 상자([-100, -20.0, p[2]], [0, 60.0, 60])                      # 정강이 발자국 위만 원통으로
    겉 = (겉 - 위) + (겉 ^ 위 ^ 원); 안 = (안 - 위) + (안 ^ 위 ^ 원기둥(p - 40 * X, p + 40 * X, r - 두께, 96))
    return dict(겉=겉, 안=안, r=r, 갈안=로프트(S, "y", d=-(두께 - 0.3)) ^ 겉)

def 발끝모양():
    j = 관절["L발끝"]; p = np.array(j["피벗mm"])
    x0, x1 = 발x[0] + 2.0, 발x[1] - 2.0
    rows = [(p[1] - 0.4, 0.8, 20.0), (-16.0, 1.0, 17.5), (-25.5, 1.5, 12.5)]
    S = [(y, 팔각(x0, x1, z0, z1, 1.0, 0.28 * (x1 - x0))) for y, z0, z1 in rows]
    겉 = 로프트(S, "y")
    안 = 자름(자름(로프트(S, "y", d=-두께), -Y, [0, p[1] - 0.4 - 두께, 0]), Y, [0, -25.5 + 두께, 0])
    # 발끝 힌지 둘레: 발 앞 아랫단 원통 컷 (발끝이 −30~20 돌 때 발 앞면과)
    return dict(겉=겉, 안=안, p=p)

def 발톱모양():
    """금 발톱 셋: 뿌리 = 발끝 앞면 · 끝 = 원화 정면 · 옆 실루엣 끝. 육각 뿔(뿌리 단면 → 끝 점)."""
    cx0, cx1 = 발x
    spec = {"바깥": ((cx0 + 5.5, -20.0, 10.0), (-77.5, -32.0, 4.5), 5.0),
            "가운데": ((-41.5, -22.0, 10.5), (-45.5, -36.0, 4.5), 5.4),
            "안": ((cx1 - 6.0, -21.0, 10.0), (-25.0, -32.5, 5.0), 4.2)}
    out = {}
    for k, (a, b, r) in spec.items():
        a, b = np.array(a), np.array(b); d = 단(b - a)
        u = 단(np.cross(d, Z)); v = np.cross(u, d)
        ring = [a + r * (np.cos(t) * u + 0.75 * np.sin(t) * v) for t in np.linspace(0, 2 * np.pi, 6, endpoint=False)]
        ring2 = [a - 3.0 * d + 0.8 * r * (np.cos(t) * u + 0.75 * np.sin(t) * v) for t in np.linspace(0, 2 * np.pi, 6, endpoint=False)]
        tip = [b + 0.35 * (np.cos(t) * u + np.sin(t) * v) for t in np.linspace(0, 2 * np.pi, 6, endpoint=False)]
        몸 = M.Manifold.hull_points(np.array(ring + ring2 + tip))
        out[k] = dict(몸=몸, 뿌리=a, 끝=b, d=d)
    return out

# ════════ ⑤ 반쪽 · 다보 · 갈비 · 패널라인 ════════════════════════════
def 뼈평면(뼈n):
    """뼈 선을 품고 x 축에 평행한 평면 (법선은 +y 쪽) — 앞뒤 반쪽 이음면."""
    s = JG.뼈선(뼈n); a = s[0][0]; b = s[-1][1]; d = 단(b - a)
    n = 단(np.cross(d, X)); n = n if n[1] > 0 else -n
    return n, (a + b) / 2

def 다보(겉, K, n, p, 후보):
    """이음면 위 후보점마다 보스(Ø4.5 · 이음면 ±4.5) — 겉 안에 다 들고 비움과 안 겹칠 때만. 핀 Ø2×2.5 은 앞 반쪽, 구멍 Ø2.4×3.0 은 뒤."""
    보스, 핀, 구멍, 쓴 = [], [], [], []
    for q0 in 후보:                                  # 후보 = 점 하나 또는 점 묶음(앞에서부터 처음 되는 것)
        묶 = [q0] if np.ndim(q0) == 1 else q0
        for q in 묶:
            q = np.asarray(q, float); b = 원기둥(q - 4.5 * n, q + 4.5 * n, 2.25, 24)
            if 부피(b - 겉) <= 0.5 and 겹(b, K) <= 0.01: break
        else: continue
        보스.append(b); 핀.append(원기둥(q - 0.5 * n, q + 2.5 * n, 1.0, 16)); 구멍.append(원기둥(q - 0.01 * n, q + 3.0 * n, 1.0 + 결합틈, 16))
        쓴.append(q.round(2).tolist())
    return 합(보스), 합(핀), 합(구멍), 쓴

def 갈비(안, K, 뼈n, ts, 덧=끼움틈, 두=3.0):
    """뼈 선 위 t(0~1) 자리에 뼈에 수직한 판(두께 3) = 안쪽 ∩ 판 − 뼈(+0.10) − 다른 비움. 이음면이 뼈를 가르니 반쪽마다 반달."""
    s = JG.뼈선(뼈n); a = s[0][0]; b = s[-1][1]; d = 단(b - a); L = np.linalg.norm(b - a)
    뼈m = 뼈캡슐(뼈n, 덧); out = []
    for t in ts:
        c = a + t * L * d
        판m = 자름(자름(안, d, c - 두 / 2 * d), -d, c + 두 / 2 * d)
        out.append(판m - 뼈m - K)                          # K = 이 뼈를 뺀 비움 (뼈 +0.4 와 +0.41 사이 0.01 지느러미가 생기지 않게)
    return 합(out)

def 홈(겉, 안쪽, 판n, 판p, 범위):
    """V 홈 근사: (겉 − 0.25 안쪽) ∩ 두께 0.8 판 ∪ (겉 − 0.5 안쪽) ∩ 두께 0.4 판, 범위 상자 안."""
    out = []
    for dd, w in ((0.25, 0.8), (0.5, 0.4)):
        판m = 자름(자름(범위, 판n, np.asarray(판p) - w / 2 * 단(판n)), -np.asarray(판n), np.asarray(판p) + w / 2 * 단(판n))
        out.append((겉 - 안쪽(dd)) ^ 판m)
    return 합(out)

# ════════ ⑥ 짓기 ════════════════════════════════════════════════
def 짓기():
    global J2
    J2 = J2껍질(); 로그("J2 볼록 껍질 %d" % len(J2))
    K, B, Jd = 비움들(); 로그("비움 · 쓸기 끝")
    부 = {}; 기록 = {}

    # ── 허벅지 ──
    허 = 허벅지모양(); 허["S"] = z단면(허["단면"], 0.30, 0.22)
    n, p = 뼈평면("L허벅지")
    껍 = 허["겉"] - 허["안"] - K["허벅지"]
    안쪽 = lambda dd: 로프트(허["S"], d=-dd)
    껍 = 껍 - 홈(허["겉"], 안쪽, Z, (0, 0, 146.0), 상자([-40, -10, 140], [0, 16, 152]))      # 앞면 가로 한 줄
    껍 = 껍 + 갈비(허["갈안"], K["허벅지_뼈빼고"], "L허벅지", [0.35, 0.80])
    zc = [133.0, 155.0]
    후보 = []
    for z0 in (135.0, 152.0):
        for 쪽 in (0, 1):
            묶 = []
            for z in (z0, z0 + 4, z0 - 4, z0 + 8, z0 - 8):
                a = 폭(z, -22, "평")
                for o in (3.9, 4.6, 5.4, 6.2):
                    x = a[0] + o if 쪽 == 0 else min(a[1], -6.5) - o
                    y = p[1] - (n[0] * (x - p[0]) + n[2] * (z - p[2])) / n[1]; 묶.append((x, y, z))
            후보.append(묶)
    보스, 핀, 구멍, 쓴 = 다보(허["겉"], K["허벅지"], n, p, 후보)
    전 = (껍 + 보스)
    부["허벅지앞"] = 자름(전, -n, p) + 핀; 부["허벅지뒤"] = 자름(전, n, p) - 구멍
    기록["허벅지"] = dict(단면수=len(허["단면"]), 다보=쓴, 이음면=dict(법선=n.round(3).tolist(), 점=p.round(2).tolist()))

    # ── 정강이 ──
    정 = 정강이모양(); 정["S"] = z단면(정["단면"], 0.42, 0.25)
    n, p = 뼈평면("L정강이")
    안쪽 = lambda dd: 로프트(정["S"], d=-dd)
    껍 = 정["겉"] - 정["안"] - K["정강이"]
    # 앞 V 셰브론 (45°) 두 줄 — 발목 위 나팔 시작 자리
    cx = (폭(50, -30, "평")[0] + 폭(50, -30, "평")[1]) / 2
    for s in (-1, 1):
        pp = np.array([cx, 0, 52.0])
        범 = 상자([cx - 20, -5, 38], [cx, 30, 60]) if s < 0 else 상자([cx, -5, 38], [cx + 20, 30, 60])
        껍 = 껍 - 홈(정["겉"], 안쪽, [s * 0.7071, 0, 0.7071], pp, 범 ^ 상자([-80, -10, 38], [0, 21, 70]))
    껍 = 껍 + 갈비(정["갈안"], K["정강이_뼈빼고"], "L정강이", [0.30, 0.62])
    후보 = []
    for z0 in (48.0, 80.0, 100.0):
        for 쪽 in (0, 1):
            묶 = []
            for z in (z0, z0 + 4, z0 - 4, z0 + 8, z0 - 8):
                a = 폭(z, -30, "평")
                for o in (3.9, 4.6, 5.4, 6.2):
                    x = a[0] + o if 쪽 == 0 else a[1] - o
                    y = p[1] - (n[0] * (x - p[0]) + n[2] * (z - p[2])) / n[1]; 묶.append((x, y, z))
            후보.append(묶)
    보스, 핀, 구멍, 쓴 = 다보(정["겉"], K["정강이"], n, p, 후보)
    # 무릎 장갑 핀 자리 (정강이 앞 벽 · 구멍 + 뒤 받침)
    무 = 무릎장갑모양(허, 정)
    무핀, 무구멍, 받침 = [], [], []
    for dx in (-5.0, 5.0):
        x = 무["cx"] + dx; z = 108.5
        ray = 트(정["겉"]).ray.intersects_location([[x, -60, z]], [[0, 1, 0]])[0]
        yf = float(ray[:, 1].min())
        무핀.append(원기둥((x, yf - 3.0, z), (x, yf + 3.2, z), 1.0, 16))
        무구멍.append(원기둥((x, yf - 1.0, z), (x, yf + 3.5, z), 1.0 + 결합틈, 16))
        받침.append(원기둥((x, yf + 1.0, z), (x, yf + 4.5, z), 2.6, 24) ^ 정["겉"])
    받침m = 합(받침) - K["정강이"]
    전 = 껍 + 보스 + 받침m
    부["정강이앞"] = 자름(전, -n, p) + 핀 - 합(무구멍); 부["정강이뒤"] = 자름(전, n, p) - 구멍 - 합(무구멍)
    기록["정강이"] = dict(단면수=len(정["단면"]), 다보=쓴, 이음면=dict(법선=n.round(3).tolist(), 점=p.round(2).tolist()))

    # ── 무릎 장갑 (정강이에 핀 둘) ──
    무몸 = 무["몸"] - K["정강이"]
    # 핀이 장갑 안쪽 앞벽까지 이어지게 기둥
    기둥 = 합([원기둥((무["cx"] + dx, 1.0, 108.5), (무["cx"] + dx, 12.0, 108.5), 2.0, 20) ^ 무["겉"] for dx in (-5.0, 5.0)]) - 정["겉"]
    부["무릎장갑"] = 무몸 + 기둥 + 합(무핀)
    기록["무릎장갑"] = dict(붙음="정강이 앞 벽 핀 Ø2 × 2 (구멍 Ø2.4)")

    # ── 발 (발등 / 발바닥 · 가름 z=6) ──
    발 = 발모양()
    껍 = 발["겉"] - 발["안"] - K["발"]
    # 발목 ±30(+3 틈): 발에서 본 정강이 아랫단 앞 · 뒤 벽이 쓸고 가는 곳을 뺀다
    발목역 = [힌지틀("L발목", -a) for a in 각들(-33, 33, 6)]
    for 벽 in (상자([-100, -40, 0], [0, 16.0, 44]), 상자([-100, 35.0, 0], [0, 80, 44]), 상자([-100, -40, 0], [-47.0, 80, 44]), 상자([-27.0, -40, 0], [0, 80, 44])):
        껍 = 껍 - 쓸기(정["겉"] ^ 벽, 발목역)
    # 발목블록이 ±30 에 지나갈 구멍은 K 가 쓸어서 냈다
    껍 = 껍 + 갈비(발["갈안"], K["발_뼈빼고"], "L발", [0.25, 0.70])
    zc = 6.0
    후보 = [(x, y, zc) for x in (발x[0] + 3.9, 발x[1] - 3.9) for y in (-3.0, 40.0)]
    보스, 핀, 구멍, 쓴 = 다보(발["겉"], K["발"], Z, np.array([0, 0, zc]), 후보)
    전 = 껍 + 보스
    부["발바닥"] = 자름(전, -Z, (0, 0, zc)) + 핀; 부["발등"] = 자름(전, Z, (0, 0, zc)) - 구멍
    기록["발"] = dict(다보=쓴, 발목원통r=발["r"])

    # ── 발끝 + 발톱 ──
    끝 = 발끝모양(); 톱 = 발톱모양()
    j = 관절["L발끝"]; pt = np.array(j["피벗mm"])
    # 발끝 ↔ 발: 힌지 축 둘레 원통으로 사이를 가른다 (발끝 = 축에서 앞, 발 = 원통 밖 앞 잘라냄)
    rc = 8.4
    원 = 원기둥(pt - 40 * X, pt + 40 * X, rc, 64); 원틈 = 원기둥(pt - 40 * X, pt + 40 * X, rc + 0.4, 64)
    앞 = 상자([-100, -60, -5], [0, pt[1], 40])
    for k in ("발바닥", "발등"):
        부[k] = 부[k] - (앞 - 원틈)                      # 발 쪽: 축 앞은 원통 안만
    끝겉 = (끝["겉"] - 원틈) + (원 ^ 발["겉"] ^ 앞)     # 발끝 쪽 = 앞 로프트 + 축 둘레 둥근 뿌리(발 앞면 안에서)
    끝몸 = 끝겉 - 끝["안"] - K["발끝"]
    발앞 = 발["겉"] ^ 상자([-100, pt[1] - 1.0, -5], [0, pt[1] + 8.0, 40])
    끝몸 = 끝몸 - 쓸기(발앞, [힌지틀("L발끝", -a) for a in 각들(-33, 23, 7)])      # 발끝 −30~+20 (+3 틈)
    끝몸 = 끝몸 + 갈비(끝겉, K["발끝_뼈빼고"], "L발끝", [0.55], 덧=끼움틈)
    톱구멍 = []
    for k, t in 톱.items():
        a = t["뿌리"]; d = t["d"]
        핀 = 원기둥(a - 3.2 * d, a + 3.0 * d, 1.0, 16); 구 = 원기둥(a - 3.6 * d, a + 3.5 * d, 1.0 + 결합틈, 16)
        부["발톱" + k] = (t["몸"] - 끝겉) + 핀
        톱구멍.append(구)
    부["발끝"] = 끝몸 - 합(톱구멍)
    기록["발끝"] = dict(원통r=rc, 발톱=list(톱))
    for k in 부:
        cs = 부[k].decompose(); 기록.setdefault("버린조각mm3", {})[k] = round(sum(c.volume() for c in cs if c.volume() < 5.0), 2)
        부[k] = 합([c for c in cs if c.volume() >= 5.0])
    return 부, 기록, dict(허=허, 정=정, 무=무, 발=발, 끝=끝, K=K, B=B, Jd=Jd)

# ════════ ⑦ 검사 · 그림 ═══════════════════════════════════════════
import 관절부품 as JB
색 = dict(흰=(0.93, 0.93, 0.95), 무릎=(0.86, 0.88, 0.93), 금=(0.95, 0.75, 0.2), 뼈=(0.25, 0.25, 0.28), 빨=(0.9, 0.1, 0.1))
def 색of(k): return 색["금"] if k.startswith("발톱") else 색["무릎"] if k == "무릎장갑" else 색["흰"]
def 거울(m): return m.mirror((1, 0, 0))

def 투영(ms, 축, lo, hi, 칸=0.25):
    """메시들 → 투영 bool 격자 (축 'y' 로 누르면 (x,z), 'x' 면 (y,z))."""
    from PIL import Image, ImageDraw
    W = int((hi[0] - lo[0]) / 칸); H = int((hi[1] - lo[1]) / 칸); im = Image.new("1", (W, H)); dr = ImageDraw.Draw(im)
    for m in ms:
        t = 트(m); V = t.vertices[:, [0, 2]] if 축 == "y" else t.vertices[:, [1, 2]]
        P = (V - np.asarray(lo)) / 칸
        for f in t.faces: dr.polygon([tuple(P[i]) for i in f], fill=1)
    return np.array(im).T                                  # [a, z]

구간표 = {"허벅지": (129.0, 152.0, ["허벅지앞", "허벅지뒤"], -22), "정강이": (30.0, 104.0, ["정강이앞", "정강이뒤", "무릎장갑"], -30),
         "무릎장갑": (108.0, 126.0, ["무릎장갑", "정강이앞", "정강이뒤"], -30),
         "발": (6.0, 20.0, ["발등", "발바닥", "발끝", "발톱바깥", "발톱가운데", "발톱안"], -40)}

def 실루엣오차(ms, 쪽="L"):
    """부품 z 범위 행마다 투영 양끝 − 원화 양끝 (mm). 정면 = x · 옆 = y. 허벅지 z>150 은 가랑이라 바깥 끝만.
    무릎장갑 옆 = 앞 끝만 (뒤는 검정 무릎). 발 정면은 발톱 퍼짐이라 따로 안 잰다 (옆만)."""
    sgn = 1 if 쪽 == "L" else -1
    out = {}
    for 이름, (z0, z1, ks, seed) in 구간표.items():
        g = [ms[k] for k in ks]
        Pf = 투영(g, "y", (-95, -5), (95, 200)); Ps = 투영(g, "x", (-55, -5), (75, 200))
        ex, ey = [], []
        for z in np.arange(z0, z1 + 0.01, 1.0):
            k = int(round((z + 5) / 0.25)); kk = int(np.argmin(abs(AZ - z)))
            if 이름 != "발":
                w1 = np.nonzero(Pf[:, k])[0]; r = (w1[0] * 0.25 - 95, w1[-1] * 0.25 - 95) if len(w1) else None
                m = _구간(F정[:, kk], AX, sgn * seed)
                if r and m:
                    if 이름 == "허벅지" and z > 150: ex.append(abs(r[0] - m[0]) if sgn > 0 else abs(r[1] - m[1]))
                    else: ex.append(max(abs(r[0] - m[0]), abs(r[1] - m[1])))
            if 이름 == "발":                                   # 발 · 발끝 · 발톱은 틈이 있어 한 조각이 아니다 → 전체 양끝
                w1 = np.nonzero(Ps[:, k])[0]; w2 = np.nonzero(F옆[:, kk])[0]
                rs = (w1[0] * 0.25 - 55, w1[-1] * 0.25 - 55) if len(w1) else None; ms_ = (AY[w2[0]], AY[w2[-1]]) if len(w2) else None
            else:
                w1 = np.nonzero(Ps[:, k])[0]; rs = (w1[0] * 0.25 - 55, w1[-1] * 0.25 - 55) if len(w1) else None; ms_ = _구간(F옆[:, kk], AY, 22)
            if rs and ms_:
                ey.append(abs(rs[0] - ms_[0]) if 이름 == "무릎장갑" else max(abs(rs[0] - ms_[0]), abs(rs[1] - ms_[1])))
        f = lambda e: dict(최대=round(float(np.max(e)), 2), p95=round(float(np.percentile(e, 95)), 2), 평균=round(float(np.mean(e)), 2),
                           안2mm=round(float(np.mean(np.array(e) <= 2.0)), 2), 행=len(e)) if e else None
        out[이름] = dict(정면=f(ex), 옆=f(ey))
    return out

def 칠하기(ax, 목록, 방위, 앙각):
    JB.칠(ax, [(트(m), c) for m, c in 목록 if not m.is_empty()], 방위=방위, 앙각=앙각)

def 그림(부L, 부R, 뼈들, 자세들, 경로, 겹표):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
    fig = plt.figure(figsize=(26, 17), dpi=90)
    gs = fig.add_gridspec(2, 4)
    ax = fig.add_subplot(gs[0, 0])
    칠하기(ax, [(m, 색["뼈"]) for m in 뼈들] + [(m, 색of(k)) for k, m in 부L.items()] + [(m, 색of(k)) for k, m in 부R.items()], 0, 0)
    ax.contour(AX, AZ, F정.T.astype(float), [0.5], colors="r", linewidths=0.8)
    ax.set_xlim(-85, 85); ax.set_ylim(-3, 175); ax.set_title("정면 · 빨강 = 원화 윤곽")
    ax = fig.add_subplot(gs[0, 1])
    칠하기(ax, [(m, 색["뼈"]) for m in 뼈들[:len(뼈들) // 2]] + [(m, 색of(k)) for k, m in 부L.items()], -90, 0)
    ax.contour(AY, AZ, F옆.T.astype(float), [0.5], colors="r", linewidths=0.8)
    ax.set_xlim(-45, 65); ax.set_ylim(-3, 175); ax.set_title("옆 (L) · 빨강 = 원화 윤곽")
    ax = fig.add_subplot(gs[0, 2])
    칠하기(ax, [(m, 색of(k)) for k, m in 부L.items()] + [(m, 색of(k)) for k, m in 부R.items()], -35, 18); ax.set_title("3/4")
    ax = fig.add_subplot(gs[0, 3])
    칠하기(ax, [(m, 색of(k)) for k, m in 부L.items()] + [(m, 색of(k)) for k, m in 부R.items()], 145, 18); ax.set_title("뒤 3/4")
    for i, (이름, (목록, 겹m)) in enumerate(자세들.items()):
        ax = fig.add_subplot(gs[1, i])
        칠하기(ax, 목록 + ([(겹m, 색["빨"])] if not 겹m.is_empty() else []), -90, 0)
        ax.set_title("%s (옆) · 장갑 겹침 %.1f mm³" % (이름, 겹표.get(이름, 0.0)))
    ax = fig.add_subplot(gs[1, 3])
    폭발 = dict(허벅지앞=(0, -18, 0), 허벅지뒤=(0, 14, 0), 무릎장갑=(0, -30, 4), 정강이앞=(0, -16, 0), 정강이뒤=(0, 14, 0),
              발등=(0, 0, 10), 발바닥=(0, 0, -10), 발끝=(0, -12, 2), 발톱바깥=(-8, -22, 0), 발톱가운데=(0, -24, 0), 발톱안=(6, -22, 0))
    칠하기(ax, [(m.translate(폭발.get(k, (0, 0, 0))), 색of(k)) for k, m in 부L.items()], -60, 15); ax.set_title("분해도 (L)")
    fig.tight_layout(); fig.savefig(경로); plt.close(fig)

def 자세검사(부, 속):
    """무릎 90/120/150 · 발목 ±30 · 발끝 −30/+20 — 움직인 쪽 장갑 ∩ 가만한 쪽 장갑 (mm³)."""
    허 = [부["허벅지앞"], 부["허벅지뒤"]]; 정 = [부["정강이앞"], 부["정강이뒤"], 부["무릎장갑"]]
    발 = [부["발등"], 부["발바닥"]]; 끝 = [부["발끝"]] + [부["발톱" + k] for k in ("바깥", "가운데", "안")]
    아래 = 정 + 발 + 끝
    out = {}; 그림용 = {}
    for θ in (90, 120, 150):
        T = 무릎틀(θ); 움 = [놓(m, T) for m in 아래]
        e = 합([a ^ b for a in 움[:3] for b in 허]); v = 부피(e)
        뼈겹 = 놓(속["B"]["L정강이"], T) ^ 합(허)
        out["무릎%d" % θ] = dict(장갑=round(v, 1), 정강이뼈비움_허벅지장갑=round(부피(뼈겹), 1))
        if θ in (90, 150):
            그림용["무릎 %d°" % θ] = ([(m, 색["흰"]) for m in 허] + [(m, 색["무릎"]) for m in 움[:3]] + [(m, 색["흰"]) for m in 움[3:]], e)
    최대 = 0
    for θ in range(90, 151, 5):
        T = 무릎틀(θ)
        if 부피(합([놓(a, T) ^ b for a in 정 for b in 허])) > 0.5: break
        최대 = θ
    out["무릎_무간섭최대각"] = 최대
    for θ in (-30, 30):
        T = 힌지틀("L발목", θ); 움 = [놓(m, T) for m in 발 + 끝]
        e = 합([a ^ b for a in 움 for b in 정]); out["발목%+d" % θ] = dict(장갑=round(부피(e), 1))
        if θ == 30: 그림용["발목 +30°"] = ([(m, 색["흰"]) for m in 정] + [(m, 색["흰"]) for m in 움], e)
    for θ in (-30, 20):
        T = 힌지틀("L발끝", θ); 움 = [놓(m, T) for m in 끝]
        e = 합([a ^ b for a in 움 for b in 발]); out["발끝%+d" % θ] = dict(장갑=round(부피(e), 1))
    ks = list(부); 정적 = {}
    for i in range(len(ks)):
        for j in range(i + 1, len(ks)):
            v = 겹(부[ks[i]], 부[ks[j]])
            if v > 0.05: 정적["%s·%s" % (ks[i], ks[j])] = round(v, 2)
    out["0자세_부품끼리"] = 정적
    return out, 그림용

def 앞차기검사(부):
    """골반 · 스커트 대리 = 몸 장 중 z 170~200 · L 쪽. 허벅지 장갑을 앞차기 45/90 으로 돌려 교집합."""
    d = np.load(os.path.join(ROOT, "out", "가동", "장384.npz")); g = d["g"]
    q = np.load(os.path.join(ROOT, "out", "분할후보", "입력.npz")); O = q["O"]; 축i = float(q["축i"])
    zs = np.nonzero(O.any((0, 1)))[0]; C = 300.0 / (zs[-1] - zs[0] + 1); y0 = np.argwhere(O[:, :, zs[0]:zs[0] + 2])[:, 1].mean()
    Bm = (g > 0) & O.repeat(2, 0).repeat(2, 1).repeat(2, 2)
    b4 = (np.array([-0.25, -0.25, -0.25]) - np.array([축i, y0, zs[0] - 0.5])) * C; h = C / 2
    zc = np.arange(384) * h + b4[2]; xc = np.arange(384) * h + b4[0]
    sel = Bm & (zc[None, None, :] > 170.0) & (zc[None, None, :] < 200.0) & (xc[:, None, None] < 0)
    from skimage.measure import marching_cubes
    idx = np.argwhere(sel); lo = idx.min(0) - 1; hi = idx.max(0) + 2
    f = np.pad(sel[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]], 1).astype(np.float32); v, fc, _, _ = marching_cubes(f, 0.5)
    골반 = 만((v - 1 + lo) * h + b4, fc)
    허 = 합([부["허벅지앞"], 부["허벅지뒤"]])
    return {"앞차기%d" % θ: round(부피(놓(허, 힌지틀("L고관절", θ)) ^ 골반), 1) for θ in (45, 90)}

def _stl왕복(m):
    import io
    b = io.BytesIO(); 트(m).export(b, file_type="stl"); b.seek(0); return trimesh.load(b, file_type="stl")

def 떼기(m, r=0.08, 번=10):
    """STL 로 한 번 내보내 다시 읽고(위치로 정점 합침) 면 넷 이상이 만나는 모서리(자기 접촉)를 찾아
    그 모서리 가운데마다 반지름 r 구를 깎아 떼어 낸다 (0.05 mm 넘게 벌어진다). 없어질 때까지 되풀이."""
    from collections import Counter
    n점 = 0
    for _ in range(번):
        t = _stl왕복(m)
        if t.is_watertight: break
        c = Counter(map(tuple, t.edges_sorted)); bad = np.array([e for e, n in c.items() if n != 2])
        if len(bad) == 0: break
        P = t.vertices[bad].mean(1)
        rr = r if _ == 0 else 0.6                           # 두 번째부터: 얇은 지느러미(두 면 사이 0 두께)를 끊는다
        P = np.unique(np.round(P / (rr * 1.5)) * (rr * 1.5), axis=0); n점 += len(P)
        m = m - 합([M.Manifold.sphere(rr, 12).translate(tuple(q)) for q in P])
        m = 합([c for c in m.decompose() if c.volume() >= 5.0])
    return m, n점

def 닫힘검사(경로):
    t = trimesh.load(경로); return bool(t.is_watertight), int(len(t.split(only_watertight=False)))

if __name__ == "__main__":
    부, 기록, 속 = 짓기()
    부R = {k: 거울(m) for k, m in 부.items()}
    for k, m in 부.items(): 로그(k, "%.2f cm³" % (부피(m) / 1000), "조각", [round(c.volume(), 1) for c in m.decompose()])
    실 = dict(L=실루엣오차(부, "L"), R=실루엣오차(부R, "R")); 로그("실루엣", json.dumps(실, ensure_ascii=False))
    자, 그림용 = 자세검사(부, 속); 로그("자세", json.dumps(자, ensure_ascii=False))
    try: 차 = 앞차기검사(부)
    except Exception as e: 차 = {"오류": repr(e)}
    로그("앞차기", 차)
    뼈들 = [속["B"][n] for n in 다리뼈]; 뼈들 = 뼈들 + [거울(m) for m in 뼈들]
    겹표 = {"무릎 90°": 자["무릎90"]["장갑"], "무릎 150°": 자["무릎150"]["장갑"], "발목 +30°": 자["발목+30"]["장갑"]}
    그림(부, 부R, 뼈들, 그림용, os.path.join(OUT, "보기.png"), 겹표)
    표 = {}
    for 쪽, D in (("L", 부), ("R", 부R)):
        for k, m in D.items():
            m, n점 = 떼기(m); D[k] = m
            f = os.path.join(OUT, "%s%s.stl" % (쪽, k)); 트(m).export(f)
            wt, nc = 닫힘검사(f)
            표["%s%s" % (쪽, k)] = dict(뗀점=n점, 부피mm3=round(부피(m), 1), 무게g=round(부피(m) * PLA, 2), 닫힘=wt, 조각=nc, 파일=os.path.basename(f))
    무게 = round(sum(v["무게g"] for v in 표.values()), 1)
    json.dump(dict(설명=__doc__, 부품=표, 기록=기록, 실루엣오차mm=실, 가동겹침mm3=자, 앞차기_골반대리겹침mm3=차, 총무게g=무게),
              open(os.path.join(OUT, "부품.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    로그("총 무게 %.1f g · 닫힘 %d/%d" % (무게, sum(v["닫힘"] for v in 표.values()), len(표)))
