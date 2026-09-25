# -*- coding: utf-8 -*-
r"""디자인 판 비평 — D1 몸통 + D2 다리 + D3 머리어깨 조립 렌더 · 블록 경계 · 뼈 노출 · 제작 결함 · 주요 관절 가동.

    python 실험_20260925/비평_조립.py [--가동없이]
    -> out/출력/오메가몬_PG/디자인/조립_2바퀴.png · 조립_2바퀴_경계.png · 조립_2바퀴_가동.png · 조립_2바퀴.json
       (1바퀴 결과 조립_1바퀴.png 는 그대로 두고 2바퀴 그림 둘째 줄에 나란히 붙인다)

원화 → mm 는 골격(D2 · 관절.json)과 같은 창 좌표를 원화 픽셀에 맞춘 값(다리 창 마스크 IoU 0.992 / 0.987):
  정면 x = (열 − 534)·0.342 · z = (951 − 행)·0.342   /   옆 y = (열 − 462)·0.349 · z = (938 − 행)·0.349
가동: 자식 하위 트리 부품을 +0.3 부풀려 나머지 모든 외장과의 교집합 V(θ). 0° 에서 3° 씩 밖으로, V − V(0) ≥ 0.5 mm³ 에서 멈춤.
L 어깨들기는 방패 연동(φ = 팔과 안 겹치는 가장 작은 힌지각)과 방패 고정 둘 다 잰다.
뼈 노출 = 정면·옆·뒤 화가 알고리즘 렌더(0.5 mm/px)에서 뼈 색이 보이는 픽셀 넓이."""
import os, sys, json, glob, time
import numpy as np, trimesh, manifold3d as M
from scipy.spatial import cKDTree
from PIL import Image

ROOT = r"G:\art2real\원화3d"; D = os.path.join(ROOT, r"out\출력\오메가몬_PG\디자인")
ART = r"G:\art2real\트레일\trail7_part3d\in"
TAG = "2바퀴"
t0 = time.time()
def log(*a): print("[%4.0fs]" % (time.time() - t0), *a, flush=True)
관 = {a["이름"]: a for a in json.load(open(os.path.join(ROOT, r"out\가동\관절.json"), encoding="utf-8"))["관절"]}
FRONT = (534.0, 951.0, 0.342); SIDE = (462.0, 938.0, 0.349); BACK = (505.0, 929.6, 0.3535)   # 뒤 원화: 머리 중심 · 높이 맞춤(정면 923 px ↔ 뒤 893 px)

# ── 부품 · 뼈 배정 · 색 ──
def 뼈(blk, n):
    s = n[0] if n[0] in "LR" else ""
    if blk == "몸통": return "가슴" if n.startswith(("가슴", "목깃")) else "복부" if n.startswith(("복부", "엠블럼")) else "허리"
    if blk == "다리":
        if n.startswith("가랑이"): return "허리"                       # 허리 뼈에 끼움(D2 기록)
        if "허벅지윗단" in n: return s + "허벅지위"                     # 허벅지위 뼈 반달 갈비
        if "허벅지" in n: return s + "허벅지"
        if "정강이" in n or "무릎" in n or "오금" in n: return s + "정강이"   # 무릎장갑·오금 = 정강이에 핀
        if "뒤꿈치" in n: return s + "발"                               # 발바닥에 핀
        if "발끝" in n or "발톱" in n: return s + "발끝"
        return s + "발"
    if n.startswith(("투구", "얼굴", "뿔", "V안테나", "볼가리개")): return "머리"
    if n in ("방패빨강", "방패금"): return "L어깨블록"
    if n.startswith("가시"): return "R어깨블록"
    if "윗팔위" in n: return s + "윗팔위"
    if "윗팔" in n: return s + "윗팔"
    return s + "어깨블록"
색이름 = {"흰": (0.93, 0.93, 0.95), "검정": (0.22, 0.22, 0.25), "검": (0.22, 0.22, 0.25), "금": (0.90, 0.72, 0.20),
        "파랑": (0.45, 0.50, 0.78), "빨": (0.78, 0.16, 0.12), "빨강": (0.78, 0.16, 0.12)}
def 색(blk, n, info):
    c = info.get("색")
    if isinstance(c, str): return 색이름.get(c, (0.9, 0.9, 0.92))
    if c: return tuple(c)
    if "파랑" in n or "엠블럼" in n: return (0.30, 0.38, 0.75)
    if n.startswith("복부") and "혀" not in n: return (0.22, 0.22, 0.25)
    if "발톱" in n or "금뿔" in n: return (0.90, 0.72, 0.20)
    return (0.90, 0.90, 0.92)
부품 = {}; 정보 = {}   # 이름 → (블록, 뼈, trimesh, 색)
for blk in ("몸통", "다리", "머리어깨"):
    info = json.load(open(os.path.join(D, blk, "부품.json"), encoding="utf-8"))["부품"]
    for n, p in info.items():
        m = trimesh.load(os.path.join(D, blk, p.get("파일", n + ".stl")))
        부품[n] = (blk, p.get("뼈") or 뼈(blk, n), m, 색(blk, n, p)); 정보[n] = p
뼈메시 = {os.path.basename(f)[:-4]: trimesh.load(f) for f in glob.glob(os.path.join(ROOT, r"out\가동\프레임\*.stl"))}
없는뼈 = sorted({v[1] for v in 부품.values()} - set(뼈메시))
log("부품", len(부품), "뼈", len(뼈메시), "배정된 뼈 중 프레임에 없는 것", 없는뼈)
def 만(tm): return M.Manifold(M.Mesh(vert_properties=np.asarray(tm.vertices, np.float32), tri_verts=np.asarray(tm.faces, np.uint32)))
MF = {n: 만(v[2]) for n, v in 부품.items()}
bad = [n for n, m in MF.items() if m.status() != M.Error.NoError or m.is_empty()]
log("manifold 실패", bad)

# ── 제작 결함: 열린 메시 · 여러 조각 · 무게 < 0.3 g · 얇은 벽(< 1.2 mm) ──
def 얇은벽(tm, k=None, 문턱=1.2):
    """표면 표본에서 안쪽 법선 방향으로 반대 법선을 가진 가장 가까운 표본까지 거리 = 두께. 두께 < 문턱인 표본 비율·최소."""
    if len(tm.faces) == 0: return None
    k = k or int(min(24000, max(6000, tm.area * 4)))   # 표본 간격 ≤ 0.5 mm
    p, fi = trimesh.sample.sample_surface_even(tm, k)
    if len(p) < 50: return None
    nrm = tm.face_normals[fi]; tree = cKDTree(p)
    dist, idx = tree.query(p, k=48, distance_upper_bound=문턱 + 0.05)
    두께 = np.full(len(p), np.inf)
    for j in range(1, 48):
        ok = np.isfinite(dist[:, j])
        if not ok.any(): continue
        q = idx[:, j][ok]; d = p[q] - p[ok]; dn = np.linalg.norm(d, axis=1) + 1e-9
        opp = (np.einsum("ij,ij->i", nrm[ok], nrm[q]) < -0.6) & (np.einsum("ij,ij->i", -nrm[ok], d / dn[:, None]) > 0.8)
        ii = np.where(ok)[0][opp]; 두께[ii] = np.minimum(두께[ii], dist[:, j][ok][opp])
    얇 = 두께 < 문턱
    return dict(얇은비율=round(float(얇.mean()), 3), 최소=round(float(두께[얇].min()), 2) if 얇.any() else None,
                자리=np.round(p[얇].mean(0), 1).tolist() if 얇.any() else None)
결함 = {"열린메시": [], "여러조각": [], "가벼움g": [], "얇은벽": [], "매니폴드실패": bad}
for n, (blk, b, tm, c) in 부품.items():
    if not tm.is_watertight: 결함["열린메시"].append(n)
    bodies = tm.split(only_watertight=False)
    if len(bodies) > 1: 결함["여러조각"].append((n, [round(float(x.volume), 1) for x in bodies]))
    g = tm.volume * 1.24e-3
    if g < 0.3: 결함["가벼움g"].append((n, round(float(g), 2)))
    w = 얇은벽(tm)
    if w and w["얇은비율"] > 0.03: 결함["얇은벽"].append((n, w))
log("제작 결함", json.dumps(결함, ensure_ascii=False))

# ── 블록 경계: 차렷 겹침 · 최소 틈 ──
def 표본(tm, k=8000):
    p, _ = trimesh.sample.sample_surface_even(tm, k) if len(tm.faces) else (np.zeros((0, 3)), None); return p
표 = {n: 표본(v[2]) for n, v in 부품.items()}
겹침, 틈 = [], {}
names = list(부품)
for i, a in enumerate(names):
    for b in names[i + 1:]:
        ba, bb = 부품[a][0], 부품[b][0]
        if ba == bb: continue
        ma, mb = MF[a], MF[b]
        if not all(ma.bounding_box()[k] - 6 <= mb.bounding_box()[k + 3] and mb.bounding_box()[k] - 6 <= ma.bounding_box()[k + 3] for k in range(3)): continue
        v = (ma ^ mb).volume()
        if v > 0.01: 겹침.append((a, b, round(v, 2)))
        d = cKDTree(표[b]).query(표[a])[0].min() if len(표[a]) and len(표[b]) else 99
        if d < 6: 틈[a + "↔" + b] = round(float(d), 2)
log("차렷 블록간 겹침", 겹침); log("블록간 가까운 짝(<6mm)", 틈)
# 외장 ∩ 뼈 (다른 뼈에 붙은 외장이 뼈를 먹는지 · 제 뼈와의 겹침도 따로)
뼈MF = {}
for bn, btm in 뼈메시.items():
    try: 뼈MF[bn] = 만(btm)
    except Exception: pass
뼈겹, 제뼈겹 = [], []
for n, (blk, b, tm, c) in 부품.items():
    for bn, bm in 뼈MF.items():
        if not all(MF[n].bounding_box()[k] <= bm.bounding_box()[k + 3] and bm.bounding_box()[k] <= MF[n].bounding_box()[k + 3] for k in range(3)): continue
        v = (MF[n] ^ bm).volume()
        if v > 0.5: (제뼈겹 if bn == b else 뼈겹).append((n, bn, round(v, 1)))
log("외장 ∩ 남의 뼈", 뼈겹); log("외장 ∩ 제 뼈(갈비·격벽 압입 아니면 결함)", 제뼈겹)
# ── 가동 ──
def 회전행렬(a, θ):
    a = np.asarray(a, float); a = a / np.linalg.norm(a); K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]]); t = np.radians(θ)
    return np.eye(3) + np.sin(t) * K + (1 - np.cos(t)) * K @ K
def 강체(R, p): p = np.asarray(p, float); return np.c_[R, p - R @ p]
def 합성(A, B): return np.c_[A[:, :3] @ B[:, :3], A[:, :3] @ B[:, 3] + A[:, 3]]
자식 = {}
for a in 관.values(): 자식.setdefault(a["부모뼈"], []).append(a["자식뼈"])
def 하위(b): out = {b}; [out.update(하위(c)) for c in 자식.get(b, [])]; return out
def 틀(j, 축, θ):
    if j["종류"] == "이중힌지":
        P2 = j["외피"]["둘째축피벗mm"]; return 합성(강체(회전행렬(축, θ / 2), j["피벗mm"]), 강체(회전행렬(축, θ / 2), P2))
    return 강체(회전행렬(축, θ), j["피벗mm"])
부풀캐시 = {}
def 부풀(n):
    if n not in 부풀캐시:
        try: 부풀캐시[n] = MF[n].minkowski_sum(M.Manifold.sphere(0.3, 8))
        except Exception: 부풀캐시[n] = MF[n]
    return 부풀캐시[n]
def bb겹(a, b): return all(a[k] <= b[k + 3] and b[k] <= a[k + 3] for k in range(3))
# 관절 부품(J2 · J4 가 관절.json 피벗·축에 놓은 조립 좌표 STL) ∩ 디자인 장갑 — 장갑 속 비움이 관절 부품을 못 담으면 안 들어간다
관절MF = {}
for f in glob.glob(os.path.join(ROOT, r"out\가동\관절배치\관절_*.stl")):   # J1 3바퀴 배치(D3 가 _조립 → 관절배치 로 바꿈)
    try:
        m = 만(trimesh.load(f))
        if m.status() == M.Error.NoError and not m.is_empty(): 관절MF[os.path.basename(f)[3:-4]] = m
    except Exception: pass
장갑관절겹 = []
for n in 부품:
    for jn, jm in 관절MF.items():
        if not bb겹(MF[n].bounding_box(), jm.bounding_box()): continue
        v = (MF[n] ^ jm).volume()
        if v > 0.5: 장갑관절겹.append((n, jn, round(v, 1)))
log("관절 부품", len(관절MF), "장갑 ∩ 관절 부품(>0.5mm³)", len(장갑관절겹), "합", round(sum(v for _, _, v in 장갑관절겹), 1), sorted(장갑관절겹, key=lambda q: -q[2])[:20])

def V(움, 고, T, 고T=None):
    tot, 짝 = 0.0, {}
    gm = {g: (MF[g].transform(고T[g]) if 고T and g in 고T else MF[g]) for g in 고}
    gbb = {g: gm[g].bounding_box() for g in 고}
    for n in 움:
        mt = 부풀(n).transform(T); bb = mt.bounding_box()
        for g in 고:
            if bb겹(bb, gbb[g]):
                v = (mt ^ gm[g]).volume()
                if v > 1e-3: 짝[(n, g)] = v; tot += v
    return tot, 짝
def 재기(jn, k, step=3, 빼기=()):
    j = 관[jn]; r = j["범위"][k]; 하 = 하위(j["자식뼈"])
    움 = [n for n, v in 부품.items() if v[1] in 하]; 고 = [n for n in 부품 if n not in 움 and n not in 빼기]
    V0, _ = V(움, 고, 틀(j, r["축"], 0.0)); res = {"목표": [r["최소"], r["최대"]], "V0": round(V0, 1)}
    for sgn, lim in ((-1, r["최소"]), (1, r["최대"])):
        got, who = 0, None
        for θ in range(step, abs(lim) + step, step):
            θ = min(θ, abs(lim)); v, 짝 = V(움, 고, 틀(j, r["축"], sgn * θ))
            if v - V0 >= 0.5:
                who = max(짝.items(), key=lambda q: q[1])[0]; break
            got = θ
            if θ == abs(lim): break
        res["-" if sgn < 0 else "+"] = sgn * got; res["막힘" + ("-" if sgn < 0 else "+")] = "·".join(who) if who else None
    return res
# L 어깨들기 + 방패 연동: 방패 힌지 = 방패빨강 러그 원(y 9·33) 중심 · 축 +y (+ = 바깥 위)
def 방패힌지():
    try:   # D3 3바퀴: 부품.json 사양에 힌지 좌표가 있으면 그것(러그 원 맞춤은 정점 떼기로 y 가 9.0 에서 벗어날 수 있다)
        p = json.load(open(os.path.join(D, "머리어깨", "부품.json"), encoding="utf-8"))["사양"].get("방패힌지mm")
        if p: return np.array(p, float)
    except Exception: pass
    v = 부품["방패빨강"][2].vertices; s = v[np.abs(v[:, 1] - 9.0) < 0.05]
    A_ = np.c_[2 * s[:, 0], 2 * s[:, 2], np.ones(len(s))]; c = np.linalg.lstsq(A_, s[:, 0] ** 2 + s[:, 2] ** 2, rcond=None)[0]
    return np.array([c[0], 21.0, c[1]])
방패P = 방패힌지(); log("방패 힌지(러그 원 맞춤)", np.round(방패P, 2))
def 재기_L어깨들기_연동(step=3):
    j = 관["L어깨들기"]; r = j["범위"][0]; 하 = 하위("L윗팔위")
    팔 = [n for n, v in 부품.items() if v[1] in 하]; 방 = ["방패빨강", "방패금"]; 고 = [n for n in 부품 if n not in 팔 and n not in 방]
    표 = []; got = 0; who = None
    for θ in range(0, r["최대"] + step, step):
        θ = min(θ, r["최대"]); T = 틀(j, r["축"], θ)
        φ = None
        for ph in range(0, 121, step):
            Tφ = 강체(회전행렬([0, 1, 0], ph), 방패P)
            if V(팔, 방, T, {g: Tφ for g in 방})[0] < 1e-3: φ = ph; break
        if φ is None: who = "팔·방패(φ 없음)"; break
        Tφ = 강체(회전행렬([0, 1, 0], φ), 방패P)
        v팔, 짝팔 = V(팔, 고, T); v방, 짝방 = V(방, 고, Tφ)
        표.append((θ, φ, round(v팔, 2), round(v방, 2)))
        if θ == 0: V0 = v팔 + v방; continue
        if v팔 + v방 - V0 >= 0.5:
            짝 = dict(짝팔); 짝.update(짝방); who = "·".join(max(짝.items(), key=lambda q: q[1])[0]); break
        got = θ
        if θ == r["최대"]: break
    return {"목표": [0, r["최대"]], "+": got, "막힘+": who, "표(θ,φ,팔∩고정,방패∩고정)": 표}
가동 = {}
if "--가동없이" not in sys.argv:
    for jn, ks in [("목위", (0, 1, 2)), ("목아래", (0, 2)), ("L어깨들기", (0,)), ("R어깨들기", (0,)), ("L어깨스윙", (0,)), ("R어깨스윙", (0,)),
                   ("L어깨회전", (0,)), ("L윗팔회전", (0,)), ("L팔꿈치", (0,)), ("R팔꿈치", (0,)), ("L팔끝회전", (0,)),
                   ("복부허리", (0,)), ("가슴복부", (0, 1, 2)), ("L고관절벌림", (0,)), ("L고관절", (0,)), ("L허벅지회전", (0,)),
                   ("L무릎", (0,)), ("L발목", (0,)), ("L발목볼", (1,)), ("L발끝", (0,))]:
        for k in ks:
            가동[f"{jn}[{k}]"] = 재기(jn, k, step=6 if jn.endswith("어깨회전") else 3); log(jn, k, 가동[f"{jn}[{k}]"])
    # 팔을 빼고 잰 고관절벌림 (팔이 늘어뜨린 채 닿는 것과 구분)
    팔부품 = [n for n, v in 부품.items() if v[1] in 하위("L윗팔위") | 하위("R윗팔위")]
    가동["L고관절벌림[0] 팔빼고"] = 재기("L고관절벌림", 0, 빼기=팔부품); log("L고관절벌림 팔빼고", 가동["L고관절벌림[0] 팔빼고"])
    가동["L어깨들기[0] 방패연동"] = 재기_L어깨들기_연동(); log("L어깨들기 방패연동", 가동["L어깨들기[0] 방패연동"])

# ── 그림 도구 ──
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
def 보기R(yaw, pitch):
    a, b = np.radians(yaw), np.radians(pitch)
    Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    base = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]])
    Rx = np.array([[1, 0, 0], [0, np.cos(b), -np.sin(b)], [0, np.sin(b), np.cos(b)]])
    return Rx @ base @ Rz
옆R = np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]], float)
뒤R = 보기R(180, 0)
def 그리기(ax, R, 뼈도=True, 자세=None, id모드=False, 뼈색=(0.55, 0.75, 0.55), 뼈알파=0.35):
    """자세: 이름 → 3×4 강체 변환. id모드: 부품 i → 빨강 (i+1)/255 · 뼈 j → 초록 (j+1)/255, 명암 없음."""
    L = np.array([0.35, -0.6, 0.72]); L /= np.linalg.norm(L)
    items = [(n, v[2], v[3], 1.0) for n, v in 부품.items()] + ([(bn, m, 뼈색, 뼈알파) for bn, m in 뼈메시.items()] if 뼈도 else [])
    P, C, Dd = [], [], []
    for i, (n, tm, c, al) in enumerate(items):
        v, f = tm.vertices, tm.faces
        if 자세 and n in 자세: T = 자세[n]; v = v @ T[:, :3].T + T[:, 3]
        tri = (v @ R.T)[f]
        nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); nn = np.linalg.norm(nrm, axis=1) + 1e-12
        vis = nrm[:, 2] / nn > 0
        if id모드:
            cc = np.tile([(i + 1) / 255.0, 0, 0, 1] if n in 부품 else [0, (i - len(부품) + 1) / 255.0, 0, 1], (len(f), 1))
        else:
            wn = np.cross(v[f][:, 1] - v[f][:, 0], v[f][:, 2] - v[f][:, 0]) / nn[:, None]
            sh = 0.35 + 0.65 * np.clip(wn @ L, 0, 1)
            cc = np.clip(np.array(c)[None] * sh[:, None], 0, 1); cc = np.c_[cc, np.full(len(cc), al)]
        P += list(tri[vis][:, :, :2]); C += list(cc[vis]); Dd += list(tri[vis][:, :, 2].mean(1))
    o = np.argsort(Dd)
    ax.add_collection(PolyCollection([P[i] for i in o], facecolors=[C[i] for i in o], edgecolors=[C[i] for i in o],
                                     linewidths=0.05 if not id모드 else 0.0, antialiased=not id모드))
    ax.autoscale(); ax.set_aspect("equal")
def 원그림(ax, f, cal, alpha=1.0):
    cx, r0, s = cal; im = Image.open(os.path.join(ART, f)).convert("RGBA"); bg = Image.new("RGBA", im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
    ax.imshow(np.array(bg.convert("RGB")), extent=[(0 - cx) * s, (1024 - cx) * s, (r0 - 1024) * s, r0 * s], alpha=alpha)
def 원마스크(f): return np.array(Image.open(os.path.join(ART, f)))[:, :, 3] > 127
Af, As, Ab = 원마스크("omega_front_clean.png"), 원마스크("omega_side.png"), 원마스크("omega_back.png")
def 원격자(A, cal, 거울=False):
    cx, r0, s = cal; uu, zz = np.meshgrid(np.arange(360) * 0.5 - 90, np.arange(700) * 0.5 - 10, indexing="ij")
    r = np.round(r0 - zz / s).astype(int); c = np.round(cx + (-uu if 거울 else uu) / s).astype(int); ok = (r >= 0) & (r < 1024) & (c >= 0) & (c < 1024)
    g = np.zeros(uu.shape, bool); g[ok] = A[r[ok], c[ok]]; return g
원F, 원S, 원B = 원격자(Af, FRONT), 원격자(As, SIDE), 원격자(Ab, BACK)   # 뒤 보기(yaw 180)는 화면 X = −x 라 뒤 원화를 그대로 겹친다
def 윤곽(ax, g, col="r"):
    ax.contour(np.arange(360) * 0.5 - 90, np.arange(700) * 0.5 - 10, g.T.astype(float), [0.5], colors=col, linewidths=0.7)

# ── id 렌더(0.5 mm/px): 뼈 노출 · 실루엣 마스크 ──
def id렌더(R, 자세=None):
    fig = plt.figure(figsize=(3.6, 7.0), dpi=100, facecolor="k"); ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor("k")   # 바탕 검정 = id 0
    그리기(ax, R, 자세=자세, id모드=True); ax.set_xlim(-90, 90); ax.set_ylim(-10, 340); ax.axis("off")
    fig.canvas.draw(); im = np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy(); plt.close(fig)
    im = im[::-1].transpose(1, 0, 2)   # [u, z, rgb] · u 0..359 · z 0..699 (아래→위)
    return im[:, :, 0].astype(int), im[:, :, 1].astype(int)   # 부품 id+1 · 뼈 id+1
이름들 = list(부품); 뼈이름들 = list(뼈메시)
노출 = {}; 마스크 = {}
for 보기이름, R in (("정면", 보기R(0, 0)), ("옆", 옆R), ("뒤", 뒤R)):
    pid, bid = id렌더(R); 마스크[보기이름] = (pid > 0) | (bid > 0)
    보임 = bid > 0; 노출[보기이름] = {"합mm2": round(float(보임.sum()) * 0.25, 1)}
    for j, bn in enumerate(뼈이름들):
        px = bid == j + 1
        if px.sum() * 0.25 >= 2:
            zs = np.where(px)[1] * 0.5 - 10; 노출[보기이름][bn] = (round(float(px.sum()) * 0.25, 1), round(float(zs.min()), 1), round(float(zs.max()), 1))
    노출[보기이름]["장갑만mm2"] = round(float((pid > 0).sum()) * 0.25, 1)
log("뼈 노출", json.dumps(노출, ensure_ascii=False))
# 실루엣: 전신 IoU + 부위별 반폭 오차(모형 − 원화, 각 z 행에서 좌·우 가장자리)
def 폭행(g, z, lo, hi):
    j = int(round((z + 10) / 0.5)); col = g[:, j]; u = np.arange(360) * 0.5 - 90; w = u[(col) & (u >= lo) & (u <= hi)]
    return (w.min(), w.max()) if len(w) else None
실루 = {}
for 이름, g, 원, zr, ur in [("정면 전신", 마스크["정면"], 원F, (0, 300), (-90, 90)), ("옆 전신", 마스크["옆"], 원S, (0, 300), (-60, 90)),
                          ("뒤 전신", 마스크["뒤"], 원B, (0, 300), (-90, 90))]:
    a, b = g & (np.arange(700)[None] * 0.5 - 10 < 300), 원 & (np.arange(700)[None] * 0.5 - 10 < 300)
    실루[이름] = {"IoU": round(float((a & b).sum() / max((a | b).sum(), 1)), 3), "모형mm2": round(float(a.sum()) * 0.25), "원화mm2": round(float(b.sum()) * 0.25)}
부위 = [("머리", (262, 292), (-20, 20)), ("어깨 L", (236, 272), (-70, -28)), ("어깨 R", (236, 276), (28, 70)), ("몸통", (190, 250), (-34, 34)),
       ("골반", (160, 190), (-40, 40)), ("허벅지 L", (130, 165), (-45, -5)), ("정강이 L", (40, 110), (-55, -10)), ("발 L", (3, 20), (-90, -15)),
       ("팔 L(팔꿈치~손)", (150, 205), (-90, -45)), ("팔 R", (150, 205), (45, 90))]
for 이름, zr, ur in 부위:
    rows = []
    for z in np.arange(zr[0], zr[1], 2.0):
        a, b = 폭행(마스크["정면"], z, *ur), 폭행(원F, z, *ur)
        if a and b: rows.append((float(z), round(a[0] - b[0], 1), round(a[1] - b[1], 1)))
    if rows:
        e = np.abs(np.array([[r[1], r[2]] for r in rows]))
        실루["정면 " + 이름] = {"p95": round(float(np.percentile(e, 95)), 1), "최대": round(float(e.max()), 1), "평균": round(float(e.mean()), 2), "행": rows}
for 이름, zr, ur in [("몸통", (190, 250), (-30, 60)), ("머리", (262, 292), (-10, 50)), ("정강이", (40, 110), (-20, 60)), ("발", (3, 20), (-60, 60))]:
    rows = []
    for z in np.arange(zr[0], zr[1], 2.0):
        a, b = 폭행(마스크["옆"], z, *ur), 폭행(원S, z, *ur)
        if a and b: rows.append((float(z), round(a[0] - b[0], 1), round(a[1] - b[1], 1)))
    if rows:
        e = np.abs(np.array([[r[1], r[2]] for r in rows]))
        실루["옆 " + 이름] = {"p95": round(float(np.percentile(e, 95)), 1), "최대": round(float(e.max()), 1), "평균": round(float(e.mean()), 2), "행": rows}
log("실루엣", json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "행"} for k, v in 실루.items()}, ensure_ascii=False))
무게 = {blk: round(sum(v[2].volume for v in 부품.values() if v[0] == blk) * 1.24e-3, 1) for blk in ("몸통", "다리", "머리어깨")}
json.dump(dict(설명=__doc__, 부품수=len(부품), 무게g=무게, 배정뼈없음=없는뼈, 제작결함=결함, 차렛블록겹침mm3=겹침, 블록간최소틈mm=틈,
               외장_남의뼈_겹침mm3=뼈겹, 외장_제뼈_겹침mm3=제뼈겹, 장갑_관절부품_겹침mm3=장갑관절겹, 뼈노출mm2=노출, 가동=가동, 실루엣=실루, 방패힌지mm=방패P.round(2).tolist()),
          open(os.path.join(D, f"조립_{TAG}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ── 그림 1: 전체 조립 + 1바퀴 나란히 ──
fig, axs = plt.subplots(2, 6, figsize=(36, 26))
ax = axs[0, 0]; 원그림(ax, "omega_front_clean.png", FRONT); ax.set_title("원화 정면 (골격 척도 mm)"); ax.set_xlim(-95, 95); ax.set_ylim(-8, 318); ax.grid(alpha=0.3)
ax = axs[0, 1]; 그리기(ax, 보기R(0, 0)); 윤곽(ax, 원F); ax.set_title("2바퀴 조립 정면 · 빨강 = 원화 윤곽 · 초록 = 뼈"); ax.set_xlim(-95, 95); ax.set_ylim(-8, 318); ax.grid(alpha=0.3)
ax = axs[0, 2]; 원그림(ax, "omega_side.png", SIDE); ax.set_title("원화 옆 (왼쪽 = 앞)"); ax.set_xlim(-60, 100); ax.set_ylim(-8, 318); ax.grid(alpha=0.3)
ax = axs[0, 3]; 그리기(ax, 옆R); 윤곽(ax, 원S); ax.set_title("2바퀴 조립 옆 (+x 에서 · 왼쪽 = 앞)"); ax.set_xlim(-60, 100); ax.set_ylim(-8, 318); ax.grid(alpha=0.3)
ax = axs[0, 4]; 그리기(ax, 보기R(-35, 10), False); ax.set_title("3/4 앞"); ax.axis("off")
ax = axs[0, 5]; 그리기(ax, 보기R(145, 10), False); ax.set_title("3/4 뒤"); ax.axis("off")
# 둘째 줄: 1바퀴 그림에서 같은 칸을 오려 붙임 (1바퀴 STL 은 남아 있지 않다)
try:
    im1 = np.array(Image.open(os.path.join(D, "조립_1바퀴.png")).convert("RGB")); W = im1.shape[1] // 6
    for k, (col, t) in enumerate(((1, "1바퀴 조립 정면"), (3, "1바퀴 조립 옆"))):
        ax = axs[1, k * 2]; ax.imshow(im1[:, col * W:(col + 1) * W]); ax.set_title(t + " (조립_1바퀴.png 오림)"); ax.axis("off")
except Exception as e: log("1바퀴 그림 없음", e)
ax = axs[1, 1]; 그리기(ax, 보기R(0, 0)); 윤곽(ax, 원F); ax.set_title("2바퀴 정면 (같은 칸)"); ax.set_xlim(-95, 95); ax.set_ylim(-8, 318); ax.grid(alpha=0.3)
ax = axs[1, 3]; 그리기(ax, 옆R); 윤곽(ax, 원S); ax.set_title("2바퀴 옆 (같은 칸)"); ax.set_xlim(-60, 100); ax.set_ylim(-8, 318); ax.grid(alpha=0.3)
ax = axs[1, 4]; 원그림(ax, "omega_back.png", BACK); ax.set_title("원화 뒤 (화면 X = −x)"); ax.set_xlim(-95, 95); ax.set_ylim(-8, 318); ax.grid(alpha=0.3)
ax = axs[1, 5]; 그리기(ax, 뒤R); 윤곽(ax, 원B); ax.set_title("2바퀴 조립 뒤 · 빨강 = 뒤 원화 윤곽"); ax.set_xlim(-95, 95); ax.set_ylim(-8, 318); ax.grid(alpha=0.3)
fig.suptitle("오메가몬 PG 디자인 판 2바퀴 조립 — D1 몸통 · D2 다리 · D3 머리어깨 (%d 부품 · %s g) · 칼 · 대포 없음" % (len(부품), sum(무게.values())), fontsize=16)
fig.tight_layout(); fig.savefig(os.path.join(D, f"조립_{TAG}.png"), dpi=80); plt.close(fig)
log("그림 1")
# ── 그림 2: 경계 확대 + 뼈 노출 지도 ──
fig, axs = plt.subplots(2, 4, figsize=(28, 20))
for ax, R, t, xl, yl in [(axs[0, 0], 보기R(0, 0), "정면 확대 목·어깨", (-65, 65), (215, 300)), (axs[0, 1], 보기R(0, 0), "정면 확대 골반", (-50, 50), (120, 215)),
                         (axs[0, 2], 옆R, "옆 확대 목·어깨", (-25, 60), (215, 300)), (axs[0, 3], 옆R, "옆 확대 골반", (-25, 60), (120, 215)),
                         (axs[1, 0], 보기R(0, 0), "정면 확대 L 팔꿈치·팔끝·손", (-95, -35), (140, 215)), (axs[1, 1], 뒤R, "뒤 확대 골반·오금", (-50, 50), (90, 215))]:
    그리기(ax, R); 윤곽(ax, 원F if R is not 옆R and R is not 뒤R else (원S if R is 옆R else 원B)); ax.set_xlim(*xl); ax.set_ylim(*yl); ax.set_title(t); ax.grid(alpha=0.3)
for ax, 보기이름, R in ((axs[1, 2], "정면", 보기R(0, 0)), (axs[1, 3], "옆", 옆R)):
    pid, bid = id렌더(R); img = np.ones(pid.shape + (3,)); img[pid > 0] = (0.85, 0.85, 0.87); img[bid > 0] = (0.1, 0.7, 0.1)
    ax.imshow(img.transpose(1, 0, 2), origin="lower", extent=[-90, 90, -10, 340]); ax.set_title("%s 뼈 노출 %s mm² (초록)" % (보기이름, 노출[보기이름]["합mm2"])); ax.set_ylim(-8, 318)
fig.tight_layout(); fig.savefig(os.path.join(D, f"조립_{TAG}_경계.png"), dpi=80); plt.close(fig)
log("그림 2")
# ── 그림 3: 자세 (L 어깨들기 최대 + 방패 연동 · R 들기 90 · L 무릎 · L 앞차기 90 + 벌림) ──
if 가동:
    def 자세틀(jn, k, θ):
        j = 관[jn]; T = 틀(j, j["범위"][k]["축"], θ); 하 = 하위(j["자식뼈"]); return {**{n: T for n, v in 부품.items() if v[1] in 하}, **{b: T for b in 하}}   # 뼈도 같이
    포즈 = []
    g = 가동["L어깨들기[0] 방패연동"]; θL = g["+"]; φ = [r[1] for r in g["표(θ,φ,팔∩고정,방패∩고정)"] if r[0] == θL]; φ = φ[0] if φ else 0
    A1 = 자세틀("L어깨들기", 0, θL); Tφ = 강체(회전행렬([0, 1, 0], φ), 방패P); A1.update({"방패빨강": Tφ, "방패금": Tφ})
    A1.update(자세틀("R어깨들기", 0, 가동["R어깨들기[0]"]["+"]))
    포즈.append((A1, 보기R(0, 0), "L 들기 %d°(방패 φ %d°) · R 들기 %d°" % (θL, φ, 가동["R어깨들기[0]"]["+"])))
    A2 = 자세틀("L무릎", 0, 가동["L무릎[0]"]["+"]); A2.update(자세틀("L팔꿈치", 0, 가동["L팔꿈치[0]"]["+"]))
    포즈.append((A2, 옆R, "L 무릎 %d° · L 팔꿈치 %d° (옆)" % (가동["L무릎[0]"]["+"], 가동["L팔꿈치[0]"]["+"])))
    A3 = 자세틀("L고관절", 0, 가동["L고관절[0]"]["+"]); 포즈.append((A3, 옆R, "L 앞차기 %d° (옆)" % 가동["L고관절[0]"]["+"]))
    A4 = 자세틀("L고관절벌림", 0, 가동["L고관절벌림[0] 팔빼고"]["+"]); 포즈.append((A4, 보기R(0, 0), "L 벌림 %d° (팔 빼고 잰 값)" % 가동["L고관절벌림[0] 팔빼고"]["+"]))
    fig, axs = plt.subplots(1, 4, figsize=(28, 12))
    for ax, (A, R, t) in zip(axs, 포즈):
        그리기(ax, R, 자세=A); ax.set_title(t); ax.set_ylim(-8, 318); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(D, f"조립_{TAG}_가동.png"), dpi=80); plt.close(fig)
log("끝")
