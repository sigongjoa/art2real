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
  · 어깨 = 「캡(어깨블록에 고정) + 날개(캡 위 바깥 모서리 y 축 힌지로 뜬다)」. 들기 힌지 피벗(x ±40)이 원화 어깨 장갑
    한가운데라 장갑을 팔에 붙이면 위 안쪽이 가슴으로 들어가고, 어깨블록에 붙이면 바깥 아래가 팔 길을 막는다 →
    조사(research_가동관절 §26 「어깨 장갑을 힌지로 띄워」)대로 바깥 반을 날개로 떼어 띄운다. 왼 날개에 방패가 붙는다.
  · 윗팔 = 원통 D16.8(회전축5 외피 R5 + 틈 0.4 + 벽 2.0 = 7.4 ≥, 원화 폭 13.5 ± 2 안). 축 = 들기 피벗 → 팔꿈치 피벗 직선.
    위 끝은 들기 축 둘레 원통(너클)이라 들기 동안 모양이 안 변한다. 윗팔회전 자리에서 축에 수직으로 가른다(틈 0.3).
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
    ts = np.arange(-15.0, 15.0, 0.1); ins = tm.contains(p + ts[:, None] * d)
    k = np.nonzero(ins[:-1] & ~ins[1:])[0]
    return p + ts[k[-1] + 1] * d
def 정리(m):
    ps = [q for q in m.decompose() if q.volume() > 1.0]
    return 합(ps)
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
        pad = 원기둥(p - 4.0 * n, p + 4.0 * n, 2.1, seg=24) ^ 겉
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
def 넣기(이름, m, 색, 묶음, 붙는곳, 비고=""):
    부품[이름] = dict(m=m, 색=색, 묶음=묶음, 붙는곳=붙는곳, 비고=비고)

색 = dict(흰=(0.93, 0.93, 0.95), 회=(0.62, 0.64, 0.68), 금=(0.90, 0.74, 0.25), 빨=(0.78, 0.16, 0.12), 파=(0.45, 0.50, 0.78),
          검=(0.22, 0.22, 0.24), 은=(0.80, 0.82, 0.86))

# ════════════════════════ 머리 ════════════════════════════
# 치수(원화): 정면 투구 폭 ±11 (z 262~285) · 꼭대기 z 291 · 볼 가리개 ±14 (z 268~278) · 얼굴 ±8 (z 263~277) · 턱 V z 262.
#           옆 얼굴 앞 y 0 · 눈썹 차양 y −1.5 (z 277~282) · 뒤 y 28 (z 285, 그 아래는 오른 어깨에 가려 안 보임).
#           뿔 밑 (y 1~10, z 281) → 끝 (0, −7, 307.5) · V 안테나 (±8, 10, 283) → (±25.5, 29.5, 302.5).
# 골격: 목위 볼 피벗 (0, 21.36, 267.38) R7.5 → 뒤통수 겉 y ≥ 21.36 + 7.5 + 0.4 + 2.0 = 31.3 (가려진 아랫부분에서만 32).
로그("머리")
Pn = P("목위")
def 머리단면(z, w, yf, yb, c): return 단면z(z, 팔각(-w, w, yf, yb, c))
투구 = 조각()
투구.더(np.vstack([머리단면(*r) for r in [(258.8, 8.4, 7.0, 29.5, 2.5), (264.0, 10.8, 3.0, 32.0, 3.6), (275.0, 11.2, 1.2, 32.0, 4.0),
                                          (283.0, 10.6, 2.6, 29.8, 4.0)]]))
투구.더(np.vstack([머리단면(*r) for r in [(283.0, 10.6, 2.6, 29.8, 4.0), (288.5, 7.8, 6.4, 26.0, 3.4), (291.3, 4.0, 10.5, 19.0, 1.5)]]))
# 볼 가리개(좌우) — 바깥면 x=14 오각, 안쪽 x=9.5
볼가 = [(4.0, 277.5), (11.5, 279.0), (16.5, 273.0), (12.5, 267.0), (5.0, 268.0)]
for s in (1, -1):
    투구.더(np.vstack([[(s * 14.0, a, b) for a, b in 볼가], [(s * 9.5, a - 1.0, b + d) for (a, b), d in zip(볼가, (0.8, 0.8, 0, -0.8, -0.8))]]), 빈=False)
# 눈썹 차양 (앞으로 −1.5 튀어나온 띠) — 앞면 가운데가 살짝 앞(V)
차양 = [(x, y, z) for x, y in [(-9.6, 0.4), (-4.0, -1.2), (0, -1.6), (4.0, -1.2), (9.6, 0.4)] for z in (277.2, 282.4)] + \
      [(x, 8.0, z) for x in (-10.0, 10.0) for z in (277.2, 282.8)]
투구.더(차양, 빈=False)
# 이마 볏 (뿔 받침) — 속 찬 조각
볏 = [(x, y, z) for x in (-4.2, 4.2) for y, z in [(0.2, 280.5), (4.6, 290.8), (12.5, 290.8), (10.0, 280.5)]]
투구.더(볏, 빈=False)
투구겉 = 투구.겉()

# 뿔: 밑 단면(z 281) 육각 · 볏 꼭대기 단면 · 끝 1.6 각 → 볼록 하나. 뿌리 = 밑 두 단면 hull
뿔밑 = 단면z(281.0, [(0, 0.8), (3.2, 3.2), (3.2, 7.6), (0, 10.0), (-3.2, 7.6), (-3.2, 3.2)])
뿔중 = 단면z(290.6, [(0, -1.4), (2.4, 0.4), (2.4, 4.4), (0, 6.2), (-2.4, 4.4), (-2.4, 0.4)])
뿔끝 = 단면z(307.6, [(0.8, -7.6), (0.8, -6.0), (-0.8, -6.0), (-0.8, -7.6)])
뿔 = 볼록(np.vstack([뿔밑, 뿔중, 뿔끝]))
뿔뿌리 = np.vstack([뿔밑, 뿔중])

# V 안테나 (좌우 따로 · 밖에서 꽂는다): 날 단면 2.8×2.0 → 끝 1.6×1.6
def 안테나(s):
    B = A(s * 7.5, 9.5, 282.5); T = A(s * 25.5, 29.5, 302.5); d = 단위(T - B)
    w = 단위(np.cross(d, A(0, 1, 0)))          # 날 폭 방향(정면에서 보이는 폭)
    th = 단위(np.cross(d, w))
    def 사각(c, a, b): return [c + i * a * w + j * b * th for i in (-1, 1) for j in (-1, 1)]
    R0 = B - 5.0 * d; E = B + 5.0 * d
    몸 = 볼록(사각(R0, 1.4, 1.0) + 사각(E, 1.4, 1.0) + 사각(T, 0.8, 0.8))
    뿌리 = np.array(사각(R0, 1.4, 1.0) + 사각(E, 1.4, 1.0))
    return 몸, 뿌리
안L, 안L뿌리 = 안테나(-1); 안R, 안R뿌리 = 안테나(1)

# 얼굴 (마스크 판): 정면 오각 · 앞면 가운데 능선(V) · 뒤 y 6.4 (머리 뼈 앞면 y≈14.4−7 = 7.4 − 0.4 − 0.6)
얼굴외곽 = [(0.0, 262.4), (7.8, 266.2), (8.0, 276.6), (-8.0, 276.6), (-7.8, 266.2)]
def 얼굴점(dy=0.0, 줄=0.0):
    pts = []
    for x, z in 얼굴외곽:
        x2 = np.sign(x) * max(abs(x) - 줄, 0); z2 = z + (줄 if z < 270 else -줄)
        yf = -0.4 + abs(x2) * 0.22 + dy
        pts += [(x2, yf, z2), (x2, 6.4, z2)]
    return pts
얼굴 = 볼록(얼굴점())
얼굴구멍 = 볼록(밀기(얼굴점(), 꽂이틈)) + 볼록([(x, y, z) for x in (-8.2, 8.2) for y in (-3, 14.0) for z in (250.0, 276.75)])

# 목 쓸기: 목위 볼에서 목 뼈(부모)가 머리(자식) 틀에서 움직이는 범위 = 머리 회전의 역
목뼈 = 뼈몸("목", 비움)
쓸 = []
for rx in (-25, -12, 0, 10, 20):
    for ry in (-15, 0, 15):
        for rz in (-45, 0, 45):
            R = Rot.from_euler("xyz", [rx, ry, rz], degrees=True).inv().as_matrix()
            쓸.append(목뼈.transform(틀(R, Pn - R @ Pn)))
목쓸기 = 합(쓸)
머리막 = 목쓸기 + 외피("목위", 비움) + 뼈몸("머리", 비움)

# 목깃(D1) 자리: z < 목깃꼭대기 에서는 목위 축 둘레 원통 r 11.2 (D1 목깃 안 반지름 11.6~12 − 0.4) ∪ 앞 ±28° 쐐기(목깃이 열린 곳)만 남긴다
목깃z = 272.6
_c = A(0, Pn[1], 0)
원통자리 = 구(Pn, 11.2, 64) + 원기둥((0, Pn[1], Pn[2]), (0, Pn[1], 목깃z), 11.2, seg=64)   # 목위 볼 둘레 구면 + 위 원통
쐐기 = 볼록([(0, Pn[1], z) for z in (240.0, 목깃z)] + [(sx * 40 * np.sin(np.radians(28)), Pn[1] - 40 * np.cos(np.radians(28)), z) for sx in (-1, 1) for z in (240.0, 목깃z)])
목깃막 = M.Manifold.cube([80, 80, 목깃z - 240.0]).translate([-40, -20, 240.0]) - 원통자리 - 쐐기
목깃막 = 목깃막 + (M.Manifold.cube([80, 20, 4.0]).translate([-40, Pn[1] + 6.0, 목깃z - 0.5]) - 구(Pn, 11.2, 64))   # 뒤통수 아래: 뒤로 끄덕일 때 목깃 윗면
투구겉 = 투구겉 - 목깃막
투구껍질 = 투구.껍질() - 목쓸기 - 목깃막
투구껍질 = 꽂이(투구껍질, 투구겉, 뿔뿌리)
for 뿌리 in (안L뿌리, 안R뿌리): 투구껍질 = 꽂이(투구껍질, 투구겉, 뿌리)
투구껍질 = 투구껍질 - 얼굴구멍 - 머리막
# 눈 틈 (차양 아래 가로 V 홈) · 투구 옆 패널라인(아래 테두리에 평행) — 규칙: 직선 · 적게
투구껍질 = V홈(투구껍질, [((-7.6, 1.3, 277.0), (7.6, 1.3, 277.0))], A(0, -1, 0), 폭=1.0, 깊=0.8)
Ys = 15.0                                          # 투구 앞/뒤 가르는 평면 y
앞, 뒤 = 투구껍질.split_by_plane([0, -1, 0], -Ys)   # -y·p > -Ys  ⇔ y < Ys
다보점 = [(-9.6, Ys, 266.0), (9.6, Ys, 266.0), (0.0, Ys, 289.2)]
앞, 뒤 = 다보붙이기(앞, 뒤, 투구겉, 머리막 + 뿔 + 안L + 안R, 다보점, A(0, 1, 0))
# 투구 뒤 → 머리 뼈 (뒤쪽 보스, z 276)
b = 뼈[ "머리"]["마디"][0]; r_at = (b[0][3] + (b[-1][3] - b[0][3]) * (276 - b[0][2]) / (b[-1][2] - b[0][2])) / 2
뒤, s1 = 보스(뒤, 투구겉, "머리", (0, Pn[1] + r_at, 276.0), A(0, 1, 0)); 사양["뼈구멍"].append(dict(부품="투구뒤", **s1))
# 얼굴 → 머리 뼈 앞면 (핀만: 얼굴 뒤 y 6.4 ~ 뼈 앞 y 7.4)
r_f = (b[0][3] + (b[-1][3] - b[0][3]) * (270 - b[0][2]) / (b[-1][2] - b[0][2])) / 2
fp = A(0, Pn[1] - r_f, 270.0)
얼굴 = 얼굴 + (원기둥((0, 5.0, 270.0), fp, 2.0, seg=24)) + 원기둥(fp - A(0, 0.3, 0), fp + A(0, 2.5, 0), 0.9, seg=20)
얼굴 = 얼굴 - 뼈몸("머리")
사양["뼈구멍"].append(dict(부품="얼굴", 뼈="머리", 점mm=fp.round(2).tolist(), 방향=[0, 1, 0], 구멍지름=2.2, 깊이=3.0))
얼굴 = V홈(얼굴, [((-7.0, -0.4 + 7.0 * 0.22, 268.6), (0, -0.4, 268.6))], A(-0.22, -1, 0))
얼굴 = V홈(얼굴, [((7.0, -0.4 + 7.0 * 0.22, 268.6), (0, -0.4, 268.6))], A(0.22, -1, 0))
넣기("투구앞", 앞, 색["흰"], "머리", "투구뒤(다보 3)")
넣기("투구뒤", 뒤, 색["흰"], "머리", "머리 뼈(보스)")
넣기("얼굴", 얼굴, 색["은"], "머리", "머리 뼈(핀) · 투구앞 창에 끼움")
넣기("뿔", 뿔, 색["은"], "머리", "투구앞 볏 소켓")
넣기("V안테나L", 안L, 색["금"], "머리", "투구앞 소켓")
넣기("V안테나R", 안R, 색["금"], "머리", "투구앞 소켓")

# ════════════════════════ 윗팔 ════════════════════════════
# 원통 D16.8 · 축 = 들기 피벗 → 팔꿈치 피벗. 원화 검은 윗팔 중심선 z236 ±44.2 / z224 ±47.4 — 이 축은 −44.8 / −49.0 (1.1 안).
# 윗팔 아래 끝 = 원화 검은 원통 끝 z≈214 (축 따라 38 mm). 윗팔회전 자리(축 위 투영 31.5 mm)에서 가른다.
Ra = 8.4; 너클반폭 = 7.6
def 윗팔(s):
    Lr = "L" if s < 0 else "R"
    H = P(Lr + "어깨들기"); E = P(Lr + "팔꿈치"); a = 단위(E - H)
    t_rot = float((P(Lr + "윗팔회전") - H) @ a); t_end = 38.0
    yv = A(0, 1, 0)
    너클 = np.vstack([원점들(H + h * yv, yv, Ra) for h in (-너클반폭, 너클반폭)])
    원 = lambda t, r=Ra: 원점들(H + t * a, a, r)
    위 = 조각().더(np.vstack([너클, 원(15.0)])).더(np.vstack([원(15.0), 원(t_rot - 관절틈 / 2)]))
    아래 = 조각().더(np.vstack([원(t_rot + 관절틈 / 2), 원(t_end)]))
    return dict(H=H, E=E, a=a, t_rot=t_rot, t_end=t_end, 위=위, 아래=아래, Lr=Lr)
팔 = {s: 윗팔(s) for s in (-1, 1)}
def 팔돌림(m, s, 도):   # 들기 θ (양 = 바깥으로 듦)
    j = 관[팔[s]["Lr"] + "어깨들기"]; return 돌림(m, j["피벗mm"], j["범위"][0]["축"], 도)

# ════════════════════════ 어깨 ════════════════════════════
# 치수(원화): 왼(L) 파랑 캡 x −51~−30.5 · z 240~266 · 깊이는 옆 그림이 없어 오른 장갑 깊이 폭(35)과 들기 피벗 y 20.5 중심으로 y 5~37.
#           오른(R) 가루몬 장갑 정면 x 31~60 · z 237~274 · 옆 y 12~47 → 앞면 y 10.4 (들기 너클 ±7.8 + 비움 0.4 + 벽 2 가 들어가게, 옆 윤곽 −1.6).
#           방패(정면): 렌즈 긴 축 (−62,237)→(−40,289) 56 mm · 폭 17 — 금 면이 보이게 앞으로 15° 틀었다.
# 캡/날개 가르는 평면 x = ±39 (들기 피벗 ±40 바로 안쪽): 캡 = 어깨블록 고정, 날개 = 캡 위 바깥 모서리 y 축 힌지.
로그("어깨")
X날 = 39.0
가슴D1 = D1()
L겉조 = 조각().더(np.vstack([단면x(-30.5, 팔각(9.0, 33.0, 242.0, 262.0, 4.0)), 단면x(-33.5, 팔각(5.0, 37.0, 240.0, 265.8, 6.5)),
                             단면x(-46.0, 팔각(5.0, 37.0, 239.5, 265.8, 7.5)), 단면x(-51.0, 팔각(9.5, 32.5, 243.5, 261.0, 5.0))]))
R겉조 = 조각().더(np.vstack([단면x(30.5, 팔각(13.5, 44.0, 240.5, 268.6, 4.0)), 단면x(33.5, 팔각(10.4, 47.0, 238.0, 272.4, 6.0)),
                             단면x(52.0, 팔각(10.4, 47.0, 237.0, 272.4, 7.0)), 단면x(60.0, 팔각(14.5, 43.0, 246.0, 268.0, 6.0))]))
힌지 = {-1: dict(p=A(-X날, 21.0, 262.6), y=(5.0, 37.0)), 1: dict(p=A(X날, 28.7, 269.3), y=(10.4, 47.0))}
def 날개돌림(m, s, 도):   # 양 = 바깥 위로 뜸
    return 돌림(m, 힌지[s]["p"], A(0, 1, 0) * (1 if s < 0 else -1), 도)

# 방패 (왼 날개에 줄기로 꽂는다)
u0 = 단위((22.0, 0, 52.0)); n0 = 단위(np.cross(A(0, 1, 0), u0)) * -1      # 바깥(−x)·위
n_ = 단위(n0 * np.cos(np.radians(15)) + A(0, -1, 0) * np.sin(np.radians(15)))
u_ = 단위(u0 - (u0 @ n_) * n_); v_ = np.cross(n_, u_)
방패외곽 = [(28, 0), (17, 19), (5, 22.5), (-5, 22.5), (-17, 19), (-28, 0), (-17, -19), (-5, -22.5), (5, -22.5), (17, -19)]
def 방패판(C, 줄, h): return [C + (a * (1 - 줄 / 28.0)) * u_ + (b * (1 - 줄 / 22.5)) * v_ + h * n_ for a, b in 방패외곽]
L겉 = L겉조.겉()
# 방패 뒷면 평면이 날개 겉에 0.6 떨어지게, 정면 투영 중심이 원화 (−51, 263) 이 되게 두 번 맞춘다
C = A(-51.0, 21.0, 263.0)
for _ in range(3):
    V_ = np.asarray(L겉.trim_by_plane([-1, 0, 0], X날).to_mesh().vert_properties)[:, :3]
    s_ = float(np.max(V_ @ n_) - C @ n_) + 0.6; C = C + s_ * n_
    proj = np.array(방패판(C, 0, 0) + 방패판(C, 0, 7.5)); cxz = (proj[:, [0, 2]].min(0) + proj[:, [0, 2]].max(0)) / 2
    C = C + A(-51.0 - cxz[0], 0, 263.0 - cxz[1]) * 0.9
빨강 = 볼록(방패판(C, 1.2, 0) + 방패판(C, 0, 1.2) + 방패판(C, 0, 4.8) + 방패판(C, 1.4, 6.0))
금자리 = 볼록(방패판(C, 4.4, 3.6) + 방패판(C, 4.4, 9.0))
빨강 = 빨강 - 금자리 - 볼록(방패판(C, 6.0, -1.0) + 방패판(C, 6.0, 1.6))      # 뒤를 판다(바닥 2.0)
금 = 볼록(방패판(C, 4.6, 3.6) + 방패판(C, 5.0, 7.2) + [C + 8.6 * n_]) - 볼록(방패판(C, 6.6, 3.5) + 방패판(C, 7.0, 5.6))
# 문장 음각: 가운데 고리 + 세모 넷 (깊이 0.5, 금 면에서)
def 금면점(a, b): # 금 면 위 점(대략) — 판 7.2 에서 가운데 8.6 까지 볼록
    r = np.hypot(a / 23.4, b / 17.9); return C + a * u_ + b * v_ + (8.6 - 1.4 * min(r, 1)) * n_
문장 = []
t = np.linspace(0, 2 * np.pi, 33)
for k in range(32):
    for r0 in (5.2,):
        p0 = 금면점(r0 * np.cos(t[k]), r0 * np.sin(t[k])); p1 = 금면점(r0 * np.cos(t[k + 1]), r0 * np.sin(t[k + 1]))
        문장.append((p0, p1))
for k in range(4):
    g = np.radians(45 + 90 * k); d2 = A(np.cos(g), np.sin(g)); q = A(-d2[1], d2[0])
    tri = [d2 * 8.0 + q * 3.0, d2 * 15.0, d2 * 8.0 - q * 3.0]
    for i in range(3):
        문장.append((금면점(*tri[i]), 금면점(*tri[(i + 1) % 3])))
금 = V홈(금, 문장, n_, 폭=0.8, 깊=0.5)
# 방패 줄기(빨강 뒤 → 날개 겉으로) Ø6
_sp = 겉점(L겉.trim_by_plane([-1, 0, 0], X날), C - 6.0 * n_, n_)
줄기끝 = _sp - 3.5 * n_
줄기 = 원기둥(C + 2.0 * n_, 줄기끝, 3.0, seg=32)
빨강 = 빨강 + 줄기
줄기뿌리 = np.vstack([원점들(C - 1.0 * n_, n_, 3.0, 16), 원점들(줄기끝, n_, 3.0, 16)])

def 어깨(s):
    Lr = "L" if s < 0 else "R"
    조 = L겉조 if s < 0 else R겉조
    겉 = 조.겉(); 껍 = 조.껍질()
    pa = 팔[s]
    팔비움 = lambda ths: 합([팔돌림(볼록(밀기(P_, 비움)), s, th) for th in ths for P_, _ in pa["위"].p + pa["아래"].p])
    공통 = 뼈몸(Lr + "어깨블록", 비움) + 뼈몸(Lr + "어깨축", 비움) + 외피(Lr + "어깨회전", 비움) + 외피(Lr + "어깨들기", 비움)
    캡막 = 공통 + 팔비움(range(0, 91, 10))      # 캡은 들기 내내 비켜야 한다
    날막 = 공통 + 팔비움([0])                    # 날개는 쉬는 자세만 — 들 때는 뜬다
    ns = A(s, 0, 0)
    날, 캡 = 껍.split_by_plane(list(ns), X날)     # s·x > 39 = 날개
    h = 힌지[s]; hp = h["p"]; y0, y1 = h["y"]; ym = (y0 + y1) / 2
    def 러그(ya, yb, r=2.6): return 원기둥((hp[0], ya, hp[2]), (hp[0], yb, hp[2]), r, seg=32)
    판 = lambda dx, dz, ya, yb: np.array([(hp[0] + dx, y, hp[2] + dz) for y in (ya, yb)])
    캡러그 = 러그(ym - 5.0, ym + 5.0) + (볼록(np.vstack([원점들(A(hp[0], y, hp[2]), A(0, 1, 0), 2.6, 16) for y in (ym - 5.0, ym + 5.0)] +
                                                  [판(-s * 5.0, -2.0, ym - 5.0, ym + 5.0)])) ^ 겉)
    틈통 = 러그(ym - 5.0 - 관절틈, ym + 5.0 + 관절틈, 2.6 + 관절틈)
    날러그 = 러그(y0 + 2.5, y1 - 2.5) + (볼록(np.vstack([판(s * 4.5, -2.6, y0 + 2.5, y1 - 2.5),
                                                       원점들(A(hp[0], y0 + 2.5, hp[2]), A(0, 1, 0), 2.6, 16),
                                                       원점들(A(hp[0], y1 - 2.5, hp[2]), A(0, 1, 0), 2.6, 16)])) ^ 겉)
    날러그 = 날러그 - 틈통
    핀구멍 = 원기둥((hp[0], y0 - 1, hp[2]), (hp[0], y1 + 1, hp[2]), 0.925, seg=24)
    # 날개가 돌 때 캡 러그판이 날개 쪽으로 안 넘게: 캡 러그판은 s·x ≤ 39 만
    날영역 = 겉.trim_by_plane(list(ns), X날 - 관절틈)
    날쓸 = 합([(날개돌림(날영역, s, ph) + 날개돌림(날영역, s, ph + 10)).hull() for ph in range(0, 90, 10)]) - 러그(y0 - 1, y1 + 1, 2.6 + 관절틈)
    날러그틈 = 러그(y0 - 1, ym - 5.0 - 관절틈, 2.6 + 관절틈) + 러그(ym + 5.0 + 관절틈, y1 + 1, 2.6 + 관절틈)
    # 뼈 잡이 격벽: |x| 33.0~34.6 판(캡 안 전체) − 관절 외피 · 팔 쓸기 · 날개 쓸기 − 어깨블록 뼈(틈 0 — 두 반쪽이 물고 닫힌다)
    격벽 = (M.Manifold.cube([1.6, 80, 80]).translate([s * 33.0 - (1.6 if s < 0 else 0), -20, 220]) ^ 겉) -         (뼈몸(Lr + "어깨축", 비움) + 외피(Lr + "어깨회전", 비움) + 외피(Lr + "어깨들기", 비움) + 팔비움(range(0, 91, 10)) + 뼈몸(Lr + "어깨블록"))
    캡 = (캡 - 캡막 - 날쓸 - 날러그틈) + 격벽 + 캡러그.trim_by_plane(list(-ns), -X날 - 0.0) + 러그(ym - 5.0, ym + 5.0)
    캡 = 캡 - 날쓸 - 날러그틈 - 핀구멍
    if 가슴D1 is not None:   # 어깨스윙(−15~30°) 동안 가슴(D1)이 캡 틀에서 쓸고 가는 부피 + 0.4 를 뺀다 = 가슴 쪽 모따기
        js = 관[Lr + "어깨스윙"]; g0 = 가슴D1 ^ M.Manifold.cube([40, 80, 60]).translate([(0 if s > 0 else -40), -20, 225])
        캡 = 캡 - 합([(돌림(g0, js["피벗mm"], js["범위"][0]["축"], -d).translate([s * 0.4, 0, 0])) for d in np.arange(-15, 30.1, 5.0)] +
                    [돌림(g0, js["피벗mm"], js["범위"][0]["축"], -d).translate([0, dy, 0]) for d in (-15, 30) for dy in (-0.4, 0.4)])
    날 = (날 + 날러그 - 날막) - 핀구멍 - 틈통
    ycut = ym
    캡앞, 캡뒤 = 캡.split_by_plane([0, -1, 0], -ycut)
    top = 264.0 if s < 0 else 270.4; bot = 242.2 if s < 0 else 241.0
    캡다보 = [(s * 31.8, ycut, bot), (s * 31.8, ycut, top - 1.0)]
    캡앞, 캡뒤 = 다보붙이기(캡앞, 캡뒤, 겉, 캡막 + 핀구멍, 캡다보, A(0, 1, 0))
    사양["뼈구멍"].append(dict(부품=Lr + "어깨캡앞/뒤", 뼈=Lr + "어깨블록", 결합="격벽이 뼈를 물고 닫힘(틈 0) — 구멍 없음"))
    사양["핀"].append(dict(부품=Lr + "어깨 날개 힌지", 지름=1.75, 길이=round(y1 - y0 + 1.0, 1), 재료="PLA 필라멘트", 구멍지름=1.85))
    return dict(겉=겉, 캡앞=캡앞, 캡뒤=캡뒤, 날=날, 캡막=캡막 + 날쓸 + 날러그틈, 날막=날막 + 틈통 + 핀구멍)
어 = {s: 어깨(s) for s in (-1, 1)}

# 왼 날개: 방패 줄기 소켓 · 패널라인 없음(방패가 덮음)
L날 = 꽂이(어[-1]["날"], L겉, 줄기뿌리) - 어[-1]["날막"]
# 오른 날개: 가시 넷 (팔각뿔 · 끝 Ø1.6 자름) + 앞면 외곽 평행 V 홈 (앞면 y=10.4, 외곽에서 3 mm 안 오각)
def 가시(b, tip, r, y끝=None, z끝=None):
    b, tip = A(*b), A(*tip); d = 단위(tip - b); L_ = np.linalg.norm(tip - b)
    b = 겉점(R겉조.겉(), b, d)
    if y끝 is not None: L_ = (y끝 - b[1]) / d[1]
    if z끝 is not None: L_ = (z끝 - b[2]) / d[2]
    tip = b + L_ * d
    몸 = 볼록(np.vstack([원점들(b - 3.0 * d, d, r, 8), 원점들(b, d, r, 8), 원점들(tip, d, 0.8, 8)]))
    뿌리 = np.vstack([원점들(b - 3.0 * d, d, r, 8), 원점들(b + 0.8 * d, d, r * (1 - 0.8 / np.linalg.norm(tip - b)), 8)])
    return 몸, 뿌리
가시들 = {"가시위": 가시((47.0, 28.7, 271.0), (47.0, 28.7, 289.0), 4.5, z끝=289.0), "가시밖": 가시((56.0, 28.7, 266.0), (61.5, 28.7, 274.0), 3.2),
          "가시앞": 가시((54.0, 22.0, 263.0), 단위((0.35, -0.85, 0.3)) * 12.0 + A(54.0, 22.0, 263.0), 4.0, y끝=8.0),
          "가시뒤": 가시((54.0, 35.4, 263.0), 단위((0.35, 0.85, 0.3)) * 12.0 + A(54.0, 35.4, 263.0), 4.0, y끝=50.0)}
R겉 = R겉조.겉(); R날 = 어[1]["날"]; R캡뒤 = 어[1]["캡뒤"]
for k, (몸, 뿌리) in 가시들.items():
    R날 = 꽂이(R날, R겉, 뿌리) - 어[1]["날막"]
R날 = V홈(R날, [((X날 + 3.0, 10.4, 243.0), (57.0, 10.4, 247.5)), ((57.0, 10.4, 247.5), (57.0, 10.4, 262.0))], A(0, -1, 0))
넣기("L어깨캡앞", 어[-1]["캡앞"], 색["파"], "L어깨", "L어깨캡뒤(다보)")
넣기("L어깨캡뒤", 어[-1]["캡뒤"], 색["파"], "L어깨", "L어깨블록 뼈(보스)")
넣기("L어깨날개", L날, 색["파"], "L어깨", "L캡 힌지(Ø1.75 핀) — 팔 들 때 띄운다")
넣기("방패빨강", 빨강, 색["빨"], "L어깨", "L어깨날개 줄기 소켓")
넣기("방패금", 금, 색["금"], "L어깨", "방패빨강 자리에 끼움(붙임)")
넣기("R어깨캡앞", 어[1]["캡앞"], 색["파"], "R어깨", "R어깨캡뒤(다보)")
넣기("R어깨캡뒤", R캡뒤, 색["파"], "R어깨", "R어깨블록 뼈(보스)")
넣기("R어깨날개", R날, 색["파"], "R어깨", "R캡 힌지(Ø1.75 핀) — 팔 들 때 띄운다")
for k, (몸, _) in 가시들.items():
    넣기(k, 몸, 색["금"], "R어깨", "R어깨날개 소켓")

# 윗팔 반쪽 · 다보 · 보스 · 고리 홈
로그("윗팔")
for s in (-1, 1):
    pa = 팔[s]; Lr = pa["Lr"]; H, a = pa["H"], pa["a"]
    j = 관[Lr + "어깨들기"]; pj = A(*j["피벗mm"]); ax = A(*j["범위"][0]["축"])
    # 부모(어깨블록 뼈 · 어깨 캡) 가 자식(윗팔위) 틀에서 쓸고 가는 부피
    부모 = 뼈몸(Lr + "어깨블록", 비움)
    부모쓸 = 합([팔돌림(부모, s, -th) for th in range(0, 91, 10)])
    for 이름, 조 in (("윗팔위", pa["위"]), ("윗팔", pa["아래"])):
        겉 = 조.겉(); 껍 = 조.껍질()
        막 = 뼈몸(Lr + "윗팔위", 비움) + 뼈몸(Lr + "윗팔", 비움) + 외피(Lr + "윗팔회전", 비움) + 외피(Lr + "어깨들기", 비움) + \
            외피(Lr + "팔꿈치", 비움) + 부모쓸
        껍 = 껍 - 막
        if 이름 == "윗팔위":
            껍 = 껍 - 고리홈(H + 24.0 * a, a, Ra)
        n_cut = 단위(A(0, 1, 0) - (A(0, 1, 0) @ a) * a)
        앞_, 뒤_ = 껍.split_by_plane(list(-n_cut), float(-n_cut @ H))
        u2 = 단위(np.cross(a, n_cut))
        if 이름 == "윗팔위": ts = [(18.0, 1), (18.0, -1), (28.5, 1), (28.5, -1)]
        else: ts = [(pa["t_rot"] + 3.4, 1), (pa["t_rot"] + 3.4, -1)]
        점들 = [H + t_ * a + sg * (Ra - 2.6) * u2 for t_, sg in ts]
        앞_, 뒤_ = 다보붙이기(앞_, 뒤_, 겉, 막, 점들, n_cut)
        # 보스 → 뼈 (뒤 반쪽, 뼈 축에서 +n 쪽으로)
        bn = Lr + 이름; ch = 뼈[bn]["마디"][0]; q0, q1 = A(*ch[0][:3]), A(*ch[-1][:3])
        tq = 0.45 if 이름 == "윗팔위" else 0.25
        qc = q0 + tq * (q1 - q0); rq = (ch[0][3] + tq * (ch[-1][3] - ch[0][3])) / 2
        뒤_, s3 = 보스(뒤_, 겉, bn, qc + rq * n_cut, n_cut); 사양["뼈구멍"].append(dict(부품=Lr + 이름 + "뒤", **s3))
        넣기(Lr + 이름 + "앞", 앞_, 색["검"], Lr + "윗팔", Lr + 이름 + "뒤(다보)")
        넣기(Lr + 이름 + "뒤", 뒤_, 색["검"], Lr + "윗팔", bn + " 뼈(보스)")
로그("부품 %d" % len(부품)); [print("   ", k, round(부피(d["m"]), 1), len(d["m"].decompose())) for k, d in 부품.items()]

# ════════════════════════ 검사 ════════════════════════════
def 조각잇기(m):  # 떨어진 조각 수
    return len(m.decompose())
결과 = {"부품": {}}
os.makedirs(OUT, exist_ok=True)
for k, d in 부품.items():
    d["m"] = 정리(d["m"]).simplify(0.02); m = d["m"]; tm = 메시(m); fn = os.path.join(OUT, k + ".stl"); tm.export(fn)
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
        V[dup] += 0.03 * (FC[dup] - VN[dup])       # 제 면들 쪽 · 안쪽으로
        tm = trimesh.Trimesh(V, tm.faces, process=False); tm.export(fn); re = trimesh.load(fn, force="mesh"); wt = bool(re.is_watertight)
        로그("  %s 겹친 정점 %d 떼기 → 닫힘 %s" % (k, int(dup.sum()), wt))
    결과["부품"][k] = dict(파일=k + ".stl", 묶음=d["묶음"], 붙는곳=d["붙는곳"], 색=d["색"], 닫힘=wt, 조각=조각잇기(m),
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
# 어깨: 캡 · 날개 vs 가슴 (어깨회전 ±180, 어깨스윙 −15~30) · 들기 θ 에 필요한 날개 φ
for s in (-1, 1):
    Lr = "L" if s < 0 else "R"
    캡 = 부품[Lr + "어깨캡앞"]["m"] + 부품[Lr + "어깨캡뒤"]["m"]
    날 = 합([부품[k]["m"] for k in 부품 if 부품[k]["묶음"] == Lr + "어깨" and "캡" not in k])
    팔m = 합([부품[k]["m"] for k in 부품 if 부품[k]["묶음"] == Lr + "윗팔"])
    어깨m = 캡 + 날
    jr = 관[Lr + "어깨회전"]; js = 관[Lr + "어깨스윙"]
    회전표 = [dict(도=d, 가슴=겹(돌림(어깨m + 팔m, jr["피벗mm"], jr["범위"][0]["축"], d), 가슴)) for d in range(-180, 180, 30)]
    스윙표 = [dict(도=d, 가슴=겹(돌림(어깨m + 팔m, js["피벗mm"], js["범위"][0]["축"], d), 가슴)) for d in (-15, 0, 15, 30)]
    들기표 = []
    for th in (0, 30, 60, 90):
        am = 팔돌림(팔m, s, th); 필요 = None
        for ph in range(0, 121, 5):
            nm_ = 날개돌림(날, s, ph)
            if 겹(am, nm_) == 0:
                필요 = ph; break
        nm_ = 날개돌림(날, s, 필요 if 필요 is not None else 0)
        들기표.append(dict(들기=th, 날개필요=필요, 날개_캡최대_0to90=max(겹(날개돌림(날, s, p_), 캡) for p_ in range(0, 91, 15)),
                          날개_머리최대_0to90=max(겹(날개돌림(날, s, p_), 머리합) for p_ in range(0, 91, 15)), 팔_캡=겹(am, 캡), 팔_날개=겹(am, nm_), 팔_가슴=겹(am, 가슴), 날개_가슴=겹(nm_, 가슴),
                          날개_머리=겹(nm_, 머리합), 날개_캡=겹(nm_, 캡)))
    최대 = 0
    for th in range(0, 91, 5):
        am = 팔돌림(팔m, s, th); 된 = False
        for ph in range(0, 121, 5):
            nm_ = 날개돌림(날, s, ph)
            if 겹(am, nm_) == 0 and 겹(nm_, 가슴) <= 0.5 and 겹(nm_, 머리합) <= 0.5 and 겹(am, 캡) <= 0.5:
                된 = True; break
        if not 된: break
        최대 = th; 최대φ = ph
    가동[Lr + "어깨"] = dict(어깨회전=회전표, 어깨스윙=스윙표, 들기=들기표, 들기최대_날개띄움포함=최대, 그때_날개φ=최대φ)
    로그(Lr, "들기 최대", 최대)
    로그(Lr, "들기", 들기표)
결과["가동"] = 가동
결과["사양"] = 사양
로그("가동 검사 끝")

# 실루엣: 정면(전 부품) · 옆(머리 + 오른 어깨)
from PIL import Image, ImageDraw
from scipy import ndimage
def 원화마스크(v):
    fn = {"앞": "omega_front_clean", "옆": "omega_side"}[v]
    a = np.array(Image.open(r"G:\art2real\트레일\trail7_part3d\in\%s.png" % fn)); m = a[..., 3] > 128
    return ndimage.binary_opening(m, iterations=2) if v == "옆" else m
사상 = {"앞": (0.34, 534.0, 954.5, 0), "옆": (0.345, 461.0, 939.0, 1)}   # s, cx, zb, 수평축(0=x,1=y)
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
묶범 = {"머리": (-30, 30, 255, 312), "L어깨": (-66, -28, 234, 292), "R어깨": (28, 64, 233, 292), "L윗팔": (-62, -36, 212, 240), "R윗팔": (36, 60, 212, 240)}
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
        ph = 가동[Lr + "어깨"]["그때_날개φ"]; th = 가동[Lr + "어깨"]["들기최대_날개띄움포함"]
        if g == Lr + "윗팔": m = 팔돌림(m, s, th)
        if g == Lr + "어깨" and "캡" not in k: m = 날개돌림(m, s, ph)
    자세.append((m, d["색"]))
자세 += [(D1(("가슴", "목깃", "엠블럼", "복부")) or 가슴, (0.8, 0.8, 0.85))]
ax = fig.add_subplot(2, 4, 5); 그리기(ax, 자세, 0, 0, None, "최대 들기 L %d°(날개 %d°) · R %d°(날개 %d°) · 회색 = D1 가슴" % (
    가동["L어깨"]["들기최대_날개띄움포함"], 가동["L어깨"]["그때_날개φ"], 가동["R어깨"]["들기최대_날개띄움포함"], 가동["R어깨"]["그때_날개φ"]))
ax = fig.add_subplot(2, 4, 6); 그리기(ax, 자세, -30, 20, None, "최대 들기 3/4")
# 분해도
분해 = []
밀 = {"투구앞": (0, -14, 4), "투구뒤": (0, 12, 0), "얼굴": (0, -26, -4), "뿔": (0, -8, 16), "V안테나L": (-10, 0, 10), "V안테나R": (10, 0, 10),
      "방패빨강": (-16, 0, 6), "방패금": (-28, -4, 10), "L어깨날개": (-8, 0, 0), "L어깨캡앞": (0, -10, 0), "L어깨캡뒤": (0, 8, 0),
      "R어깨날개": (10, 0, 0), "R어깨캡앞": (0, -10, 0), "R어깨캡뒤": (0, 8, 0), "가시위": (10, 0, 12), "가시밖": (16, 0, 8), "가시앞": (14, -10, 4), "가시뒤": (14, 10, 4)}
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
    for r in 가동[Lr + "어깨"]["들기"]:
        txt.append("%s 들기 %2d°: 날개 %s° · 팔∩캡 %.1f · 팔∩날개 %.1f · 날개∩머리 %.1f · 날개∩가슴 %.1f · 팔∩가슴 %.1f" % (
            Lr, r["들기"], r["날개필요"], r["팔_캡"], r["팔_날개"], r["날개_머리"], r["날개_가슴"], r["팔_가슴"]))
    txt.append("%s 들기 최대(날개 띄움 · 가슴/머리 겹침 ≤0.5) %d° (날개 %d°)" % (Lr, 가동[Lr + "어깨"]["들기최대_날개띄움포함"], 가동[Lr + "어깨"]["그때_날개φ"]))
    txt.append("%s 어깨회전 ±180 가슴 최대 %.1f · 스윙 −15~30 가슴 최대 %.1f" % (Lr, max(r["가슴"] for r in 가동[Lr + "어깨"]["어깨회전"]),
                                                                  max(r["가슴"] for r in 가동[Lr + "어깨"]["어깨스윙"])))
ax.text(0, 1, "\n".join(txt), va="top", fontsize=8.5, family="Malgun Gothic")
fig.suptitle("오메가몬 PG 디자인 판 — 머리 · 어깨 · 윗팔 (도형으로 새로 지음 · 원화는 치수/윤곽만)", fontsize=13)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "보기.png"), dpi=110)
로그("끝", os.path.join(OUT, "보기.png"))
