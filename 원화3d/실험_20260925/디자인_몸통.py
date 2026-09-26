# -*- coding: utf-8 -*-
"""오메가몬 PG(전고 300 mm) 가동 키트 — 「디자인 판」 몸통 · 허리 외장 (3바퀴 · 2026-09-26 · 출력해서 조립되는 상태가 목표).

    python 디자인_몸통.py   -> out/출력/오메가몬_PG/디자인/몸통/*.stl · 부품.json · 키트.json · 보기.png

부품을 도형으로 새로 짓는다(원화에서는 치수 · 윤곽만). 좌우 대칭 팔각 단면을 hull 로 이은 각진 로프트 · 껍질 2.0(바깥 로프트 − 구 r2 침식 = 법선 두께 2.0 균일).
속 비움 = **뼈 실물(프레임 STL) + J2 관절 부품 실물(_조립/관절_*.stl · J4 가 관절.json 자리에 놓은 것) + 0.3** · 움직이는 이웃은 가동 범위로 쓸어 낸 hull.
  1·2바퀴의 「관절 외피 +0.3」 방식은 버렸다(외피보다 J2 부품이 커서 49 쌍 1170 mm³ 겹침).
뼈 결합 = 장갑 안쪽 보스(Ø5) 끝 핀 Ø2.0 × 3.0 → 뼈 구멍 Ø2.2 × 3. 자리는 관절.json 「장갑구멍」(J1) 이 있으면 그것, 없으면 이 파일의 기본 자리(키트.json 에 적음).
앞뒤 반쪽 = 평면 이음 + 다보(핀 Ø2.0 / 구멍 Ø2.4). 스커트 앞/뒤 = 1.75 필라멘트 핀 힌지(러그 1.75 압입 · 너클 1.95).
좌표 = 골격(관절.json)과 같다: mm · 원점 발바닥 중앙 · [x 좌우, y 깊이(작은 y = 앞), z 높이].
원화 → mm = 골격 척도(비평_조립.py): 정면 x = (열 − 534)·0.342 · z = (951 − 행)·0.342 / 옆 y = (열 − 462)·0.349 · z = (938 − 행)·0.349."""
import os, json, time, glob
os.environ.setdefault("OMP_NUM_THREADS", "4")
import numpy as np
import manifold3d as mf
import trimesh
from scipy.spatial import ConvexHull, cKDTree
from PIL import Image

ROOT = r"G:\art2real\원화3d"
OUT = os.path.join(ROOT, "out", "출력", "오메가몬_PG", "디자인", "몸통"); os.makedirs(OUT, exist_ok=True)
ART = r"G:\art2real\트레일\trail7_part3d\in"
PG = os.path.join(ROOT, "out", "출력", "오메가몬_PG")
FRAME = os.path.join(ROOT, "out", "가동", "프레임")
J2D = os.path.join(ROOT, "out", "가동", "관절배치")                       # J1 3바퀴가 관절.json 자리에 놓은 J2 부품 (배치파일)
if not os.path.isdir(J2D): J2D = os.path.join(PG, "_조립")               # 없으면 J4 의 1바퀴 배치
D2 = os.path.join(PG, "디자인", "다리"); D3 = os.path.join(PG, "디자인", "머리어깨")
SEG = 40
T0 = time.time()
def log(*a): print("[%5.1fs]" % (time.time() - T0), *a, flush=True)

JS = json.load(open(os.path.join(ROOT, "out", "가동", "관절.json"), encoding="utf-8"))
JT = {j["이름"]: j for j in JS["관절"]}
BONE = JS["뼈"]
FRX = lambda c: (c - 534.0) * 0.342; FRZ = lambda r: (951.0 - r) * 0.342; SDY = lambda c: (c - 462.0) * 0.349; SDZ = lambda r: (938.0 - r) * 0.349

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
def z에서(a):
    a = np.asarray(a, float); a = a / np.linalg.norm(a); z = np.array([0, 0, 1.0])
    v = np.cross(z, a); c = a @ z
    if np.linalg.norm(v) < 1e-9: return np.eye(3) if c > 0 else np.diag([1, -1, -1.0])
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]); return np.eye(3) + K + K @ K / (1 + c)
def 원기둥(p, a, L, r, seg=SEG):
    m = mf.Manifold.cylinder(L, r, r, seg, True)
    return m.transform(np.hstack([z에서(a), np.asarray(p, float)[:, None]]).tolist())
def 원통(a_pt, b_pt, r, seg=SEG):
    a_pt, b_pt = np.asarray(a_pt, float), np.asarray(b_pt, float)
    return 원기둥((a_pt + b_pt) / 2, b_pt - a_pt, float(np.linalg.norm(b_pt - a_pt)), r, seg)
def 구(p, r): return mf.Manifold.sphere(r, SEG).translate(tuple(map(float, p)))
def 캡슐(a, b, ra, rb): return mf.Manifold.batch_hull([구(a, ra), 구(b, rb)])
def 상자(lo, hi): lo = np.asarray(lo, float); return mf.Manifold.cube(tuple(np.asarray(hi, float) - lo)).translate(tuple(lo))
def 반공간(n, d): return 상자((-400,) * 3, (400,) * 3).trim_by_plane(tuple(n), float(d))
def 메시(m):
    t = m.to_mesh(); return np.asarray(t.vert_properties)[:, :3], np.asarray(t.tri_verts)
def 만(tm): return mf.Manifold(mf.Mesh(vert_properties=np.asarray(tm.vertices, np.float32), tri_verts=np.asarray(tm.faces, np.uint32)))
def 껍질점(P, pad):                            # 점 무리 → 볼록 껍질(+pad: 여섯 방향으로 벌린 점)
    P = np.asarray(P, float)
    if pad: P = np.vstack([P + d for d in np.vstack([np.eye(3), -np.eye(3)]) * pad])
    return mf.Manifold.hull_points(P[ConvexHull(P).vertices].tolist())

# ── 뼈 · J2 관절 부품 실물 ───────────────────────────────────────────
_stl = {}
def STL(path):
    if path not in _stl: _stl[path] = trimesh.load(path, force="mesh")
    return _stl[path]
def 뼈STL(n): return STL(os.path.join(FRAME, n + ".stl"))
def 뼈조각(n, pad):                           # 쓸기용 볼록 조각 = 프레임 STL 의 볼록 껍질(+pad). (관절.json 마디 캡슐은 STL 과 다르다 — 어깨축이 z 263 까지 있음)
    return [껍질점(뼈STL(n).vertices, pad)]
def 뼈실물(n, pad=0.3):                        # 정지 빼기용: 프레임 STL 그대로(+pad 민코프스키)
    m = 만(뼈STL(n))
    return m.minkowski_sum(mf.Manifold.sphere(pad, 8)) if pad else m
def J2(n, 역할, pad=0.3):                     # 관절 n 의 부모/자식/핀/링크 STL → 볼록 껍질(+pad). 없으면 빈 목록
    fs = sorted(glob.glob(os.path.join(J2D, "관절_%s_%s*.stl" % (n, 역할))))
    return [껍질점(STL(f).vertices, pad) for f in fs]
def J2실물(n):
    return [만(STL(f)) for f in sorted(glob.glob(os.path.join(J2D, "관절_%s_*.stl" % n)))]
J2목록 = sorted(glob.glob(os.path.join(J2D, "관절_*.stl")))
J1구멍있음 = any(BONE[n].get("장갑구멍") for n in ("가슴", "복부", "허리"))
log("뼈 STL", len(glob.glob(os.path.join(FRAME, "*.stl"))), "· J2 STL", len(J2목록), "(%s)" % os.path.basename(J2D), "· 장갑구멍" if J1구멍있음 else "· 장갑구멍 없음(기본 자리)")

# ── 단면 · 로프트 · 껍질 ─────────────────────────────────────────────
def 단면점(w, yf, yb, cf, cb, k):
    cf = min(cf, 0.45 * w, 0.45 * (yb - yf)); cb = min(cb, 0.45 * w, 0.45 * (yb - yf)); k = min(k, 0.4 * (yb - yf))
    return [(-w + cf, yf + k), (0.0, yf), (w - cf, yf + k), (w, yf + k + cf), (w, yb - cb), (w - cb, yb),
            (-w + cb, yb), (-w, yb - cb), (-w, yf + k + cf)]
def 오프(pts, d):
    if abs(d) < 1e-9: return np.array(pts)
    ps = mf.CrossSection([pts]).offset(d, mf.JoinType.Miter).to_polygons()
    if not ps:
        q = np.array(pts); c = q.mean(0); return c + 0.05 * (q - c)
    return max(ps, key=lambda q: abs(ConvexHull(q).volume))
def 로프트(secs, d=0.0, zs=None):
    ds = d if isinstance(d, (list, tuple, np.ndarray)) else [d] * len(secs)
    P = []
    for i, s in enumerate(secs):
        q = 오프(단면점(*s[1:]), ds[i]); z = s[0] if zs is None else zs[i]
        P.append(np.c_[q, np.full(len(q), z)])
    return 합([mf.Manifold.hull_points(np.vstack([a, b]).tolist()) for a, b in zip(P[:-1], P[1:])])
def 껍질(secs, t=2.0, 위닫=True, 아래닫=True, 빼기=None):
    """바깥 로프트(− 빼기: 이웃 쓸기 자리) − (열린 끝을 4 mm 늘린 같은 것을 구 r=t 로 침식) → 법선 두께 t 균일 (쓸기로 깎인 면도 t 를 따른다).
    안쪽을 0.01 밀어 둔다 — 속 비움 면과 정확히 맞닿는 모서리(STL 면 4 장)를 막는다."""
    ext = ([(secs[0][0] - 4.0,) + tuple(secs[0][1:])] if not 아래닫 else []) + list(secs) + ([(secs[-1][0] + 4.0,) + tuple(secs[-1][1:])] if not 위닫 else [])
    바깥 = 로프트(secs); 늘림 = 로프트(ext)
    if 빼기 is not None: 바깥 = 바깥 - 빼기; 늘림 = 늘림 - 빼기
    안 = 늘림.minkowski_difference(mf.Manifold.sphere(t, 16)).translate((0.007, 0.011, 0.013))
    return 바깥, 안

# ── 치수 (원화에서 읽은 것 · 골격 척도로 환산: z, 반폭 w, 앞 yf, 뒤 yb, 앞모따기 cf, 뒤모따기 cb, 용골 k) ─────────
SX = 0.342 / 0.3243                            # 1바퀴 치수(가로 0.3243 척도)를 골격 척도로
def SY(y): return 1.0325 * y - 0.52
def 재척도(secs): return [(z, w * SX, SY(yf), SY(yb), cf, cb, k) for z, w, yf, yb, cf, cb, k in secs]
# 가슴 = 앞 두 면 + 용골(k ≈ 0.29 w · 앞면 수평각 ≈ 16°) · 3바퀴: 등 z 224~234 를 3~4 앞으로 · 앞 z 227~236 을 3 앞으로
가슴S = 재척도([(222.0, 13.0, 12.0, 34.5, 3, 4, 0.0),
        (223.5, 14.0, 10.0, 36.5, 3, 5, 0.0),
        (227.0, 17.5, -5.5, 39.5, 3, 6, 3.0),
        (231.0, 22.0, -9.5, 42.0, 3, 6, 5.5),
        (236.0, 27.5, -9.0, 45.0, 2, 7, 8.0),
        (252.0, 28.0, -8.0, 46.0, 2, 7, 8.0),
        (257.0, 28.0, -2.0, 46.0, 3, 7, 6.0),
        (265.0, 26.5, 6.5, 44.0, 4, 6, 3.0)])
복부S = 재척도([(200.5, 14.5, 2.5, 28.5, 4, 3, 0.0),         # 3바퀴: 앞면을 뒤로 — 혀(가슴에 붙음)가 앞숙임 때 지나가는 자리 · 아래는 J2 복부허리 둘레 벽 1.2 확보
        (205.0, 14.5, 2.5, 28.5, 4, 3, 0.0),
        (212.0, 12.0, 2.8, 27.0, 4, 3, 0.0),
        (220.0, 13.5, 1.5, 29.0, 4, 3, 0.0),
        (222.3, 14.5, 1.5, 29.0, 4, 3, 0.0)])
벨트S = 재척도([(189.0, 22.0, -1.0, 33.0, 3, 3, 0.0),
        (196.0, 22.0, -1.0, 33.0, 3, 3, 0.0),
        (199.5, 17.0, 1.0, 31.0, 3, 3, 0.0)])
def 판단면(tab, 두께, 뒤한, 앞=True, cf=1.5, k=1.0):
    out = []; 뒤한 = SY(뒤한)
    for z, w, y in tab:
        w, y = w * SX, SY(y)
        if 앞: yf, yb = y, min(y + 두께, 뒤한)
        else: yb, yf = y, max(y - 두께, 뒤한)
        c = min(cf, w / 3)
        out.append((z, w, yf, yb, c if 앞 else 0.4, 0.4 if 앞 else c, k if 앞 else 0.0))
    return out
혀S = 판단면([(204.5, 0.6, -3.5), (219.0, 5.0, -6.3), (226.0, 8.5, -7.3), (231.5, 12.0, -8.3)], 7.0, -0.2, k=1.0)   # 3바퀴: 가슴앞과 한 몸 · 윗단 z 231.5
앞치마S = 판단면([(152.5, 0.6, -3.0), (160.0, 3.0, -5.0), (170.0, 6.0, -6.5), (183.0, 9.0, -8.0), (193.0, 10.0, -4.5)], 3.5, -1.3, k=1.2)
뒤치마S = 판단면([(172.5, 0.6, 36.5), (177.0, 7.0, 37.5), (190.0, 20.5, 38.5), (197.5, 17.5, 37.8)], 3.8, 33.4, 앞=False)   # 3바퀴: 아랫단 3 mm 올림
Y가슴 = 19.6; Y복부 = 14.7; Y벨트 = 15.0

# ── 속 비움(keepout) ────────────────────────────────────────────────
def 쓸기_축(조각들, p, a, 각들):
    out = []
    for m in 조각들:
        cs = [돌려(m, p, a, t) for t in 각들]
        out += [mf.Manifold.batch_hull([c0, c1]) for c0, c1 in zip(cs[:-1], cs[1:])]
    return out
def 쓸기_볼(조각들, p, 범위, 비틀=0):           # 볼: x·y 범위 모서리 자세 hull · 비틀기는 그 hull 을 z 로 다시 쓸기
    xs = [범위[0][0], 0, 범위[0][1]]; ys = [범위[1][0], 0, 범위[1][1]]
    out = []
    for m in 조각들:
        h = mf.Manifold.batch_hull([돌려(돌려(m, p, (1, 0, 0), ax), p, (0, 1, 0), ay) for ax in xs for ay in ys])
        out += 쓸기_축([h], p, (0, 0, 1), 각격자(-비틀, 비틀, 10)) if 비틀 else [h]
    return out
def 범위(n, i=0): r = JT[n]["범위"][i]; return r["축"], r["최소"], r["최대"]
def 각격자(lo, hi, st=7.5): return list(np.linspace(lo, hi, max(2, int(np.ceil((hi - lo) / st)) + 1)))
def 볼범위(n): r = JT[n]["범위"]; return [(r[0]["최소"], r[0]["최대"]), (r[1]["최소"], r[1]["최대"])], max(abs(r[2]["최소"]), abs(r[2]["최대"]))

log("속 비움 짓는 중 (뼈 실물 + J2 실물 + 0.3)")
K = {}; 정지 = {}
# 가슴 무리
정지["가슴"] = [뼈실물("가슴")] + J2("목아래", "부모") + J2("가슴복부", "자식") + J2("L어깨스윙", "부모") + J2("R어깨스윙", "부모")
r목, t목 = 볼범위("목아래")
목 = 쓸기_볼(뼈조각("목", 0.3) + J2("목아래", "자식") + J2("목위", "부모") + J2("목위", "자식"), JT["목아래"]["피벗mm"], r목, t목)
어깨 = []
for s in "LR":
    j21 = JT[s + "어깨회전"]; p21 = np.array(j21["피벗mm"]); a21 = np.array(j21["축"])
    blk = np.asarray(뼈STL(s + "어깨블록").vertices); d = blk - p21; t_ = d @ a21; rad = np.linalg.norm(d - np.outer(t_, a21), axis=1).max() + 0.3
    봉투 = 원통(p21 + a21 * max(t_.min(), 0.0), p21 + a21 * (t_.max() + 0.3), rad)          # 어깨블록 = 회전축 둘레 봉투(회전 ±180)
    들기 = J2(s + "어깨들기", "부모")
    for q in 들기:                                                                            # 들기 부모 부품도 회전축 둘레 봉투
        v = np.asarray(메시(q)[0]); dd = v - p21; tt = dd @ a21; rr = np.linalg.norm(dd - np.outer(tt, a21), axis=1).max()
        봉투 = 봉투 + 원통(p21 + a21 * tt.min(), p21 + a21 * tt.max(), rr)
    ax, lo, hi = 범위(s + "어깨스윙")
    어깨 += 쓸기_축(뼈조각(s + "어깨축", 0.3) + J2(s + "어깨스윙", "자식") + J2(s + "어깨회전", "부모") + J2(s + "어깨회전", "자식") + [봉투],
                 JT[s + "어깨스윙"]["피벗mm"], ax, 각격자(lo, hi))
r3, t3 = 볼범위("가슴복부"); r3i = [(-r3[0][1], -r3[0][0]), (-r3[1][1], -r3[1][0])]      # 복부 쪽이 가슴에 대해 도는 것 = 역범위
배밑 = 쓸기_볼(뼈조각("복부", 0.3) + J2("가슴복부", "부모") + J2("복부허리", "자식"), JT["가슴복부"]["피벗mm"], r3i, t3)
K["가슴"] = 정지["가슴"] + 목 + 어깨 + 배밑
# 복부 무리
정지["복부"] = [뼈실물("복부")] + J2("가슴복부", "부모") + J2("복부허리", "자식")
위가슴 = 쓸기_볼(뼈조각("가슴", 0.3)[:1] + J2("가슴복부", "자식"), JT["가슴복부"]["피벗mm"], r3, t3)
ax4, lo4, hi4 = 범위("복부허리")
허리돌 = 쓸기_축(뼈조각("허리", 0.3) + J2("복부허리", "부모") + J2("L고관절벌림", "부모") + J2("R고관절벌림", "부모"), JT["복부허리"]["피벗mm"], ax4, 각격자(lo4, hi4))
K["복부"] = 정지["복부"] + 위가슴 + 허리돌
# 허리 무리(벨트)
정지["허리"] = [뼈실물("허리")] + J2("복부허리", "부모") + J2("L고관절벌림", "부모") + J2("R고관절벌림", "부모")
배돌 = 쓸기_축(뼈조각("복부", 0.3) + J2("복부허리", "자식") + J2("가슴복부", "부모"), JT["복부허리"]["피벗mm"], ax4, 각격자(lo4, hi4))
다리 = []; 다리정 = []
for s in "LR":
    p5 = JT[s + "고관절벌림"]["피벗mm"]; a5, l5, h5 = 범위(s + "고관절벌림")
    p7 = JT[s + "고관절"]["피벗mm"]; a7, l7, h7 = 범위(s + "고관절")
    블록 = 뼈조각(s + "고관절블록", 0.3) + J2(s + "고관절벌림", "자식") + J2(s + "고관절", "부모") + J2(s + "고관절", "핀")
    허벅 = 뼈조각(s + "허벅지위", 0.3) + J2(s + "고관절", "자식") + J2(s + "허벅지회전", "부모")
    다리정 += 블록 + 허벅 + 뼈조각(s + "허벅지", 0.3)
    g5 = 각격자(l5, h5, 11); g7 = 각격자(l7, h7, 15)
    for m in 블록: 다리 += 쓸기_축([m], p5, a5, g5)
    for m in 허벅:
        for t5 in g5:
            다리 += [mf.Manifold.batch_hull([돌려(돌려(m, p7, a7, c0), p5, a5, t5), 돌려(돌려(m, p7, a7, c1), p5, a5, t5)]) for c0, c1 in zip(g7[:-1], g7[1:])]
K["허리"] = 정지["허리"] + 배돌 + 다리
K["치마"] = 정지["허리"] + 다리정
KM = {k: 합(v).translate((0.017, 0.023, 0.031)) for k, v in K.items()}   # 0.03 흔들기: 껍질 안쪽 면과 정확히 맞닿는 모서리(STL 면 4 장) 방지 (틈 0.3 안)
def J2실물또는껍질(n, 역할):
    out = []
    for f in sorted(glob.glob(os.path.join(J2D, "관절_%s_%s*.stl" % (n, 역할)))):
        t = STL(f); out.append(만(t) if t.is_watertight else 껍질점(t.vertices, 0.0))
    return out
KJ2 = {}                                          # 핀이 닿으면 안 되는 것 = 정지 J2 실물(껍질 아님) + 이웃 쓸기 (뼈 실물은 뺌 — 핀은 뼈 구멍에 들어간다)
KJ2["가슴"] = 합(J2실물또는껍질("목아래", "부모") + J2실물또는껍질("가슴복부", "자식") + J2실물또는껍질("L어깨스윙", "부모") + J2실물또는껍질("R어깨스윙", "부모") + 목 + 어깨 + 배밑)
KJ2["복부"] = 합(J2실물또는껍질("가슴복부", "부모") + J2실물또는껍질("복부허리", "자식") + 위가슴 + 허리돌)
KJ2["허리"] = 합(J2실물또는껍질("복부허리", "부모") + J2실물또는껍질("L고관절벌림", "부모") + J2실물또는껍질("R고관절벌림", "부모") + 배돌 + 다리)
log("속 비움 조각", {k: len(v) for k, v in K.items()})

class 안검사:                                  # 볼록 조각들 안인 점? (다보 자리 찾기용 · 정지 실물은 껍질로 근사)
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

# ── 뼈 결합 자리 (관절.json 「장갑구멍」 또는 기본) ─────────────────────────
def 뼈축(n, z):                                # 뼈 STL 의 x=0 근처 · 높이 z 근처 정점 평균 = 축 위 점
    v = np.asarray(뼈STL(n).vertices); w = v[(np.abs(v[:, 2] - z) < 2.5) & (np.abs(v[:, 0]) < 4)]
    if len(w) == 0: w = v[np.abs(v[:, 2] - z) < 6]
    return np.array([0.0, float(w[:, 1].mean()), z]), 0.0
def 뼈겉점(n, p, d):                            # 뼈 STL 겉에서 p 를 지나 d 방향으로 나가는 점 (p 에서 d 쪽으로 가장 먼 겉점 · 없으면 p)
    tm = 뼈STL(n); loc, _, _ = tm.ray.intersects_location([np.asarray(p, float) - 20 * np.asarray(d, float)], [np.asarray(d, float)], multiple_hits=True)
    if len(loc) == 0: return np.asarray(p, float)
    return loc[np.argmax(loc @ np.asarray(d, float))]
def 기본구멍():
    """J1 「장갑구멍」이 없거나 못 쓸 때의 기본 자리: 뼈 겉점 · 방향(뼈 → 장갑 벽) · 무리."""
    L = []
    for z in (230.0, 238.0):
        c, _ = 뼈축("가슴", z); L.append(dict(뼈="가슴", 입구mm=뼈겉점("가슴", c, (0, 1, 0)), 방향=(0, 1, 0), 무리="가슴", 쪽="뒤"))
    c, _ = 뼈축("복부", 209.4)
    L.append(dict(뼈="복부", 입구mm=뼈겉점("복부", c, (0, -1, 0)), 방향=(0, -1, 0), 무리="복부", 쪽="앞"))
    L.append(dict(뼈="복부", 입구mm=뼈겉점("복부", c, (0, 1, 0)), 방향=(0, 1, 0), 무리="복부", 쪽="뒤"))
    for sx in (-1, 1):                             # 허리: 가운데(x 0)는 J2 복부허리 부모 자리라 뼈가 없다 → J1 구멍처럼 x ±9 (고관절 팔 위)
        c = np.array([sx * 7.3, 13.0, 194.0])           # x 9 면 핀이 R고관절벌림 부모(x ≥ 9.5)에 0.2 mm³ 닿는다
        for d, 쪽 in (((0, -1, 0), "앞"), ((0, 1, 0), "뒤")):
            q = 뼈겉점("허리", c, d)
            if np.linalg.norm(q - c) > 0.5: L.append(dict(뼈="허리", 입구mm=q, 방향=d, 무리="허리", 쪽=쪽))
    for e in L: e["출처"] = "기본"
    return L
def J1구멍():
    """관절.json 뼈[n]["장갑구멍"]: 위치mm = 뼈 겉 구멍 입구 · 방향 = 뼈 속으로(핀이 들어가는 방향) · 지름 2.2 · 깊이 3 (J1 3바퀴 · 뼈 STL 에 이미 뚫려 있음)."""
    L = []
    for n in ("가슴", "복부", "허리"):
        for e in BONE[n].get("장갑구멍", []):
            d = -np.asarray(e["방향"], float); d /= np.linalg.norm(d)          # 밖 = 뼈 → 장갑
            L.append(dict(뼈=n, 입구mm=np.asarray(e["위치mm"], float), 방향=d, 무리=n, 쪽="앞" if d[1] < 0 else "뒤", 지름=e.get("지름", 2.2), 깊이=e.get("깊이", 3.0)))
    return L
구멍목록 = J1구멍() if J1구멍있음 else 기본구멍()
구멍출처 = "관절.json 뼈.장갑구멍(J1 3바퀴)" if J1구멍있음 else "기본 자리(이 파일)"
log("뼈 결합 자리", 구멍출처, len(구멍목록))

# ── 부품 짓기 ─────────────────────────────────────────────────────
부품 = {}; 정보 = {}; 키트 = {"뼈구멍": [], "설명": ""}
def 반쪽(m, y, 앞): return m.trim_by_plane((0, -1, 0), -y) if 앞 else m.trim_by_plane((0, 1, 0), y)
def 원점찾기(씨, 무리, 반지름, y0, y1, 안쪽):
    for d in np.linspace(0, 4, 17):
        for ang in np.linspace(0, 2 * np.pi, 13)[:-1] if d > 0 else [0]:
            x, z = 씨[0] + d * np.cos(ang), 씨[1] + d * np.sin(ang)
            t = np.linspace(0, 2 * np.pi, 16, endpoint=False)
            P = np.array([[x + (반지름 + 0.4) * np.cos(a), yy, z + (반지름 + 0.4) * np.sin(a)] for a in t for yy in np.linspace(y0, y1, 6)] + [[x, yy, z] for yy in np.linspace(y0, y1, 6)])
            if not INK[무리](P).any() and 안쪽(np.array([[x, (y0 + y1) / 2, z]])):
                return float(x), float(z)
    return None
def 로프트안(secs):
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
핀D, 핀L, 구멍D, 구멍L, 보스D = 2.0, 3.0, 2.2, 3.0, 5.0
def 모서리이음(secs):
    """4바퀴(원형사 교본 분할 규칙 3 · 「이음매는 안 보이는 곳」): 옆면 한가운데 평면 대신 앞면 ↔ 옆면 모서리 선 y(z) = yf + k + cf 를 따라 가른다."""
    zs, ys = [], []
    for z, w, yf, yb, cf, cb, k in secs:
        cf_ = min(cf, 0.45 * w, 0.45 * (yb - yf)); k_ = min(k, 0.4 * (yb - yf)); zs.append(z); ys.append(yf + k_ + cf_ + 1.0)   # 모서리에서 옆면 쪽 1 mm — 모서리를 정확히 지나면 앞판 끝이 칼날(벽<1.2 23%)
    zs, ys = np.array(zs), np.array(ys); o = np.argsort(zs); zs, ys = zs[o], ys[o]
    return lambda z: float(np.interp(z, zs, ys))
def 이음영역(이음, z0, z1):
    """y < 이음(z) 인 앞 영역: (y, z) 다각형을 x 로 민 기둥."""
    zz = np.linspace(z0 - 30.0, z1 + 30.0, 121)
    poly = [(-200.0, zz[0])] + [(이음(z), z) for z in zz] + [(-200.0, zz[-1])]
    q = np.asarray(poly, float); a = 0.5 * np.sum(q[:, 0] * np.roll(q[:, 1], -1) - np.roll(q[:, 0], -1) * q[:, 1])
    cs = mf.CrossSection([(q if a > 0 else q[::-1]).tolist()])
    return cs.extrude(400.0).transform([[0, 0, 1, -200.0], [1, 0, 0, 0], [0, 1, 0, 0]])
def 앞뒤블록(이름, secs, ysplit, 무리, 위닫, 아래닫, 다보씨, 추가빼기=None, 이음=None):
    """앞뒤 반쪽 블록: 껍질 + 다보 기둥 + 뼈 결합 보스 − 속 비움 → 반쪽 나눔 + 다보 핀 · 구멍 + 뼈 핀. 이음(z) 가 있으면 그 선으로 가른다."""
    바깥, 안 = 껍질(secs, 2.0, 위닫, 아래닫, 추가빼기)
    몸 = 바깥 - 안
    y_lo = min(s[2] for s in secs) - 5; y_hi = max(s[3] for s in secs) + 5
    다보 = []
    for 씨 in 다보씨:                              # 씨앗을 차례로 시도 · 두 쌍이면 그만
        if len(다보) >= 4: break
        q = 원점찾기(씨, 무리, 2.5, y_lo + 5, y_hi - 5, 로프트안(secs))
        if q is None: log("  !! 다보 자리 없음", 이름, 씨); continue
        if any(abs(q[1] - z) < 6 and abs(abs(q[0]) - abs(x)) < 6 for x, z in 다보): continue
        for sx in (1, -1): 다보.append((sx * abs(q[0]), q[1]))
    몸 = 몸 + (합([원통((x + 0.011, y_lo, z + 0.017), (x + 0.011, y_hi, z + 0.017), 2.5, 36) for x, z in 다보]) ^ 바깥)
    결합 = []
    for e in [e for e in 구멍목록 if e["무리"] == 무리] + [e for e in 기본구멍() if e["무리"] == 무리]:
        p = np.asarray(e["입구mm"], float); dv = np.asarray(e["방향"], float)
        보스 = 원통(p + 0.3 * dv + (0.011, 0.007, 0.013), p + 60 * dv, 보스D / 2, 36) ^ 바깥
        남 = 보스 - KM[무리]                          # 속 비움(뼈 · J2 + 0.3)을 뺀 뒤에도 뼈 구멍 앞까지 이어져야 쓸 수 있다
        핀검 = 원통(p - (핀L - 0.3) * dv, p + 0.9 * dv, 핀D / 2 + 0.15, 24)
        if 보스.is_empty() or 남.volume() < 0.85 * 보스.volume() or (남 ^ 구(p + 0.9 * dv, 1.3)).is_empty() or (보스 ^ 안).volume() < 1.0            or (핀검 ^ KJ2[무리]).volume() > 0.05:
            if e.get("출처", "") != "기본": log("  !! 뼈 구멍 못 씀(속 비움 충돌 · 부품 밖)", 이름, e["뼈"], np.round(p, 1), "→ 기본 자리로"); 
            continue
        if any(np.linalg.norm(p - np.asarray(q["입구mm"])) < 4 for q in 결합) or sum(q["쪽"] == e["쪽"] for q in 결합) >= 2: continue
        결합.append(e); 몸 = 몸 + 보스
    몸 = 몸 - KM[무리]
    if 이음 is None:
        앞 = 반쪽(몸, ysplit, True); 뒤 = 반쪽(몸, ysplit, False); 이음 = lambda z: ysplit
    else:
        zz_ = [s_[0] for s_ in secs]; 영 = 이음영역(이음, min(zz_), max(zz_)); 앞 = 몸 ^ 영; 뒤 = 몸 - 영
    for x, z in 다보:
        yq = 이음(z)
        앞 = 앞 + 원통((x, yq - 0.5, z), (x, yq + 2.5, z), 1.0, 24)
        뒤 = 뒤 - 원통((x, yq - 0.1, z), (x, yq + 3.0, z), 1.2, 24)
    for e in 결합:                                # 핀 Ø2.0 × 3.0: 보스 끝(뼈 겉 +0.3)에서 뼈 구멍 속으로 (뼈 구멍 Ø2.2 × 3)
        p = np.asarray(e["입구mm"], float); dv = np.asarray(e["방향"], float)
        pin = 원통(p - (핀L - 0.3) * dv, p + 0.9 * dv, 핀D / 2, 24)
        if e["쪽"] == "앞": 앞 = 앞 + pin
        else: 뒤 = 뒤 + pin
        키트["뼈구멍"].append(dict(부품=이름 + e["쪽"], 뼈=e["뼈"], 입구mm=[round(float(v), 2) for v in p], 방향_뼈속=[round(float(v), 3) for v in -dv],
                                 구멍지름=구멍D, 깊이=구멍L, 핀="장갑 보스 핀 Ø%.1f × %.1f (뼈 겉에서 0.3 틈)" % (핀D, 핀L),
                                 출처="J1 장갑구멍(뼈에 이미 뚫림)" if e.get("출처") != "기본" else "기본 자리 — J1 에 구멍 요청"))
    정보[이름 + "앞"] = dict(다보=[dict(xz=[round(x, 2), round(z, 2)], 이음y=ysplit, 핀="Ø2.0×2.5(앞 반쪽)", 구멍="Ø2.4×3.0(뒤 반쪽) — 한쪽 0.20") for x, z in 다보],
                         뼈결합=[dict(뼈=e["뼈"], 입구mm=[round(float(v), 2) for v in e["입구mm"]]) for e in 결합 if e["쪽"] == "앞"])
    정보[이름 + "뒤"] = dict(다보=정보[이름 + "앞"]["다보"], 뼈결합=[dict(뼈=e["뼈"], 입구mm=[round(float(v), 2) for v in e["입구mm"]]) for e in 결합 if e["쪽"] == "뒤"])
    return 앞, 뒤, 바깥

# 머리 쓸기 (D3 투구·얼굴 실메시를 목위 볼 둘레로 돌린 hull 쌍 합) · 혀 ↔ 가슴 서로 쓸기
log("가슴")
목구멍 = 상자((-11.8 * SX, SY(5.0), 256.0), (11.8 * SX, SY(33.0), 270.0))
머리점 = np.vstack([STL(os.path.join(D3, n + ".stl")).vertices for n in ("투구앞", "투구뒤", "얼굴") if os.path.exists(os.path.join(D3, n + ".stl"))])
머리껍질 = 껍질점(머리점[머리점[:, 2] < 285.0], 0.5)
p2 = JT["목위"]["피벗mm"]
def 머리자세(m, ax_, ay_, az_): return 돌려(돌려(돌려(m, p2, (0, 0, 1), az_), p2, (0, 1, 0), ay_), p2, (1, 0, 0), ax_)
_xs, _ys, _zs = [-25, -12.5, 0, 10, 20], [-15, 0, 15], [-30, -15, 0, 15, 30]
머리쓸기 = []
for ay_ in _ys:
    for ax_ in _xs:
        cs_ = [머리자세(머리껍질, ax_, ay_, az_) for az_ in _zs]; 머리쓸기 += [mf.Manifold.batch_hull([a, b]) for a, b in zip(cs_[:-1], cs_[1:])]
    for az_ in _zs:
        cs_ = [머리자세(머리껍질, ax_, ay_, az_) for ax_ in _xs]; 머리쓸기 += [mf.Manifold.batch_hull([a, b]) for a, b in zip(cs_[:-1], cs_[1:])]
머리쓸기M = 합(머리쓸기)
p3 = JT["가슴복부"]["피벗mm"]
def 토막들(secs, pad):
    out = []
    for a_, b_ in zip(secs[:-1], secs[1:]):
        qa, qb = 오프(단면점(*a_[1:]), pad), 오프(단면점(*b_[1:]), pad)
        out.append(mf.Manifold.hull_points(np.vstack([np.c_[qa, np.full(len(qa), a_[0])], np.c_[qb, np.full(len(qb), b_[0])]]).tolist()))
    return out
def 볼쓸기전부(조각, p, rx, ry, rz, st=2.5):        # 세 축 각각의 쓸기 합(각 축 따로 도는 자세를 다 덮음)
    out = []
    for ax_, (lo_, hi_) in (((1, 0, 0), rx), ((0, 1, 0), ry), ((0, 0, 1), rz)):
        out += 쓸기_축(조각, p, ax_, 각격자(lo_, hi_, st))
    return out
혀쓸기M = 합(볼쓸기전부(토막들(혀S, 0.6), p3, (-15, 20), (-15, 15), (-30, 30)))          # 혀(가슴에 붙음 · +엠블럼 0.4 + 틈)가 복부에 대해 도는 자리
가슴쓸기M = 합(볼쓸기전부(토막들(가슴S, 0.6)[:5], p3, (-15, 20), (-15, 15), (-30, 30)))   # 가슴 아래가 복부 · 혀에 대해 도는 자리
가슴앞, 가슴뒤, 가슴바깥 = 앞뒤블록("가슴", 가슴S, Y가슴, "가슴", True, False, [(-23.2, 240.0), (-19.5, 233.0), (-20.0, 229.0), (-21.0, 259.0), (-18.0, 262.0)], 목구멍 + 머리쓸기M,
                          이음=모서리이음(가슴S))   # 4바퀴: 옆면 가운데(y 19.6) 평면 → 앞 모서리 선
log("복부")
복부앞, 복부뒤, 복부바깥 = 앞뒤블록("복부", 복부S, Y복부, "복부", True, True, [(-9.9, 204.5), (-9.9, 214.0), (-8.0, 219.0)], 가슴쓸기M + 혀쓸기M, 이음=모서리이음(복부S))
log("벨트")
벨트앞, 벨트뒤, 벨트바깥 = 앞뒤블록("벨트", 벨트S, Y벨트, "허리", True, True, [(-17.5, 194.0)], 이음=모서리이음(벨트S))

# 스커트 힌지 (1.75 필라멘트 핀 · 축 · 러그 · 핀 끝 모두 벨트 안)
R너클 = 2.2
def 핀구멍(c, a, t0, t1, d): c = np.asarray(c, float); a = np.asarray(a, float); return 원통(c + a * t0, c + a * t1, d / 2, 24)
yF = 벨트S[0][2]; yB = 벨트S[0][3]
축앞 = ((0, yF + 2.4, 195.0), (1, 0, 0)); 축뒤 = ((0, yB - 2.4, 196.0), (1, 0, 0))
for 이름_, (c_, a_), 쪽_ in (("앞", 축앞, -1), ("뒤", 축뒤, 1)):
    c_ = np.array(c_, float); r_ = R너클 + 0.4
    y0_, y1_ = sorted([c_[1] + 쪽_ * 8, c_[1] - 쪽_ * r_])
    홈_ = 상자((-6.3, y0_, 189.5), (6.3, y1_, c_[2] + r_))
    ly0, ly1 = sorted([c_[1] - 쪽_ * r_, c_[1] + 쪽_ * 4])
    러그_ = 합([상자((6.3, ly0, c_[2] - r_), (9.5, ly1, c_[2] + r_)), 상자((-9.5, ly0, c_[2] - r_), (-6.3, ly1, c_[2] + r_))]) ^ 벨트바깥
    if 이름_ == "앞": 벨트앞 = (벨트앞 + (러그_ - KM["허리"])) - 홈_ - 핀구멍(c_, a_, -9.0, 9.0, 1.75)
    else: 벨트뒤 = (벨트뒤 + (러그_ - KM["허리"])) - 홈_ - 핀구멍(c_, a_, -9.0, 9.0, 1.75)

log("스커트 · 뿔 · 혀 · 목깃")
def 힌지스커트(secs, 축, 웹상자, 앞):
    m = 로프트(secs); c_ = np.array(축[0], float); 너클 = 원통(c_ + (-6.0, 0, 0), c_ + (6.0, 0, 0), R너클)
    m = m + 너클 + mf.Manifold.batch_hull([너클, 상자(*웹상자)])
    return m - 핀구멍(*축, -7, 7, 1.95)
앞치마 = 힌지스커트(앞치마S, 축앞, ((-6.0, 앞치마S[-1][3] - 2.0, 190.8), (6.0, 앞치마S[-1][3], 192.8)), True)
뒤치마 = 힌지스커트(뒤치마S, 축뒤, ((-6.0, 뒤치마S[-1][2], 192.0), (6.0, 뒤치마S[-1][2] + 2.0, 194.0)), False)
# 옆 스커트는 허벅지 윗단 장갑에 붙였다(디자인_다리.py 4바퀴) — 벨트 힌지 첫 판은 팔이 막대로 보이고 벌림 45° 에 걸렸다
# 허리 금 뿔: 각진 뿔(초승달 · 사각 밑동 → 납작 능선 → 끝) · 벨트 옆에 핀 Ø2
def 뿔(sx):
    wB = 벨트S[0][1]; yc = SY(15.0)
    밑 = 상자((wB, yc - 5.0, 192.0), (wB + 3.2, yc + 5.0, 197.5))
    중 = mf.Manifold.hull_points([(wB - 0.6, yc - 2.6, 203.0), (wB + 3.8, yc - 2.6, 203.0), (wB - 0.6, yc + 2.6, 203.0), (wB + 3.8, yc + 2.6, 203.0),
                                  (wB + 1.6, yc - 0.8, 205.5), (wB + 1.6, yc + 0.8, 205.5)])
    끝 = mf.Manifold.hull_points([(wB + 1.6, yc - 0.6, 210.5), (wB + 1.6, yc + 0.6, 210.5), (wB + 2.2, yc, 210.8), (wB + 1.0, yc, 210.8)])
    m = mf.Manifold.batch_hull([밑, 중]) + mf.Manifold.batch_hull([중, 끝])
    m = m + 원통((wB + 0.5, yc, 194.5), (wB - 2.4, yc, 194.5), 1.0, 24)
    return m if sx > 0 else m.mirror((1, 0, 0))
뿔L = 뿔(-1); 뿔R = 뿔(1)
for sx in (-1, 1):
    h_ = 원통((sx * (벨트S[0][1] + 0.5), SY(15.0), 194.5), (sx * (벨트S[0][1] - 3.0), SY(15.0), 194.5), 1.2, 24)
    벨트앞 = 벨트앞 - h_; 벨트뒤 = 벨트뒤 - h_
정보["허리금뿔"] = dict(결합="벨트 옆벽(이음 y=15 위)에 핀 Ø2.0 (구멍 Ø2.4 관통) · 앞/뒤 반쪽이 반씩 문다")
# 혀(가슴 아래 가운데 판): 3바퀴부터 **가슴앞과 한 몸**(원화에서 흰 판은 가슴에서 내려온다 · 복부는 검정 속) — 핀 · 틈 없음 · 앞숙임은 복부 앞면을 뒤로 물려 확보
혀 = 로프트(혀S) - KM["가슴"]
정보["혀(가슴 아래 판)"] = dict(결합="가슴앞과 한 몸(2바퀴까지는 복부 핀) · 엠블럼 한 몸(원판 Ø6 · 0.4 솟음 · 둘레 홈 0.5)")
def 앞면띠(polys, 바깥secs, d_in, d_out, 여유=0.0, 쪽=(-1, -Y가슴)):   # 정면 다각형(들)을 y 로 밀어 겉 띠(d_in ~ d_out)와 교차
    if not isinstance(polys, list) or not isinstance(polys[0], (list, tuple, np.ndarray)) or np.ndim(polys[0]) == 1: polys = [polys]
    cs = None
    for q in polys:
        q = np.asarray(q, float); c1 = mf.CrossSection([q.tolist()])
        if c1.area() <= 0: c1 = mf.CrossSection([q[::-1].tolist()])
        cs = c1 if cs is None else cs + c1
    if 여유: cs = cs.offset(여유, mf.JoinType.Miter)
    pr = cs.extrude(80).transform([[1, 0, 0, 0], [0, 0, 1, -30], [0, 1, 0, 0]])
    # 단면 오프셋은 수평이라 앞면이 z 로 기운 곳(가슴 위 z 252→265 · 50°)은 법선 두께가 cos 배로 얇아진다 → 단면마다 1/cos 로 키운다
    zs_ = np.array([q[0] for q in 바깥secs]); yy = np.array([q[2] if 쪽[0] < 0 else q[3] for q in 바깥secs]); sc = []
    for i in range(len(zs_)):
        sl = 0.0
        for j in (i - 1, i + 1):
            if 0 <= j < len(zs_): sl = max(sl, np.arctan2(abs(yy[j] - yy[i]), abs(zs_[j] - zs_[i])))
        sc.append(min(1.0 / np.cos(sl), 2.2))
    띠 = 로프트(바깥secs, [d_out * c for c in sc]) - 로프트(바깥secs, [d_in * c for c in sc])
    return pr ^ 띠 ^ 반공간((0, 쪽[0], 0), 쪽[1])
원 = [(3.0 * np.cos(t), 222.0 + 3.0 * np.sin(t)) for t in np.linspace(0, 2 * np.pi, 33)[:-1]]
원홈 = [(3.5 * np.cos(t), 222.0 + 3.5 * np.sin(t)) for t in np.linspace(0, 2 * np.pi, 33)[:-1]]
# 4바퀴(09-26 겉모습 검토): 원화 엠블럼 = 금 테(r 3.2~4.5) + 파란 알 + 십자 가시(위 z 237 · 아래 224 · 좌우 x ±6) · 중심 (0, 231)
#   → 금 부품 하나(테 + 가시 + 알 돔 · 알은 파랑 도색) · 혀에 0.5 자리 홈 · 붙임
EC = (0.0, 222.5)   # 원화 231 은 가슴 아랫단(240) 9 mm 아래 — 모델 가슴 아랫단 231.5 기준으로 9 mm 아래(231 에 두니 가슴 턱에 반 가려 초승달)
def 둘레(r, n=40, c=EC): return [(c[0] + r * np.cos(t), c[1] + r * np.sin(t)) for t in np.linspace(0, 2 * np.pi, n + 1)[:-1]]
가시들 = [[(EC[0] + a, EC[1] + b) for a, b in q] for q in ([(-0.9, 4.0), (0.0, 6.2), (0.9, 4.0)], [(-0.9, -4.0), (0.0, -7.0), (0.9, -4.0)],
                                                        [(-4.0, 0.9), (-6.2, 0.0), (-4.0, -0.9)], [(4.0, 0.9), (6.2, 0.0), (4.0, -0.9)])]
테판 = [둘레(4.5)] + 가시들
엠블럼 = 앞면띠(테판, 혀S, -0.5, 1.0, 쪽=(-1, 5.0)) + 앞면띠([둘레(3.0)], 혀S, -0.5, 1.6, 쪽=(-1, 5.0))   # 쪽 y ≤ −5: 혀 뒷면(y ≈ −1.3)까지 잘려 두 조각이 됐다
혀 = 혀 - 앞면띠(테판, 혀S, -0.5, 1.0, 여유=0.12, 쪽=(-1, 5.0))
정보["가슴엠블럼"] = dict(결합="혀 0.5 자리 홈(틈 0.12)에 붙임", 색="금 · 가운데 알 파랑 도색", 지름=9.0)
가슴앞 = 가슴앞 + 혀
# 목깃: U(앞 트임) · 옆 날개 · 앞 경사 · 안쪽 = 머리 쓸기 밖
목깃겉 = [(-18.5 * SX, SY(7.0)), (18.5 * SX, SY(7.0)), (18.5 * SX, SY(34.5)), (15.5 * SX, SY(37.5)), (-15.5 * SX, SY(37.5)), (-18.5 * SX, SY(34.5))]
def 층(pts, z, d=0.0):
    q = 오프(pts, d); return np.c_[q, np.full(len(q), z)]
목깃 = mf.Manifold.hull_points(np.vstack([층(목깃겉, 265.0), 층(목깃겉, 270.5)]).tolist()) + \
       mf.Manifold.hull_points(np.vstack([층(목깃겉, 270.5), 층(목깃겉, 272.0, -1.5)]).tolist())
for sx in (-1, 1):                                   # 날개: z 265 → 276 · x 13~19.5 · 바깥으로 기욺 (원화 z 262~275 x ±12~17)
    날 = [(sx * 13.0, SY(8.0), 265.0), (sx * 19.5, SY(8.0), 265.0), (sx * 13.0, SY(28.0), 265.0), (sx * 19.5, SY(28.0), 265.0),
         (sx * 16.0, SY(10.0), 276.0), (sx * 20.5, SY(10.0), 276.0), (sx * 16.0, SY(24.0), 276.0), (sx * 20.5, SY(24.0), 276.0)]
    목깃 = 목깃 + mf.Manifold.hull_points(날)
목깃 = 목깃 - 상자((-11.8 * SX, 0.0, 262.0), (11.8 * SX, SY(33.0), 290.0))
n = np.array([0, -5.0, 8.0]); n /= np.linalg.norm(n)
목깃 = 목깃.trim_by_plane(tuple(-n), float(-n @ np.array([0, SY(7.0), 265.5])))
목깃 = 목깃 - KM["가슴"] - 머리쓸기M
for sx in (-1, 1):
    목깃 = 목깃 + 원통((sx * 16.0, SY(27.0), 262.5), (sx * 16.0, SY(27.0), 265.1), 1.0, 24)
    가슴뒤 = 가슴뒤 - 원통((sx * 16.0, SY(27.0), 261.5), (sx * 16.0, SY(27.0), 265.5), 1.2, 24)
정보["목깃"] = dict(결합="가슴뒤 윗면에 핀 Ø2.0 × 2 (구멍 Ø2.4 관통) · x ±16.0 y %.1f" % SY(27.0))

# ── 가슴 앞 테 판 + 파랑 줄 (원호 3 줄 + 바깥 끝 이음 갈비 = 한쪽 한 판 · 두께 1.4 · 홈 0.6 · 다보 1) ─────
def 파랑원호():
    a = np.array(Image.open(os.path.join(ART, "omega_front_clean.png")).convert("RGBA")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]; blue = (b - r > 35) & (b > 90) & (a[..., 3] > 128)
    from scipy import ndimage
    R_, C_ = np.mgrid[0:1024, 0:1024]; X = FRX(C_); Z = FRZ(R_)
    m = ndimage.binary_opening(blue & (Z > 232) & (Z < 264) & (np.abs(X) < 29.5), np.ones((2, 2)))
    lab, k = ndimage.label(m); 줄 = []
    for i in range(1, k + 1):
        w = lab == i
        if w.sum() < 25: continue
        P = np.c_[X[w], Z[w]]
        if P[:, 0].mean() > 0: P[:, 0] *= -1
        줄.append(P)
    최 = None
    for cx in np.arange(-10, 12.1, 1.0):
        for cz in np.arange(180, 240.1, 1.0):
            e = sum(np.std(np.hypot(P[:, 0] - cx, P[:, 1] - cz)) * len(P) for P in 줄)
            if 최 is None or e < 최[0]: 최 = (e, cx, cz)
    _, cx, cz = 최
    띠들 = []
    for P in 줄:
        rr = np.hypot(P[:, 0] - cx, P[:, 1] - cz); th = np.arctan2(P[:, 1] - cz, P[:, 0] - cx)
        띠들.append((float(np.median(rr)), float(np.percentile(rr, 85) - np.percentile(rr, 15)), float(np.percentile(th, 3)), float(np.percentile(th, 97))))
    띠들.sort(); 합친 = []
    while 띠들:
        a0 = 띠들.pop(0)
        j = min(range(len(띠들)), key=lambda j: abs(띠들[j][0] - a0[0])) if 띠들 else None
        if j is not None and abs(띠들[j][0] - a0[0]) < 2.0:
            b0 = 띠들.pop(j); a0 = tuple((u + v) / 2 for u, v in zip(a0, b0))
        합친.append(a0)
    return cx, cz, 합친
cx, cz, 원호들 = 파랑원호()
원호들 = sorted(sorted(원호들, key=lambda o: o[3] - o[2])[-4:])   # 4바퀴: 원화는 한쪽 4 줄 (3바퀴는 3 줄 + 가운데 이음 갈비 → 「キ」 로 읽혔다)
log("  파랑 원호 중심 (%.1f, %.1f) · 줄 %d · 반지름 %s" % (cx, cz, len(원호들), [round(o[0], 1) for o in 원호들]))
def 원호띠(rm, t, t0, t1):
    """끝으로 갈수록 가늘어지는 바나나 띠: 폭 = t · sin(π u)^0.6 (최소 1.2)."""
    ts = np.linspace(t0, t1, 24); u = (ts - t0) / (t1 - t0); w = np.maximum(t * np.sin(np.pi * u) ** 0.6, 2.4)   # 끝 최소 2.4 — 0.03 g 줄이 나왔다
    return [(cx + (rm + wi / 2) * np.cos(v), cz + (rm + wi / 2) * np.sin(v)) for v, wi in zip(ts, w)] +            [(cx + (rm - wi / 2) * np.cos(v), cz + (rm - wi / 2) * np.sin(v)) for v, wi in list(zip(ts, w))[::-1]]
파랑폴리 = [원호띠(rm, max(t, 3.6), t0, t1) for rm, t, t0, t1 in 원호들]
we = 가슴S[3][1] - 2.0
테 = [(-we, 236.5), (0.0, 231.5), (we, 236.5), (we, 256.0), (-we, 256.0)]
가슴앞 = (가슴앞 + 앞면띠(테, 가슴S, -0.5, 1.0, 쪽=(-1, -8.0))) - 머리쓸기M - KM["가슴"]
파랑 = {}
for sx, nm in ((1, "L"), (-1, "R")):           # 원호는 왼쪽(x<0)으로 접어 읽었다 → L 은 그대로
    옆한 = 상자((-25.0, -60, 200), (25.0, 60, 280))                     # 모따기(|x| > 27) 앞에서 끝
    for i, q in enumerate(파랑폴리):
        pl = [(sx * x, z) for x, z in q]
        판 = 앞면띠(pl, 가슴S, -1.2, 0.8, 쪽=(-1, -8.0)) ^ 옆한              # 두께 2.0 (자리 홈 1.2 + 겉 0.8) · 줄마다 따로 · 붙임
        가슴앞 = 가슴앞 - (앞면띠(pl, 가슴S, -1.2, 2.0, 여유=0.1, 쪽=(-1, -8.0)) ^ 상자((-25.1, -60, 200), (25.1, 60, 280)))
        파랑["%s%d" % (nm, i + 1)] = 판 - KM["가슴"]
# 등판(4바퀴 · 원화 뒤): 어깨뼈 판 둘(가운데 x 0 에서 V 로 만남) + 아래 육각 판 · 0.8 솟음 · 판 사이 0.8 틈이 곧 패널라인
어깨뼈L = [(-29.5, 247.5), (-29.5, 261.5), (-19.0, 265.5), (0.0, 259.0), (0.0, 250.5), (-9.5, 249.0), (-14.5, 244.5), (-16.0, 241.0)]
육각 = [(-9.0, 249.0), (9.0, 249.0), (14.0, 240.0), (10.0, 228.0), (-10.0, 228.0), (-14.0, 240.0)]
def 줄임(pts, d=0.4): return 오프(np.asarray(pts, float), -d).tolist()
등판들 = [줄임(어깨뼈L), 줄임([(-x, z) for x, z in 어깨뼈L][::-1]), 줄임(육각)]
가슴뒤 = 가슴뒤 + (앞면띠(등판들, 가슴S, -0.3, 0.8, 쪽=(1, Y가슴)) - KM["가슴"])
정보["등판"] = dict(설명="어깨뼈 판 2 + 육각 판 1 · 0.8 솟음 · 판 사이 0.8 틈", 근거="원화 뒤 (x, z) 꼭짓점")
정보["가슴파랑줄"] = dict(결합="가슴앞 0.6 자리 홈(틈 0.1)에 붙임 · 줄마다 따로", 두께=1.4, 줄=len(원호들))

# ── 패널라인 · 단차 ──────────────────────────────────────────────────
def 홈(부, secs, 경로들, 쪽, 단=((0.8, 0.17), (0.53, 0.34), (0.27, 0.5))):
    if not isinstance(경로들[0][0], (list, tuple)): 경로들 = [경로들]
    칼 = []
    for 경로 in 경로들:
        for (x0, z0), (x1, z1) in zip(경로[:-1], 경로[1:]):
            d = np.array([x1 - x0, z1 - z0]); d /= np.linalg.norm(d); nrm = np.array([-d[1], d[0]])
            for w, dep in 단:
                a = np.array([x0, z0]) - d * w / 2; b = np.array([x1, z1]) + d * w / 2
                칼.append(앞면띠([a + nrm * w / 2, b + nrm * w / 2, b - nrm * w / 2, a - nrm * w / 2], secs, -dep, 1.5, 쪽=쪽))
    return 부 - 합(칼)
log("패널라인")
가슴앞 = 홈(가슴앞, 가슴S, [(0.0, 233.5), (0.0, 255.0)], (-1, -8.0))
등판 = [[(0, 257.0), (10.0, 251.0), (10.0, 233.0), (0, 227.0), (-10.0, 233.0), (-10.0, 251.0)]]
for sx in (-1, 1):
    등판.append([(sx * 13.0, 259.0), (sx * 25.5, 259.0), (sx * 25.5, 243.0), (sx * 19.0, 236.5), (sx * 13.0, 242.5)])
가슴뒤 = (가슴뒤 + 앞면띠(등판, 가슴S, -0.5, 0.8, 쪽=(1, 30.0))) - KM["가슴"] - 머리쓸기M
앞치마 = 앞치마 + 앞면띠([(-6.5, 190.5), (6.5, 190.5), (3.8, 172.0), (0.0, 161.0), (-3.8, 172.0)], 앞치마S, -0.3, 0.6, 쪽=(-1, 0.0))
앞치마 = 홈(앞치마, 앞치마S, [[(-6.5, 192.2), (-1.0, 186.7)], [(6.5, 192.2), (1.0, 186.7)]], (-1, 0.0))
뒤치마 = 뒤치마 + 앞면띠([(-15.0, 194.5), (15.0, 194.5), (15.0, 187.0), (5.0, 178.0), (-5.0, 178.0), (-15.0, 187.0)], 뒤치마S, -0.3, 0.6, 쪽=(1, 34.5))
앞치마 = 앞치마 - KM["치마"]; 뒤치마 = 뒤치마 - KM["치마"]
벨트앞 = 홈(벨트앞, 벨트S, [[(-19.0, 192.5), (-8.0, 192.5)], [(8.0, 192.5), (19.0, 192.5)]], (-1, -5.0))

부품 = {"가슴앞": 가슴앞, "가슴뒤": 가슴뒤, "가슴엠블럼": 엠블럼, "목깃": 목깃, "복부앞": 복부앞, "복부뒤": 복부뒤,
       "허리벨트앞": 벨트앞, "허리벨트뒤": 벨트뒤, "허리V스커트앞": 앞치마, "허리스커트뒤": 뒤치마, "허리금뿔L": 뿔L, "허리금뿔R": 뿔R}
부품.update({"가슴파랑줄" + k_: m_ for k_, m_ in 파랑.items()})
색 = {"허리금뿔L": (0.90, 0.72, 0.20), "허리금뿔R": (0.90, 0.72, 0.20), "가슴엠블럼": (0.90, 0.72, 0.20), "복부앞": (0.22, 0.22, 0.24), "복부뒤": (0.22, 0.22, 0.24)}
색.update({"가슴파랑줄" + k_: (0.30, 0.40, 0.75) for k_ in 파랑})
무리 = {n: ("가슴" if n.startswith(("가슴", "목깃")) else "복부" if n.startswith("복부") else "허리") for n in 부품}

# ── 저장 · 닫힘 · 얇은 벽 ──────────────────────────────────────────────
log("저장 · 닫힘 · 얇은 벽")
def 얇은벽(tm, n=25000, 한계=1.2):
    """겉 표본 P 마다 안쪽 법선 원뿔(반각 45°) 안의 다른 표본 Q(법선이 마주 보는 것)까지 최소 거리 = 벽 두께.
    (광선 방식은 패널라인 홈 턱 · 오목 모서리 이웃 면을 0.1 mm 벽으로 잘못 셌다.) 한계 미만 비율 · 최소."""
    P, fi = trimesh.sample.sample_surface(tm, n); N = tm.face_normals[fi]
    tr = cKDTree(P); d = np.full(len(P), 99.0); mid = np.zeros_like(P)
    nb = tr.query_ball_point(P, 2.0)
    for i, js in enumerate(nb):
        if len(js) < 2: continue
        js = np.array(js); v = P[js] - P[i]; L = np.linalg.norm(v, axis=1)
        ok = (L > 0.05) & (-(v @ N[i]) > 0.7 * L) & (np.einsum("ij,j->i", N[js], N[i]) < -0.3)
        if ok.any(): k = js[ok][np.argmin(L[ok])]; d[i] = L[ok].min(); mid[i] = (P[i] + P[k]) / 2
    cand = np.nonzero(d < 한계)[0]                      # 후보만: 가운뎃점이 속(재료)인 것이 진짜 벽 (홈 턱 사이 · 오목 모서리는 공기)
    if len(cand):
        inside = tm.contains(mid[cand]); d[cand[~inside]] = 99.0
    return float((d < 한계).mean()), float(d.min())
def 벌리기(v, f, 거리=0.03):
    """manifold 출력은 위상은 닫혀 있지만 두 덩이가 한 모서리에서 만나는 자기 접촉이 있으면 STL 로 읽을 때 면 4 장 모서리가 된다.
    같은 자리(1e-6)의 꼭짓점 짝을 각자의 면 법선 평균 쪽으로 0.03 씩 벌린다."""
    v = np.array(v, float); tr = cKDTree(v); pairs = tr.query_pairs(1e-4)
    if not pairs: return v
    fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]); fn /= np.linalg.norm(fn, axis=1)[:, None] + 1e-12
    vn = np.zeros_like(v); np.add.at(vn, f.ravel(), np.repeat(fn, 3, 0)); vn /= np.linalg.norm(vn, axis=1)[:, None] + 1e-12
    done = set()
    for i, j in sorted(pairs):                     # i 는 제 법선 쪽으로 · j 는 법선이 같은 방향(접힌 지느러미)이면 반대쪽, 마주 보면(두 덩이 접촉) 제 쪽으로
        if i in done or j in done: continue
        v[i] += 거리 * vn[i]; v[j] += 거리 * vn[j] * (-1.0 if vn[i] @ vn[j] > 0 else 1.0); done |= {i, j}
    return v
결과 = {}
for n, m in list(부품.items()):
    if m.is_empty(): log("  !! 빈 부품", n); continue
    cs = m.decompose(); 조각 = len(cs)
    if 조각 > 1:
        vm = max(c.volume() for c in cs); m = 합([c for c in cs if c.volume() >= 0.05 * vm]); 부품[n] = m; 조각 = len(m.decompose())
    v, f = 메시(m); p = os.path.join(OUT, n + ".stl")
    v = 벌리기(v, f)
    trimesh.Trimesh(v, f).export(p)
    t = trimesh.load(p, force="mesh")
    _, cnt = np.unique(t.edges_sorted, axis=0, return_counts=True)
    얇, 최소 = 얇은벽(t)
    결과[n] = dict(파일=n + ".stl", 색=list(색.get(n, (0.93, 0.93, 0.95))), 부피mm3=round(m.volume(), 1), 무게g=round(m.volume() / 1000 * 1.24, 2), 닫힘=bool(t.is_watertight),
                  모서리4면=int((cnt > 2).sum()), 조각=조각, 얇은벽1_2미만=round(얇, 3), 최소벽mm=round(최소, 2), 크기mm=[round(float(e), 1) for e in t.extents], 뼈무리=무리[n])
    log("  %-10s %6.2f g  닫힘 %s  4면 %d  조각 %d  벽<1.2 %4.1f%%  최소 %.2f" % (n, m.volume() / 1000 * 1.24, t.is_watertight, (cnt > 2).sum(), 조각, 얇 * 100, 최소))
for f in glob.glob(os.path.join(OUT, "*.stl")):
    if os.path.basename(f)[:-4] not in 결과: os.remove(f); log("  지움(없어진 부품)", os.path.basename(f))

# ── 검사: 장갑 ∩ J2 실물 · 장갑 ∩ 뼈 실물 ───────────────────────────────
log("장갑 ∩ J2 · 뼈")
근처 = ["목아래", "목위", "가슴복부", "복부허리", "L고관절벌림", "R고관절벌림", "L어깨스윙", "R어깨스윙", "L어깨회전", "R어깨회전", "L고관절", "R고관절", "L어깨들기", "R어깨들기"]
J2겹 = {}
for jn in 근처:
    for f in sorted(glob.glob(os.path.join(J2D, "관절_%s_*.stl" % jn))):
        jm = 만(STL(f))
        if jm.status() != mf.Error.NoError: continue
        for n, m in 부품.items():
            v = (m ^ jm).volume()
            if v > 0.01: J2겹[n + "↔" + os.path.basename(f)[3:-4]] = round(v, 2)
뼈겹 = {}; 뼈겹_구멍뺀 = {}
for bn in ("가슴", "복부", "허리", "목", "L고관절블록", "R고관절블록", "L어깨축", "R어깨축", "L어깨블록", "R어깨블록", "L허벅지위", "R허벅지위"):
    bm = 만(뼈STL(bn))
    bm2 = bm - 합([원통(np.asarray(e["입구mm"]) + 0.5 * np.asarray(e["방향"]), np.asarray(e["입구mm"]) - 구멍L * np.asarray(e["방향"]), 구멍D / 2, 24) for e in 키트["뼈구멍"] and 구멍목록 + 기본구멍() if e["뼈"] == bn])
    for n, m in 부품.items():
        v = (m ^ bm).volume(); v2 = (m ^ bm2).volume()
        if v > 0.01: 뼈겹[n + "↔" + bn] = round(v, 2)
        if v2 > 0.01: 뼈겹_구멍뺀[n + "↔" + bn] = round(v2, 2)
log("  장갑∩J2", sum(J2겹.values()), J2겹); log("  장갑∩뼈(핀 포함)", sum(뼈겹.values()), "· 뼈에 구멍 뚫으면", sum(뼈겹_구멍뺀.values()), 뼈겹_구멍뺀)

# ── 가동 검사 ─────────────────────────────────────────────────────
log("가동 검사")
G = {k: 합([부품[n] for n in 부품 if 무리[n] == k]) for k in ("가슴", "복부", "허리")}
가동 = {}
def 틈(A, B, n=4000):                            # 두 부품 최소 거리 (표면 표본 ↔ 표면 표본 · mm)
    ta = trimesh.Trimesh(*메시(A)); tb = trimesh.Trimesh(*메시(B))
    pa, _ = trimesh.sample.sample_surface(ta, n); pb, _ = trimesh.sample.sample_surface(tb, n)
    return float(cKDTree(pb).query(pa)[0].min())
def 한계(child, others, p, ax, lo, hi, st=3, 부풀=0.3):
    """자식 부품을 +부풀 로 두고 3° 씩 밖으로 돌려 겹침(교집합 부피 − 0°) ≥ 0.5 에서 멈춤 (비평_조립.py 와 같은 규칙, 부풀림은 최소거리 < 부풀 로 대신)."""
    out = []
    for sg, lim in ((-1, lo), (1, hi)):
        a = 0
        while abs(a) < abs(lim) + 1e-6:
            q = 돌려(child, p, ax, a + st * sg)
            if (q ^ others).volume() >= 0.5 or 틈(q, others, 2500) < 부풀: break
            a += st * sg
        out.append(int(a))
    return out
for nm, ax, lo, hi in (("앞뒤", (1, 0, 0), -15, 20), ("옆", (0, 1, 0), -15, 15), ("비틀기", (0, 0, 1), -30, 30)):
    가동["가슴복부 " + nm] = dict(목표=[lo, hi], 잰=한계(G["가슴"], G["복부"], p3, ax, lo, hi))
p4 = JT["복부허리"]["피벗mm"]
가동["복부허리 비틀기"] = dict(목표=[-45, 45], 잰=한계(합([G["가슴"], G["복부"]]), G["허리"], p4, (0, 0, 1), -45, 45, 5))
# 다리 (뼈 + J2 + D2 허벅지 · 윗단 장갑 실물) ↔ 벨트 · 스커트 · 뿔
허리부품 = 합([부품[n] for n in ("허리벨트앞", "허리벨트뒤", "허리V스커트앞", "허리스커트뒤", "허리금뿔L", "허리금뿔R")])
def D2들(s, names): return [만(STL(os.path.join(D2, s + n_ + ".stl"))) for n_ in names if os.path.exists(os.path.join(D2, s + n_ + ".stl"))]
for s in "LR":
    p5 = JT[s + "고관절벌림"]["피벗mm"]; a5, l5, h5 = 범위(s + "고관절벌림"); p7 = JT[s + "고관절"]["피벗mm"]; a7, l7, h7 = 범위(s + "고관절")
    블록 = 합([만(뼈STL(s + "고관절블록"))] + J2실물(s + "고관절벌림")[1:] + J2실물(s + "고관절"))
    허벅 = 합([만(뼈STL(s + "허벅지위")), 만(뼈STL(s + "허벅지"))] + J2실물(s + "허벅지회전") + D2들(s, ("허벅지앞", "허벅지뒤", "허벅지윗단앞", "허벅지윗단뒤")))
    차렷 = (합([블록, 허벅]) ^ 허리부품).volume()
    가동[s + "다리 차렷 겹침mm3"] = round(차렷, 2)
    def 다리자세(t5, t7): return 돌려(합([블록, 돌려(허벅, p7, a7, t7)]), p5, a5, t5)
    res = {}
    for 이름_, (t5s, t7s) in (("벌림", ([l5, 0, 20, 33, 45], [0])), ("앞차기", ([0], [-30, -15, 0, 45, 90]))):
        for t5 in t5s:
            for t7 in t7s:
                q = 다리자세(t5, t7); v_ = (q ^ 허리부품).volume()
                res["벌림%+d 앞차기%+d" % (t5, t7)] = round(v_, 2) if v_ < 0.01 else {n: round((q ^ 부품[n]).volume(), 2) for n in ("허리벨트앞", "허리벨트뒤", "허리V스커트앞", "허리스커트뒤", "허리금뿔" + s) if (q ^ 부품[n]).volume() > 0.01}
    가동[s + "다리 겹침mm3"] = res
for k, v in 가동.items(): log("  ", k, v)

# ── 실루엣 ───────────────────────────────────────────────────────
log("실루엣")
전체 = 합(list(부품.values()))
def 투영(m, 축):
    T = [[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0]] if 축 == "앞" else [[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0]]
    return m.transform(T).project().to_polygons()
def 래스터(polys, 범위_, px=0.2):
    from PIL import ImageDraw
    (a0, a1), (z0, z1) = 범위_; W = int((a1 - a0) / px); H = int((z1 - z0) / px)
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    def 넓이(q): return 0.5 * np.sum(q[:, 0] * np.roll(q[:, 1], -1) - np.roll(q[:, 0], -1) * q[:, 1])
    for q in sorted(polys, key=lambda q: -abs(넓이(q))):
        d.polygon([((x - a0) / px, (z1 - z) / px) for x, z in q], fill=255 if 넓이(q) > 0 else 0)
    return np.array(im) > 0
F = 래스터(투영(전체, "앞"), ((-60, 60), (140, 280))); S = 래스터(투영(전체, "옆"), ((-40, 80), (140, 280)))
def 원화윤곽():
    fa = np.array(Image.open(os.path.join(ART, "omega_front_clean.png")).convert("RGBA")).astype(int)
    sa = np.array(Image.open(os.path.join(ART, "omega_side.png")).convert("RGBA")).astype(int)
    fm = fa[..., 3] > 128; sm = sa[..., 3] > 128
    front = {}; side = {}
    for z in np.arange(150, 273, 0.5):
        r = int(round(951 - z / 0.342)); row = fm[r]; c = 534
        if row[c]:
            a = c
            while a > 0 and row[a - 1]: a -= 1
            b = c
            while b < 1023 and row[b + 1]: b += 1
            xl, xr = FRX(a), FRX(b + 1)
            if z < 234:
                cs_ = np.nonzero(row[int(534 - 33 / 0.342):int(534 + 33 / 0.342)])[0] + int(534 - 33 / 0.342)
                xl, xr = FRX(cs_[0]), FRX(cs_[-1] + 1)
            if 234 <= z <= 268 and (xr - xl) / 2 > 32:
                rgb = fa[r, :, :3].sum(-1); out = []
                for sgn in (-1, 1):
                    cc = int(round(534 + sgn * 34 / 0.342))
                    while rgb[cc] > 100 and abs(FRX(cc)) > 21: cc -= sgn
                    out.append(FRX(cc))
                xl, xr = out
            front[z] = (xl, xr)
        r = int(round(938 - z / 0.349)); c0, c1 = int(462 - 15 / 0.349), int(462 + 50 / 0.349)
        cs_ = np.nonzero(sm[r, c0:c1])[0]
        if len(cs_): side[z] = (SDY(c0 + cs_[0]), SDY(c0 + cs_[-1] + 1))
    return front, side
원F, 원S = 원화윤곽()
def 가장자리(M, 범위_, z, px=0.2):
    (a0, a1), (z0, z1) = 범위_; r = int((z1 - z) / px)
    if r < 0 or r >= M.shape[0]: return None
    c = np.nonzero(M[r])[0]
    return None if len(c) == 0 else (a0 + c[0] * px, a0 + (c[-1] + 1) * px)
틈줄 = {"정면": [], "옆": []}
오차 = {"정면": [], "옆앞": [], "옆뒤": []}; 오차줄 = {"정면": [], "옆앞": [], "옆뒤": []}
for z, (xl, xr) in 원F.items():
    if not (188 <= z <= 272): continue
    e = 가장자리(F, ((-60, 60), (140, 280)), z)
    if e is None or (e[1] - e[0]) < 0.6 * (xr - xl): 틈줄["정면"].append(float(z)); continue
    v = max(abs(e[0] - xl), abs(e[1] - xr)); 오차["정면"].append(v); 오차줄["정면"].append((float(z), round(float(v), 2)))
for z, (yf, yb) in 원S.items():
    e = 가장자리(S, ((-40, 80), (140, 280)), z)
    if e is None or (z >= 170 and (e[1] - e[0]) < 0.6 * (yb - yf)): 틈줄["옆"].append(float(z)); continue
    if 150 <= z <= 257: 오차["옆앞"].append(abs(e[0] - yf)); 오차줄["옆앞"].append((float(z), round(float(abs(e[0] - yf)), 2)))
    if 170 <= z <= 236: 오차["옆뒤"].append(abs(e[1] - yb)); 오차줄["옆뒤"].append((float(z), round(float(abs(e[1] - yb)), 2)))
실루엣 = {k: dict(최대=round(float(max(v)), 2), 평균=round(float(np.mean(v)), 2), 줄수=len(v), 넘침2mm=int(sum(x > 2 for x in v)),
                  나쁜줄=sorted(오차줄[k], key=lambda q: -q[1])[:6]) for k, v in 오차.items() if v}
실루엣["틈줄z"] = 틈줄
for k, v in 실루엣.items(): log("  실루엣", k, v)

# ── 부품.json · 키트.json ─────────────────────────────────────────
힌지정보 = {"규격": "힌지1.75 (관절규격.json) — 핀 = 1.75 PLA 필라멘트 · 러그 구멍 1.75(압입) · 너클 구멍 1.95 · 축방향 틈 0.3 · 너클 R 2.2",
          "허리V스커트앞": dict(축점=[round(float(v), 2) for v in 축앞[0]], 축=list(축앞[1]), 핀길이=18.0, 러그="허리벨트앞 속 x ±(6.3~9.5) · 핀 끝 벨트 안", 너클="x ±6.0 · 벨트 앞 가운데 홈 x ±6.3 안"),
          "허리스커트뒤": dict(축점=[round(float(v), 2) for v in 축뒤[0]], 축=list(축뒤[1]), 핀길이=18.0, 러그="허리벨트뒤 속 x ±(6.3~9.5)", 너클="x ±6.0")}
json.dump(dict(설명=__doc__, 부품=결과, 결합정보=정보, 힌지=힌지정보, 가동검사=가동, 실루엣mm=실루엣, 장갑J2겹침mm3=J2겹, 장갑뼈겹침mm3=뼈겹, 장갑뼈겹침_구멍뚫은뼈mm3=뼈겹_구멍뺀,
               속비움="뼈 실물(프레임 STL) + J2 실물(_조립/관절_*.stl) + 0.3 · 이웃은 가동 범위 쓸기", 뼈결합자리=구멍출처,
               총무게g=round(sum(r["무게g"] for r in 결과.values()), 1), 재질="PLA 1.24 g/cm³ · 채움 100 % 가정"),
          open(os.path.join(OUT, "부품.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
키트["설명"] = "몸통 · 허리 디자인 판의 뼈 결합: 장갑 보스(Ø5) 끝 핀 Ø2.0 × 3.0 → 뼈 구멍 Ø2.2 × 3.0. 입구 = 뼈 겉 점 · 방향_뼈속 = 구멍이 파고드는 방향. 자리 출처: " + 구멍출처
json.dump(키트, open(os.path.join(OUT, "키트.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ── 그림 ─────────────────────────────────────────────────────────
log("그림")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
def 그리기(ax, 목록, R, 제목):
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
def 보기R(yaw, pitch):
    a, b = np.radians(yaw), np.radians(pitch)
    Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    base = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]])
    Rx = np.array([[1, 0, 0], [0, np.cos(b), -np.sin(b)], [0, np.sin(b), np.cos(b)]])
    return Rx @ base @ Rz
목록 = [(m, 색.get(n, (0.88, 0.88, 0.90))) for n, m in 부품.items()]
fig = plt.figure(figsize=(26, 12))
ax = fig.add_subplot(1, 6, 1)
fa = Image.open(os.path.join(ART, "omega_front_clean.png")).convert("RGBA"); bg = Image.new("RGBA", fa.size, (255, 255, 255, 255)); bg.alpha_composite(fa)
ax.imshow(np.array(bg.convert("RGB")), extent=[FRX(0), FRX(1024), FRZ(1024), FRZ(0)], alpha=0.35)
그리기(ax, 목록, 보기R(0, 0), "정면 + 원화(흐림) · 빨강 = 원화 윤곽")
zz = sorted(원F); ax.plot([원F[z][0] for z in zz], zz, "r-", lw=0.8); ax.plot([원F[z][1] for z in zz], zz, "r-", lw=0.8)
ax.set_xlim(-45, 45); ax.set_ylim(145, 280)
ax = fig.add_subplot(1, 6, 2)
sa = Image.open(os.path.join(ART, "omega_side.png")).convert("RGBA"); bg = Image.new("RGBA", sa.size, (255, 255, 255, 255)); bg.alpha_composite(sa)
ax.imshow(np.array(bg.convert("RGB")), extent=[SDY(0), SDY(1024), SDZ(1024), SDZ(0)], alpha=0.35)
그리기(ax, 목록, np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]]), "옆(왼쪽 = 앞) + 원화")
zz = sorted(원S); ax.plot([원S[z][0] for z in zz], zz, "r-", lw=0.8); ax.plot([원S[z][1] for z in zz], zz, "r-", lw=0.8)
ax.set_xlim(-25, 65); ax.set_ylim(145, 280)
ax = fig.add_subplot(1, 6, 3); 그리기(ax, 목록, 보기R(-35, 12), "3/4 앞")
ax = fig.add_subplot(1, 6, 4); 그리기(ax, 목록, 보기R(145, 12), "3/4 뒤")
# 속: 앞 반쪽 빼고 뒤 반쪽 + 뼈 + J2 (속 비움이 실물을 담는지)
ax = fig.add_subplot(1, 6, 5)
속목록 = [(부품[n], 색.get(n, (0.88, 0.88, 0.90))) for n in ("가슴뒤", "복부뒤", "허리벨트뒤", "허리스커트뒤")]
속목록 += [(만(뼈STL(b)), (0.3, 0.75, 0.35)) for b in ("가슴", "복부", "허리", "목", "L어깨축", "R어깨축", "L고관절블록", "R고관절블록")]
속목록 += [(만(STL(f)), (0.85, 0.35, 0.3)) for jn in ("목아래", "가슴복부", "복부허리", "L고관절벌림", "R고관절벌림", "L어깨스윙", "R어깨스윙") for f in glob.glob(os.path.join(J2D, "관절_%s_*.stl" % jn))]
그리기(ax, 속목록, 보기R(-20, 8), "속: 뒤 반쪽 + 뼈(초록) + J2(빨강)")
ax = fig.add_subplot(1, 6, 6)
벌림 = {"가슴앞": (0, -30, 25), "가슴뒤": (0, 25, 25), "가슴엠블럼": (0, -45, 10), "목깃": (0, 0, 55), "복부앞": (0, -20, 0), "복부뒤": (0, 18, 0),
       "허리벨트앞": (0, -15, -15), "허리벨트뒤": (0, 18, -15),
       **{"가슴파랑줄" + k_: (0, -45, 25) for k_ in 파랑}, "허리V스커트앞": (0, -35, -30), "허리스커트뒤": (0, 35, -30), "허리금뿔L": (-20, 0, 5), "허리금뿔R": (20, 0, 5)}
그리기(ax, [(m.translate(벌림[n]), c) for (n, m), (_, c) in zip(부품.items(), 목록)], 보기R(-35, 12), "분해도")
for a in fig.axes[2:]: a.set_xticks([])
fig.suptitle("오메가몬 PG 디자인 판 3바퀴 — 몸통 · 허리 (%d 부품 · %.0f g · 장갑∩J2 %.1f · 장갑∩뼈(구멍 뚫은 뼈) %.1f mm³ · 실루엣 정면 최대 %.1f / 옆앞 %.1f / 옆뒤 %.1f mm)" % (
    len(부품), sum(r["무게g"] for r in 결과.values()), sum(J2겹.values()), sum(뼈겹_구멍뺀.values()), 실루엣["정면"]["최대"], 실루엣["옆앞"]["최대"], 실루엣["옆뒤"]["최대"]), fontsize=13)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "보기.png"), dpi=100); plt.close(fig)
log("끝", OUT)
