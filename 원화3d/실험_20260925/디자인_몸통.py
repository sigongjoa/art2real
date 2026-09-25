# -*- coding: utf-8 -*-
"""오메가몬 PG(전고 300 mm) 가동 키트 — 「디자인 판」 몸통 · 허리 외장 (2026-09-25).

    python 디자인_몸통.py   -> out/출력/오메가몬_PG/디자인/몸통/*.stl · 부품.json · 키트.json · 보기.png

몸 부피를 깎지 않고 부품을 도형으로 새로 짓는다. 원화에서는 치수와 윤곽만 읽었다(아래 「치수」 표 — 원화에 mm 격자를 얹고 손으로 읽음).
  단면 = 좌우 대칭 팔각(앞 모서리 모따기 cf · 뒤 cb · 앞 가운데 용골 k) · 이웃 단면끼리 hull → 평면 면 · 선명한 모서리의 각진 로프트.
  껍질 2.0 mm (기울기 보정: 수평 안쪽 오프셋 = 2 / cos θ) · 앞뒤 반쪽 = 평면 이음 + 다보(핀 Ø2.0 · 구멍 Ø2.4 = 한쪽 0.20).
  속 비움 = 뼈 +0.4 · 관절 외피 +0.3 · 움직이는 이웃 뼈/외피는 가동 범위로 쓸어 낸 부피(hull) 까지.
  스커트 앞/뒤/옆 = 1.75 필라멘트 핀 힌지(관절규격 힌지1.75 틈: 러그 압입 1.75 · 너클 1.95 · 축방향 0.3) — 다리 가동을 스커트가 비켜 준다.
  패널라인 = 규칙(직선 + 45° 꺾임 · 좌우 대칭) · V 홈 폭 0.8 · 깊이 0.5 불리언.
좌표 = 골격(관절.json)과 같다: mm · 원점 발바닥 중앙 · [x 좌우, y 깊이(작은 y = 앞), z 높이].
원화 → mm 보정(몸통 폭 윤곽 맞춤): 정면 x = (열 − 534.7)·0.3243 · z = (975 − 행)·0.3305 / 옆 y = (열 − 460.5)·0.338 · z = (938 − 행)·0.347."""
import os, json, time
os.environ.setdefault("OMP_NUM_THREADS", "4")
import numpy as np
import manifold3d as mf
import trimesh
from scipy.spatial import ConvexHull
from PIL import Image

ROOT = r"G:\art2real\원화3d"
OUT = os.path.join(ROOT, "out", "출력", "오메가몬_PG", "디자인", "몸통"); os.makedirs(OUT, exist_ok=True)
ART = r"G:\art2real\트레일\trail7_part3d\in"
SEG = 40
T0 = time.time()
def log(*a): print("[%5.1fs]" % (time.time() - T0), *a, flush=True)

JS = json.load(open(os.path.join(ROOT, "out", "가동", "관절.json"), encoding="utf-8"))
JT = {j["이름"]: j for j in JS["관절"]}
BONE = JS["뼈"]

# ── 기본 도형 ────────────────────────────────────────────────────
U = mf.OpType.Add
def 합(ms):
    ms = [m for m in ms if m is not None and not m.is_empty()]
    return mf.Manifold.batch_boolean(ms, U) if ms else mf.Manifold()
def 회전행렬(a, deg):
    a = np.asarray(a, float); a = a / np.linalg.norm(a); t = np.radians(deg)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + np.sin(t) * K + (1 - np.cos(t)) * K @ K
def 돌려(m, p, a, deg):
    R = 회전행렬(a, deg); p = np.asarray(p, float); t = p - R @ p
    return m.transform(np.hstack([R, t[:, None]]).tolist())
def z에서(a):                                  # z 축 → a 로 돌리는 행렬
    a = np.asarray(a, float); a = a / np.linalg.norm(a); z = np.array([0, 0, 1.0])
    v = np.cross(z, a); c = a @ z
    if np.linalg.norm(v) < 1e-9: return np.eye(3) if c > 0 else np.diag([1, -1, -1.0])
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]); return np.eye(3) + K + K @ K / (1 + c)
def 원기둥(p, a, L, r, seg=SEG):                # 가운데 p · 축 a · 길이 L
    m = mf.Manifold.cylinder(L, r, r, seg, True)
    return m.transform(np.hstack([z에서(a), np.asarray(p, float)[:, None]]).tolist())
def 원통(a_pt, b_pt, r, seg=SEG):             # 두 끝점 사이 원기둥
    a_pt, b_pt = np.asarray(a_pt, float), np.asarray(b_pt, float)
    return 원기둥((a_pt + b_pt) / 2, b_pt - a_pt, float(np.linalg.norm(b_pt - a_pt)), r, seg)
def 구(p, r): return mf.Manifold.sphere(r, SEG).translate(tuple(map(float, p)))
def 캡슐(a, b, ra, rb): return mf.Manifold.batch_hull([구(a, ra), 구(b, rb)])
def 상자(lo, hi): lo = np.asarray(lo, float); return mf.Manifold.cube(tuple(np.asarray(hi, float) - lo)).translate(tuple(lo))
def 반공간(n, d): return 상자((-400,) * 3, (400,) * 3).trim_by_plane(tuple(n), float(d))   # n·p ≥ d 쪽
def 뼈조각(n, pad):                           # 뼈 → 볼록 캡슐 조각들
    return [캡슐(a[:3], b[:3], a[3] / 2 + pad, b[3] / 2 + pad) for ch in BONE[n]["마디"] for a, b in zip(ch[:-1], ch[1:])]
def 외피(n, pad=0.3):
    j = JT[n]; s = j["외피"]; p = j["피벗mm"]
    if s["모양"] == "구": return 구(p, s["반지름mm"] + pad)
    L = s.get("길이mm", s.get("폭mm")) + 2 * pad
    return 원기둥(p, j["축"], L, s["반지름mm"] + pad)

# ── 단면 · 로프트 ─────────────────────────────────────────────────
def 단면점(w, yf, yb, cf, cb, k):
    cf = min(cf, 0.45 * w, 0.45 * (yb - yf)); cb = min(cb, 0.45 * w, 0.45 * (yb - yf)); k = min(k, 0.4 * (yb - yf))
    return [(-w + cf, yf + k), (0.0, yf), (w - cf, yf + k), (w, yf + k + cf), (w, yb - cb), (w - cb, yb),
            (-w + cb, yb), (-w, yb - cb), (-w, yf + k + cf)]
def 오프(pts, d):
    if abs(d) < 1e-9: return np.array(pts)
    ps = mf.CrossSection([pts]).offset(d, mf.JoinType.Miter).to_polygons()
    if not ps:                                  # 오프셋에 사라진 가는 단면(끝 뾰족) → 무게중심 쪽으로 줄인 점
        q = np.array(pts); c = q.mean(0); return c + 0.05 * (q - c)
    return max(ps, key=lambda q: abs(ConvexHull(q).volume))
def 로프트(secs, d=0.0, zs=None):
    """secs = [(z, w, yf, yb, cf, cb, k)] · d = 수평 오프셋(각 단면 따로 · 리스트면 단면별) · zs = 단면 높이 바꿔치기."""
    ds = d if isinstance(d, (list, tuple, np.ndarray)) else [d] * len(secs)
    P = []
    for i, s in enumerate(secs):
        q = 오프(단면점(*s[1:]), ds[i]); z = s[0] if zs is None else zs[i]
        P.append(np.c_[q, np.full(len(q), z)])
    return 합([mf.Manifold.hull_points(np.vstack([a, b]).tolist()) for a, b in zip(P[:-1], P[1:])])
def 껍질(secs, t=2.0, 위닫=True, 아래닫=True):
    """바깥 로프트 − 안 로프트. 안 = 수평 안쪽 t/cos θ (θ = 이웃 단면 벽 기울기) · 닫힌 끝은 t 만큼 안으로 · 열린 끝은 밖으로 1."""
    zs = np.array([s[0] for s in secs]); ti = []
    for i in range(len(secs)):
        sl = 0.0
        for j in (i - 1, i + 1):
            if 0 <= j < len(secs):
                dz = abs(zs[j] - zs[i]); dh = max(abs(secs[j][1] - secs[i][1]), abs(secs[j][2] - secs[i][2]), abs(secs[j][3] - secs[i][3]))
                sl = max(sl, np.arctan2(dh, dz))
        ti.append(-min(t / np.cos(sl), 1.8 * t))
    zi = zs.copy().astype(float); zi[0] += t if 아래닫 else -1.0; zi[-1] += -t if 위닫 else 1.0
    return 로프트(secs), 로프트(secs, ti, zi), 로프트(secs, ti, zs.astype(float))   # 바깥 · 안(끝 처리) · 안(원높이)

# ── 치수 (원화에서 읽은 것: z, 반폭 w, 앞 yf, 뒤 yb, 앞모따기 cf, 뒤모따기 cb, 용골 k) ─────────
가슴S = [(223.5, 14.0, 16.0, 40.0, 4, 5, 0.0),
        (227.0, 17.5, 4.0, 43.0, 4, 6, 1.5),
        (231.0, 22.0, -3.5, 45.0, 5, 6, 2.5),
        (236.0, 27.5, -6.0, 46.0, 6, 7, 2.5),
        (252.0, 28.0, -6.5, 46.0, 6, 7, 2.5),
        (257.0, 28.0, 0.0, 46.0, 6, 7, 2.0),
        (263.5, 26.5, 7.0, 44.0, 5, 6, 1.0)]
복부S = [(200.5, 13.5, 0.2, 27.5, 3, 3, 0.0),
        (205.0, 13.5, 0.2, 27.5, 3, 3, 0.0),
        (212.0, 12.0, 0.2, 27.0, 3, 3, 0.0),
        (220.0, 13.5, 0.4, 29.0, 3, 3, 0.0),
        (222.3, 14.5, 1.0, 29.0, 3, 3, 0.0)]
벨트S = [(189.0, 22.0, -1.0, 33.0, 3, 3, 0.0),
        (196.0, 22.0, -1.0, 33.0, 3, 3, 0.0),
        (199.5, 17.0, 1.0, 31.0, 3, 3, 0.0)]
def 판단면(tab, 두께, 뒤한, 앞=True, cf=1.5, k=1.0):   # 판 부품: (z, 반폭, 겉면 y) → 두께 판(겉면 쪽 모따기 · 용골)
    out = []
    for z, w, y in tab:
        if 앞: yf, yb = y, min(y + 두께, 뒤한)
        else: yb, yf = y, max(y - 두께, 뒤한)
        c = min(cf, w / 3)
        out.append((z, w, yf, yb, c if 앞 else 0.4, 0.4 if 앞 else c, k if 앞 else 0.0))
    return out
혀S = 판단면([(204.5, 0.6, -3.5), (219.0, 5.0, -6.3), (226.0, 8.5, -7.0), (229.0, 10.5, -6.8)], 7.0, -0.2, k=1.0)
앞치마S = 판단면([(152.5, 0.6, -3.0), (160.0, 3.0, -5.0), (170.0, 6.0, -6.5), (183.0, 9.0, -8.0), (193.0, 10.0, -4.5)], 3.5, -1.3, k=1.2)
뒤치마S = 판단면([(167.5, 0.6, 36.5), (172.0, 7.0, 37.5), (190.0, 20.5, 38.5), (197.5, 17.5, 37.8)], 3.8, 33.4, 앞=False)
Y가슴 = 19.6; Y복부 = 14.7; Y벨트 = 15.0         # 앞뒤 반쪽 이음 평면 (가슴 = 어깨축 평면 · 복부 = 뼈 축 · 벨트 = 뼈 축)

# ── 속 비움(keepout) — 볼록 조각 목록 ────────────────────────────────
def 쓸기_축(조각들, p, a, 각들):                # 한 축 회전: 이웃 각 두 벌의 hull 합
    out = []
    for m in 조각들:
        cs = [돌려(m, p, a, t) for t in 각들]
        out += [mf.Manifold.batch_hull([c0, c1]) for c0, c1 in zip(cs[:-1], cs[1:])]
    return out
def 쓸기_볼(조각들, p, 범위):                  # 볼: 범위 모서리 자세들의 hull(볼록 근사 · 넉넉)
    xs = [범위[0][0], 0, 범위[0][1]]; ys = [범위[1][0], 0, 범위[1][1]]
    out = []
    for m in 조각들:
        cs = [돌려(돌려(m, p, (1, 0, 0), ax), p, (0, 1, 0), ay) for ax in xs for ay in ys]
        out.append(mf.Manifold.batch_hull(cs))
    return out
def 범위(n, i=0): r = JT[n]["범위"][i]; return r["축"], r["최소"], r["최대"]
def 각격자(lo, hi, st=7.5): return list(np.linspace(lo, hi, max(2, int(np.ceil((hi - lo) / st)) + 1)))

log("속 비움 짓는 중")
K = {}
# 가슴 무리(가슴 뼈에 붙는 것)
정 = 뼈조각("가슴", 0.4) + [외피("목아래"), 외피("가슴복부"), 외피("L어깨스윙"), 외피("R어깨스윙")]
목 = 쓸기_볼(뼈조각("목", 0.4) + [외피("목위")], JT["목아래"]["피벗mm"], [(-15, 15), (-15, 15)])
어깨 = []
for s in "LR":
    j21 = JT[s + "어깨회전"]; p21 = np.array(j21["피벗mm"]); a21 = np.array(j21["축"])
    blk = np.array([q[:3] for ch in BONE[s + "어깨블록"]["마디"] for q in ch]); rr = max(q[3] for ch in BONE[s + "어깨블록"]["마디"] for q in ch) / 2
    d = blk - p21; t_ = d @ a21; rad = np.linalg.norm(d - np.outer(t_, a21), axis=1).max() + rr + 0.4
    봉투 = 원통(p21 + a21 * min(t_.min() - rr, 0), p21 + a21 * (t_.max() + rr), rad)          # 어깨블록 = 회전축 둘레 봉투
    j23 = JT[s + "어깨들기"]; p23 = np.array(j23["피벗mm"]); t23 = (p23 - p21) @ a21
    r23 = np.linalg.norm((p23 - p21) - t23 * a21) + np.hypot(j23["외피"]["반지름mm"] + 0.3, j23["외피"]["폭mm"] / 2 + 0.3)
    봉투23 = 원통(p21 + a21 * (t23 - j23["외피"]["반지름mm"] - 0.3), p21 + a21 * (t23 + j23["외피"]["반지름mm"] + 0.3), r23)
    ax, lo, hi = 범위(s + "어깨스윙")
    어깨 += 쓸기_축(뼈조각(s + "어깨축", 0.4) + [외피(s + "어깨회전"), 봉투, 봉투23], JT[s + "어깨스윙"]["피벗mm"], ax, 각격자(lo, hi))
배밑 = 쓸기_볼(뼈조각("복부", 0.4) + [외피("복부허리")], JT["가슴복부"]["피벗mm"], [(-20, 20), (-15, 15)])
K["가슴"] = 정 + 목 + 어깨 + 배밑
# 복부 무리
위가슴 = 쓸기_볼([캡슐(*[q[:3] for q in (BONE["가슴"]["마디"][0][0], BONE["가슴"]["마디"][0][-1])], 7.4, 7.4)], JT["가슴복부"]["피벗mm"], [(-15, 20), (-15, 15)])
ax4, lo4, hi4 = 범위("복부허리")
허리돌 = 쓸기_축(뼈조각("허리", 0.4) + [외피("L고관절벌림"), 외피("R고관절벌림")], JT["복부허리"]["피벗mm"], ax4, 각격자(lo4, hi4))
K["복부"] = 뼈조각("복부", 0.4) + [외피("가슴복부"), 외피("복부허리")] + 위가슴 + 허리돌
# 허리 무리(벨트) — 다리 = 벌림 × 앞차기 두 겹 쓸기
다리 = []; 다리정 = []
for s in "LR":
    p5 = JT[s + "고관절벌림"]["피벗mm"]; a5, l5, h5 = 범위(s + "고관절벌림")
    p7 = JT[s + "고관절"]["피벗mm"]; a7, l7, h7 = 범위(s + "고관절")
    블록 = 뼈조각(s + "고관절블록", 0.4) + [외피(s + "고관절")]
    허벅 = 뼈조각(s + "허벅지위", 0.4) + [외피(s + "허벅지회전")]
    다리정 += 블록 + 허벅 + 뼈조각(s + "허벅지", 0.4)
    g5 = 각격자(l5, h5, 11); g7 = 각격자(l7, h7, 15)
    for m in 블록: 다리 += 쓸기_축([m], p5, a5, g5)
    for m in 허벅:
        for t5 in g5:
            다리 += [mf.Manifold.batch_hull([돌려(돌려(m, p7, a7, c0), p5, a5, t5), 돌려(돌려(m, p7, a7, c1), p5, a5, t5)]) for c0, c1 in zip(g7[:-1], g7[1:])]
K["벨트"] = 뼈조각("허리", 0.4) + 뼈조각("복부", 0.4) + [외피("복부허리"), 외피("L고관절벌림"), 외피("R고관절벌림")] + 다리
K["치마"] = 뼈조각("허리", 0.4) + [외피("L고관절벌림"), 외피("R고관절벌림")] + 다리정      # 스커트: 쉰 자세만 (움직이면 힌지로 비킴)
KM = {k: 합(v) for k, v in K.items()}
log("속 비움 조각", {k: len(v) for k, v in K.items()})

class 안검사:                                  # 볼록 조각들 안인 점?
    def __init__(s, 조각들):
        s.eq = []
        for m in 조각들:
            v = np.asarray(m.to_mesh().vert_properties)[:, :3]
            if len(v) >= 4: s.eq.append(ConvexHull(v).equations)
    def __call__(s, P):
        P = np.atleast_2d(P); r = np.zeros(len(P), bool)
        for e in s.eq: r |= (P @ e[:, :3].T + e[:, 3] <= 0).all(1)
        return r
INK = {k: 안검사(v) for k, v in K.items()}

# ── 부품 짓기 ─────────────────────────────────────────────────────
부품 = {}; 정보 = {}; 키트 = {"뼈구멍": [], "핀": []}
def 반쪽(m, y, 앞):
    return m.trim_by_plane((0, -1, 0), -y) if 앞 else m.trim_by_plane((0, 1, 0), y)
def 원점찾기(씨, 무리, 반지름, y0, y1, 안쪽):     # 이음면 다보 자리: 씨앗 근처에서 기둥(반지름 + 0.4)이 속 비움에 안 닿고 안 로프트 안인 곳
    for d in np.linspace(0, 4, 17):
        for ang in np.linspace(0, 2 * np.pi, 13)[:-1] if d > 0 else [0]:
            x, z = 씨[0] + d * np.cos(ang), 씨[1] + d * np.sin(ang)
            t = np.linspace(0, 2 * np.pi, 16, endpoint=False)
            P = np.array([[x + (반지름 + 0.4) * np.cos(a), yy, z + (반지름 + 0.4) * np.sin(a)] for a in t for yy in np.linspace(y0, y1, 6)] + [[x, yy, z] for yy in np.linspace(y0, y1, 6)])
            if not INK[무리](P).any() and 안쪽(np.array([[x, (y0 + y1) / 2, z]])):
                return float(x), float(z)
    return None
def 로프트안(secs):                          # 점이 바깥 로프트 안? (단면 선형 보간)
    zs = np.array([s[0] for s in secs])
    def f(P):
        out = []
        for x, y, z in P:
            if z < zs[0] or z > zs[-1]: out.append(False); continue
            i = min(np.searchsorted(zs, z) - 1, len(zs) - 2); i = max(i, 0); u = (z - zs[i]) / (zs[i + 1] - zs[i])
            s = [secs[i][k] * (1 - u) + secs[i + 1][k] * u for k in range(1, 4)]
            out.append(abs(x) < s[0] - 2.5 and s[1] + 2.5 < y < s[2] - 2.5)
        return np.array(out)
    return f

def 앞뒤블록(이름, secs, ysplit, 무리, 위닫, 아래닫, 다보씨, 기둥들, 추가빼기=None):
    """앞뒤 반쪽 블록: 껍질 + 다보 기둥 + 뼈 결합 기둥 − 속 비움 → 반쪽 나눔 + 핀 · 구멍."""
    바깥, 안, _ = 껍질(secs, 2.0, 위닫, 아래닫)
    몸 = 바깥 - 안
    zs = [s[0] for s in secs]; y_lo = min(s[2] for s in secs) - 5; y_hi = max(s[3] for s in secs) + 5
    다보 = []
    for 씨 in 다보씨:
        q = 원점찾기(씨, 무리, 2.5, y_lo + 5, y_hi - 5, 로프트안(secs))
        if q is None: log("  !! 다보 자리 없음", 이름, 씨); continue
        for sx in (1, -1):
            다보.append((sx * abs(q[0]), q[1]))
    기둥 = 합([원통((x, y_lo, z), (x, y_hi, z), 2.5) for x, z in 다보]) ^ 바깥
    몸 = 몸 + 기둥
    결합 = []
    for (p, 방향, 쪽) in 기둥들:                   # p = 뼈 겉 점 · 방향 = 뼈 → 벽(단위) · 쪽 = 앞/뒤
        p = np.asarray(p, float); dv = np.asarray(방향, float)
        몸 = 몸 + (원통(p + 0.0 * dv, p + 60 * dv, 3.0) ^ 바깥)
        결합.append((p, dv, 쪽))
    몸 = 몸 - KM[무리]
    if 추가빼기 is not None: 몸 = 몸 - 추가빼기
    앞 = 반쪽(몸, ysplit, True); 뒤 = 반쪽(몸, ysplit, False)
    for x, z in 다보:                             # 핀 = 앞 반쪽 · 구멍 = 뒤 반쪽
        앞 = 앞 + 원통((x, ysplit - 0.5, z), (x, ysplit + 2.5, z), 1.0, 24)
        뒤 = 뒤 - 원통((x, ysplit - 0.1, z), (x, ysplit + 3.0, z), 1.2, 24)
    for p, dv, 쪽 in 결합:                        # 결합 핀 Ø3.0 × 4 (뼈 쪽 구멍 Ø3.2 × 4.5)
        pin = 원통(p - 4.0 * dv, p + 0.6 * dv, 1.5, 24)
        if 쪽 == "앞": 앞 = 앞 + pin
        else: 뒤 = 뒤 + pin
        키트["뼈구멍"].append(dict(부품=이름 + 쪽, 뼈=무리 if 무리 != "벨트" else "허리", 입구mm=[round(float(v), 2) for v in p],
                                 방향=[round(float(v), 3) for v in -dv], 지름=3.2, 깊이=4.5, 핀="부품 쪽 Ø3.0 × 4.0 (뼈 겉에서 0.4 틈 건너)"))
    정보[이름 + "앞"] = dict(다보=[dict(xz=[round(x, 2), round(z, 2)], 이음y=ysplit, 핀="Ø2.0×2.5(앞 반쪽)", 구멍="Ø2.4×3.0(뒤 반쪽) — 한쪽 0.20") for x, z in 다보])
    정보[이름 + "뒤"] = dict(다보=정보[이름 + "앞"]["다보"])
    return 앞, 뒤, 바깥

# 뼈 축 위 점
def 뼈축(n, z, ch=0):
    m = np.array(BONE[n]["마디"][ch]); i = np.argsort(m[:, 2]); zz = m[i, 2]
    return np.array([np.interp(z, zz, m[i, 0]), np.interp(z, zz, m[i, 1]), z]), float(np.interp(z, zz, m[i, 3])) / 2

log("가슴")
목구멍 = 상자((-11.8, 5.0, 256.0), (11.8, 33.0, 270.0))
# 어깨 창: 어깨 쓸기(스윙 × 회전)가 옆벽(|x| > 21)을 지나는 곳을 감싸는 모따기 팔각 창(축 x) — 둥근 덩어리 구멍 대신
창 = []
for sx in (-1, 1):
    반 = [m for m in 어깨 if (m.bounding_box()[0] + m.bounding_box()[3]) * sx > 0]
    bb = (합(반) ^ 상자((21 if sx > 0 else -29.5, -60, 150), (29.5 if sx > 0 else -21, 100, 300))).bounding_box()
    y0, z0, y1, z1 = bb[1] - 0.5, bb[2] - 0.5, bb[4] + 0.5, bb[5] + 0.5; c = min(3.0, (y1 - y0) / 4, (z1 - z0) / 4)
    oct_ = [(y0 + c, z0), (y1 - c, z0), (y1, z0 + c), (y1, z1 - c), (y1 - c, z1), (y0 + c, z1), (y0, z1 - c), (y0, z0 + c)]
    m = mf.CrossSection([oct_]).extrude(40).transform([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0]])   # (y, z, e) → (x=e, y, z)
    창.append(m.translate((0 if sx > 0 else -40, 0, 0)) ^ 상자((21 if sx > 0 else -60, -60, 150), (60 if sx > 0 else -21, 100, 300)))
    log("  어깨 창", "L" if sx < 0 else "R", "y %.1f~%.1f z %.1f~%.1f" % (y0, y1, z0, z1))
창 = 합(창)
기둥 = []
for z in (230.0, 238.0):
    c, r = 뼈축("가슴", z); 기둥.append((c + np.array([0, r / np.cos(np.radians(18.8)), 0]), (0, 1, 0), "뒤"))
# 혀 자리: 혀(복부 쪽)를 가슴복부 볼 범위로 쓸어(+0.4) 가슴에서 뺀다 → 가슴 아래 가운데에 혀가 들어가는 홈
p3 = JT["가슴복부"]["피벗mm"]
혀토막 = []
for a_, b_ in zip(혀S[:-1], 혀S[1:]):
    qa, qb = 오프(단면점(*a_[1:]), 0.4), 오프(단면점(*b_[1:]), 0.4)
    혀토막.append(mf.Manifold.hull_points(np.vstack([np.c_[qa, np.full(len(qa), a_[0])], np.c_[qb, np.full(len(qb), b_[0])]]).tolist()))
혀쓸기 = []
for ax_, lo_, hi_ in [((1, 0, 0), -20, 15), ((0, 1, 0), -15, 15), ((0, 0, 1), -30, 30)]:
    혀쓸기 += 쓸기_축(혀토막[1:], p3, ax_, 각격자(lo_, hi_, 2.5))
혀쓸기M = 합(혀쓸기)
가슴앞, 가슴뒤, 가슴바깥 = 앞뒤블록("가슴", 가슴S, Y가슴, "가슴", True, False, [(-22.0, 240.0), (-20.0, 259.0)], 기둥, 목구멍 + 창 + 혀쓸기M)
# 혀 윗끝 · 복부 윗면 = 가슴 바깥 로프트(+0.4)를 가슴복부 볼 범위로 쓸어 낸 부피 밖 (로프트 토막은 볼록 → hull 쓸기 = 평면 면)
p3 = JT["가슴복부"]["피벗mm"]
가슴토막 = []
zs_ = [s_[0] for s_ in 가슴S]
for a_, b_ in zip(가슴S[:-1], 가슴S[1:]):
    qa, qb = 오프(단면점(*a_[1:]), 0.4), 오프(단면점(*b_[1:]), 0.4)
    가슴토막.append(mf.Manifold.hull_points(np.vstack([np.c_[qa, np.full(len(qa), a_[0])], np.c_[qb, np.full(len(qb), b_[0])]]).tolist()))
가슴쓸기 = []
for ax_, lo_, hi_ in [((1, 0, 0), -15, 20), ((0, 1, 0), -15, 15), ((0, 0, 1), -30, 30)]:
    가슴쓸기 += 쓸기_축(가슴토막[:4], p3, ax_, 각격자(lo_, hi_, 2.5))
가슴쓸기M = 합(가슴쓸기)
log("복부")
기둥 = []
c, r = 뼈축("복부", 209.4); 기둥 += [(c - np.array([0, r, 0]), (0, -1, 0), "앞"), (c + np.array([0, r, 0]), (0, 1, 0), "뒤")]
복부앞, 복부뒤, 복부바깥 = 앞뒤블록("복부", 복부S, Y복부, "복부", True, True, [(-9.9, 204.5), (-9.9, 214.0)], 기둥, 가슴쓸기M)
log("벨트")
기둥 = []
c, r = 뼈축("허리", 193.5); 기둥 += [(c - np.array([0, r, 0]), (0, -1, 0), "앞"), (c + np.array([0, r, 0]), (0, 1, 0), "뒤")]
벨트앞, 벨트뒤, 벨트바깥 = 앞뒤블록("벨트", 벨트S, Y벨트, "벨트", True, False, [(-17.5, 193.5)], 기둥)

# 스커트 힌지 (1.75 필라멘트 핀): 러그 = 벨트 쪽(구멍 1.75 압입) · 너클 = 스커트 쪽(구멍 1.95)
R너클 = 2.2
def 러그(축점, 축, 구간들, 벽점, 벽방향):          # 벽방향 = 축에서 벨트 벽 쪽 단위벡터
    ms = []
    a = np.asarray(축, float); c = np.asarray(축점, float); w = np.asarray(벽방향, float)
    for t0, t1 in 구간들:
        cy = 원통(c + a * t0, c + a * t1, R너클)
        웹 = mf.Manifold.batch_hull([cy, 원통(c + a * t0 + w * 벽점, c + a * t1 + w * 벽점, R너클)])
        ms.append(웹)
    return 합(ms)
힌지 = {}
# 앞 스커트: 축 x · (y −3.6, z 195)
축앞 = ((0, -3.6, 195.0), (1, 0, 0)); 러그앞 = 러그(*축앞, [(-9.3, -6.3), (6.3, 9.3)], 3.6, (0, 1, 0))
축뒤 = ((0, 35.8, 198.3), (1, 0, 0)); 러그뒤 = 러그(*축뒤, [(-9.3, -6.3), (6.3, 9.3)], 4.0, (0, -1, 0))
벨트앞 = 벨트앞 + (러그앞 - KM["벨트"]); 벨트뒤 = 벨트뒤 + (러그뒤 - KM["벨트"])
옆러그 = []
for sx in (-1, 1):
    c = (sx * 24.8, 0, 195.8)
    옆러그.append((sx, c, 러그(c, (0, 1, 0), [(3.5, 7.2), (24.8, 28.5)], 3.5, (-sx, 0, 0))))
for sx, c, m in 옆러그:
    m = m - KM["벨트"]
    벨트앞 = 벨트앞 + (m ^ 반공간((0, -1, 0), -Y벨트)); 벨트뒤 = 벨트뒤 + (m ^ 반공간((0, 1, 0), Y벨트))
def 핀구멍(c, a, t0, t1, d): c = np.asarray(c, float); a = np.asarray(a, float); return 원통(c + a * t0, c + a * t1, d / 2, 24)
벨트앞 = 벨트앞 - 핀구멍(*축앞, -10, 10, 1.75)
벨트뒤 = 벨트뒤 - 핀구멍(*축뒤, -10, 10, 1.75)
for sx, c, _ in 옆러그:
    h = 핀구멍(c, (0, 1, 0), 2.5, 29.5, 1.75); 벨트앞 = 벨트앞 - h; 벨트뒤 = 벨트뒤 - h

log("스커트 · 혀 · 목깃")
def 판로프트(secs): return 로프트(secs)
앞치마 = 판로프트(앞치마S)
앞치마 = 앞치마 + 원통(np.array(축앞[0]) + (-6.0, 0, 0), np.array(축앞[0]) + (6.0, 0, 0), R너클)
for sx in (-1, 1):
    앞치마 = 앞치마 - 상자((min(sx * 5.95, sx * 9.65), -12, 191.6), (max(sx * 5.95, sx * 9.65), 2, 199))
앞치마 = 앞치마 - 핀구멍(*축앞, -7, 7, 1.95) - KM["치마"]
뒤치마 = 판로프트(뒤치마S)
뒤치마 = 뒤치마 + 원통(np.array(축뒤[0]) + (-6.0, 0, 0), np.array(축뒤[0]) + (6.0, 0, 0), R너클)
for sx in (-1, 1):
    뒤치마 = 뒤치마 - 상자((min(sx * 5.95, sx * 9.65), 30, 195), (max(sx * 5.95, sx * 9.65), 45, 202))
뒤치마 = 뒤치마 - 핀구멍(*축뒤, -7, 7, 1.95) - KM["치마"]
# 옆 스커트: yz 윤곽 · 두께 2.5 · 아래로 8° 벌어짐 (왼쪽 = x<0 을 짓고 거울)
옆윤곽 = [(-0.5, 177), (3.5, 177), (9, 180.5), (23, 180.5), (28.5, 176), (30.5, 168), (35.5, 168), (35.5, 186), (29, 190),
         (24.1, 190), (24.1, 195.0), (7.9, 195.0), (7.9, 190), (3, 190), (-0.5, 187)]
def 옆치마(sx):
    cs = mf.CrossSection([옆윤곽])
    if cs.area() <= 0: cs = mf.CrossSection([옆윤곽[::-1]])
    m = cs.extrude(2.5)                                   # (y, z, 0..2.5) → x
    m = m.transform([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0]])  # (u,v,w) → (x=w, y=u, z=v)
    m = m.translate((24.8 - 1.25, 0, 0))
    tn = np.tan(np.radians(8))
    m = m.warp(lambda v: (v[0] + max(0.0, 195.8 - v[2]) * tn, v[1], v[2]))
    m = m + 원통((24.8, 7.5, 195.8), (24.8, 24.5, 195.8), R너클)
    m = m - 핀구멍((24.8, 0, 195.8), (0, 1, 0), 2.5, 29.5, 1.95)
    if sx < 0: m = m.mirror((1, 0, 0))
    return m - KM["치마"]
옆L = 옆치마(-1); 옆R = 옆치마(1)
혀 = 판로프트(혀S)
# 혀 → 복부 앞 핀 Ø2 (구멍 Ø2.4 = 복부 앞벽 관통)
혀핀 = [(0.0, 208.0), (0.0, 216.5)]
for x, z in 혀핀:
    혀 = 혀 + 원통((x, -0.5, z), (x, 2.4, z), 1.0, 24); 복부앞 = 복부앞 - 원통((x, -1, z), (x, 3.0, z), 1.2, 24)
정보["혀(복부 앞 판)"] = dict(결합="복부앞 앞벽에 핀 Ø2.0 × 2 (구멍 Ø2.4 관통)", 핀xz=혀핀)
# 목깃: U(앞 트임) · 겉 위 모서리 1.5 모따기 · 앞쪽 45° 경사
목깃겉 = [(-18.5, 7.0), (18.5, 7.0), (18.5, 34.5), (15.5, 37.5), (-15.5, 37.5), (-18.5, 34.5)]
def 층(pts, z, d=0.0):
    q = 오프(pts, d); return np.c_[q, np.full(len(q), z)]
목깃 = mf.Manifold.hull_points(np.vstack([층(목깃겉, 263.5), 층(목깃겉, 270.5)]).tolist()) + \
       mf.Manifold.hull_points(np.vstack([층(목깃겉, 270.5), 층(목깃겉, 272.0, -1.5)]).tolist())
목깃 = 목깃 - 상자((-11.8, 0.0, 262.0), (11.8, 33.0, 280.0))
n = np.array([0, -5.0, 8.0]); n /= np.linalg.norm(n)       # 앞 경사면: (y 7, z 267) 과 (y 15, z 272) 를 지나는 면 위를 버림
목깃 = 목깃.trim_by_plane(tuple(-n), float(-n @ np.array([0, 7.0, 267.0])))
목깃 = 목깃 - KM["가슴"]
for sx in (-1, 1):
    목깃 = 목깃 + 원통((sx * 15.15, 27.0, 261.0), (sx * 15.15, 27.0, 263.6), 1.0, 24)
    가슴뒤 = 가슴뒤 - 원통((sx * 15.15, 27.0, 260.0), (sx * 15.15, 27.0, 264.0), 1.2, 24)
정보["목깃"] = dict(결합="가슴뒤 윗면에 핀 Ø2.0 × 2 (구멍 Ø2.4 관통) · x ±15.15 y 27")

# ── 가슴 파랑 판 (원화 파랑 영역 → 사다리꼴 · 좌우 평균 대칭) ────────────────
def 파랑사다리꼴():
    a = np.array(Image.open(os.path.join(ART, "omega_front_clean.png")).convert("RGBA")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]; blue = (b - r > 35) & (b > 90) & (a[..., 3] > 128)
    from scipy import ndimage
    R_, C_ = np.mgrid[0:1024, 0:1024]; X = (C_ - 534.7) * 0.3243; Z = (975 - R_) * 0.3305
    m = ndimage.binary_opening(blue & (Z > 234) & (Z < 262) & (np.abs(X) < 27.8), np.ones((2, 2)))
    lab, k = ndimage.label(m); 판 = []
    for i in range(1, k + 1):
        w = lab == i
        if w.sum() < 25: continue
        P = np.c_[X[w], Z[w]]
        if P[:, 0].mean() > 0: P[:, 0] *= -1                    # 오른쪽은 왼쪽으로 접어 같은 무리에
        판.append(P)
    # 짝(왼 · 접은 오른) 끼리 합쳐 주축 사다리꼴
    쓴 = []; out = []
    for i, P in enumerate(판):
        if i in 쓴: continue
        j = min((j for j in range(len(판)) if j != i and j not in 쓴), key=lambda j: np.linalg.norm(판[j].mean(0) - P.mean(0)))
        쓴 += [i, j]; Q = np.vstack([P, 판[j]]); c = Q.mean(0)
        u, s_, vt = np.linalg.svd(Q - c, full_matrices=False); d = vt[0]; nrm = np.array([-d[1], d[0]])
        t = (Q - c) @ d; h = (Q - c) @ nrm; t0, t1 = np.percentile(t, [2, 98])
        def 폭(sel): return np.percentile(h[sel], [5, 95]) if sel.sum() > 5 else np.array([-0.8, 0.8])
        a0 = 폭(t < t0 + 0.3 * (t1 - t0)); a1 = 폭(t > t1 - 0.3 * (t1 - t0))
        q = [c + d * t0 + nrm * a0[0], c + d * t1 + nrm * a1[0], c + d * t1 + nrm * a1[1], c + d * t0 + nrm * a0[1]]
        out.append(np.array(q))
    return out
사다리 = 파랑사다리꼴()
log("파랑 판", len(사다리), "짝")
def 앞면띠(poly_xz, 바깥secs, d_in, d_out, 여유=0.0, 쪽=(-1, -Y가슴)):   # 정면에서 본 다각형을 y 로 밀어 겉 띠(바깥 d_out ~ 안 d_in)와 교차
    q = np.asarray(poly_xz, float)
    cs = mf.CrossSection([q.tolist()])
    if cs.area() <= 0: cs = mf.CrossSection([q[::-1].tolist()])
    if 여유: cs = cs.offset(여유, mf.JoinType.Miter)
    pr = cs.extrude(80).transform([[1, 0, 0, 0], [0, 0, 1, -30], [0, 1, 0, 0]])   # (x, z_, e) → (x, y=e−30, z=z_)
    띠 = 로프트(바깥secs, d_out) - 로프트(바깥secs, d_in)
    return pr ^ 띠 ^ 반공간((0, 쪽[0], 0), 쪽[1])        # 쪽 = (−1, −y) → y ≤ y 쪽만 · (1, y) → y ≥ y 쪽만
파랑 = []
for q in 사다리:
    for sx in (1, -1):
        qq = q.copy(); qq[:, 0] *= sx
        파랑.append(앞면띠(qq, 가슴S, -0.6, 0.4))
        가슴앞 = 가슴앞 - 앞면띠(qq, 가슴S, -0.6, 1.0, 여유=0.1)
파랑판 = 합(파랑)
# 엠블럼(혀 위 원판 · 파랑): 주머니 0.6 · 판 1.0
원 = [(3.0 * np.cos(t), 222.0 + 3.0 * np.sin(t)) for t in np.linspace(0, 2 * np.pi, 33)[:-1]]
엠블럼 = 앞면띠(원, 혀S, -0.6, 0.4, 쪽=(-1, 2.0))
혀 = 혀 - 앞면띠(원, 혀S, -0.6, 1.0, 여유=0.1, 쪽=(-1, 2.0))

# ── 패널라인 (규칙: 직선 + 45° · 좌우 대칭 · 적게) ─────────────────────
def 홈(부, secs, 경로들, 쪽, 단=((0.8, 0.17), (0.53, 0.34), (0.27, 0.5))):
    """패널라인 V 홈(3 단 근사: 폭 0.8/0.53/0.27 · 깊이 0.17/0.34/0.5) = 정면(또는 뒤)에서 본 띠를 y 로 밀어 겉 띠와 교차해 뺀다.
    깊이는 로프트 수평 오프셋 — 겉면이 기울면 법선 깊이는 cos θ 배(얕아짐)."""
    if not isinstance(경로들[0][0], (list, tuple)): 경로들 = [경로들]
    칼 = []
    for 경로 in 경로들:
        for (x0, z0), (x1, z1) in zip(경로[:-1], 경로[1:]):
            d = np.array([x1 - x0, z1 - z0]); d /= np.linalg.norm(d); nrm = np.array([-d[1], d[0]])
            for w, dep in 단:
                a = np.array([x0, z0]) - d * w / 2; b = np.array([x1, z1]) + d * w / 2
                q = [a + nrm * w / 2, b + nrm * w / 2, b - nrm * w / 2, a - nrm * w / 2]
                칼.append(앞면띠(q, secs, -dep, 1.5, 쪽=쪽))
    return 부 - 합(칼)
def 메시(m):
    t = m.to_mesh(); return np.asarray(t.vert_properties)[:, :3], np.asarray(t.tri_verts)
log("패널라인")
가슴앞 = 홈(가슴앞, 가슴S, [(0.0, 237.5), (0.0, 255.0)], (-1, -Y가슴))
가슴뒤 = 홈(가슴뒤, 가슴S, [(-11.0, 228.5), (-11.0, 250.0), (-7.0, 254.0), (7.0, 254.0), (11.0, 250.0), (11.0, 228.5)], (1, Y가슴))
앞치마 = 홈(앞치마, 앞치마S, [[(-6.5, 191.5), (-1.0, 186.0)], [(6.5, 191.5), (1.0, 186.0)]], (-1, 0.0))
뒤치마 = 홈(뒤치마, 뒤치마S, [(-12.0, 190.0), (0.0, 178.0), (12.0, 190.0)], (1, 34.5))
벨트앞 = 홈(벨트앞, 벨트S, [(-14.0, 192.5), (14.0, 192.5)], (-1, 5.0))
복부앞 = 복부앞  # 복부는 혀 뒤 · 검정 프레임 — 선 없음

부품 = {"가슴앞": 가슴앞, "가슴뒤": 가슴뒤, "가슴파랑판": 파랑판, "목깃": 목깃, "복부앞": 복부앞, "복부뒤": 복부뒤,
       "복부앞판_혀": 혀, "엠블럼": 엠블럼, "허리벨트앞": 벨트앞, "허리벨트뒤": 벨트뒤,
       "허리V스커트앞": 앞치마, "허리스커트뒤": 뒤치마, "허리스커트옆L": 옆L, "허리스커트옆R": 옆R}
색 = {"가슴파랑판": (0.30, 0.40, 0.75), "엠블럼": (0.30, 0.40, 0.75), "복부앞": (0.22, 0.22, 0.24), "복부뒤": (0.22, 0.22, 0.24)}
무리 = {"가슴앞": "가슴", "가슴뒤": "가슴", "가슴파랑판": "가슴", "목깃": "가슴", "복부앞": "복부", "복부뒤": "복부", "복부앞판_혀": "복부",
       "엠블럼": "복부", "허리벨트앞": "허리", "허리벨트뒤": "허리", "허리V스커트앞": "허리", "허리스커트뒤": "허리", "허리스커트옆L": "허리", "허리스커트옆R": "허리"}

# ── 저장 · 닫힘 ───────────────────────────────────────────────────
log("저장 · 닫힘 검사")
결과 = {}
for n, m in 부품.items():
    if m.is_empty(): log("  !! 빈 부품", n); continue
    cs = m.decompose(); 조각 = len(cs)
    if 조각 > 1 and n not in ("가슴파랑판",):        # 부스러기(최대 조각 2 % 미만) 버림
        vm = max(c.volume() for c in cs); m = 합([c for c in cs if c.volume() >= 0.02 * vm]); 부품[n] = m; 조각 = len(m.decompose())
    v, f = 메시(m); p = os.path.join(OUT, n + ".stl")
    trimesh.Trimesh(v, f).export(p)
    t = trimesh.load(p, force="mesh")
    edges = t.edges_sorted; _, cnt = np.unique(edges, axis=0, return_counts=True)
    결과[n] = dict(파일=n + ".stl", 부피mm3=round(m.volume(), 1), 무게g=round(m.volume() / 1000 * 1.24, 2), 닫힘=bool(t.is_watertight),
                  모서리4면=int((cnt > 2).sum()), 조각=조각, 크기mm=[round(float(e), 1) for e in t.extents], 뼈무리=무리[n])
    log("  %-10s 부피 %8.0f  닫힘 %s  4면모서리 %d  조각 %d" % (n, m.volume(), t.is_watertight, (cnt > 2).sum(), 조각))

# ── 가동 검사: 부품끼리 ─────────────────────────────────────────────
log("가동 검사")
G = {k: 합([부품[n] for n in 부품 if 무리[n] == k]) for k in ("가슴", "복부", "허리")}
가동 = {}
p3 = JT["가슴복부"]["피벗mm"]
for nm, ax, ang in [("앞숙임+20", (1, 0, 0), 20), ("뒤젖힘-15", (1, 0, 0), -15), ("옆+15", (0, 1, 0), 15), ("옆-15", (0, 1, 0), -15),
                    ("비틀+30", (0, 0, 1), 30), ("비틀-30", (0, 0, 1), -30)]:
    가동["가슴복부 " + nm] = round((돌려(G["가슴"], p3, ax, ang) ^ G["복부"]).volume(), 2)
p4 = JT["복부허리"]["피벗mm"]
for ang in (-45, 45):
    가동["복부허리 %+d" % ang] = round((돌려(합([G["가슴"], G["복부"]]), p4, (0, 0, 1), ang) ^ G["허리"]).volume(), 2)
# 다리 뼈대(뼈 + 외피)가 벨트/스커트에 닿는지 (허벅지 장갑은 D2 몫이라 뼈대만)
벨트류 = 합([부품["허리벨트앞"], 부품["허리벨트뒤"]])
for s in "LR":
    p5 = JT[s + "고관절벌림"]["피벗mm"]; a5, l5, h5 = 범위(s + "고관절벌림"); p7 = JT[s + "고관절"]["피벗mm"]; a7, l7, h7 = 범위(s + "고관절")
    뼈대 = 합(뼈조각(s + "고관절블록", 0) + 뼈조각(s + "허벅지위", 0) + 뼈조각(s + "허벅지", 0) + [외피(s + "고관절", 0), 외피(s + "허벅지회전", 0)])
    블록 = 합(뼈조각(s + "고관절블록", 0) + [외피(s + "고관절", 0)]); 허벅 = 뼈대 - 블록
    for t5 in (l5, 0, h5):
        for t7 in (l7, 0, 45, h7):
            q = 돌려(합([블록, 돌려(허벅, p7, a7, t7)]), p5, a5, t5)
            v벨 = (q ^ 벨트류).volume(); 치 = {n: round((q ^ 부품[n]).volume(), 1) for n in ("허리V스커트앞", "허리스커트뒤", "허리스커트옆" + s)}
            가동["%s다리 벌림%+d 앞차기%+d" % (s, t5, t7)] = dict(벨트=round(v벨, 2), 스커트=치)
for k, v in 가동.items(): log("  ", k, v)

# ── 실루엣: 조립 투영 vs 원화 윤곽 ─────────────────────────────────
log("실루엣")
전체 = 합(list(부품.values()))
def 투영(m, 축):                              # 축 = "앞"(x,z) · "옆"(y,z) → 다각형들
    T = [[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0]] if 축 == "앞" else [[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0]]
    return m.transform(T).project().to_polygons()
def 래스터(polys, 범위_, px=0.2):
    (a0, a1), (z0, z1) = 범위_
    W = int((a1 - a0) / px); H = int((z1 - z0) / px)
    im = Image.new("L", (W, H), 0)
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    # 짝수-홀수 대신: 바깥 윤곽(양 넓이)은 채우고 구멍(음 넓이)은 비움
    def 넓이(q): return 0.5 * np.sum(q[:, 0] * np.roll(q[:, 1], -1) - np.roll(q[:, 0], -1) * q[:, 1])
    for q in sorted(polys, key=lambda q: -abs(넓이(q))):
        area = 넓이(q)
        pts = [((x - a0) / px, (z1 - z) / px) for x, z in q]
        d.polygon(pts, fill=255 if area > 0 else 0)
    return np.array(im) > 0
정면P = 투영(전체, "앞"); 옆P = 투영(전체, "옆")
F = 래스터(정면P, ((-60, 60), (140, 280))); S = 래스터(옆P, ((-40, 80), (140, 280)))
def 원화윤곽():
    fa = np.array(Image.open(os.path.join(ART, "omega_front_clean.png")).convert("RGBA")).astype(int)
    sa = np.array(Image.open(os.path.join(ART, "omega_side.png")).convert("RGBA")).astype(int)
    def 금(a): return (a[..., 0] > 140) & (a[..., 1] > 100) & (a[..., 2] < 130) & (a[..., 0] - a[..., 2] > 60)
    fm = (fa[..., 3] > 128) & ~금(fa); sm = (sa[..., 3] > 128) & ~금(sa)
    front = {}; side = {}
    for z in np.arange(150, 273, 0.5):
        r = int(round(975 - z / 0.3305)); row = fm[r]; c = 535
        if row[c]:
            a = c
            while a > 0 and row[a - 1]: a -= 1
            b = c
            while b < 1023 and row[b + 1]: b += 1
            xl, xr = (a - 534.7) * 0.3243, (b + 1 - 534.7) * 0.3243
            if 234 <= z <= 268 and (xr - xl) / 2 > 30:    # 어깨 공과 붙은 줄: 가슴 먹선(|x| 32 → 안으로 첫 검정)
                rgb = fa[r, :, :3].sum(-1); out = []
                for sgn in (-1, 1):
                    cc = int(round(534.7 + sgn * 32 / 0.3243))
                    while rgb[cc] > 100 and abs(cc - 534.7) * 0.3243 > 20: cc -= sgn
                    out.append((cc - 534.7) * 0.3243)
                xl, xr = out
            front[z] = (xl, xr)
        r = int(round(938 - z / 0.347)); c0, c1 = int(460.5 - 15 / 0.338), int(460.5 + 50 / 0.338)
        cs_ = np.nonzero(sm[r, c0:c1])[0]
        if len(cs_): side[z] = ((c0 + cs_[0] - 460.5) * 0.338, (c0 + cs_[-1] + 1 - 460.5) * 0.338)
    return front, side
원F, 원S = 원화윤곽()
def 가장자리(M, 범위_, z, px=0.2):
    (a0, a1), (z0, z1) = 범위_; r = int((z1 - z) / px)
    if r < 0 or r >= M.shape[0]: return None
    c = np.nonzero(M[r])[0]
    return None if len(c) == 0 else (a0 + c[0] * px, a0 + (c[-1] + 1) * px)
틈줄 = {"정면": [], "옆": []}   # 부품 사이 가동 틈(조립 투영 폭 < 원화 60 %) — 오차에서 빼고 따로 적는다
오차 = {"정면": [], "옆앞": [], "옆뒤": []}; 오차줄 = {"정면": [], "옆앞": [], "옆뒤": []}
for z, (xl, xr) in 원F.items():
    if not (188 <= z <= 272): continue
    e = 가장자리(F, ((-60, 60), (140, 280)), z)
    if e is None or (e[1] - e[0]) < 0.6 * (xr - xl): 틈줄["정면"].append(float(z)); continue
    v = max(abs(e[0] - xl), abs(e[1] - xr)); 오차["정면"].append(v); 오차줄["정면"].append((z, round(v, 2)))
for z, (yf, yb) in 원S.items():
    e = 가장자리(S, ((-40, 80), (140, 280)), z)
    if e is None or (z >= 170 and (e[1] - e[0]) < 0.6 * (yb - yf)): 틈줄["옆"].append(float(z)); continue
    if 150 <= z <= 257: 오차["옆앞"].append(abs(e[0] - yf)); 오차줄["옆앞"].append((z, round(abs(e[0] - yf), 2)))
    if 170 <= z <= 236: 오차["옆뒤"].append(abs(e[1] - yb)); 오차줄["옆뒤"].append((z, round(abs(e[1] - yb), 2)))
실루엣 = {k: dict(최대=round(max(v), 2), 평균=round(float(np.mean(v)), 2), 줄수=len(v), 넘침2mm=int(sum(x > 2 for x in v)),
                  나쁜줄=sorted(오차줄[k], key=lambda q: -q[1])[:6]) for k, v in 오차.items() if v}
실루엣["틈줄z"] = 틈줄
for k, v in 실루엣.items(): log("  실루엣", k, v)

# ── 부품.json · 키트.json ─────────────────────────────────────────
힌지정보 = {"규격": "힌지1.75 (관절규격.json) — 핀 = 1.75 PLA 필라멘트 · 러그 구멍 1.75(압입) · 너클 구멍 1.95 · 축방향 틈 0.3 · 너클 R 2.2",
          "허리V스커트앞": dict(축점=list(축앞[0]), 축=list(축앞[1]), 핀길이=18.6, 러그="허리벨트앞 x ±(6.3~9.3)", 너클="x ±6.0"),
          "허리스커트뒤": dict(축점=list(축뒤[0]), 축=list(축뒤[1]), 핀길이=18.6, 러그="허리벨트뒤 x ±(6.3~9.3)", 너클="x ±6.0"),
          "허리스커트옆": dict(축점="(±24.8, ·, 195.8)", 축=[0, 1, 0], 핀길이=25.0, 러그="벨트 옆 y 3.5~7.2 (앞 반쪽) · 24.8~28.5 (뒤 반쪽)", 너클="y 7.5~24.5")}
json.dump(dict(설명=__doc__, 부품=결과, 결합정보=정보, 힌지=힌지정보, 가동검사_겹침mm3=가동, 실루엣mm=실루엣,
               총무게g=round(sum(r["무게g"] for r in 결과.values()), 1), 재질="PLA 1.24 g/cm³ · 속 빈 껍질 2.0 mm 그대로(채움 100 % 가정)"),
          open(os.path.join(OUT, "부품.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(dict(설명="몸통 · 허리 디자인 판이 뼈에 요구하는 구멍 (뼈 메시에 아직 안 뚫음). 방향 = 뼈 겉 → 뼈 속.", **키트),
          open(os.path.join(OUT, "키트.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ── 그림 ─────────────────────────────────────────────────────────
log("그림")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
def 그리기(ax, 목록, R, 제목, 뼈=None):
    L = np.array([0.35, -0.6, 0.72]); L /= np.linalg.norm(L)
    polys, cols, deps = [], [], []
    for m, c in 목록:
        v, f = 메시(m); vv = v @ R.T
        tri = vv[f]; n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); nn = np.linalg.norm(n, axis=1) + 1e-12; n /= nn[:, None]
        vis = n[:, 2] > 0
        sh = 0.35 + 0.65 * np.clip((np.cross(v[f][:, 1] - v[f][:, 0], v[f][:, 2] - v[f][:, 0]) / nn[:, None]) @ L, 0, 1)
        for t, s, d in zip(tri[vis], sh[vis], tri[vis][:, :, 2].mean(1)):
            polys.append(t[:, :2]); cols.append(np.clip(np.array(c) * s, 0, 1)); deps.append(d)
    o = np.argsort(deps)
    ax.add_collection(PolyCollection([polys[i] for i in o], facecolors=[cols[i] for i in o], edgecolors=[cols[i] for i in o], linewidths=0.1))
    ax.autoscale(); ax.set_aspect("equal"); ax.set_title(제목, fontsize=10)
def 보기R(yaw, pitch):                          # 화면 x · 화면 y(위) · 깊이(카메라 쪽 +)
    a, b = np.radians(yaw), np.radians(pitch)
    Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    base = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]])            # 앞(−y)에서 봄: 화면 x = x, 위 = z, 깊이 = −y
    Rx = np.array([[1, 0, 0], [0, np.cos(b), -np.sin(b)], [0, np.sin(b), np.cos(b)]])
    return Rx @ base @ Rz
목록 = [(m, 색.get(n, (0.88, 0.88, 0.90))) for n, m in 부품.items()]
fig = plt.figure(figsize=(22, 12))
# 1 정면 + 원화
ax = fig.add_subplot(1, 5, 1)
fa = Image.open(os.path.join(ART, "omega_front_clean.png")).convert("RGBA"); bg = Image.new("RGBA", fa.size, (255, 255, 255, 255)); bg.alpha_composite(fa)
ax.imshow(np.array(bg.convert("RGB")), extent=[(0 - 534.7) * 0.3243, (1024 - 534.7) * 0.3243, (975 - 1024) * 0.3305, 975 * 0.3305], alpha=0.35)
그리기(ax, 목록, 보기R(0, 0), "정면 + 원화(흐림) · 빨강 = 원화 윤곽")
zz = sorted(원F); ax.plot([원F[z][0] for z in zz], zz, "r-", lw=0.8); ax.plot([원F[z][1] for z in zz], zz, "r-", lw=0.8)
ax.set_xlim(-45, 45); ax.set_ylim(145, 278)
# 2 옆 + 원화 (작은 y = 앞 = 왼쪽)
ax = fig.add_subplot(1, 5, 2)
sa = Image.open(os.path.join(ART, "omega_side.png")).convert("RGBA"); bg = Image.new("RGBA", sa.size, (255, 255, 255, 255)); bg.alpha_composite(sa)
ax.imshow(np.array(bg.convert("RGB")), extent=[(0 - 460.5) * 0.338, (1024 - 460.5) * 0.338, (938 - 1024) * 0.347, 938 * 0.347], alpha=0.35)
그리기(ax, 목록, np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]]), "옆(왼쪽 = 앞) + 원화")
zz = sorted(원S); ax.plot([원S[z][0] for z in zz], zz, "r-", lw=0.8); ax.plot([원S[z][1] for z in zz], zz, "r-", lw=0.8)
ax.set_xlim(-25, 65); ax.set_ylim(145, 278)
ax = fig.add_subplot(1, 5, 3); 그리기(ax, 목록, 보기R(-35, 12), "3/4 앞")
ax = fig.add_subplot(1, 5, 4); 그리기(ax, 목록, 보기R(145, 12), "3/4 뒤")
# 5 분해도
벌림 = {"가슴앞": (0, -30, 25), "가슴뒤": (0, 25, 25), "가슴파랑판": (0, -45, 25), "목깃": (0, 0, 55), "복부앞": (0, -20, 0), "복부뒤": (0, 18, 0),
       "복부앞판_혀": (0, -38, 0), "엠블럼": (0, -48, 0), "허리벨트앞": (0, -15, -15), "허리벨트뒤": (0, 18, -15),
       "허리V스커트앞": (0, -35, -30), "허리스커트뒤": (0, 35, -30), "허리스커트옆L": (-22, 0, -25), "허리스커트옆R": (22, 0, -25)}
ax = fig.add_subplot(1, 5, 5)
그리기(ax, [(m.translate(벌림[n]), c) for (n, m), (_, c) in zip(부품.items(), 목록)], 보기R(-35, 12), "분해도")
for a in fig.axes: a.set_xticks([]) if a not in fig.axes[:2] else None
fig.suptitle("오메가몬 PG 디자인 판 — 몸통 · 허리 (%d 부품 · %.0f g · 실루엣 정면 최대 %.1f / 옆앞 %.1f / 옆뒤 %.1f mm)" % (
    len(부품), sum(r["무게g"] for r in 결과.values()), 실루엣["정면"]["최대"], 실루엣["옆앞"]["최대"], 실루엣["옆뒤"]["최대"]), fontsize=13)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "보기.png"), dpi=110); plt.close(fig)
log("끝", OUT)
