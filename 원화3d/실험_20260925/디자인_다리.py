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
다리관절 = ["L고관절벌림", "L고관절", "L허벅지회전", "L무릎", "L발목볼", "L발목", "L발끝"]
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
        h = JG.볼록덧(v["m"], 비움틈); g = h.to_mesh(); V, F = np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts)
        if len(F) == 0: 로그("  J2 빈 조각", n, k, v["m"].volume()); continue
        out["%s|%s" % (n, k)] = (V, F)
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
허벅지위, 허벅지아래 = 186.0, 126.0
허앞컷 = ((0, 0.55, 0.835), (0, 12.0, 128.5))
정뒤컷 = ((0, -0.80, -0.60), (0, 38.0, 92.0))          # 2바퀴: 8 mm 낮춤 · 빈 곳은 검정 오금
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
    컷.append(허앞컷)                                             # 앞 아랫단
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
    """오각 방패: 아랫단 ~ z 122 는 원화 정면 폭 · 앞선 그대로, 그 위는 뾰족 끝(z 134.5)으로 좁아짐. 앞 모따기 = 능선 + 용골 1 mm."""
    rows = []
    for z, y1 in ((104.0, 17.0), (110.0, 15.5), (116.0, 14.0), (122.0, 13.0), (126.0, 12.5)):
        a = 폭(z, -30, "평"); rows.append((z, (a[0] + a[1]) / 2, (a[1] - a[0]) / 2 - 0.3, 깊이(z)[0], y1))
    c1 = rows[-1][1]; w1 = rows[-1][2]
    rows += [(129.5, c1, 0.55 * w1, 2.5, 12.5), (132.0, c1, 0.28 * w1, 6.0, 12.5), (134.5, c1, 0.8, 9.5, 12.5)]
    S = [(z, 팔각(c - w, c + w, y0, y1, 0.45 * min(2 * w, y1 - y0), 0.1)) for z, c, w, y0, y1 in rows]
    겉 = 로프트(S)
    안 = 로프트([(z, 팔각(c - w + 두께, c + w - 두께, y0 + 두께, y1 + 10, 0.45 * min(2 * w, y1 - y0), 0.1)) for z, c, w, y0, y1 in rows[:-2]])
    안 = 자름(안, Z, [0, 0, 104.0 + 1.2])
    용골 = M.Manifold.hull_points(np.array([[c + dx, y0 + dy, z] for z, c, w, y0, y1 in (rows[0], rows[3]) for dx in (-1.1, 1.1) for dy in (-1.0, 2.5)]))
    겉 = 겉 + 용골
    cn, cp = 허앞컷; cn = 단(cn)
    m = 겉 - 안 - 자름(로프트(허["S"], d=1.2), cn, np.asarray(cp) - 0.4 * cn) - 정["겉"]      # 허벅지 앞 판(0.8) + 틈 0.4
    return dict(겉=겉, 몸=m, cx=(rows[1][1] + rows[2][1]) / 2)

def 오금모양(정):
    """검정 오금: 정강이 뒤 윗단(8 mm 낮춤)과 허벅지 뒤 아랫단 사이 · 원화 옆 뒤선까지."""
    rows = []
    for z in (94.0, 104.0, 114.0, 124.0, 130.0):
        a = 폭(z, -30, "평"); b = 깊이(z); rows.append((z, 팔각(a[0] + 2.0, a[1] - 2.0, 24.0, b[1] - 0.5, 0.5, 3.0)))
    return dict(겉=로프트(rows), 바닥=94.0)

# 발: y 방향 로프트 · 단면 (x, z) — 윗선은 옆 마스크 앞선, 폭은 정면 z 22~26 에서
발x = (-61.0, -20.0)
발원r = 16.8
발안쪽컷 = ((-1.0, 0.0, 1.75), (-41.25, 0, 0))     # 원화 정면: 발 안쪽 아랫단 (z 3 에서 x −36 · z 12 에서 −20)
def 발모양():
    rows = [(-9.0, 0.0, 19.0), (-2.0, 0.0, 24.0), (4.0, 0.0, 26.0), (22.0, 0.0, 27.0), (38.0, 0.0, 26.0), (45.0, 1.5, 24.5), (49.5, 5.0, 19.0)]
    x0, x1 = 발x
    def 단(y, z0, z1, 좁=0.0):
        return 팔각(x0 + 좁, x1 - 좁, z0, z1, 1.2, 0.30 * (x1 - x0))   # b = z · 앞(작은 b) = 바닥 모따기 작게 · 위 모따기 크게
    S = [(y, 단(y, z0, z1, 1.5 if y > 45 else 0.0)) for y, z0, z1 in rows]
    겉 = 로프트(S, "y"); 안 = 로프트(S, "y", d=-두께)
    안 = 자름(자름(안, Y, [0, -9.0 + 두께, 0]), -Y, [0, 49.5 - 두께, 0])
    겉 = 자름(겉, *발안쪽컷); 안 = 자름(안, 발안쪽컷[0], np.asarray(발안쪽컷[1]) + 두께 * np.asarray(발안쪽컷[0]) / np.linalg.norm(발안쪽컷[0]))
    # 발목 힌지 둘레 원통: 정강이 아랫단이 ±30 에 안 닿게 발 윗면을 축 둘레 반지름 r 안으로
    j = 관절["L발목"]; p = np.array(j["피벗mm"])
    r = 발원r
    원 = 원기둥(p - 40 * X, p + 40 * X, r, 96)
    위 = 상자([-100, -20.0, p[2]], [0, 60.0, 60])                      # 정강이 발자국 위만 원통으로
    겉 = (겉 - 위) + (겉 ^ 위 ^ 원); 안 = (안 - 위) + (안 ^ 위 ^ 원기둥(p - 40 * X, p + 40 * X, r - 두께, 96))
    return dict(겉=겉, 안=안, r=r, S=S, 갈안=로프트(S, "y", d=-(두께 - 0.3)) ^ 겉)

def 발끝모양():
    j = 관절["L발끝"]; p = np.array(j["피벗mm"])
    x0, x1 = 발x[0] + 2.0, 발x[1] - 2.0
    rows = [(p[1] - 0.4, 0.8, 20.0), (-16.0, 1.0, 17.5), (-25.5, 1.5, 12.5)]
    S = [(y, 팔각(x0, x1, z0, z1, 1.0, 0.28 * (x1 - x0))) for y, z0, z1 in rows]
    겉 = 자름(로프트(S, "y"), *발안쪽컷)
    안 = 자름(자름(로프트(S, "y", d=-두께), -Y, [0, p[1] - 0.4 - 두께, 0]), Y, [0, -25.5 + 두께, 0])
    # 발끝 힌지 둘레: 발 앞 아랫단 원통 컷 (발끝이 −30~20 돌 때 발 앞면과)
    return dict(겉=겉, 안=안, p=p)

def 발톱모양():
    """금 발톱 셋: 뿌리 = 발끝 앞면 · 끝 = 원화 정면 · 옆 실루엣 끝. 육각 뿔(뿌리 단면 → 끝 점)."""
    cx0, cx1 = 발x
    spec = {"바깥": ((cx0 + 4.0, -13.0, 17.0), (-86.0, -27.0, 3.5), 6.0, (-74.0, -21.0, 11.0), 4.5),   # 원화 정면: 발 옆 높이에서 바깥 아래로 긴 사선 (꺾임 하나)
            "가운데": ((-41.5, -22.0, 10.5), (-45.5, -36.0, 3.0), 5.4),
            "안": ((cx1 - 6.0, -21.0, 12.0), (-28.0, -32.5, 8.5), 4.0),          # 2바퀴: 안쪽 3 mm 줄임 (허벅지회전 L·R) · 원화 정면 안쪽선에 맞춰 높임
            "뒤꿈치": ((-41.5, 44.5, 4.5), (-41.5, 51.0, 7.0), 4.0)}
    out = {}
    for k, sp in spec.items():
        a, b, r = np.array(sp[0]), np.array(sp[1]), sp[2]; d = 단(b - a)
        u = 단(np.cross(d, Z)); v = np.cross(u, d)
        고리 = lambda c, rr, dd=d: [c + rr * (np.cos(t) * u + 0.75 * np.sin(t) * v) for t in np.linspace(0, 2 * np.pi, 6, endpoint=False)]
        tip = [b + 0.35 * (np.cos(t) * u + np.sin(t) * v) for t in np.linspace(0, 2 * np.pi, 6, endpoint=False)]
        if len(sp) > 3:                                  # 꺾인 발톱: 뿌리 → 꺾임 → 끝 두 토막
            mid = 고리(np.array(sp[3]), sp[4])
            몸 = M.Manifold.hull_points(np.array(고리(a, r) + 고리(a - 3.0 * d, 0.8 * r) + mid)) + M.Manifold.hull_points(np.array(mid + tip))
        else:
            몸 = M.Manifold.hull_points(np.array(고리(a, r) + 고리(a - 3.0 * d, 0.8 * r) + tip))
        out[k] = dict(몸=몸, 뿌리=a, 끝=b, d=d)
    return out

# ════════ ⑤ 반쪽 · 다보 · 갈비 · 패널라인 ════════════════════════════
def 뼈평면(뼈n):
    """뼈 선을 품고 x 축에 평행한 평면 (법선은 +y 쪽) — 앞뒤 반쪽 이음면."""
    s = JG.뼈선(뼈n); a = s[0][0]; b = s[-1][1]; d = 단(b - a)
    n = 단(np.cross(d, X)); n = n if n[1] > 0 else -n
    return n, (a + b) / 2

def 다보(겉, K, n, p, 후보, 앞길이=4.5, 뒤길이=4.5):
    """이음면 위 후보점마다 보스(Ø4.5 · 이음면 ±4.5) — 겉 안에 다 들고 비움과 안 겹칠 때만. 핀 Ø2×2.5 은 앞 반쪽, 구멍 Ø2.4×3.0 은 뒤."""
    보스, 핀, 구멍, 쓴 = [], [], [], []
    for q0 in 후보:                                  # 후보 = 점 하나 또는 점 묶음(앞에서부터 처음 되는 것)
        묶 = [q0] if np.ndim(q0) == 1 else q0
        for q in 묶:
            q = np.asarray(q, float); b = 원기둥(q - 앞길이 * n, q + 뒤길이 * n, 2.25, 24)
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

# ════════ ⑤½ 골반 (2바퀴): 허벅지 윗단 · 가랑이 · 허리 쪽 쓸기 ═══════════════
벨트밑 = 188.0                                  # D1 벨트 아랫면 (비평 1바퀴)
벌림범위, 차기범위 = (-10.0, 45.0), (-30.0, 90.0)
def 역(T): R = T[:, :3]; return np.c_[R.T, -R.T @ T[:, 3]]
def 허리틀(a, k):
    """허벅지위(고관절 아래) 의 허리 기준 자세 = 벌림(a) ∘ 앞차기(k)."""
    return 합성(힌지틀("L고관절벌림", a), 힌지틀("L고관절", k))

def 격자쓸기(m, A, Kk, 틀=None):
    """허리에 붙은 볼록 조각 m 을 허벅지위 기준으로 옮긴 자세들(벌림 × 앞차기 격자)을 두 방향으로 이어 쓴다."""
    틀 = 틀 or (lambda a, k: 역(허리틀(a, k)))
    out = [쓸기(m, [틀(a, k) for k in Kk]) for a in A] + [쓸기(m, [틀(a, k) for a in A]) for k in Kk]
    return 합(out)

def 몸장점(z0, z1, xmax):
    d = np.load(os.path.join(ROOT, "out", "가동", "장384.npz")); g = d["g"]
    q = np.load(os.path.join(ROOT, "out", "분할후보", "입력.npz")); O = q["O"]; 축i = float(q["축i"])
    zs = np.nonzero(O.any((0, 1)))[0]; C = 300.0 / (zs[-1] - zs[0] + 1); y0 = np.argwhere(O[:, :, zs[0]:zs[0] + 2])[:, 1].mean()
    Bm = (g > 0) & O.repeat(2, 0).repeat(2, 1).repeat(2, 2)
    b4 = (np.array([-0.25, -0.25, -0.25]) - np.array([축i, y0, zs[0] - 0.5])) * C; h = C / 2
    P = np.argwhere(Bm) * h + b4
    return P[(P[:, 2] >= z0) & (P[:, 2] <= z1) & (np.abs(P[:, 0]) <= xmax)]

def 벨트대리():
    """D1 벨트 대리 = 몸 장 z 188~206 · |x| ≤ 36 의 볼록 껍질 + 0.5. (D1 실제 벨트 메시가 나오면 바꾼다)"""
    return JG.볼록덧(M.Manifold.hull_points(몸장점(벨트밑 + 0.5, 206.0, 36.0)), 0.5)

def 가랑이모양():
    """검정 가랑이 블록 (허리 뼈에 붙음 · x ±8 · z 164~188). 대칭 팔각 로프트."""
    rows = [(164.0, 4.6, 7.0, 23.0), (169.0, 8.15, 3.0, 27.0), (벨트밑 - 0.3, 8.15, 2.0, 28.0)]
    S = [(z, 팔각(-w, w, y0, y1, 2.0, 2.0)) for z, w, y0, y1 in rows]
    return dict(겉=로프트(S), 안=자름(자름(로프트(S, d=-두께), Z, [0, 0, 164.0 + 두께]), -Z, [0, 0, 벨트밑 - 0.3 - 두께]),
                갈안=로프트(S, d=-(두께 - 0.3)), S=S)

def 허리조각():
    """허리에 붙은 것 중 허벅지위가 스칠 수 있는 볼록 조각들 (+0.4): 허리 뼈 L 가지 · 가운데 · 고관절벌림 외피 · J2."""
    ms = [JG.캡슐(a, b, ra + 비움틈, rb + 비움틈, 20) for a, b, ra, rb in JG.뼈선("허리") if min(a[0], b[0]) < 1.0]
    ms += [JG.외피메시(관절["L고관절벌림"], 비움틈, 40)] + [m for k, m in J2.items() if k.split("|")[0] == "L고관절벌림"]
    return ms

# ════════ ⑥ 짓기 ════════════════════════════════════════════════
def 볼(t, xx=0.0):
    bp = 관절["L발목볼"]["피벗mm"]; return 합성(강체(회전행렬(Y, t), bp), 강체(회전행렬(X, xx), bp))
def 발틀(t, a, xx=0.0): return 합성(볼(t, xx), 힌지틀("L발목", a))
발목격자 = dict(t=각들(-27, 27, 9), a=각들(-33, 33, 11), x=(-10.0, 0.0, 10.0))
def 발목쓸기(m, 앞=True):
    """볼록 m 을 발목 격자(옆기울기 t × 힌지 a, 볼 x ±10) 로 쓴다. 앞=True: 발 자세로(정강이 기준) · False: 역(발 기준)."""
    f = (lambda t, a, xx: 발틀(t, a, xx)) if 앞 else (lambda t, a, xx: 역(발틀(t, a, xx)))
    G = 발목격자; out = []
    for xx in G["x"]:
        out += [쓸기(m, [f(t, a, xx) for a in G["a"]]) for t in G["t"]] + [쓸기(m, [f(t, a, xx) for t in G["t"]]) for a in G["a"]]
    return 합(out)

def 판올림(겉단면, 축, 범위, 높이=0.8):
    """판 겹침 단차: 로프트를 높이만큼 부풀린 것 − 원래 겉, 범위(볼록) 안만."""
    return (로프트(겉단면, 축, d=높이) - 로프트(겉단면, 축, d=-0.3)) ^ 범위     # 0.3 겹쳐 붙인다 (겉과 같은 면을 공유하면 STL 에서 자기 접촉)

def 이음후보(p, n, zs, 폭seed, 안쪽한계=None, 간격=(3.9, 4.6, 5.4, 6.2, 7.0), 흔들=(0, 4, -4, 8, -8)):
    후보 = []
    for z0 in zs:
        for 쪽 in (0, 1):
            묶 = []
            for z in [z0 + d for d in 흔들]:
                a = 폭(z, 폭seed, "평")
                for o in 간격:
                    x = a[0] + o if 쪽 == 0 else (min(a[1], 안쪽한계) if 안쪽한계 is not None else a[1]) - o
                    y = p[1] - (n[0] * (x - p[0]) + n[2] * (z - p[2])) / n[1]; 묶.append((x, y, z))
            후보.append(묶)
    return 후보

def 짓기():
    global J2
    J2 = J2껍질(); 로그("J2 볼록 껍질 %d" % len(J2))
    K, B, Jd = 비움들(); 로그("비움 · 쓸기 끝")
    부 = {}; 기록 = {}; 중앙 = {}

    # ── 허리 쪽 쓸기 (벨트 대리 · 가랑이 · 허리 뼈 · 고관절벌림) : 허벅지위 기준 벌림 × 앞차기 격자 ──
    가 = 가랑이모양(); 벨 = 벨트대리()
    A = 각들(벌림범위[0] - 2, 벌림범위[1] + 2, 7); Kk = 각들(차기범위[0] - 2, 차기범위[1] + 2, 8)
    허리쓸 = 합([격자쓸기(벨, A, Kk), 격자쓸기(JG.볼록덧(가["겉"], 비움틈), A, Kk)] + [격자쓸기(m, A, Kk) for m in 허리조각()])
    로그("허리 쪽 쓸기 끝")
    차기역 = [역(힌지틀("L고관절", k)) for k in 각들(차기범위[0] - 2, 차기범위[1] + 2, 8)]
    블록쓸 = 합([쓸기(JG.캡슐(a, b, ra + 비움틈, rb + 비움틈, 20), 차기역) for a, b, ra, rb in JG.뼈선("L고관절블록")]
               + [쓸기(m, 차기역) for k, m in J2.items() if k.split("|")[0] == "L고관절"])
    회 = 관절["L허벅지회전"]; ra = 단(회["축"]); rp = np.array(회["피벗mm"])
    회틀 = [강체(회전행렬(ra, a), rp) for a in 각들(-47, 47, 10)]
    K윗L = [B["L허벅지위"], JG.외피메시(관절["L고관절"], 비움틈, 40), Jd["L허벅지회전"], 쓸기(B["L허벅지"], 회틀), 블록쓸, 허리쓸]
    K윗 = 합(K윗L); K윗_뼈빼고 = 합(K윗L[1:])

    # ── 허벅지 (윗단 = 허벅지위 뼈 · 아래 = 허벅지 뼈 · 사이 = 허벅지회전 회전면 ±0.2) ──
    허 = 허벅지모양(); 허["S"] = z단면(허["단면"], 0.30, 0.22)
    # 무릎 뒤: 정강이 뒤 윗덩이를 무릎 0~138° 로 쓴 곳을 허벅지에서 뺀다 (둘째 축 둘레 원호가 저절로 생긴다)
    정 = 정강이모양(); 정["S"] = z단면(정["단면"], 0.42, 0.25)
    무릎틀들 = [무릎틀(θ) for θ in 각들(0, 141, 3)]
    무릎쓸 = 합([쓸기(JG.볼록덧(M.Manifold.batch_hull([정["겉"] ^ 상자([-100, 22.0, z], [0, 80, z + 6.0])]), 0.3), 무릎틀들) for z in np.arange(70.0, 130.0, 6.0)])
    허겉 = 허["겉"] - 무릎쓸 - 허리쓸
    아래겉 = 자름(허겉, ra, rp + 0.2 * ra); 윗겉 = 자름(허겉, -ra, rp - 0.2 * ra)
    # 아래 (허벅지)
    n, p = 뼈평면("L허벅지")
    껍 = 아래겉 - 허["안"] - K["허벅지"]
    cx = sum(폭(135, -22, "평")) / 2
    껍 = 껍 + 판올림(허["S"], "z", 자름(상자([-60, -20, 128.5], [0, 12, 142]), 단([-0.7071, 0, -0.7071]), (cx, 0, 139.0)))   # 앞 바깥 아래 45° 판
    껍 = 껍 + 갈비(허["갈안"] ^ 아래겉, K["허벅지_뼈빼고"], "L허벅지", [0.35, 0.80])
    보스, 핀, 구멍, 쓴 = 다보(아래겉, K["허벅지"], n, p, 이음후보(p, n, (130.0, 138.0, 145.0), -22, -6.5, 간격=(3.9, 4.6, 5.4, 6.2, 7.0, 8.0, 9.0), 흔들=(0, 2, -2, 3, -3)), 앞길이=2.0, 뒤길이=4.0)
    # 속이 무릎 · 회전 쓸기로 꽉 차 다보 보스가 안 들어간다 → 이음 턱: 앞 반쪽 벽 안쪽 절반(1 mm)이 이음면 너머 1.5 mm 들어가고 뒤 반쪽은 1.7 mm 파낸다
    벽안 = (로프트(허["S"], d=-1.0) - 로프트(허["S"], d=-2.05)) ^ 아래겉
    턱 = 자름(자름(벽안, n, p), -n, p + 1.5 * n) - K["허벅지"]
    턱자리 = 자름(자름(로프트(허["S"], d=-0.8) - 로프트(허["S"], d=-2.3), n, p - 0.01 * n), -n, p + 1.7 * n)
    전 = 껍 + 보스
    부["허벅지앞"] = 자름(전, -n, p) + 핀 + 턱; 부["허벅지뒤"] = 자름(전, n, p) - 구멍 - 턱자리
    기록["허벅지"] = dict(단면수=len(허["단면"]), 다보=쓴, 이음턱="앞 반쪽 벽 안쪽 1 mm × 1.5 mm (뒤 1.7 파냄 · 틈 0.2)", 회전면=dict(축=ra.round(3).tolist(), 점=rp.round(2).tolist()))
    # 윗단 (허벅지위)
    n, p = 뼈평면("L허벅지위")
    껍 = 윗겉 - 허["안"] - K윗
    껍 = 껍 + 갈비(허["갈안"] ^ 윗겉, K윗_뼈빼고, "L허벅지위", [0.55])
    보스, 핀, 구멍, 쓴 = 다보(윗겉, K윗, n, p, 이음후보(p, n, (152.0, 160.0, 168.0), -22, -8.0), 앞길이=2.0, 뒤길이=4.0)
    전 = 껍 + 보스
    부["허벅지윗단앞"] = 자름(전, -n, p) + 핀; 부["허벅지윗단뒤"] = 자름(전, n, p) - 구멍
    기록["허벅지윗단"] = dict(다보=쓴, 붙음="허벅지위 뼈 (반달 갈비)", 쓸기="벨트 대리 · 가랑이 · 허리 뼈 · 고관절벌림 (벌림 %s × 앞차기 %s)" % (벌림범위, 차기범위))

    # ── 가랑이 (검정 · 허리 뼈 · 가운데 x=0 에서 L/R 반쪽) ──
    허리뼈 = 뼈캡슐("허리", 끼움틈)
    움L = [쓸기(JG.캡슐(a, b, ra_ + 비움틈, rb + 비움틈, 20), [힌지틀("L고관절벌림", a_) for a_ in A]) for a, b, ra_, rb in JG.뼈선("L고관절블록")]
    움L += [쓸기(JG.외피메시(관절["L고관절"], 비움틈, 40), [힌지틀("L고관절벌림", a_) for a_ in A])]
    움L += [격자쓸기(JG.캡슐(a, b, ra_ + 비움틈, rb + 비움틈, 20), A, Kk, 틀=허리틀) for a, b, ra_, rb in JG.뼈선("L허벅지위")]
    움L += [JG.외피메시(관절["L고관절벌림"], 비움틈, 40)] + [m for k, m in J2.items() if k.split("|")[0] in ("L고관절벌림", "L고관절")]
    K가 = 합(움L); K가 = K가 + 거울(K가)
    가몸 = 가["겉"] - 가["안"] - K가 - 뼈캡슐("허리", 비움틈)
    판m = 자름(자름(가["갈안"], Z, (0, 0, 176.0)), -Z, (0, 0, 179.0))
    가몸 = 가몸 + (판m - 허리뼈 - K가)
    보스, 핀, 구멍, 쓴 = 다보(가["겉"], K가 + 뼈캡슐("허리", 비움틈), X, np.zeros(3),
                         [[(0, y, z) for y in (6.0, 8.0, 22.0, 24.0) for z in (zz, zz + 3)] for zz in (170.0, 183.0)] + [[(0, 25.0, 176.0), (0, 5.0, 176.0)]])
    반 = 자름(가몸 + 보스, -X, (-0.02, 0, 0))          # x=0 에 뼈 캡슐 정점이 있어 0.02 비켜 가른다 (L·R 사이 0.04)
    중앙["가랑이L"] = 반 + 핀; 중앙["가랑이R"] = 거울(반) - 구멍
    기록["가랑이"] = dict(다보=쓴, 붙음="허리 뼈 (가운데 판이 +0.10 로 끼움)")

    # ── 정강이 ──
    n, p = 뼈평면("L정강이")
    껍 = 정["겉"] - 정["안"] - K["정강이"]
    cxs = [(z, sum(폭(z, -30, "평")) / 2) for z in (46.0, 96.0)]
    앞판범위 = M.Manifold.hull_points(np.array([[c + dx, y, z] for z, c in cxs for dx in (-4.0, 4.0) for y in (-20.0, 22.0)]))
    껍 = 껍 + 판올림(정["S"], "z", 앞판범위 ^ 상자([-100, -20, 0], [0, 20, 200]))            # 앞 가운데 판 0.8 올림
    껍 = 껍 + 갈비(정["갈안"], K["정강이_뼈빼고"], "L정강이", [0.30, 0.62])
    보스, 핀, 구멍, 쓴 = 다보(정["겉"], K["정강이"], n, p, 이음후보(p, n, (46.0, 72.0, 98.0), -30), 앞길이=2.0, 뒤길이=4.0)
    무 = 무릎장갑모양(허, 정)
    무핀, 무구멍, 받침 = [], [], []
    for dx in (-5.0, 5.0):
        x = 무["cx"] + dx; z = 108.5
        ray = 트(정["겉"]).ray.intersects_location([[x, -60, z]], [[0, 1, 0]])[0]
        yf = float(ray[:, 1].min())
        무핀.append(원기둥((x, yf - 3.0, z), (x, yf + 3.2, z), 1.0, 16))
        무구멍.append(원기둥((x, yf - 1.0, z), (x, yf + 3.5, z), 1.0 + 결합틈, 16))
        받침.append(원기둥((x, yf + 1.0, z), (x, yf + 4.5, z), 2.6, 24) ^ 정["겉"])
    전 = 껍 + 보스 + (합(받침) - K["정강이"])
    부["정강이앞"] = 자름(전, -n, p) + 핀 - 합(무구멍); 부["정강이뒤"] = 자름(전, n, p) - 구멍 - 합(무구멍)
    기록["정강이"] = dict(단면수=len(정["단면"]), 다보=쓴)

    # ── 무릎 장갑 (방패 · 용골 · 정강이에 핀 둘) ──
    기둥 = 합([원기둥((무["cx"] + dx, 1.0, 108.5), (무["cx"] + dx, 12.0, 108.5), 2.0, 20) ^ 무["겉"] for dx in (-5.0, 5.0)]) - 정["겉"]
    부["무릎장갑"] = 무["몸"] - K["정강이"] + 기둥 + 합(무핀)
    기록["무릎장갑"] = dict(붙음="정강이 앞 벽 핀 Ø2 × 2 (구멍 Ø2.4)", 모양="오각 방패 + 용골 1 mm")

    # ── 오금 (검정 · 정강이 뒤 윗단 위 · 정강이 속으로 혀) ──
    오 = 오금모양(정)
    역무릎 = [역(무릎틀(θ)) for θ in 각들(0, 141, 3)]
    허뒤덩들 = [JG.볼록덧(M.Manifold.batch_hull([허겉 ^ 상자([-100, 20.0, z], [0, 80, z + 6.0])]), 0.4) for z in np.arange(112.0, 176.0, 6.0)]
    오몸 = 오["겉"] - 합([쓸기(m, 역무릎) for m in 허뒤덩들 if not m.is_empty()]) - K["정강이"] - 정["겉"]
    # 정강이 뒤 윗단 절단면(두께 2 뚜껑)에 핀 둘: 오금 쪽 핀 · 정강이 쪽 구멍 + 속 받침
    nn = 단(정뒤컷[0]); 오핀, 오구멍, 오받침 = [], [], []
    for dx in (-6.0, 6.0):
        c = sum(폭(98.0, -30, "평")) / 2 + dx; y = 33.0; z = 정뒤컷[1][2] - 0.8 * (y - 정뒤컷[1][1]) / 0.6
        q = np.array([c, y, z])
        오핀.append(원기둥(q - 2.5 * nn, q + 3.0 * nn, 1.0, 16)); 오구멍.append(원기둥(q - 0.5 * nn, q + 3.4 * nn, 1.0 + 결합틈, 16))
        오받침.append(원기둥(q + 1.0 * nn, q + 5.0 * nn, 2.6, 24) ^ 정["겉"])
    부["정강이뒤"] = 부["정강이뒤"] + (합(오받침) - K["정강이"] - 오몸) - 합(오구멍)
    부["오금"] = 오몸 + 합(오핀)
    기록["오금"] = dict(붙음="정강이 뒤 윗단 절단면에 핀 Ø2 × 2 (속 받침)")

    # ── 발 (발등 / 발바닥 · 가름 z=6) ──
    발 = 발모양()
    껍 = 발["겉"] - 발["안"] - K["발"]
    # 발목 옆기울기 ±25 · 힌지 ±30 · 볼 x ±10 (+2~3 틈): 발에서 본 정강이 아랫단 네 벽이 쓰는 곳을 뺀다
    발목컷 = 합([발목쓸기(정["겉"] ^ 벽, 앞=False) for 벽 in (상자([-100, -40, 0], [0, 16.0, 44]), 상자([-100, 35.0, 0], [0, 80, 44]),
                                                          상자([-100, -40, 0], [-47.0, 80, 44]), 상자([-27.0, -40, 0], [0, 80, 44]))])
    껍 = 껍 + 판올림(발["S"], "y", 상자([발x[0] + 4.0, -8.0, 14.0], [발x[1] - 4.0, 4.0, 40]))       # 발등 앞 판 0.8 올림
    껍 = 껍 + 갈비(발["갈안"], K["발_뼈빼고"], "L발", [0.25, 0.70])
    zc = 6.0
    후보 = [[(x, y, zc) for x in xs for y in ys] for xs in ((발x[0] + 3.9, 발x[0] + 5.0), (-30.0, -32.0, -34.0, -28.0)) for ys in ((-3.0, 0.0, 3.0), (40.0, 37.0, 34.0))]
    보스, 핀, 구멍, 쓴 = 다보(발["겉"], K["발"], Z, np.array([0, 0, zc]), 후보)
    전 = 껍 + 보스 - 발목컷                          # 갈비 · 보스까지 붙인 뒤에 뺀다 (갈비가 쓸린 곳을 다시 채우지 않게)
    부["발바닥"] = 자름(전, -Z, (0, 0, zc)) + 핀; 부["발등"] = 자름(전, Z, (0, 0, zc)) - 구멍
    기록["발"] = dict(다보=쓴, 발목원통r=발["r"])

    # 발목 띠: 2바퀴에 정강이 · 발목블록 두 자리에 시험했으나 발목 ±25/±30 쓸기가 거의 다 먹었다 (28~93 mm³) → 뺐다. 검은 띠 = 발목블록 뼈 자체.

    # ── 발끝 + 발톱 ──
    끝 = 발끝모양(); 톱 = 발톱모양()
    j = 관절["L발끝"]; pt = np.array(j["피벗mm"])
    rc = 8.4
    원 = 원기둥(pt - 40 * X, pt + 40 * X, rc, 64); 원틈 = 원기둥(pt - 40 * X, pt + 40 * X, rc + 0.4, 64)
    앞 = 상자([-100, -60, -5], [0, pt[1], 40])
    for k in ("발바닥", "발등"):
        부[k] = 부[k] - (앞 - 원틈) - (원틈 ^ 상자([-100, pt[1] - 0.01, -5], [0, pt[1] + 10.0, 40]))   # 뒤 반원도 비워 발끝 뿌리가 돌아 들어올 자리
    끝겉 = (끝["겉"] - 원틈) + (원 ^ 발["겉"] ^ 앞)
    끝몸 = 끝겉 - 끝["안"] - K["발끝"]
    발앞 = JG.볼록덧(M.Manifold.batch_hull([발["겉"] ^ 상자([-100, pt[1] - 1.0, -5], [0, pt[1] + 8.0, 40])]), 0.9)   # 발등 앞 판(0.8) 포함
    끝몸 = 끝몸 - 쓸기(발앞, [힌지틀("L발끝", -a) for a in 각들(-36, 24, 4)])
    끝몸 = 끝몸 + 갈비(끝겉, K["발끝_뼈빼고"], "L발끝", [0.55], 덧=끼움틈)
    톱구멍 = []; 뒤구멍 = []
    for k, t in 톱.items():
        a = t["뿌리"]; d = t["d"]
        핀 = 원기둥(a - 3.2 * d, a + (3.0 if k == "뒤꿈치" else 6.0) * d, 1.0, 16); 구 = 원기둥(a - 3.6 * d, a + (4.5 if k == "뒤꿈치" else 6.5) * d, 1.0 + 결합틈, 16)
        if k == "뒤꿈치":
            부["발톱뒤꿈치"] = (t["몸"] - 부["발바닥"] - 부["발등"] - 발["겉"]) + 핀; 뒤구멍.append(구)
        else:
            부["발톱" + k] = (t["몸"] - 끝겉 - 쓸기(발앞, [힌지틀("L발끝", -a_) for a_ in 각들(-36, 24, 4)])) + 핀; 톱구멍.append(구)
    부["발끝"] = 끝몸 - 합(톱구멍); 부["발바닥"] = 부["발바닥"] - 합(뒤구멍)
    기록["발끝"] = dict(원통r=rc, 발톱=list(톱))
    for D in (부, 중앙):
        for k in D:
            cs = D[k].decompose(); 기록.setdefault("버린조각mm3", {})[k] = round(sum(c.volume() for c in cs if c.volume() < 5.0), 2)
            D[k] = 합([c for c in cs if c.volume() >= (20.0 if k == "오금" else 5.0)])
    return 부, 기록, dict(허=허, 정=정, 무=무, 발=발, 끝=끝, K=K, B=B, Jd=Jd, 중앙=중앙, 벨=벨, 가=가)

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

검정 = ("가랑이", "오금", "발목띠")
색["검"] = (0.2, 0.2, 0.22); 색["벨"] = (0.55, 0.62, 0.75)
def 색of(k): return 색["금"] if k.startswith("발톱") else 색["무릎"] if k == "무릎장갑" else 색["검"] if k.startswith(검정) else 색["흰"]

구간표 = {"허벅지윗단": (160.0, 185.0, ["허벅지윗단앞", "허벅지윗단뒤"], -22),
         "허벅지": (129.0, 152.0, ["허벅지앞", "허벅지뒤", "허벅지윗단앞", "허벅지윗단뒤"], -22),
         "무릎옆": (110.0, 140.0, ["허벅지앞", "허벅지뒤", "정강이앞", "정강이뒤", "무릎장갑", "오금"], -30),
         "정강이": (30.0, 104.0, ["정강이앞", "정강이뒤", "무릎장갑", "오금"], -30),
         "무릎장갑": (108.0, 126.0, ["무릎장갑", "정강이앞", "정강이뒤"], -30),
         "발": (3.0, 20.0, ["발등", "발바닥", "발끝", "발톱바깥", "발톱가운데", "발톱안", "발톱뒤꿈치"], -40)}

def 실루엣오차(ms, 쪽="L"):
    """부품 z 범위 행마다 투영 양끝 − 원화 양끝 (mm). 정면 = x · 옆 = y.
    허벅지윗단: 정면 바깥 끝 · 옆 뒤 끝만 (안쪽 = 가랑이 · 앞 = D1 앞 스커트). 허벅지 z>150 정면 바깥 끝만.
    무릎장갑 옆 = 앞 끝만. 무릎옆 = 옆만 (무릎 뒤 오금 포함). 발 정면 = z 3~14 전체 양끝 (발톱 포함)."""
    sgn = 1 if 쪽 == "L" else -1
    out = {}
    for 이름, (z0, z1, ks, seed) in 구간표.items():
        g = [ms[k] for k in ks if k in ms]
        Pf = 투영(g, "y", (-95, -5), (95, 200)); Ps = 투영(g, "x", (-55, -5), (75, 200))
        ex, ey = [], []
        for z in np.arange(z0, z1 + 0.01, 1.0):
            k = int(round((z + 5) / 0.25)); kk = int(np.argmin(abs(AZ - z)))
            w1 = np.nonzero(Pf[:, k])[0]; r = (w1[0] * 0.25 - 95, w1[-1] * 0.25 - 95) if len(w1) else None
            if 이름 == "발":
                if z <= 14 and r:
                    # 원화 정면: 이 발 쪽 조각들 (가운데 x=0 기준 같은 쪽 전부)
                    row = F정[:, kk] & ((AX < 0) if sgn > 0 else (AX > 0)); w2 = np.nonzero(row)[0]
                    if len(w2): ex.append(max(abs(r[0] - AX[w2[0]]), abs(r[1] - AX[w2[-1]])))
            elif 이름 != "무릎옆":
                m = _구간(F정[:, kk], AX, sgn * seed)
                if r and m:
                    바깥만 = 이름 == "허벅지윗단" or (이름 == "허벅지" and z > 150)
                    ex.append((abs(r[0] - m[0]) if sgn > 0 else abs(r[1] - m[1])) if 바깥만 else max(abs(r[0] - m[0]), abs(r[1] - m[1])))
            w1 = np.nonzero(Ps[:, k])[0]; rs = (w1[0] * 0.25 - 55, w1[-1] * 0.25 - 55) if len(w1) else None
            if 이름 == "발": w2 = np.nonzero(F옆[:, kk])[0]; ms_ = (AY[w2[0]], AY[w2[-1]]) if len(w2) else None
            else: ms_ = _구간(F옆[:, kk], AY, 22)
            if rs and ms_:
                if 이름 == "무릎장갑": ey.append(abs(rs[0] - ms_[0]))
                elif 이름 == "허벅지윗단": ey.append(abs(rs[1] - ms_[1]))
                else: ey.append(max(abs(rs[0] - ms_[0]), abs(rs[1] - ms_[1])))
        f = lambda e: dict(최대=round(float(np.max(e)), 2), p95=round(float(np.percentile(e, 95)), 2), 평균=round(float(np.mean(e)), 2),
                           안2mm=round(float(np.mean(np.array(e) <= 2.0)), 2), 행=len(e)) if e else None
        out[이름] = dict(정면=f(ex), 옆=f(ey))
    return out

def 칠하기(ax, 목록, 방위, 앙각):
    JB.칠(ax, [(트(m), c) for m, c in 목록 if not m.is_empty()], 방위=방위, 앙각=앙각)

허벅지아래사슬 = ["허벅지앞", "허벅지뒤", "정강이앞", "정강이뒤", "무릎장갑", "오금", "발등", "발바닥", "발끝", "발톱바깥", "발톱가운데", "발톱안", "발톱뒤꿈치"]
정강이사슬 = ["정강이앞", "정강이뒤", "무릎장갑", "오금"]
발사슬 = ["발등", "발바닥", "발끝", "발톱바깥", "발톱가운데", "발톱안", "발톱뒤꿈치"]

def 체인틀(k, 허리=None, 회=0.0, 무=0.0):
    """L 부품 k 의 자세: 허리(벌림, 앞차기) ∘ 허벅지회전 ∘ 무릎."""
    T = np.c_[np.eye(3), np.zeros(3)]
    if k in 정강이사슬 + 발사슬 and 무: T = 합성(무릎틀(무), T)
    if k in 허벅지아래사슬 and 회:
        j = 관절["L허벅지회전"]; T = 합성(강체(회전행렬(j["축"], 회), j["피벗mm"]), T)
    if 허리 is not None: T = 합성(허리틀(*허리), T)
    return T

def 겹합(A, Bs):
    return 합([a ^ b for a in A for b in Bs])

def 자세검사(부, 부R, 속):
    중 = 속["중앙"]; 벨 = 속["벨"]
    허 = [부[k] for k in ("허벅지앞", "허벅지뒤", "허벅지윗단앞", "허벅지윗단뒤")]
    out = {}; 그림용 = {}
    # 무릎
    for θ in (90, 120, 135, 150):
        e = 겹합([놓(부[k], 무릎틀(θ)) for k in 정강이사슬], 허); out["무릎%d" % θ] = round(부피(e), 1)
        if θ in (135, 150):
            그림용["무릎 %d°" % θ] = ([(부[k], 색of(k)) for k in ("허벅지앞", "허벅지뒤", "허벅지윗단앞", "허벅지윗단뒤")]
                                    + [(놓(부[k], 무릎틀(θ)), 색of(k)) for k in 정강이사슬 + 발사슬], e, -90)
    최대 = 0
    for θ in range(90, 151, 3):
        if 부피(겹합([놓(부[k], 무릎틀(θ)) for k in 정강이사슬], 허)) > 0.5: break
        최대 = θ
    out["무릎_무간섭최대각"] = 최대
    # 발목 격자 (옆기울기 t · 힌지 a · 볼 x)
    발목 = {}
    정 = [부[k] for k in 정강이사슬]
    for t in (-25, 0, 25):
        for a in (-30, 0, 30):
            for xx in (-10, 0, 10):
                v = 부피(겹합([놓(부[k], 발틀(t, a, xx)) for k in 발사슬], 정))
                if v > 0.05: 발목["t%+d a%+d x%+d" % (t, a, xx)] = round(v, 1)
    out["발목_격자_겹침(0.05 넘는 것만)"] = 발목
    out["발목옆기울기±25"] = round(max(부피(겹합([놓(부[k], 발틀(t, 0)) for k in 발사슬], 정)) for t in (-25, 25)), 1)
    out["발목힌지±30"] = round(max(부피(겹합([놓(부[k], 발틀(0, a)) for k in 발사슬], 정)) for a in (-30, 30)), 1)
    e = 겹합([놓(부[k], 발틀(25, 0)) for k in 발사슬], 정)
    그림용["발목 옆기울기 +25°"] = ([(부[k], 색of(k)) for k in 정강이사슬]
                                  + [(놓(부[k], 발틀(25, 0)), 색of(k)) for k in 발사슬], e, 0)
    발 = [부["발등"], 부["발바닥"]]
    out["발끝-30"] = round(부피(겹합([놓(부[k], 힌지틀("L발끝", -30)) for k in ("발끝", "발톱바깥", "발톱가운데", "발톱안")], 발)), 1)
    out["발끝+20"] = round(부피(겹합([놓(부[k], 힌지틀("L발끝", 20)) for k in ("발끝", "발톱바깥", "발톱가운데", "발톱안")], 발)), 1)
    # 허리 쪽: 벨트 대리 · 가랑이 · R 다리(가만)
    고정 = [벨, 중["가랑이L"], 중["가랑이R"]]; R다리 = list(부R.values())
    for 이름, (a, k) in {"벌림+45": (45, 0), "벌림-10": (-10, 0), "앞차기+90": (0, 90), "뒤차기-30": (0, -30),
                        "벌림45+앞차기90": (45, 90), "벌림45+뒤차기-30": (45, -30)}.items():
        움 = [놓(m, 체인틀(n, (a, k))) for n, m in 부.items()]
        out["허리_" + 이름] = dict(벨트대리가랑이=round(부피(겹합(움, 고정)), 1), R다리=round(부피(겹합(움, R다리)), 1))
        if 이름 in ("벌림+45", "앞차기+90"):
            그림용[이름] = ([(벨, 색["벨"]), (중["가랑이L"], 색["검"]), (중["가랑이R"], 색["검"])] + [(m, 색of(n)) for n, m in zip(부, 움)],
                          겹합(움, 고정), 0 if 이름 == "벌림+45" else -90)
    # 허벅지회전 ±45: L 아래 사슬 vs R 다리 · L 윗단
    윗 = [부["허벅지윗단앞"], 부["허벅지윗단뒤"]]
    for r in (-45, -24, 45):
        움 = [놓(부[n], 체인틀(n, None, r)) for n in 허벅지아래사슬]
        out["허벅지회전%+d" % r] = dict(R다리=round(부피(겹합(움, R다리)), 1), L윗단=round(부피(겹합(움, 윗)), 1))
    # 0 자세
    모두 = dict(부); 모두.update(중); ks = list(모두); 정적 = {}
    for i in range(len(ks)):
        for j in range(i + 1, len(ks)):
            v = 겹(모두[ks[i]], 모두[ks[j]])
            if v > 0.05: 정적["%s·%s" % (ks[i], ks[j])] = round(v, 2)
    out["0자세_부품끼리"] = 정적
    out["0자세_벨트대리"] = round(부피(겹합(list(모두.values()), [벨])), 1)
    return out, 그림용

def 그림(부L, 부R, 중, 뼈들, 자세들, 경로):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
    fig = plt.figure(figsize=(32, 18), dpi=80)
    gs = fig.add_gridspec(2, 5)
    전부 = [(m, 색of(k)) for k, m in 부L.items()] + [(m, 색of(k)) for k, m in 부R.items()] + [(m, 색["검"]) for m in 중.values()]
    ax = fig.add_subplot(gs[0, 0])
    칠하기(ax, [(m, 색["뼈"]) for m in 뼈들] + 전부, 0, 0)
    ax.contour(AX, AZ, F정.T.astype(float), [0.5], colors="r", linewidths=0.8)
    ax.set_xlim(-90, 90); ax.set_ylim(-3, 195); ax.set_title("정면 · 빨강 = 원화 윤곽 (벨트 z 188 위는 D1)")
    ax = fig.add_subplot(gs[0, 1])
    칠하기(ax, [(m, 색["뼈"]) for m in 뼈들[:len(뼈들) // 2]] + [(m, 색of(k)) for k, m in 부L.items()] + [(m, 색["검"]) for m in 중.values()], -90, 0)
    ax.contour(AY, AZ, F옆.T.astype(float), [0.5], colors="r", linewidths=0.8)
    ax.set_xlim(-45, 65); ax.set_ylim(-3, 195); ax.set_title("옆 (L) · 빨강 = 원화 윤곽")
    ax = fig.add_subplot(gs[0, 2]); 칠하기(ax, 전부, -35, 18); ax.set_title("3/4")
    ax = fig.add_subplot(gs[0, 3]); 칠하기(ax, 전부, 145, 18); ax.set_title("뒤 3/4")
    ax = fig.add_subplot(gs[0, 4])
    폭발 = dict(허벅지윗단앞=(0, -18, 16), 허벅지윗단뒤=(0, 14, 16), 허벅지앞=(0, -18, 0), 허벅지뒤=(0, 14, 0), 무릎장갑=(0, -30, 4), 정강이앞=(0, -16, 0),
              정강이뒤=(0, 14, 0), 오금=(0, 30, 6), 발목띠=(-14, 0, 0), 발등=(0, 0, 10), 발바닥=(0, 0, -10), 발끝=(0, -12, 2),
              발톱바깥=(-8, -22, 0), 발톱가운데=(0, -24, 0), 발톱안=(6, -22, 0), 발톱뒤꿈치=(0, 12, -6))
    칠하기(ax, [(m.translate(폭발.get(k, (0, 0, 0))), 색of(k)) for k, m in 부L.items()] + [(중["가랑이L"].translate((8, 0, 18)), 색["검"])], -60, 15)
    ax.set_title("분해도 (L + 가랑이L)")
    for i, (이름, (목록, 겹m, 방위)) in enumerate(자세들.items()):
        if i >= 5: break
        ax = fig.add_subplot(gs[1, i])
        칠하기(ax, 목록 + ([(겹m, 색["빨"])] if not 겹m.is_empty() else []), 방위, 0)
        ax.set_title("%s · 겹침 %.1f mm³ (빨강)" % (이름, 부피(겹m)))
    fig.tight_layout(); fig.savefig(경로); plt.close(fig)

def 떼기(m, r=0.08, 번=10):
    """STL 로 한 번 내보내 다시 읽고(위치로 정점 합침) 면 넷 이상이 만나는 모서리(자기 접촉)를 찾아
    그 모서리 가운데마다 구를 깎아 떼어 낸다 (첫 번 0.08 · 다음부터 0.6 = 얇은 지느러미 끊기). 없어질 때까지 되풀이."""
    from collections import Counter
    n점 = 0
    for _ in range(번):
        t = _stl왕복(m)
        if t.is_watertight: break
        c = Counter(map(tuple, t.edges_sorted)); bad = np.array([e for e, n in c.items() if n != 2])
        if len(bad) == 0: break
        P = t.vertices[bad].mean(1)
        rr = r if _ == 0 else 0.6 if _ < 4 else 1.2
        P = np.unique(np.round(P / (rr * 1.5)) * (rr * 1.5), axis=0); n점 += len(P)
        m = m - 합([M.Manifold.sphere(rr, 12).translate(tuple(q)) for q in P])
        m = 합([c for c in m.decompose() if c.volume() >= 5.0])
    return m, n점

def _stl왕복(m):
    import io
    b = io.BytesIO(); 트(m).export(b, file_type="stl"); b.seek(0); return trimesh.load(b, file_type="stl")

def 닫힘검사(경로):
    t = trimesh.load(경로); return bool(t.is_watertight), int(len(t.split(only_watertight=False)))

if __name__ == "__main__":
    부, 기록, 속 = 짓기()
    중 = 속["중앙"]
    for k, m in list(부.items()) + list(중.items()): 로그(k, "%.2f cm³" % (부피(m) / 1000), "조각", [round(c.volume(), 1) for c in m.decompose()])
    표 = {}
    for k in list(부): 부[k], n = 떼기(부[k]); 표.setdefault("_뗀점", {})[k] = n
    for k in list(중): 중[k], n = 떼기(중[k]); 표.setdefault("_뗀점", {})[k] = n
    부R = {k: 거울(m) for k, m in 부.items()}
    실 = dict(L=실루엣오차(부, "L"), R=실루엣오차(부R, "R")); 로그("실루엣", json.dumps(실, ensure_ascii=False))
    자, 그림용 = 자세검사(부, 부R, 속); 로그("자세", json.dumps(자, ensure_ascii=False))
    뼈들 = [속["B"][n] for n in 다리뼈]; 뼈들 = 뼈들 + [거울(m) for m in 뼈들]
    골반뼈 = [뼈캡슐(n, 0.0) for n in ("허리", "L고관절블록", "L허벅지위")]; 골반뼈 += [거울(m) for m in 골반뼈[1:]]
    외장 = list(부.values()) + list(부R.values()) + list(중.values())
    보임 = {}
    for 이름, 축, lo, hi in (("정면", "y", (-60, 150), (60, 188)), ("옆", "x", (-30, 150), (60, 188))):
        Pb = 투영(골반뼈 + 뼈들, 축, lo, hi); Pa = 투영(외장, 축, lo, hi); 보임[이름] = round(float((Pb & ~Pa).sum()) * 0.0625, 1)
    자["골반_보이는뼈mm2(z150~188 투영)"] = 보임; 로그("보이는 뼈", 보임)
    그림(부, 부R, 중, 뼈들, 그림용, os.path.join(OUT, "보기.png"))
    뗀 = 표.pop("_뗀점")
    for f in os.listdir(OUT):
        if f.endswith(".stl"): os.remove(os.path.join(OUT, f))
    for 이름, m in [("L" + k, m) for k, m in 부.items()] + [("R" + k, m) for k, m in 부R.items()] + list(중.items()):
        f = os.path.join(OUT, "%s.stl" % 이름); 트(m).export(f)
        wt, nc = 닫힘검사(f)
        표[이름] = dict(뗀점=뗀.get(이름[1:], 뗀.get(이름, 0)), 부피mm3=round(부피(m), 1), 무게g=round(부피(m) * PLA, 2), 닫힘=wt, 조각=nc,
                      색="금" if "발톱" in 이름 else "검정" if any(s in 이름 for s in 검정) else "흰")
    무게 = round(sum(v["무게g"] for v in 표.values()), 1)
    json.dump(dict(설명=__doc__, 부품=표, 기록=기록, 실루엣오차mm=실, 가동겹침mm3=자, 총무게g=무게),
              open(os.path.join(OUT, "부품.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    로그("총 무게 %.1f g · 닫힘 %d/%d · 부품 %d" % (무게, sum(v["닫힘"] for v in 표.values()), len(표), len(표)))
