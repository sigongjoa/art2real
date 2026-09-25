# -*- coding: utf-8 -*-
"""오메가몬 PG(300 mm) 「디자인 판」 외장 — 머리 · 어깨 · 윗팔 (2026-09-25).

    python 디자인_머리어깨.py
      -> out/출력/오메가몬_PG/디자인/머리어깨/*.stl (조립 좌표 mm) · 부품.json · 보기.png

몸 부피를 깎지 않고 **도형으로 새로 짓는다**. 원화는 치수 · 윤곽만 읽는다(아래 「치수」 주석이 근거).
좌표 = 관절.json 과 같다: mm · 원점 발바닥 중앙 · [x 좌우(L = 작은 x = 칼 팔), y 깊이(작은 y 가 앞), z 높이].
원화 → mm: 정면 x=(px-534)*0.34, z=(954.5-py)*0.34 · 옆 y=(px-461)*0.345, z=(939-py)*0.345
          (192³ 키트 몸 O 의 투영과 IoU 최대로 맞춘 값 — 정면 0.924 · 옆 0.923).

짓는 법
  · 부품 = 볼록 조각(단면 다각형 몇 개의 hull)의 합 + CSG. 껍질 = 조각 합 − (각 조각을 평면들로 정확히 2.0 안쪽으로 민 것) 합.
  · 속 비움 = 뼈(관절.json 마디, 반지름 +0.4) · 관절 외피(+0.4) · 움직이는 이웃이 쓸고 가는 부피(+0.4).
  · 머리 = x 대칭(조각 점을 대칭으로 둔다). 목위 볼(끄덕 −25~20 · 옆 ±15 · 비틀기 ±45)에 목 뼈가 쓸고 가는 부피를 뺀다.
  · 어깨(2바퀴) = 돔(어깨블록 고정) + 아래 덮개(윗팔위에 붙어 들기 축과 같은 축으로 1:1). 덮개 = 겉 ∩ {들기 피벗 둘레 각
    −150°~25°} ∩ {반지름 ≤ r_c}, 들면 돔 밑으로 포개진다(돔 = 겉 − 덮개·팔 쓸기). 왼 방패는 돔 위 바깥 y 축 힌지 —
    들 때 덮개가 밀어 올린다(φ(θ) = 팔과 안 겹치는 가장 작은 φ).
  · 윗팔 = 원통 D16.8, 축 = 윗팔회전 축(2바퀴 J1: 들기 → 팔꿈치 직선과 같다). 위 끝은 들기 축 둘레 너클.
  · 팔끝(2바퀴) = 짐승 머리 팔끝 몸체를 각진 로프트 판으로. 팔끝회전 자리에서 위(팔끝)/아래(손) 로 가른다. 무기는 쥠 회전축8.
  · 반쪽 이음 = 평면 + 다보(패드 Ø4.2 · 핀 Ø1.8×2.5 · 구멍 한쪽 +0.20). 장갑→뼈 = 보스 Ø4 + 핀 Ø1.8×2.5 (뼈 구멍은 부품.json).
  · 꽂는 부품(뿔 · 안테나 · 가시 · 방패 줄기) = 뿌리 볼록체를 주인 부품에 +0.15 로 파고, 둘레에 1.6 두께 받침을 덧댄다.
  · 패널라인 = V 홈 폭 0.8 · 깊이 0.5, 외곽 평행 · 직선만."""
import os, sys, json, time
os.environ.setdefault("OMP_NUM_THREADS", "4")
import numpy as np, trimesh, manifold3d as M
from scipy.spatial import ConvexHull, HalfspaceIntersection
from scipy.spatial.transform import Rotation as Rot

ROOT = r"G:\art2real\원화3d"
OUT = os.path.join(ROOT, "out", "출력", "오메가몬_PG", "디자인", "머리어깨"); os.makedirs(OUT, exist_ok=True)
J = json.load(open(os.path.join(ROOT, "out", "가동", "관절.json"), encoding="utf-8"))
관 = {j["이름"]: j for j in J["관절"]}
뼈 = J["뼈"]
두께, 비움, 관절틈, 다보틈, 꽂이틈 = 2.0, 0.4, 0.3, 0.20, 0.15
SEG = 48
t0 = time.time()
def 로그(*a): print("[%4.0fs]" % (time.time() - t0), *a, flush=True)

# ── 기본 도형 ───────────────────────────────────────────────
A = lambda *v: np.array(v, float)
def 단위(v): v = np.asarray(v, float); return v / np.linalg.norm(v)
def 볼록(P): return M.Manifold.hull_points(np.asarray(P, float))
def 밀기(P, t):
    """볼록 점집합 P 의 hull 을 면마다 t 만큼 민다(t<0 안쪽). 정확한 평면 오프셋 — 비스듬한 면도 두께 t."""
    P = np.asarray(P, float); h = ConvexHull(P); eq = h.equations.copy(); eq[:, 3] -= t
    c = P[h.vertices].mean(0)
    return HalfspaceIntersection(eq, c).intersections
def 합(ms):
    ms = [m for m in ms if m is not None and not m.is_empty()]
    return M.Manifold.batch_boolean(ms, M.OpType.Add) if ms else M.Manifold()
def 틀(R, t):  # 3x3 회전 + 이동 → 3x4
    return np.hstack([R, np.asarray(t, float).reshape(3, 1)])
def 돌림(m, 피벗, 축, 도):
    R = Rot.from_rotvec(단위(축) * np.radians(도)).as_matrix(); p = np.asarray(피벗, float)
    return m.transform(틀(R, p - R @ p))
def 돌림점(P, 피벗, 축, 도):
    R = Rot.from_rotvec(단위(축) * np.radians(도)).as_matrix(); p = np.asarray(피벗, float)
    return (np.asarray(P) - p) @ R.T + p
def 기저(a):
    a = 단위(a); t = A(0, 1, 0) if abs(a[1]) < 0.9 else A(1, 0, 0)
    u = 단위(np.cross(t, a)); v = np.cross(a, u); return u, v, a
def 원기둥(p0, p1, r, r1=None, seg=SEG):
    p0, p1 = A(*p0), A(*p1); d = p1 - p0; L = np.linalg.norm(d); u, v, a = 기저(d)
    c = M.Manifold.cylinder(L, r, r if r1 is None else r1, seg)
    return c.transform(틀(np.stack([u, v, a], 1), p0))
def 구(p, r, seg=SEG): return M.Manifold.sphere(r, seg).translate(list(map(float, p)))
def 원점들(c, a, r, n=SEG, 기준=None):
    u, v, a = 기저(a) if 기준 is None else (기준[0], 기준[1], 단위(a))
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return np.asarray(c, float) + r * (np.cos(t)[:, None] * u + np.sin(t)[:, None] * v)
def 팔각(w0, w1, h0, h1, c):
    """직사각 [w0,w1]×[h0,h1] 모서리 c 모따기 — 2D 8 점."""
    return [(w0 + c, h0), (w1 - c, h0), (w1, h0 + c), (w1, h1 - c), (w1 - c, h1), (w0 + c, h1), (w0, h1 - c), (w0, h0 + c)]
def 단면x(x, 점2):  return [(x, a, b) for a, b in 점2]          # (y,z) 단면
def 단면z(z, 점2):  return [(a, b, z) for a, b in 점2]          # (x,y) 단면
def 대칭(점2):  return 점2 + [(-a, b) for a, b in 점2]
def 메시(m):
    t = m.to_mesh(); return trimesh.Trimesh(np.asarray(t.vert_properties)[:, :3], np.asarray(t.tri_verts), process=False)
def 부피(m): return 0.0 if m.is_empty() else m.volume()

def 겉점(겉, p, d, 안=False):
    """p 에서 d 로 가며 겉 밖으로 나가는 첫 점(0.1 mm)."""
    tm = 메시(겉); p = A(*p); d = 단위(d)
    ts = np.arange(-15.0, 45.0, 0.1); ins = tm.contains(p + ts[:, None] * d)
    k = np.nonzero(ins[:-1] & ~ins[1:])[0]
    return p + ts[k[-1] + 1] * d
버린조각 = {}
def 정리(m, 이름=None):
    """가장 큰 조각만 남긴다(속 빈 곳은 채움). 떨어져 나간 조각 부피는 버린조각[이름] 에 적는다."""
    ps = sorted([q for q in m.decompose() if q.volume() > 0], key=lambda q: -q.volume())
    if not ps: return m
    if 이름 and len(ps) > 1: 버린조각[이름] = [round(q.volume(), 1) for q in ps[1:]]
    return ps[0]
class 조각:
    """볼록 조각들의 합. 속 = 빈 조각만 안쪽으로 두께 밀기."""
    def __init__(s): s.p = []          # (점, 빈가)
    def 더(s, P, 빈=True): s.p.append((np.asarray(P, float), 빈)); return s
    def 겉(s): return 합([볼록(P) for P, _ in s.p])
    def 속(s, t=두께): return 합([볼록(밀기(P, -t)) for P, 빈 in s.p if 빈])
    def 껍질(s, t=두께): return s.겉() - s.속(t)
    def 거울(s):
        n = 조각(); n.p = [(P * A(-1, 1, 1), b) for P, b in s.p]; return n

# ── 골격에서 읽는 것 ─────────────────────────────────────────
def 뼈몸(이름, 더r=0.0):
    out = []
    for chain in 뼈[이름]["마디"]:
        for a, b in zip(chain[:-1], chain[1:]):
            out.append(볼록(np.vstack([원점들(a[:3], A(0, 0, 1), a[3] / 2 + 더r, 24), 원점들(a[:3], A(1, 0, 0), a[3] / 2 + 더r, 24),
                                   원점들(a[:3], A(0, 1, 0), a[3] / 2 + 더r, 24),
                                   원점들(b[:3], A(0, 0, 1), b[3] / 2 + 더r, 24), 원점들(b[:3], A(1, 0, 0), b[3] / 2 + 더r, 24),
                                   원점들(b[:3], A(0, 1, 0), b[3] / 2 + 더r, 24)])))
    return 합(out)
def 외피(이름, 더r=0.0):
    j = 관[이름]; p = A(*j["피벗mm"]); e = j["외피"]; ax = 단위(j["축"])
    if e["모양"] == "구": return 구(p, e["반지름mm"] + 더r)
    if e["모양"] == "원기둥":
        L = e.get("폭mm", e.get("길이mm", 0) + 1) / 2 + 더r
        return 원기둥(p - L * ax, p + L * ax, e["반지름mm"] + 더r)
    q = A(*e["둘째축피벗mm"]); L = e["폭mm"] / 2 + 더r
    return (원기둥(p - L * ax, p + L * ax, e["반지름mm"] + 더r) + 원기둥(q - L * ax, q + L * ax, e["반지름mm"] + 더r)).hull()
P = lambda n: A(*관[n]["피벗mm"])

# ── 결합 ──────────────────────────────────────────────────
def 다보붙이기(a, b, 겉, 막, 점들, n):
    n = 단위(n); pads_a, pads_b, pins, holes = [], [], [], []
    for p in 점들:
        p = A(*p)
        pad = (원기둥(p - 4.0 * n, p + 4.0 * n, 2.1, seg=24) ^ 겉) - 막
        if 부피(pad ^ 원기둥(p - 1.5 * n, p + 3.5 * n, 1.3, seg=16)) < 0.9 * np.pi * 1.3 ** 2 * 5.0:
            사양.setdefault("버린다보", []).append(np.round(p, 1).tolist()); continue
        pads_a.append(pad.trim_by_plane(list(-n), float(-n @ p)))
        pads_b.append(pad.trim_by_plane(list(n), float(n @ p)))
        pins.append(원기둥(p - 0.5 * n, p + 2.5 * n, 0.9, seg=20))
        holes.append(원기둥(p - 0.01 * n, p + 3.0 * n, 0.9 + 다보틈, seg=20))
    a = (a + 합(pads_a)) - 막 + 합(pins)
    b = (b + 합(pads_b)) - 막 - 합(holes)
    return a, b
def 보스(부품, 겉, 뼈이름, 뼈점, 방향, 길=30.0):
    """뼈 겉점에서 방향으로 Ø4 보스(겉 안으로 자름) + 뼈로 핀 Ø1.8×2.5. 반환 (부품, 구멍 사양)."""
    d = 단위(방향); p = A(*뼈점)
    b = (원기둥(p, p + 길 * d, 2.0, seg=24) ^ 겉) - 뼈몸(뼈이름)
    pin = 원기둥(p + 1.5 * d, p - 2.5 * d, 0.9, seg=20)
    return 부품 + b + pin, {"뼈": 뼈이름, "점mm": p.round(2).tolist(), "방향": (-d).round(3).tolist(), "구멍지름": round(1.8 + 2 * 다보틈, 2), "깊이": 3.0}
def 꽂이(주인, 주인겉, 뿌리점, 틈=꽂이틈, 받침=1.6):
    """주인에 뿌리 소켓: 받침(뿌리 +받침 ∩ 주인 겉) 덧대고 뿌리 +틈 판다."""
    받 = 볼록(밀기(뿌리점, 받침)) ^ 주인겉
    return (주인 + 받) - 볼록(밀기(뿌리점, 틈))
def V홈(부품, 선들, n, 폭=0.8, 깊=0.5):
    """평면(법선 n, 겉쪽) 위 선분들에 V 홈."""
    n = 단위(n); out = []
    for p0, p1 in 선들:
        p0, p1 = A(*p0), A(*p1); t = 단위(p1 - p0); w = 단위(np.cross(n, t))
        pts = []
        for p in (p0, p1):
            pts += [p + 0.4 * w * 폭 / 0.8 + 0.3 * n, p - 0.4 * w * 폭 / 0.8 + 0.3 * n, p - 깊 * n]
            pts += [p + (0.4 * 폭 / 0.8 + 0.24) * w + 0.3 * n, p - (0.4 * 폭 / 0.8 + 0.24) * w + 0.3 * n]
        out.append(볼록(pts))
    return 부품 - 합(out)
def 고리홈(c, a, r, 폭=0.8, 깊=0.5):
    """원통(중심 c, 축 a, 반지름 r) 둘레 V 고리 홈 부피."""
    cs = M.CrossSection([[(r + 0.3, 폭 / 2 + 0.24), (r - 깊, 0.0), (r + 0.3, -폭 / 2 - 0.24)]])
    g = M.Manifold.revolve(cs, SEG); u, v, a = 기저(a)
    return g.transform(틀(np.stack([u, v, a], 1), c))

def D1(앞글자=("가슴", "목깃", "엠블럼")):
    """D1 몸통 STL(있으면) — 가슴 · 목깃 등 이름 앞글자로 고른다."""
    d = os.path.join(ROOT, "out", "출력", "오메가몬_PG", "디자인", "몸통"); ms = []
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.endswith(".stl") and f.startswith(앞글자):
                t = trimesh.load(os.path.join(d, f), force="mesh")
                try: ms.append(M.Manifold(M.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32))))
                except Exception: pass
    return 합(ms) if ms else None
부품 = {}          # 이름 -> dict(m, 색, 묶음, 뼈, 비고)
사양 = {"뼈구멍": [], "핀": []}
def 넣기(이름, m, 색, 묶음, 붙는곳, 비고="", 뼈=None):
    부품[이름] = dict(m=m, 색=색, 묶음=묶음, 붙는곳=붙는곳, 비고=비고, 뼈=뼈)

색 = dict(흰=(0.93, 0.93, 0.95), 회=(0.62, 0.64, 0.68), 금=(0.90, 0.74, 0.25), 빨=(0.78, 0.16, 0.12), 파=(0.45, 0.50, 0.78),
          검=(0.22, 0.22, 0.24), 은=(0.80, 0.82, 0.86))

# ════════════════════════ 머리 ════════════════════════════
# 치수(원화): 정면 투구 폭 ±11 (z 262~285) · 꼭대기 z 291 · 볼 가리개 ±14 (z 268~281, 아래로 좁아지는 역사다리꼴) · 얼굴 ±8 · 턱 V z 262.
#           옆 얼굴 앞 y 0 · 이마 차양 y −1.5 에서 1.5 더 튀어나옴 · 뒤통수 둥글게 y 28~32.
#           뿔 밑 (y 1~10, z 281) → 끝 (0, −7, 307.5) · V 안테나 (±8, 10, 283) → (±25.5, 29.5, 302.5).
# 2바퀴: 머리 전체를 목위 볼 기준 +2 mm 올림(턱 · 가슴앞 0.9 mm 틈) · 단면 = 앞 좁고 뒤 둥근 다각 · 차양 돌출 · 볼 가리개 따로.
# 골격: 목위 볼 피벗 (0, 21.36, 267.38) R7.5 → 뒤통수 겉 y ≥ 31.3.
로그("머리")
Pn = P("목위"); HZ = 2.0
def 머리판(z, wf, w, yf, yb, n=6):
    """앞 폭 ±wf(평평한 앞면) → 옆 ±w → 뒤 타원 호(n 점)."""
    yc = yf + 0.45 * (yb - yf); pts = [(wf, yf), (w, yf + 0.28 * (yb - yf))]
    pts += [(w * np.cos(t), yc + (yb - yc) * np.sin(t)) for t in np.linspace(0, np.pi / 2, n)]
    pts += [(-x, y) for x, y in pts]
    return 단면z(z + HZ, pts)
투구 = 조각()
판들 = [(258.8, 5.0, 8.4, 7.0, 29.5), (264.0, 7.0, 10.6, 3.0, 32.0), (275.0, 8.2, 11.2, 1.2, 32.0), (283.0, 7.6, 10.8, 2.6, 30.0)]
투구.더(np.vstack([머리판(*r) for r in 판들]))
투구.더(np.vstack([머리판(*r) for r in [(283.0, 7.6, 10.8, 2.6, 30.0), (288.5, 5.0, 8.2, 6.4, 26.5), (291.3, 2.2, 4.4, 10.5, 20.0)]]))
# 이마 차양: 앞으로 −3.0 (얼굴 앞면 −0.4 보다 2.6 앞) · 아랫면은 뒤로 비스듬(그늘이 지게)
차양 = [(x, y, z + HZ) for x, y in [(-9.8, -0.6), (-4.0, -2.4), (0, -3.0), (4.0, -2.4), (9.8, -0.6)] for z in (279.4, 282.6)] + \
      [(x, y + 1.6, 277.6 + HZ) for x, y in [(-9.4, -0.6), (0, -3.0), (9.4, -0.6)]] + [(x, 8.0, z + HZ) for x in (-10.2, 10.2) for z in (277.2, 283.0)]
투구.더(차양, 빈=False)
볏 = [(x, y, z + HZ) for x in (-4.2, 4.2) for y, z in [(0.2, 280.5), (4.6, 290.8), (12.5, 290.8), (10.0, 280.5)]]
투구.더(볏, 빈=False)
투구겉 = 투구.겉()

뿔밑 = 단면z(281.0 + HZ, [(0, 0.8), (3.2, 3.2), (3.2, 7.6), (0, 10.0), (-3.2, 7.6), (-3.2, 3.2)])
뿔중 = 단면z(290.6 + HZ, [(0, -1.4), (2.4, 0.4), (2.4, 4.4), (0, 6.2), (-2.4, 4.4), (-2.4, 0.4)])
뿔끝 = 단면z(307.6 + HZ, [(0.8, -7.6), (0.8, -6.0), (-0.8, -6.0), (-0.8, -7.6)])
뿔 = 볼록(np.vstack([뿔밑, 뿔중, 뿔끝])); 뿔뿌리 = np.vstack([뿔밑, 뿔중])

def 안테나(s):
    B = A(s * 7.5, 9.5, 282.5 + HZ); T = A(s * 25.5, 29.5, 302.5 + HZ); d = 단위(T - B)
    w = 단위(np.cross(d, A(0, 1, 0))); th = 단위(np.cross(d, w))
    def 사각(c, a, b): return [c + i * a * w + j * b * th for i in (-1, 1) for j in (-1, 1)]
    R0 = B - 5.0 * d; E = B + 5.0 * d
    return 볼록(사각(R0, 1.4, 1.0) + 사각(E, 1.4, 1.0) + 사각(T, 0.8, 0.8)), np.array(사각(R0, 1.4, 1.0) + 사각(E, 1.4, 1.0))
안L, 안L뿌리 = 안테나(-1); 안R, 안R뿌리 = 안테나(1)

# 볼 가리개(좌우 따로): 역사다리꼴 판 — 위 (y 3~17, z 281) 넓고 아래 (y 6~13.5, z 270.5) 좁다 · 바깥으로 5° 벌어짐
def 볼가리개(s):
    위 = [(3.0, 276.0), (16.5, 276.0)]; 아래 = [(13.0, 268.5), (6.5, 268.5)]      # +HZ → z 268.5~278 (원화 볼 가리개 z 268~279)
    겉점_ = [(s * (13.9 + 0.09 * (z - 270)), y, z + HZ) for y, z in 위 + 아래]
    안점 = [(s * 11.5, y, z + HZ) for y, z in 위 + 아래]
    몸 = 볼록(겉점_ + 안점)
    뿌리 = np.vstack([원점들(A(s * 12.0, 10.0, 272.0 + HZ), A(1, 0, 0), 1.3, 12), 원점들(A(s * 9.0, 10.0, 272.0 + HZ), A(1, 0, 0), 1.3, 12)])
    return 몸 + 볼록(뿌리), 뿌리
볼L, 볼L뿌리 = 볼가리개(-1); 볼R, 볼R뿌리 = 볼가리개(1)

얼굴외곽 = [(0.0, 262.4), (7.8, 266.2), (8.0, 276.6), (-8.0, 276.6), (-7.8, 266.2)]
def 얼굴점():
    return [(x, y, z + HZ) for x, z in 얼굴외곽 for y in (-0.4 + abs(x) * 0.22, 6.4)]
얼굴 = 볼록(얼굴점())
얼굴구멍 = 볼록(밀기(얼굴점(), 꽂이틈)) + 볼록([(x, y, z) for x in (-8.2, 8.2) for y in (-3, 14.0) for z in (250.0, 276.75 + HZ)])

목뼈 = 뼈몸("목", 비움)
쓸 = []
for rx in (-25, -12, 0, 10, 20):
    for ry in (-15, 0, 15):
        for rz in (-45, 0, 45):
            R = Rot.from_euler("xyz", [rx, ry, rz], degrees=True).inv().as_matrix()
            쓸.append(목뼈.transform(틀(R, Pn - R @ Pn)))
목쓸기 = 합(쓸)
머리막 = 목쓸기 + 외피("목위", 비움) + 뼈몸("머리", 비움)
# 목위 볼 둘레 구면 컷: 피벗 높이 아래는 구 r 11.2 (볼 외피 7.9 + 벽 2 + 1.3) ∪ 앞 ±28° 쐐기(얼굴) 안만 · 쐐기 안도 턱 원호 r 21.8 안만
쐐기 = 볼록([(0, Pn[1], z) for z in (230.0, Pn[2])] + [(sx * 40 * np.sin(np.radians(28)), Pn[1] - 40 * np.cos(np.radians(28)), z)
                                                   for sx in (-1, 1) for z in (230.0, Pn[2])])
아래막 = M.Manifold.cube([80, 80, Pn[2] - 230.0]).translate([-40, -20, 230.0]) - 구(Pn, 11.2, 64) - (쐐기 ^ 구(Pn, 21.8, 64))
투구겉 = 투구겉 - 아래막
투구껍질 = 투구.껍질() - 목쓸기 - 아래막
투구껍질 = 꽂이(투구껍질, 투구겉, 뿔뿌리)
for 뿌리 in (안L뿌리, 안R뿌리, 볼L뿌리, 볼R뿌리): 투구껍질 = 꽂이(투구껍질, 투구겉, 뿌리)
투구껍질 = 투구껍질 - 얼굴구멍 - 머리막 - 볼록(밀기(볼L뿌리, 꽂이틈)) - 볼록(밀기(볼R뿌리, 꽂이틈))
# 판 단차: 투구 옆면 가운데 0.6 mm 오목 판(외곽에서 2.5 mm 안) + 그 경계 V 홈 없음 · 눈 틈 V 홈
투구껍질 = V홈(투구껍질, [((-7.6, 1.3, 277.0 + HZ), (7.6, 1.3, 277.0 + HZ))], A(0, -1, 0), 폭=1.0, 깊=0.8)
Ys = 15.0
앞, 뒤 = 투구껍질.split_by_plane([0, -1, 0], -Ys)
다보점 = [(-9.6, Ys, 267.0 + HZ), (9.6, Ys, 267.0 + HZ), (0.0, Ys, 289.2 + HZ)]
앞, 뒤 = 다보붙이기(앞, 뒤, 투구겉, 머리막 + 뿔 + 안L + 안R, 다보점, A(0, 1, 0))
b = 뼈["머리"]["마디"][0]; r_at = (b[0][3] + (b[-1][3] - b[0][3]) * (276 - b[0][2]) / (b[-1][2] - b[0][2])) / 2
뒤, s1 = 보스(뒤, 투구겉, "머리", (0, Pn[1] + r_at, 276.0), A(0, 1, 0)); 사양["뼈구멍"].append(dict(부품="투구뒤", **s1))
r_f = (b[0][3] + (b[-1][3] - b[0][3]) * (270 - b[0][2]) / (b[-1][2] - b[0][2])) / 2
fp = A(0, Pn[1] - r_f, 270.0)
얼굴 = 얼굴 + 원기둥((0, 5.0, 270.0), fp, 2.0, seg=24) + 원기둥(fp - A(0, 0.3, 0), fp + A(0, 2.5, 0), 0.9, seg=20)
얼굴 = 얼굴 - 뼈몸("머리") - 아래막
사양["뼈구멍"].append(dict(부품="얼굴", 뼈="머리", 점mm=fp.round(2).tolist(), 방향=[0, 1, 0], 구멍지름=2.2, 깊이=3.0))
얼굴 = V홈(얼굴, [((-7.0, -0.4 + 7.0 * 0.22, 268.6 + HZ), (0, -0.4, 268.6 + HZ))], A(-0.22, -1, 0))
얼굴 = V홈(얼굴, [((7.0, -0.4 + 7.0 * 0.22, 268.6 + HZ), (0, -0.4, 268.6 + HZ))], A(0.22, -1, 0))
얼굴 = V홈(얼굴, [((-5.5, -0.4 + 5.5 * 0.22, 271.6 + HZ), (0, -0.4, 271.6 + HZ))], A(-0.22, -1, 0))
얼굴 = V홈(얼굴, [((5.5, -0.4 + 5.5 * 0.22, 271.6 + HZ), (0, -0.4, 271.6 + HZ))], A(0.22, -1, 0))
넣기("투구앞", 앞, 색["흰"], "머리", "투구뒤(다보 3)", 뼈="머리")
넣기("투구뒤", 뒤, 색["흰"], "머리", "머리 뼈(보스)", 뼈="머리")
넣기("얼굴", 얼굴, 색["은"], "머리", "머리 뼈(핀) · 투구앞 창에 끼움", 뼈="머리")
넣기("뿔", 뿔, 색["은"], "머리", "투구앞 볏 소켓", 뼈="머리")
넣기("V안테나L", 안L, 색["금"], "머리", "투구앞 소켓", 뼈="머리")
넣기("V안테나R", 안R, 색["금"], "머리", "투구앞 소켓", 뼈="머리")
넣기("볼가리개L", 볼L, 색["회"], "머리", "투구 옆 소켓", 뼈="머리")
넣기("볼가리개R", 볼R, 색["회"], "머리", "투구 옆 소켓", 뼈="머리")

# ════════════════════════ 윗팔 ════════════════════════════
# 골격 2바퀴(J1): 팔 L 기준 거울 대칭 · 윗팔회전 축 = 들기 피벗 → 팔꿈치 직선 = 원통 축. 윗팔위 뼈는 11.5 mm 로 짧다.
Ra = 8.4; 너클반폭 = 7.6
def 윗팔(s):
    Lr = "L" if s < 0 else "R"
    H = P(Lr + "어깨들기"); E = P(Lr + "팔꿈치"); a = 단위(관[Lr + "윗팔회전"]["축"])
    t_rot = float((P(Lr + "윗팔회전") - H) @ a); t_end = 38.0
    yv = A(0, 1, 0)
    너클 = np.vstack([원점들(H + h * yv, yv, Ra) for h in (-너클반폭, 너클반폭)])
    원 = lambda t, r=Ra: 원점들(H + t * a, a, r)
    위 = 조각().더(np.vstack([너클, 원(t_rot - 관절틈 / 2)]))
    아래 = 조각().더(np.vstack([원(t_rot + 관절틈 / 2), 원(t_end)]))
    return dict(H=H, E=E, a=a, t_rot=t_rot, t_end=t_end, 위=위, 아래=아래, Lr=Lr)
팔 = {s: 윗팔(s) for s in (-1, 1)}
def 팔돌림(m, s, 도):   # 들기 θ (양 = 바깥으로 듦)
    j = 관[팔[s]["Lr"] + "어깨들기"]; return 돌림(m, j["피벗mm"], j["범위"][0]["축"], 도)
for s in (-1, 1):
    ax_ = 관[팔[s]["Lr"] + "어깨들기"]["범위"][0]["축"]
    t_ = 돌림점(팔[s]["E"][None], 팔[s]["H"], ax_, 30)[0]
    assert s * (t_[0] - 팔[s]["E"][0]) > 0, "들기 + 가 바깥이 아니다"

# ════════════════════════ 어깨 ════════════════════════════
# 2바퀴: 어깨 장갑 = 돔(어깨블록 고정) + 아래 덮개(윗팔위에 붙어 들기 축과 **같은 축**으로 1:1 로 돈다).
#   아래 덮개 = 겉 ∩ {들기 피벗 둘레 각 α ∈ (−150°, 25°)} ∩ {반지름 ≤ r_c}. 들면 돔 밑으로 포개져 들어간다(돔 = 겉 − 덮개 쓸기).
#   캠/링크 없이 강체 연결이라 「날개를 먼저 드는」 손질이 없다. 왼쪽 방패는 돔 위 바깥 힌지 · 들 때 덮개가 밀어 올린다.
# 치수(원화): L 캡 x −51~−30.5 · z 240~266 · y 5~37(옆 그림 없음 — R 깊이 폭과 피벗 y 20.5 기준). R 돔 x 30.5~60 · z 237~274 · y 10.4~47.
로그("어깨")
α_s = 25.0
r_c = {-1: 11.0, 1: 16.5}      # 돔 안 반지름(25~115° 부채꼴 최소)보다 작게 — 들면 돔 속으로 들어간다
가슴D1 = D1()
def 돔단면(z, x0, x1, y0, y1, c): return 단면z(z, 팔각(x0, x1, y0, y1, c))
L겉조 = 조각().더(np.vstack([돔단면(*r) for r in [(240.0, -46.0, -34.0, 10.0, 32.0, 3.0), (244.0, -50.0, -31.0, 6.0, 36.0, 6.0),
                                                 (257.0, -51.0, -30.5, 5.0, 37.0, 7.5), (263.5, -48.5, -31.5, 8.0, 34.0, 6.5), (266.3, -44.5, -34.5, 13.0, 29.0, 3.0)]]))
R겉조 = 조각().더(np.vstack([돔단면(*r) for r in [(236.8, 38.0, 51.0, 19.0, 39.0, 4.0), (242.0, 32.5, 58.0, 12.0, 46.0, 7.0),
                                                 (256.0, 30.5, 60.0, 10.4, 47.0, 8.5), (266.0, 31.5, 58.5, 12.0, 45.5, 8.5),
                                                 (271.0, 34.0, 54.0, 16.0, 41.5, 6.5), (273.0, 37.5, 49.0, 21.0, 36.5, 3.0)]]))
def 쐐기영역(s, α1=α_s, α0=-150.0, rr=None):
    """들기 피벗 둘레 (x-z) 각 α0~α1 (바깥 수평 = 0, 위 = +) · 반지름 rr 안 · y 전체."""
    H = 팔[s]["H"]; angs = np.radians(np.linspace(α0, α1, 12)); R_ = 80.0 if rr is None else rr
    pts = [(H[0], y, H[2]) for y in (-30, 70)]
    pts += [(H[0] + s * R_ * np.cos(t), y, H[2] + R_ * np.sin(t)) for t in angs for y in (-30, 70)]
    w = 볼록(pts)
    if rr is not None: w = w ^ 원기둥((H[0], -30, H[2]), (H[0], 70, H[2]), rr, seg=96)
    return w
def 쓸기(m, s, th0, th1, 걸음=10.0):
    ths = list(np.arange(th0, th1, 걸음)) + [th1]
    return 합([(팔돌림(m, s, a) + 팔돌림(m, s, b)).hull() for a, b in zip(ths[:-1], ths[1:])])

u0 = 단위((22.0, 0, 52.0)); n0 = 단위(np.cross(A(0, 1, 0), u0)) * -1
n_ = 단위(n0 * np.cos(np.radians(15)) + A(0, -1, 0) * np.sin(np.radians(15)))
u_ = 단위(u0 - (u0 @ n_) * n_); v_ = np.cross(n_, u_)
방패외곽 = [(28, 0), (17, 19), (5, 22.5), (-5, 22.5), (-17, 19), (-28, 0), (-17, -19), (-5, -22.5), (5, -22.5), (17, -19)]
def 방패판(C, 줄, h): return [C + (a * (1 - 줄 / 28.0)) * u_ + (b * (1 - 줄 / 22.5)) * v_ + h * n_ for a, b in 방패외곽]
L겉 = L겉조.겉()
C = A(-51.0, 21.0, 263.0)
for _ in range(3):
    V_ = np.asarray(L겉.to_mesh().vert_properties)[:, :3]
    s_ = float(np.max(V_ @ n_) - C @ n_) + 0.8; C = C + s_ * n_
    proj = np.array(방패판(C, 0, 0) + 방패판(C, 0, 7.5)); cxz = (proj[:, [0, 2]].min(0) + proj[:, [0, 2]].max(0)) / 2
    C = C + A(-51.0 - cxz[0], 0, 263.0 - cxz[1]) * 0.9
V_ = np.asarray(L겉.to_mesh().vert_properties)[:, :3]; C = C + (float(np.max(V_ @ n_) - C @ n_) + 0.8) * n_
빨강 = 볼록(방패판(C, 1.2, 0) + 방패판(C, 0, 1.2) + 방패판(C, 0, 4.8) + 방패판(C, 1.4, 6.0))
금자리 = 볼록(방패판(C, 4.4, 3.6) + 방패판(C, 4.4, 9.0))
빨강 = 빨강 - 금자리 - 볼록(방패판(C, 6.0, -1.0) + 방패판(C, 6.0, 1.6))
금 = 볼록(방패판(C, 4.6, 3.6) + 방패판(C, 5.0, 7.2) + [C + 8.6 * n_]) - 볼록(방패판(C, 6.6, 3.5) + 방패판(C, 7.0, 5.6))
def 금면점(a, b):
    r = np.hypot(a / 23.4, b / 17.9); return C + a * u_ + b * v_ + (8.6 - 1.4 * min(r, 1)) * n_
문장 = []
t = np.linspace(0, 2 * np.pi, 33)
for k in range(32):
    문장.append((금면점(5.2 * np.cos(t[k]), 5.2 * np.sin(t[k])), 금면점(5.2 * np.cos(t[k + 1]), 5.2 * np.sin(t[k + 1]))))
for k in range(4):
    g = np.radians(45 + 90 * k); d2 = A(np.cos(g), np.sin(g)); q = A(-d2[1], d2[0])
    tri = [d2 * 8.0 + q * 3.0, d2 * 15.0, d2 * 8.0 - q * 3.0]
    for i in range(3): 문장.append((금면점(*tri[i]), 금면점(*tri[(i + 1) % 3])))
금 = V홈(금, 문장, n_, 폭=0.8, 깊=0.5)
# 방패 안쪽 윗모서리 5 mm 모따기 (목깃 쪽)
k_ = 단위(u_ - n_); 모서리 = C + 28.0 * u_
빨강 = 빨강.trim_by_plane(list(-k_), float(-k_ @ 모서리) + 3.5); 금 = 금.trim_by_plane(list(-k_), float(-k_ @ 모서리) + 3.5)
# 방패 힌지: 돔 위 바깥 (들기 피벗 둘레 60° 방향 겉) · 축 y · 방패는 바깥 위로 뜬다(아래 덮개가 밀어 올림)
_hp0 = 겉점(L겉, 팔[-1]["H"] + A(0, 0.5, 0), A(-np.cos(np.radians(62)), 0, np.sin(np.radians(62))))
_dir = A(-np.cos(np.radians(62)), 0, np.sin(np.radians(62))); _hp0 = _hp0 + 2.8 * _dir
방패힌지 = dict(p=A(_hp0[0], 21.0, _hp0[2]), y=(9.0, 33.0))
def 방패돌림(m, 도): return 돌림(m, 방패힌지["p"], A(0, 1, 0), 도)       # L: +y 축 둘레 + = 바깥(−x) 위로
assert 방패돌림(구(C - 20 * u_, 0.5), 30).bounding_box()[0] < (C - 20 * u_)[0], "방패 뜸 방향"

def 어깨(s):
    Lr = "L" if s < 0 else "R"
    조 = L겉조 if s < 0 else R겉조
    겉 = 조.겉(); 껍 = 조.껍질(); pa = 팔[s]; H = pa["H"]
    덮영역 = 쐐기영역(s, rr=r_c[s])
    S점 = 조.p[0][0]
    덮겉 = 볼록(밀기(S점, -(두께 + 비움))) ^ 덮영역          # 돔보다 2.4 안쪽 겹(포개짐 단차)
    팔겉 = pa["위"].겉() + pa["아래"].겉()
    팔비움 = 합([볼록(밀기(P_, 비움)) for P_, _ in pa["위"].p + pa["아래"].p])
    공통 = 뼈몸(Lr + "어깨블록", 비움) + 뼈몸(Lr + "어깨축", 비움) + 외피(Lr + "어깨회전", 비움) + 외피(Lr + "어깨들기", 비움)
    # 돔: 덮개 영역(+틈) 과 팔이 0~90° 쓸고 가는 부피를 뺀다
    덮틈 = 볼록(밀기(S점, -두께)) ^ 쐐기영역(s, α1=α_s + 1.5, rr=r_c[s] + 비움)
    덮쓸 = 쓸기(덮틈, s, -1.5, 91.5, 7.5)
    팔쓸 = 합([쓸기(볼록(밀기(P_, 비움)), s, 0.0, 90.0, 7.5) for P_, _ in pa["위"].p + pa["아래"].p])
    돔막 = 공통 + 덮쓸 + 팔쓸 + 쐐기영역(s)
    돔 = 껍 - 돔막
    # 뼈 잡이 격벽 (|x| 33.0~34.6)
    격벽 = (M.Manifold.cube([1.6, 80, 80]).translate([s * 33.0 - (1.6 if s < 0 else 0), -20, 220]) ^ 겉) - (돔막 + 뼈몸(Lr + "어깨블록"))
    돔 = 돔 + 격벽
    if 가슴D1 is not None:   # 어깨스윙 −15~30° 동안 D1 가슴이 쓸고 가는 부피 +0.4 = 가슴 쪽 모따기
        js = 관[Lr + "어깨스윙"]; g0 = 가슴D1 ^ M.Manifold.cube([40, 80, 60]).translate([(0 if s > 0 else -40), -20, 225])
        가쓸 = 합([돌림(g0, js["피벗mm"], js["범위"][0]["축"], -d).translate([s * 0.4, 0, 0]) for d in np.arange(-15, 30.1, 5.0)] +
                  [돌림(g0, js["피벗mm"], js["범위"][0]["축"], -d).translate([0, dy, 0]) for d in (-15, 30) for dy in (-0.4, 0.4)])
        # 모따기 면이 구멍으로 뚫리지 않게: 깎은 면을 따라 2 mm 벽을 다시 세운다(쓸기를 ±2 mm 밀어 합친 것 − 쓸기)
        불린 = 합([가쓸.translate(list(v)) for v in ((s * 2.0, 0, 0), (0, 2.0, 0), (0, -2.0, 0), (0, 0, 2.0), (0, 0, -2.0))] + [가쓸])
        돔 = (돔 - 가쓸) + (((불린 - 가쓸) ^ 겉) - 돔막)
    # 아래 덮개(윗팔위): 껍질 ∩ 덮개 영역 + 너클 잇는 판(가르는 면 y=H.y 둘레 두께 3) − 부모(어깨블록 뼈 · 들기 외피 · 어깨회전 외피) 쓸기
    #   − 아래 윗팔(윗팔회전 자식) 원통 +0.4
    부모쓸 = 합([팔돌림(공통, s, -th) for th in range(0, 91, 10)])
    아래팔막 = 원기둥(H + (pa["t_rot"] - 0.2) * pa["a"], H + 60.0 * pa["a"], Ra + 비움, seg=64)
    판 = (M.Manifold.cube([80, 3.0, 80]).translate([H[0] - 40, H[1] - 1.5, H[2] - 40]) ^ 덮겉)
    덮 = ((덮겉 - 볼록(밀기(S점, -(2 * 두께 + 비움)))) + 판) - 부모쓸 - 아래팔막
    return dict(겉=겉, 돔=돔, 덮=덮, 돔막=돔막, 덮겉=덮겉, 부모쓸=부모쓸, 아래팔막=아래팔막, 공통=공통)
어 = {s: 어깨(s) for s in (-1, 1)}

# 방패 힌지 러그: 돔 가운데 러그 · 방패 양 러그 · Ø1.75 핀
hp = 방패힌지["p"]; y0, y1 = 방패힌지["y"]; ym = (y0 + y1) / 2
def 러그(ya, yb, r=2.4): return 원기둥((hp[0], ya, hp[2]), (hp[0], yb, hp[2]), r, seg=32)
틈통 = 러그(ym - 4.0 - 관절틈, ym + 4.0 + 관절틈, 2.4 + 관절틈)
방러그틈 = 러그(y0 - 0.5, ym - 4.0 - 관절틈, 2.4 + 관절틈) + 러그(ym + 4.0 + 관절틈, y1 + 0.5, 2.4 + 관절틈)
핀구멍 = 원기둥((hp[0], y0 - 1, hp[2]), (hp[0], y1 + 1, hp[2]), 0.925, seg=24)
돔러그 = 러그(ym - 4.0, ym + 4.0) + (볼록(np.vstack([원점들(A(hp[0], y, hp[2]), A(0, 1, 0), 2.4, 16) for y in (ym - 4.0, ym + 4.0)] +
                                          [np.array([(hp[0] + 3.0, y, hp[2] - 3.0) for y in (ym - 4.0, ym + 4.0)])])))
방패러그 = 러그(y0, ym - 4.0 - 관절틈) + 러그(ym + 4.0 + 관절틈, y1)
_뒤 = [C + a * u_ + b * v_ + 0.5 * n_ for a in (12.0, 20.0) for b in (-10.0, 10.0)]
방패러그 = 방패러그 + 볼록(np.vstack([원점들(A(hp[0], y0, hp[2]), A(0, 1, 0), 2.4, 16), 원점들(A(hp[0], y1, hp[2]), A(0, 1, 0), 2.4, 16), np.array(_뒤)])) - 틈통
빨강 = ((빨강 + 방패러그) - 틈통 - 금자리 - 핀구멍) - 볼록(밀기(np.vstack([P_ for P_, _ in L겉조.p]), 0.3))
L돔 = ((어[-1]["돔"] + 돔러그) - 방러그틈 - 핀구멍 - 어[-1]["돔막"])
방쓸 = 합([방패돌림(빨강 + 금, ph) for ph in range(2, 92, 3)]) - 러그(y0 - 1, y1 + 1, 2.4 + 관절틈)
L돔 = L돔 - 방쓸                      # 방패가 뜨는 길(힌지 둘레 제외)
사양["핀"].append(dict(부품="방패 힌지", 지름=1.75, 길이=round(y1 - y0 + 1.0, 1), 재료="PLA 필라멘트", 구멍지름=1.85))

def 가시(b, tip, r, y끝=None, z끝=None):
    b, tip = A(*b), A(*tip); d = 단위(tip - b); L_ = np.linalg.norm(tip - b)
    b = 겉점(R겉조.겉(), b, d)
    if y끝 is not None: L_ = (y끝 - b[1]) / d[1]
    if z끝 is not None: L_ = (z끝 - b[2]) / d[2]
    tip = b + L_ * d
    몸 = 볼록(np.vstack([원점들(b - 3.0 * d, d, r, 8), 원점들(b, d, r, 8), 원점들(tip, d, 0.8, 8)]))
    뿌리 = np.vstack([원점들(b - 3.0 * d, d, r, 8), 원점들(b + 0.8 * d, d, r * (1 - 0.8 / np.linalg.norm(tip - b)), 8)])
    return 몸, 뿌리
# 가시 넷: 돔(각 α ≥ 25°)에서 방사로
가시들 = {"가시위": 가시((46.0, 28.7, 271.0), (46.0, 28.7, 290.0), 4.5, z끝=290.0),
          "가시밖": 가시((56.0, 28.7, 266.0), (61.5, 28.7, 274.5), 3.2),
          "가시앞": 가시((54.0, 22.0, 263.0), 단위((0.35, -0.85, 0.3)) * 12.0 + A(54.0, 22.0, 263.0), 4.0, y끝=8.0),
          "가시뒤": 가시((54.0, 35.4, 263.0), 단위((0.35, 0.85, 0.3)) * 12.0 + A(54.0, 35.4, 263.0), 4.0, y끝=50.0)}
R겉 = R겉조.겉(); R돔 = 어[1]["돔"]
for k, (몸, 뿌리) in 가시들.items():
    R돔 = 꽂이(R돔, R겉, 뿌리) - 어[1]["돔막"]
# 판 단차: R 돔 앞면 가운데 0.8 오목 판(외곽 평행 3 mm 안) · L 돔 위 0.6 오목
R돔 = R돔 - (볼록([(x, y, z) for x in (40.0, 53.0) for y in (9.0, 11.2) for z in (259.0, 268.0)]))
def 돔반쪽(s, 돔, 겉, 막):
    ycut = 21.0 if s < 0 else 28.7
    앞_, 뒤_ = 돔.split_by_plane([0, -1, 0], -ycut)
    H = 팔[s]["H"]; 점 = []
    for st, dd in (((s * 34.0, ycut, 261.0), A(-s, 0, 0)), ((s * 37.0, ycut, 258.0), A(0, 0, 1)), ((s * 47.0, ycut, 258.0), A(s * 0.5, 0, 0.87))):
        dd = 단위(dd); p_ = 겉점(겉, A(*st), dd) - 3.2 * dd; p_[1] = ycut; 점.append(p_)
    return 다보붙이기(앞_, 뒤_, 겉, 막, 점, A(0, 1, 0))
L돔앞, L돔뒤 = 돔반쪽(-1, L돔, L겉, 어[-1]["돔막"] + 핀구멍 + 방쓸)
R돔앞, R돔뒤 = 돔반쪽(1, R돔, R겉, 어[1]["돔막"])
for s in (-1, 1):
    Lr = "L" if s < 0 else "R"
    사양["뼈구멍"].append(dict(부품=Lr + "어깨돔앞/뒤", 뼈=Lr + "어깨블록", 결합="격벽이 뼈를 물고 닫힘(틈 0) — 구멍 없음"))
넣기("L어깨돔앞", L돔앞, 색["파"], "L어깨", "L어깨돔뒤(다보)", 뼈="L어깨블록")
넣기("L어깨돔뒤", L돔뒤, 색["파"], "L어깨", "L어깨블록 뼈(격벽)", 뼈="L어깨블록")
넣기("방패빨강", 빨강, 색["빨"], "L어깨", "L돔 힌지(Ø1.75 핀) — 들 때 아래 덮개가 밀어 올린다", 뼈="L어깨블록")
넣기("방패금", 금, 색["금"], "L어깨", "방패빨강 자리에 끼움(붙임)", 뼈="L어깨블록")
넣기("R어깨돔앞", R돔앞, 색["파"], "R어깨", "R어깨돔뒤(다보)", 뼈="R어깨블록")
넣기("R어깨돔뒤", R돔뒤, 색["파"], "R어깨", "R어깨블록 뼈(격벽)", 뼈="R어깨블록")
for k, (몸, _) in 가시들.items():
    넣기(k, 몸 - 어[1]["돔막"], 색["금"], "R어깨", "R어깨돔 소켓", 뼈="R어깨블록")

# 윗팔 반쪽(윗팔위 = 너클 + 아래 덮개 · 윗팔 = 원통) · 다보 · 보스 · 고리 홈
로그("윗팔")
for s in (-1, 1):
    pa = 팔[s]; Lr = pa["Lr"]; H, a = pa["H"], pa["a"]
    for 이름, 조 in (("윗팔위", pa["위"]), ("윗팔", pa["아래"])):
        겉 = 조.겉(); 껍 = 조.껍질()
        막 = 뼈몸(Lr + "윗팔위", 비움) + 뼈몸(Lr + "윗팔", 비움) + 외피(Lr + "윗팔회전", 비움) + 외피(Lr + "어깨들기", 비움) + 외피(Lr + "팔꿈치", 비움)
        if 이름 == "윗팔위":
            껍 = 껍 + 어[s]["덮"]; 겉 = 겉 + 어[s]["덮겉"]
            막 = 막 + 어[s]["부모쓸"] + 어[s]["아래팔막"]
            색_ = 색["파"]
        else:
            껍 = 껍 - 고리홈(H + 26.0 * a, a, Ra); 색_ = 색["검"]
        껍 = 껍 - 막
        n_cut = 단위(A(0, 1, 0) - (A(0, 1, 0) @ a) * a)
        앞_, 뒤_ = 껍.split_by_plane(list(-n_cut), float(-n_cut @ H))
        u2 = 단위(np.cross(a, n_cut))
        if 이름 == "윗팔위":
            점들 = []
            for ang in (-60.0, 0.0):
                dd = A(s * np.cos(np.radians(ang)), 0, np.sin(np.radians(ang)))
                p_ = 겉점(어[s]["덮겉"], H + A(0, 0.01, 0), dd) - 3.2 * dd; 점들.append(p_ + (n_cut @ (H - p_)) * n_cut)
        else:
            ts = [(pa["t_rot"] + 4.0, 1), (pa["t_rot"] + 4.0, -1), (pa["t_end"] - 4.0, 1), (pa["t_end"] - 4.0, -1)]
            점들 = [H + t_ * a + sg * (Ra - 2.6) * u2 for t_, sg in ts]
        앞_, 뒤_ = 다보붙이기(앞_, 뒤_, 겉, 막, 점들, n_cut)
        bn = Lr + 이름; ch = 뼈[bn]["마디"][0]; q0, q1 = A(*ch[0][:3]), A(*ch[-1][:3])
        tq = 0.5
        qc = q0 + tq * (q1 - q0); rq = (ch[0][3] + tq * (ch[-1][3] - ch[0][3])) / 2
        뒤_, s3 = 보스(뒤_, 겉, bn, qc + rq * n_cut, n_cut); 사양["뼈구멍"].append(dict(부품=Lr + 이름 + "뒤", **s3))
        넣기(Lr + 이름 + "앞", 앞_, 색_, Lr + "윗팔", Lr + 이름 + "뒤(다보)", 뼈=bn)
        넣기(Lr + 이름 + "뒤", 뒤_, 색_, Lr + "윗팔", bn + " 뼈(보스)", 뼈=bn)

# ════════════════════════ 팔끝 (짐승 머리 팔끝 몸체 · 단순 각진 판) ════════════════════════════
# 치수(원화 정면, 골격 척도): L 워그레이몬 머리(주황) x −90~−57 · z 145~226, 은 뿔 둘 (−78,206)→(−96,238) · (−88,170)→(−110,195).
#   R 가루몬 늑대 머리(파랑) x 41~93 · z 145~232, 귀 둘 z 240, 주둥이 아래 바깥 (93, 165).
#   깊이는 옆 그림에 없어 y 2~31 (팔 뼈 y 15~16 중심). L 안쪽 가장자리는 원화(−57)보다 뼈(팔끝 −60~−62, R7+2.4)가 우선 → −51.
# 팔끝회전 자리에서 축에 수직으로 가른다: 위 = 팔끝(팔꿈치 자식) · 아래 = 손(팔끝회전 자식). 무기 = 쥠 회전축8 자식 끝 Ø5 D 컷(J2)
#   으로 꽂고, 장갑은 쥠 축을 따라 통로 Ø13.8 을 판다.
로그("팔끝")
def 팔끝(s):
    Lr = "L" if s < 0 else "R"
    if s < 0:
        단 = [(152.0, -84.0, -66.0, 6.0, 26.0, 4.0), (165.0, -89.0, -52.0, 2.0, 30.0, 6.0), (190.0, -90.0, -50.5, 2.0, 31.0, 7.0),
             (212.0, -84.0, -50.5, 4.0, 29.0, 6.0), (223.0, -74.0, -62.0, 9.0, 24.0, 3.0)]
        뿔들 = [((-78.0, 16.0, 206.0), (-96.0, 16.0, 238.0), 4.5), ((-88.0, 16.0, 172.0), (-110.0, 16.0, 195.0), 4.0)]
        쥠 = "L칼쥠"; 색_ = (0.93, 0.55, 0.18)
    else:
        단 = [(150.0, 52.0, 86.0, 6.0, 26.0, 4.0), (165.0, 46.0, 92.0, 3.0, 30.0, 6.0), (185.0, 41.5, 87.0, 2.0, 31.0, 7.0),
             (205.0, 43.0, 80.0, 4.0, 29.0, 6.0), (222.0, 58.0, 78.0, 8.0, 25.0, 3.0)]
        뿔들 = [((67.0, 16.0, 219.0), (69.0, 16.0, 240.0), 3.5), ((76.0, 16.0, 218.0), (79.0, 16.0, 238.0), 3.5)]
        쥠 = "R대포쥠"; 색_ = 색["파"]
    조 = 조각().더(np.vstack([돔단면(*r) for r in 단[:3]])).더(np.vstack([돔단면(*r) for r in 단[2:]]))
    if s > 0:   # 주둥이: 아래 바깥으로
        조.더([(x, y, z) for x, z in [(78.0, 186.0), (78.0, 158.0), (95.0, 175.0), (93.0, 162.0)] for y in (7.0, 25.0)])
    for b_, t_, r_ in 뿔들:
        b_, t_ = A(*b_), A(*t_); d = 단위(t_ - b_)
        조.더(np.vstack([원점들(b_ - 3.0 * d, d, r_, 8), 원점들(t_, d, 0.8, 8)]), 빈=False)
    겉 = 조.겉(); 껍 = 조.껍질()
    # 팔꿈치 원판(정면에서 보이는 둥근 판): 앞면에서 1.5 mm 돋움 + 가운데 R4.5 오목 1.5 (단차 · 몰드)
    ec = A(s * 57.5, 겉점(겉, A(s * 57.5, 16.0, 201.0), A(0, -1, 0))[1], 201.0)
    원판 = 원기둥(ec + A(0, 3.0, 0), ec - A(0, 1.5, 0), 8.0, seg=48) - 원기둥(ec + A(0, 0.5, 0), ec - A(0, 2.0, 0), 4.5, seg=40)
    껍 = 껍 + 원판; 겉 = 겉 + 원판
    jw = 관[Lr + "팔끝회전"]; pw = A(*jw["피벗mm"]); aw = 단위(jw["축"])      # aw = 아래(손) 쪽
    jg = 관[쥠]; pg = A(*jg["피벗mm"]); ag = 단위(jg["축"])                  # ag 반대 = 무기 쪽
    통로 = 원기둥(pg, pg - 60.0 * ag, 6.5 + 비움, seg=48)
    막 = 뼈몸(Lr + "팔끝", 비움) + 뼈몸(Lr + "손", 비움) + 외피(Lr + "팔꿈치", 비움) + 외피(Lr + "팔끝회전", 비움) + 외피(쥠, 비움) + 통로
    # 팔꿈치 0~150° 굽힘 동안 부모(윗팔 원통 +0.4)가 팔끝 틀에서 쓸고 가는 부피
    je = 관[Lr + "팔꿈치"]; P1 = A(*je["피벗mm"]); P2 = A(*je["외피"]["둘째축피벗mm"]); ae = je["범위"][0]["축"]
    부모 = 합([볼록(밀기(P_, 비움)) for P_, _ in 팔[s]["아래"].p]) + 뼈몸(Lr + "윗팔", 비움)
    쓸_ = []
    for th in np.arange(0, 150.1, 10.0):
        m_ = 돌림(돌림(부모, P1, ae, -th / 2), P2, ae, -th / 2); 쓸_.append(m_)
    팔꿈쓸 = 합([(a_ + b_).hull() for a_, b_ in zip(쓸_[:-1], 쓸_[1:])])
    막 = 막 + 팔꿈쓸
    껍 = 껍 - 막
    위_, 아래_ = 껍.split_by_plane(list(-aw), float(-aw @ pw) + 관절틈 / 2)
    아래_ = 아래_.trim_by_plane(list(aw), float(aw @ pw) + 관절틈 / 2)
    out = {}
    for 이름, part, bn in (("팔끝", 위_, Lr + "팔끝"), ("손", 아래_, Lr + "손")):
        ycut = 16.0
        앞_, 뒤_ = part.split_by_plane([0, -1, 0], -ycut)
        ch = 뼈[bn]["마디"][0]; q0, q1 = A(*ch[0][:3]), A(*ch[-1][:3]); qm = (q0 + q1) / 2
        ax_ = 단위(q1 - q0)
        # 다보: 뼈 둘레 바깥 · 안쪽 (가르는 면 위, 벽 안쪽 3.5 mm)
        cs = []
        for dx in (-1, 1):
            p_ = 겉점(겉, A(qm[0], ycut, qm[2]) + A(dx * 3.0, 0, 0), A(dx, 0, 0)) - A(dx * 3.2, 0, 0); p_[1] = ycut; cs.append(p_)
        앞_, 뒤_ = 다보붙이기(앞_, 뒤_, 겉, 막, cs, A(0, 1, 0))
        뒤_, s4 = 보스(뒤_, 겉, bn, qm + (ch[0][3] / 2) * A(0, 1, 0), A(0, 1, 0)); 사양["뼈구멍"].append(dict(부품=Lr + 이름 + "뒤", **s4))
        out[이름] = (앞_, 뒤_, bn)
    사양.setdefault("무기소켓", []).append(dict(쥠=쥠, 피벗mm=pg.round(2).tolist(), 축=(-ag).round(3).tolist(),
                                            결합="쥠 회전축8(J2) 자식 끝 Ø5 D 컷에 무기 촉 Ø4.6 D 를 꽂는다 · 장갑 통로 Ø%.1f" % (2 * (6.5 + 비움))))
    return out, 색_
for s in (-1, 1):
    Lr = "L" if s < 0 else "R"
    out, 색_ = 팔끝(s)
    for 이름, (앞_, 뒤_, bn) in out.items():
        넣기(Lr + 이름 + "앞", 앞_, 색_, Lr + "팔끝", Lr + 이름 + "뒤(다보)", 뼈=bn)
        넣기(Lr + 이름 + "뒤", 뒤_, 색_, Lr + "팔끝", bn + " 뼈(보스)", 뼈=bn)
로그("부품 %d" % len(부품)); [print("   ", k, round(부피(d["m"]), 1), len(d["m"].decompose())) for k, d in 부품.items()]

# ════════════════════════ 검사 ════════════════════════════
def 조각잇기(m):  # 떨어진 조각 수
    return len(m.decompose())
결과 = {"부품": {}}
os.makedirs(OUT, exist_ok=True)
for f_ in os.listdir(OUT):          # 1바퀴 이름(캡 · 날개 등) 남지 않게
    if f_.endswith(".stl"): os.remove(os.path.join(OUT, f_))
for k, d in 부품.items():
    d["m"] = 정리(d["m"], k).simplify(0.02); m = d["m"]; tm = 메시(m); fn = os.path.join(OUT, k + ".stl"); tm.export(fn)
    re = trimesh.load(fn, force="mesh"); wt = bool(re.is_watertight)
    if not wt:   # 자기 접촉: 같은 자리에 겹친 정점(서로 다른 면 무리)을 각자 법선 안쪽으로 0.03 mm 밀어 뗀다(위상은 manifold 그대로)
        V = tm.vertices.copy(); key = np.round(V / 1e-4).astype(np.int64)
        _, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
        dup = cnt[inv.ravel()] > 1
        VN = np.zeros_like(V); np.add.at(VN, tm.faces.ravel(), np.repeat(tm.face_normals, 3, 0))
        VN /= np.linalg.norm(VN, axis=1, keepdims=True) + 1e-12
        FC = np.zeros_like(V); np.add.at(FC, tm.faces.ravel(), np.repeat(tm.triangles_center, 3, 0))
        FC = FC / np.bincount(tm.faces.ravel(), minlength=len(V))[:, None] - V
        FC /= np.linalg.norm(FC, axis=1, keepdims=True) + 1e-12
        for 양 in (0.03, 0.06, 0.10):
            V2 = V.copy(); V2[dup] += 양 * (FC[dup] - VN[dup])       # 제 면들 쪽 · 안쪽으로
            t2 = trimesh.Trimesh(V2, tm.faces, process=False); t2.export(fn); re = trimesh.load(fn, force="mesh"); wt = bool(re.is_watertight)
            if wt: break
        로그("  %s 겹친 정점 %d 떼기 → 닫힘 %s" % (k, int(dup.sum()), wt))
    결과["부품"][k] = dict(파일=k + ".stl", 뼈=d["뼈"], 묶음=d["묶음"], 붙는곳=d["붙는곳"], 색=d["색"], 닫힘=wt, 조각=조각잇기(m),
                        부피mm3=round(부피(m), 1), 무게g_PLA=round(부피(m) * 1.24e-3, 2), 삼각형=int(len(re.faces)),
                        크기mm=np.round(re.extents, 1).tolist())
로그("STL 닫힘 %d/%d" % (sum(v["닫힘"] for v in 결과["부품"].values()), len(부품)))

# 가동 간섭 (manifold 교집합 mm³)
머리들 = [부품[k]["m"] for k in 부품 if 부품[k]["묶음"] == "머리"]; 머리합 = 합(머리들)
목 = 뼈몸("목")
가슴후보 = os.path.join(ROOT, "out", "출력", "오메가몬_PG", "디자인", "몸통")
if os.path.isdir(가슴후보) and any(f.endswith(".stl") for f in os.listdir(가슴후보)):
    ms = []
    for f in os.listdir(가슴후보):
        if f.endswith(".stl"):
            t = trimesh.load(os.path.join(가슴후보, f))
            try: ms.append(M.Manifold(M.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32))))
            except Exception: pass
    가슴 = 합(ms); 가슴출처 = "D1 몸통 STL %d 개" % len(ms)
else:   # 대용: 192 키트 몸 O ∩ E13 가슴 라벨 (칸 1.97 mm — 거칠다)
    from skimage.measure import marching_cubes
    d192 = np.load(os.path.join(ROOT, "out", "분할후보", "입력.npz")); O = d192["O"]; axi = float(d192["축i"])
    zs = np.nonzero(O.any((0, 1)))[0]; Cm = 300.0 / (zs[-1] - zs[0] + 1); y0 = np.argwhere(O[:, :, zs[0]:zs[0] + 2])[:, 1].mean()
    lab = np.load(os.path.join(ROOT, "out", "분할후보", "E13", "lab.npy"))
    nm = {v: int(k) for k, v in json.load(open(os.path.join(ROOT, "out", "분할후보", "E13", "이름.json"), encoding="utf-8")).items()}
    G = O & np.isin(lab, [nm["가슴앞"], nm["가슴뒤"], nm["가슴판"]])
    xmm_ = (np.arange(192) - axi) * Cm; zmm_ = (np.arange(192) - (zs[0] - 0.5)) * Cm
    G &= (np.abs(xmm_) <= 29.0)[:, None, None] & (zmm_ <= 262.0)[None, None, :]      # 원화 가슴 가장자리 ±30 · 목깃은 D1 몫
    G = np.pad(G, 1).astype(np.float32); v_, f_, _, _ = marching_cubes(G, 0.5)
    v_ = v_ - 1; v_ = np.stack([(v_[:, 0] - axi) * Cm, (v_[:, 1] - y0) * Cm, (v_[:, 2] - (zs[0] - 0.5)) * Cm], 1)
    t = trimesh.Trimesh(v_, f_[:, ::-1]); 가슴 = M.Manifold(M.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))
    가슴출처 = "대용(키트 몸 O ∩ E13 가슴 라벨 ∩ |x|≤29 ∩ z≤262, 칸 1.97 mm)"
가동 = {"가슴출처": 가슴출처}
def 겹(a, b): return round(부피(a ^ b), 2)
# 목: 머리(목위 범위 끝 조합) vs 목 뼈 · 가슴
목표 = []
for rx in (-25, 0, 20):
    for ry in (-15, 0, 15):
        for rz in (-45, 0, 45):
            R = Rot.from_euler("xyz", [rx, ry, rz], degrees=True).as_matrix(); m = 머리합.transform(틀(R, Pn - R @ Pn))
            목표.append(dict(목위=[rx, ry, rz], 목뼈=겹(m, 목), 가슴=겹(m, 가슴)))
def 한축(ax_, rng):
    ok = []
    for d in rng:
        e = [0, 0, 0]; e["xyz".index(ax_)] = d
        R = Rot.from_euler("xyz", e, degrees=True).as_matrix()
        if 겹(머리합.transform(틀(R, Pn - R @ Pn)), 가슴) > 0.5: break
        ok.append(d)
    return ok[-1] if ok else None
가동["목위_한축한계(가슴∩머리 ≤0.5mm³)"] = {"끄덕+x": 한축("x", range(0, 26, 5)), "끄덕-x": 한축("x", range(0, -26, -5)),
                                        "옆+y": 한축("y", range(0, 16, 5)), "비틀기+z": 한축("z", range(0, 46, 5))}
로그("목위 한축 한계", 가동["목위_한축한계(가슴∩머리 ≤0.5mm³)"])
가동["목위_27자세"] = dict(목뼈최대=max(r["목뼈"] for r in 목표), 가슴최대=max(r["가슴"] for r in 목표),
                         가슴0자세=[r["가슴"] for r in 목표 if r["목위"] == [0, 0, 0]][0], 표=목표)
# 목아래까지 함께(끄덕 끝)
Pd = P("목아래"); 둘 = []
for ra, rb in ((-15, -25), (15, 20), (-15, 20), (15, -25)):
    R1 = Rot.from_euler("x", rb, degrees=True).as_matrix(); m = 머리합.transform(틀(R1, Pn - R1 @ Pn))
    R2 = Rot.from_euler("x", ra, degrees=True).as_matrix(); m = m.transform(틀(R2, Pd - R2 @ Pd))
    둘.append(dict(목아래x=ra, 목위x=rb, 가슴=겹(m, 가슴)))
가동["목아래+목위"] = 둘
# 어깨: 들기 θ — 팔(윗팔 · 아래 덮개 · 팔끝 전부) 을 θ 로 · 방패는 아래 덮개가 밀어 올린 만큼 φ(θ) (= 팔과 안 겹치는 가장 작은 φ)
for s in (-1, 1):
    Lr = "L" if s < 0 else "R"
    돔 = 합([부품[k]["m"] for k in 부품 if 부품[k]["묶음"] == Lr + "어깨" and not k.startswith("방패")])
    방 = 합([부품[k]["m"] for k in 부품 if k.startswith("방패")]) if s < 0 else None
    팔m = 합([부품[k]["m"] for k in 부품 if 부품[k]["묶음"] in (Lr + "윗팔", Lr + "팔끝")])
    jr = 관[Lr + "어깨회전"]; js = 관[Lr + "어깨스윙"]
    전체 = 돔 + 팔m + (방 if 방 is not None else M.Manifold())
    회전표 = [dict(도=d, 가슴=겹(돌림(전체, jr["피벗mm"], jr["범위"][0]["축"], d), 가슴)) for d in range(-180, 180, 30)]
    스윙표 = [dict(도=d, 가슴=겹(돌림(전체, js["피벗mm"], js["범위"][0]["축"], d), 가슴)) for d in (-15, 0, 15, 30)]
    들기표 = []; 최대 = 0; 최대φ = 0
    for th in range(0, 91, 5):
        am = 팔돌림(팔m, s, th); φ = 0
        if 방 is not None:
            φ = None
            for ph in range(0, 121, 3):
                if 겹(am, 방패돌림(방, ph)) == 0: φ = ph; break
        bm = 방패돌림(방, φ or 0) if 방 is not None else M.Manifold()
        r = dict(들기=th, 방패φ=φ, 팔_돔=겹(am, 돔), 팔_가슴=겹(am, 가슴), 팔_머리=겹(am, 머리합),
                 방패_가슴=겹(bm, 가슴), 방패_머리=겹(bm, 머리합), 방패_돔=겹(bm, 돔))
        들기표.append(r)
        if φ is None or max(v for k_, v in r.items() if k_ not in ("들기", "방패φ")) > 0.5: break
        최대 = th; 최대φ = φ
    가동[Lr + "어깨"] = dict(어깨회전=회전표, 어깨스윙=스윙표, 들기=들기표, 들기최대=최대, 그때_방패φ=최대φ)
    로그(Lr, "들기 최대", 최대, "방패", 최대φ, "막힘 행", 들기표[-1])
# 팔꿈치 0~150 (이중힌지 반씩): 팔끝 무리 vs 나머지 내 부품
for s in (-1, 1):
    Lr = "L" if s < 0 else "R"; je = 관[Lr + "팔꿈치"]; P1 = A(*je["피벗mm"]); P2 = A(*je["외피"]["둘째축피벗mm"]); ae = je["범위"][0]["축"]
    fm = 합([부품[k]["m"] for k in 부품 if 부품[k]["묶음"] == Lr + "팔끝"])
    고 = 합([부품[k]["m"] for k in 부품 if 부품[k]["묶음"] != Lr + "팔끝"]) + 가슴
    V0 = 겹(fm, 고); 된 = 0
    for th in range(10, 151, 10):
        if 겹(돌림(돌림(fm, P2, ae, th / 2), P1, ae, th / 2), 고) - V0 > 0.5: break
        된 = th
    가동[Lr + "팔꿈치"] = dict(최대=된, V0=V0); 로그(Lr, "팔꿈치 최대", 된)
결과["가동"] = 가동; 결과["버린조각mm3"] = 버린조각; 로그("버린 조각", 버린조각)
결과["사양"] = 사양
로그("가동 검사 끝")

# 실루엣: 정면(전 부품) · 옆(머리 + 오른 어깨)
from PIL import Image, ImageDraw
from scipy import ndimage
def 원화마스크(v):
    fn = {"앞": "omega_front_clean", "옆": "omega_side"}[v]
    a = np.array(Image.open(r"G:\art2real\트레일\trail7_part3d\in\%s.png" % fn)); m = a[..., 3] > 128
    return ndimage.binary_opening(m, iterations=2) if v == "옆" else m
사상 = {"앞": (0.342, 534.0, 951.0, 0), "옆": (0.349, 462.0, 938.0, 1)}   # 비평_조립.py 와 같은 골격 척도   # s, cx, zb, 수평축(0=x,1=y)
def 투영마스크(ms, v, res=0.2, 범=(-100, 100, 180, 320)):
    k = 사상[v][3]; W = int((범[1] - 범[0]) / res); Hh = int((범[3] - 범[2]) / res)
    img = Image.new("1", (W, Hh), 0); dr = ImageDraw.Draw(img)
    for m in ms:
        tm = 메시(m); V2 = np.stack([(tm.vertices[:, k] - 범[0]) / res, (범[3] - tm.vertices[:, 2]) / res], 1)
        for f in tm.faces: dr.polygon([tuple(V2[i]) for i in f], fill=1)
    return np.array(img), 범, res
def 원화격자(v, 범, res):
    s, cx, zb, k = 사상[v]; m = 원화마스크(v)
    xs = 범[0] + (np.arange(int((범[1] - 범[0]) / res)) + 0.5) * res; zs_ = 범[3] - (np.arange(int((범[3] - 범[2]) / res)) + 0.5) * res
    px = np.clip(np.rint(cx + xs / s).astype(int), 0, 1023); py = np.clip(np.rint(zb - zs_ / s).astype(int), 0, 1023)
    return m[py][:, px]
def 실루엣(ms, v, 범):
    mine, 범, res = 투영마스크(ms, v, 범=범); art = 원화격자(v, 범, res)
    경 = lambda b: b & ~ndimage.binary_erosion(b)
    dA = ndimage.distance_transform_edt(~경(art)) * res          # 원화 윤곽까지
    bg = ndimage.distance_transform_edt(art) * res                # 원화 배경까지
    e = 경(mine) & (bg <= 3.0)                                    # 원화 바깥 윤곽 근처의 내 윤곽만
    d = dA[e]
    if len(d) == 0: return None, mine, art
    return dict(점=int(len(d)), 중앙=round(float(np.median(d)), 2), p95=round(float(np.percentile(d, 95)), 2), 최대=round(float(d.max()), 2),
                안2mm=round(float((d <= 2.0).mean()), 3)), mine, art
실 = {}
묶범 = {"머리": (-30, 30, 255, 312), "L어깨": (-66, -28, 234, 292), "R어깨": (28, 64, 233, 292), "L윗팔": (-62, -36, 212, 240), "R윗팔": (36, 60, 212, 240),
      "L팔끝": (-112, -40, 140, 240), "R팔끝": (38, 100, 140, 242)}
for g, 범 in 묶범.items():
    ms = [부품[k]["m"] for k in 부품 if 부품[k]["묶음"] == g]
    r, _, _ = 실루엣(ms, "앞", 범); 실["앞_" + g] = r
for g, 범 in {"머리": (-10, 40, 256, 312), "R어깨": (5, 60, 234, 292)}.items():
    ms = [부품[k]["m"] for k in 부품 if 부품[k]["묶음"] == g]
    r, _, _ = 실루엣(ms, "옆", 범); 실["옆_" + g] = r
결과["실루엣mm"] = 실
결과["총무게g_PLA"] = round(sum(v["무게g_PLA"] for v in 결과["부품"].values()), 1)
json.dump(결과, open(os.path.join(OUT, "부품.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1,
          default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
로그("실루엣", json.dumps(실, ensure_ascii=False))

# ════════════════════════ 그림 ════════════════════════════
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
plt.rcParams["font.family"] = ["Malgun Gothic"]; plt.rcParams["axes.unicode_minus"] = False
def 그리기(ax, 목록, 방위=0.0, 앙각=0.0, 원화=None, 제목=""):
    """목록 = [(manifold, 색)] · 방위 0 = 정면(−y 에서 봄), 90 = 옆(+x 에서 봄). 정사영 · 뒤→앞 칠하기."""
    az, el = np.radians(방위), np.radians(앙각)
    Rz = np.array([[np.cos(az), np.sin(az), 0], [-np.sin(az), np.cos(az), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, np.cos(el), -np.sin(el)], [0, np.sin(el), np.cos(el)]])
    R = Rx @ Rz; polys, cols, dep = [], [], []
    for m, c in 목록:
        if m.is_empty(): continue
        tm = 메시(m); v2, f2 = trimesh.remesh.subdivide_to_size(tm.vertices, tm.faces, 1.5)   # 큰 삼각형 칠하기 순서 어긋남 방지
        tm = trimesh.Trimesh(v2, f2, process=False); V = tm.vertices @ R.T; F = tm.faces; N = tm.face_normals @ R.T
        vis = N[:, 1] < 0
        sh = 0.38 + 0.62 * np.clip((tm.face_normals @ R.T) @ 단위((-0.35, -0.75, 0.55)), 0, 1)
        for f, s_ in zip(F[vis], sh[vis]):
            polys.append(V[f][:, [0, 2]]); cols.append(np.clip(np.array(c) * s_, 0, 1)); dep.append(V[f][:, 1].mean())
    o = np.argsort(dep)[::-1]
    ax.add_collection(PolyCollection([polys[i] for i in o], facecolors=[cols[i] for i in o], edgecolors="none", antialiased=False))
    if 원화 is not None:
        for c_ in 원화: ax.plot(c_[:, 0], c_[:, 1], color=(0.9, 0.1, 0.5), lw=0.7)
    ax.set_aspect("equal"); ax.autoscale_view(); ax.set_title(제목, fontsize=9); ax.axis("off")
def 원화윤곽(v, 범=(-100, 100, 180, 320), res=0.25):
    from skimage.measure import find_contours
    art = 원화격자(v, 범, res)
    cs = find_contours(art.astype(float), 0.5)
    return [np.stack([범[0] + (c[:, 1] + 0.5) * res, 범[3] - (c[:, 0] + 0.5) * res], 1) for c in cs if len(c) > 30]
기본 = [(d["m"], d["색"]) for d in 부품.values()]
뼈들 = [(뼈몸(n), (0.55, 0.55, 0.55)) for n in ("머리", "목", "가슴") if n in 뼈]
fig = plt.figure(figsize=(22, 14))
ax = fig.add_subplot(2, 4, 1); 그리기(ax, 기본, 0, 0, 원화윤곽("앞", (-100, 100, 200, 320)), "정면 + 원화 윤곽(분홍)")
ax.set_xlim(-72, 72); ax.set_ylim(206, 312)
ax = fig.add_subplot(2, 4, 2); 그리기(ax, [(d["m"], d["색"]) for d in 부품.values() if d["묶음"] in ("머리", "R어깨")], 90, 0,
                                   원화윤곽("옆", (-20, 70, 200, 320)), "옆(+x 에서) 머리 + 오른 어깨 + 원화 윤곽")
ax.set_xlim(-15, 62); ax.set_ylim(228, 312)
ax = fig.add_subplot(2, 4, 3); 그리기(ax, 기본, -35, 18, None, "3/4 (앞 왼쪽 위)")
ax = fig.add_subplot(2, 4, 4); 그리기(ax, 기본, 215, 18, None, "3/4 (뒤)")
# 들기 90° + 날개 띄움
자세 = []
for k, d in 부품.items():
    m = d["m"]; g = d["묶음"]
    for s in (-1, 1):
        Lr = "L" if s < 0 else "R"
        ph = 가동[Lr + "어깨"]["그때_방패φ"] or 0; th = 가동[Lr + "어깨"]["들기최대"]
        if g in (Lr + "윗팔", Lr + "팔끝"): m = 팔돌림(m, s, th)
        if s < 0 and k.startswith("방패"): m = 방패돌림(m, ph)
    자세.append((m, d["색"]))
자세 += [(D1(("가슴", "목깃", "엠블럼", "복부")) or 가슴, (0.8, 0.8, 0.85))]
ax = fig.add_subplot(2, 4, 5); 그리기(ax, 자세, 0, 0, None, "최대 들기 L %d°(방패 밀려 %d°) · R %d° · 회색 = D1 가슴" % (
    가동["L어깨"]["들기최대"], 가동["L어깨"]["그때_방패φ"] or 0, 가동["R어깨"]["들기최대"]))
ax = fig.add_subplot(2, 4, 6); 그리기(ax, 자세, -30, 20, None, "최대 들기 3/4")
# 분해도
분해 = []
밀 = {"투구앞": (0, -14, 4), "투구뒤": (0, 12, 0), "얼굴": (0, -26, -4), "뿔": (0, -8, 16), "V안테나L": (-10, 0, 10), "V안테나R": (10, 0, 10),
      "방패빨강": (-16, 0, 6), "방패금": (-28, -4, 10), "L어깨돔앞": (0, -10, 4), "L어깨돔뒤": (0, 8, 4),
      "R어깨돔앞": (0, -10, 4), "R어깨돔뒤": (0, 8, 4), "볼가리개L": (-8, 0, 0), "볼가리개R": (8, 0, 0), "가시위": (10, 0, 12), "가시밖": (16, 0, 8), "가시앞": (14, -10, 4), "가시뒤": (14, 10, 4)}
for k, d in 부품.items():
    o = 밀.get(k)
    if o is None:
        o = (0, -8, 0) if k.endswith("앞") else (0, 8, 0)
        o = (o[0] + (-8 if k.startswith("L") else 8), o[1], -14 if "윗팔" in k and "위" not in k else 0)
    분해.append((d["m"].translate(list(map(float, o))), d["색"]))
ax = fig.add_subplot(2, 4, 7); 그리기(ax, 분해, -35, 18, None, "분해도")
ax = fig.add_subplot(2, 4, 8); ax.axis("off")
txt = ["부품 %d · 닫힘 %d/%d · 무게 %.1f g (PLA 꽉 참)" % (len(부품), sum(v["닫힘"] for v in 결과["부품"].values()), len(부품), 결과["총무게g_PLA"]), ""]
for k, r in 실.items():
    if r: txt.append("%s 실루엣  중앙 %.2f · p95 %.2f · 최대 %.2f · ±2 안 %.0f%%" % (k, r["중앙"], r["p95"], r["최대"], 100 * r["안2mm"]))
txt += ["", "목위 한 축 한계(D1 목깃·가슴과 ≤0.5 mm³): " + json.dumps(가동["목위_한축한계(가슴∩머리 ≤0.5mm³)"], ensure_ascii=False), "목위 27 자세: 목뼈 겹침 최대 %.2f mm³ · 가슴 최대 %.2f (0 자세 %.2f)" % (가동["목위_27자세"]["목뼈최대"], 가동["목위_27자세"]["가슴최대"], 가동["목위_27자세"]["가슴0자세"])]
for Lr in ("L", "R"):
    for r in 가동[Lr + "어깨"]["들기"][::3] + 가동[Lr + "어깨"]["들기"][-1:]:
        txt.append("%s 들기 %2d°: 방패 %s° · 팔∩돔 %.1f · 팔∩가슴 %.1f · 팔∩머리 %.1f · 방패∩가슴 %.1f · 방패∩머리 %.1f · 방패∩돔 %.1f" % (
            Lr, r["들기"], r["방패φ"], r["팔_돔"], r["팔_가슴"], r["팔_머리"], r["방패_가슴"], r["방패_머리"], r["방패_돔"]))
    txt.append("%s 들기 최대(조립 · 겹침 ≤0.5) %d° (방패 %s°) · 팔꿈치 %d°" % (Lr, 가동[Lr + "어깨"]["들기최대"], 가동[Lr + "어깨"]["그때_방패φ"], 가동[Lr + "팔꿈치"]["최대"]))
    txt.append("%s 어깨회전 ±180 가슴 최대 %.1f · 스윙 −15~30 가슴 최대 %.1f" % (Lr, max(r["가슴"] for r in 가동[Lr + "어깨"]["어깨회전"]),
                                                                  max(r["가슴"] for r in 가동[Lr + "어깨"]["어깨스윙"])))
ax.text(0, 1, "\n".join(txt), va="top", fontsize=8.5, family="Malgun Gothic")
fig.suptitle("오메가몬 PG 디자인 판 — 머리 · 어깨 · 윗팔 (도형으로 새로 지음 · 원화는 치수/윤곽만)", fontsize=13)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "보기.png"), dpi=110)
로그("끝", os.path.join(OUT, "보기.png"))
