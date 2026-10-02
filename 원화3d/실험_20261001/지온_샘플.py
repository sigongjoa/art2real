# -*- coding: utf-8 -*-
"""지온 데이터 타입 시각화 시험 — 받은 샘플 3D(Printables 1649494 Low Poly Mech Head · CC0)를 지온.py 그래프로 표현한다.
(10-02 사용자 「이 데이터 타입을 어떻게 시각화? 기존 샘플 3D 아무거나 받아서 표현해 보자」)
1) 출력판 STL 을 연결 조각으로 나눠 부품 5(투구 · 총 둘 · 핀 둘)  2) 구멍을 광선으로 찾아 조립(핀 반은 투구, 반은 총)
3) 부품마다 지온 4 속성을 3D 에서 자동으로 읽음(긴 축 단면 20 장: 원형도 · 넓이 변화 · 끝 넓이 · 중심선 휨)
4) 지온.py 그래프(붙음 · 관계 · 조인트) json + 부품 obj(조립 · 분해) → 지온_샘플_렌더.py 가 그린다."""
import os, sys, json, numpy as np, trimesh
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 지온 as G
D = r"G:\art2real\원화3d\out\샘플\메크머리_CC0"; O = os.path.join(D, "지온"); os.makedirs(O, exist_ok=True)

m = trimesh.load(os.path.join(D, "helmet-guns-and-connectors.stl"), force="mesh")
조각 = sorted([p for p in m.split(only_watertight=False) if p.volume > 1], key=lambda p: -p.volume)[:5]
투구, 총들, 핀들 = 조각[0], sorted(조각[1:3], key=lambda p: p.centroid[0]), sorted(조각[3:5], key=lambda p: p.centroid[0])

def 지온읽기(p, n=20):
    """긴 축 따라 단면 n 장 → (지온, 근거)."""
    c = p.centroid; ax = np.linalg.svd(p.vertices - c, full_matrices=False)[2][0]
    t = (p.vertices - c) @ ax; ts = np.linspace(t.min(), t.max(), n + 2)[1:-1]
    A, R, C = [], [], []
    for s in ts:
        sec = p.section(plane_origin=c + ax * s, plane_normal=ax)
        if sec is None: A.append(0); R.append(0); C.append(c + ax * s); continue
        pl, _ = sec.to_2D(); a = sum(q.area for q in pl.polygons_full); per = sum(q.exterior.length for q in pl.polygons_full)
        A.append(a); R.append(4 * np.pi * a / per**2 if per else 0); C.append(sec.vertices.mean(0))
    A = np.array(A); R = np.array(R); C = np.array(C); L = t.max() - t.min()
    단면 = G.단면.둥 if np.median(R[A > 0]) > 0.93 else G.단면.각    # 정팔각 0.95 · 모깎은 팔각 ~0.88 → 0.93 위만 둥
    off = np.linalg.norm((C - c) - np.outer((C - c) @ ax, ax), axis=1).max() / L
    축 = G.축.휨 if off > 0.08 else G.축.곧
    mid = A[n // 5: -n // 5].mean(); e1, e2 = sorted([A[: n // 5].mean(), A[-n // 5:].mean()])
    rng = (A.max() - A.min()) / max(A.mean(), 1e-9)
    if rng < 0.3: 크기 = G.크기.일정
    elif e1 < 0.5 * e2: 크기 = G.크기.좁아짐          # 한 끝만 작음
    elif mid > 1.15 * e2: 크기 = G.크기.불룩
    elif mid < 0.85 * e1: 크기 = G.크기.잘록
    else: 크기 = G.크기.일정
    tip = min(A[0], A[-1]) / max(A.max(), 1e-9)
    끝 = G.끝.뾰족 if tip < 0.2 else (G.끝.둥긂 if tip < 0.6 else G.끝.잘림)
    return G.지온(단면, 축, 크기, 끝), {"원형도중앙": round(float(np.median(R[A > 0])), 2), "중심선휨/길이": round(float(off), 3), "넓이변화": round(float(rng), 2), "끝넓이비": round(float(tip), 2), "길이mm": round(float(L), 1)}

def 구멍(p, 방향들):
    """방향마다 바깥에서 광선을 쏴 표면에서 3 mm 넘게 더 들어가는 점들 = 구멍. 가장 큰 무리의 방향 · 중심 · 깊이."""
    best = None; ri = trimesh.ray.ray_triangle.RayMeshIntersector(p)
    for d in 방향들:
        d = np.array(d, float); u = np.cross(d, [0, 0, 1] if abs(d[2]) < 0.9 else [1, 0, 0]); u /= np.linalg.norm(u); v = np.cross(d, u)
        c = p.centroid; ext = p.extents.max(); g = np.linspace(-ext / 2, ext / 2, 60)
        o = np.array([c - d * ext + u * a + v * b for a in g for b in g])
        loc, idx, _ = ri.intersects_location(o, np.repeat(d[None], len(o), 0), multiple_hits=False)
        if len(idx) < 50: continue
        depth = (loc - o[idx]) @ d; base = np.percentile(depth, 20)
        deep = depth > base + 3
        if deep.sum() < 5: continue
        pts = loc[deep]; mouth = o[idx][deep] + d * base
        cand = (int(deep.sum()), d, mouth.mean(0), float(np.median(depth[deep] - base)))
        if best is None or cand[0] > best[0]: best = cand
    return best

# 투구 구멍: ±x · 총 구멍: 네 옆
h_holes = {s: 구멍(투구, [(s, 0, 0)]) for s in (-1, 1)}
g_holes = [구멍(g, [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)]) for g in 총들]
for s, h in h_holes.items(): print("투구 구멍", s, None if h is None else (h[0], h[2].round(1), round(h[3], 1)))
for g in g_holes: print("총 구멍", None if g is None else (g[0], g[1], g[2].round(1), round(g[3], 1)))

# 조립: 투구는 그대로. 핀 축 = x · 반은 투구 구멍 안. 총은 구멍이 투구 쪽(-s)을 보게 돌려 핀 바깥 끝에.
def 축맞춤(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b); v = np.cross(a, b); c = a @ b
    if np.linalg.norm(v) < 1e-9: return np.eye(4) if c > 0 else trimesh.transformations.rotation_matrix(np.pi, [0, 0, 1])
    return trimesh.transformations.rotation_matrix(np.arccos(np.clip(c, -1, 1)), v)
조립 = {"투구": 투구.copy()}; 붙는자리 = {}
for k, s in enumerate((-1, 1)):
    _, d, mouth, depth = h_holes[s]               # d = 광선 방향(바깥 → 안) = (s,0,0) 이면 -s 쪽 면에서 들어감
    이름 = "왼" if mouth[0] < 투구.centroid[0] else "오른"   # 쪽은 실제 자리로(찾은 순서 아님)
    pin = 핀들[k].copy(); pax = np.linalg.svd(pin.vertices - pin.centroid, full_matrices=False)[2][0]
    pin.apply_transform(축맞춤(pax, np.array([1., 0, 0]))); pin.apply_translation(-pin.centroid)
    plen = pin.extents[0]; pin.apply_translation(mouth - d * (plen / 2 - min(depth, plen / 2)))   # 구멍 깊이만큼 안에
    조립[f"핀/{이름}"] = pin; 붙는자리[f"핀/{이름}"] = mouth
    gun = 총들[k].copy(); gh = g_holes[k]; gd = gh[1]
    gun.apply_transform(축맞춤(-gd, d)); T = trimesh.transformations.rotation_matrix(0, [0, 0, 1])
    gh2 = 구멍(gun, [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)])
    pin_out = mouth - d * (plen - min(depth, plen / 2)); gun.apply_translation(pin_out - gh2[2] + d * min(gh2[3], plen / 2))
    조립[f"총/{이름}"] = gun; 붙는자리[f"총/{이름}"] = pin_out

# 그래프
g = G.그래프(); 근거 = {}
for 키, p in 조립.items():
    j, why = 지온읽기(p); 이름, 쪽 = (키.split("/") + ["가운데"])[:2]; 근거[키] = why
    g.더하기(G.부품(이름, 쪽, {"투구": 0, "총": 1, "핀": 2}[이름], j, "3D", [G.관찰("3D", [], j, {"폭": round(float(p.extents[0]), 1), "깊이": round(float(p.extents[1]), 1), "높이": round(float(p.extents[2]), 1)}, json.dumps(why, ensure_ascii=False))]))
for 쪽 in ("왼", "오른"):
    g.붙음들.append(G.붙음(f"핀/{쪽}", "투구/가운데", G.관계.안, "핀", "투구 옆 구멍(광선)"))
    g.붙음들.append(G.붙음(f"총/{쪽}", f"핀/{쪽}", G.관계.끝가운데, "핀(회전)", "총 옆 구멍에 핀 끝"))
경보 = g.검사(); print("검사", 경보)
g.저장(os.path.join(O, "그래프.json"))
# 분해: 자식은 부모에서 조인트 방향(바깥 x)으로 25 mm 씩 — 누적
펼침 = {"투구/가운데": np.zeros(3)}
for e in g.붙음들:
    s = -1 if e.자식.endswith("왼") else 1; 펼침[e.자식] = 펼침[e.부모] + np.array([s * 25.0, 0, 0])
    assert np.sign(조립[e.자식].centroid[0] - 투구.centroid[0]) == s, e.자식   # 펼침 방향 = 실제 쪽
for 키, p in 조립.items():
    k2 = 키 if "/" in 키 else 키 + "/가운데"; p.export(os.path.join(O, f"조립_{k2.replace('/', '_')}.obj"))
    q = p.copy(); q.apply_translation(펼침[k2]); q.export(os.path.join(O, f"분해_{k2.replace('/', '_')}.obj"))
json.dump({"근거": 근거, "붙는자리": {k: v.round(2).tolist() for k, v in 붙는자리.items()}, "펼침": {k: v.tolist() for k, v in 펼침.items()}, "경보": 경보},
          open(os.path.join(O, "자리.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k, p in g.부품들.items(): print(k, p.지온, 근거[k if k != "투구/가운데" else "투구"])
