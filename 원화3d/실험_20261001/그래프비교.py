# -*- coding: utf-8 -*-
"""연결 그래프 비교 (10-05 사용자 「우리 3D 로 뽑은 데이터도 연결 관계 파악」)
우리 CAD v62: 부품 STL 마다 노드 · 두 부품 표면 점 사이 거리 < 1 단위인 표본 비율 × 넓이 = 맞닿음
TripoSG T6: 부분그래프 json(PartField 20) 의 「이름(눈)」을 같은 갈래로 묶음
둘 다 갈래(뿔 · 안테나 · 차양 · 돔 · 눈 · 얼굴 · 아래 얼굴 · 볼 · 속)끼리의 맞닿음 표 → 차이"""
import json, itertools, numpy as np, trimesh
from scipy.spatial import cKDTree
SC = "C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/7cb277a7-139e-42d2-8434-a71e5084b8ad/scratchpad/cad/"
갈래C = {"horn": "뿔", "antenna": "안테나", "visor": "차양", "helmet": "돔", "faceplate": "얼굴", "eye": "눈", "socket": "눈", "mask": "아래 얼굴", "spike": "볼", "core": "속"}
P = {}
for f, g in 갈래C.items():
    try: m = trimesh.load(SC + f"{f}_v62.stl")
    except Exception: continue
    pts, _ = trimesh.sample.sample_surface(m, max(2000, int(m.area / 4))); P[f] = (pts, m.area)
C = {}
for a, b in itertools.combinations(P, 2):
    da, _ = cKDTree(P[b][0]).query(P[a][0]); r = (da < 1.0).mean() * P[a][1]
    ga, gb = sorted((갈래C[a], 갈래C[b]))
    if ga != gb and r > 1: C[(ga, gb)] = C.get((ga, gb), 0) + r
G = json.load(open("G:/art2real/원화3d/out/오메가몬2/지표/트리포분할/트리포_T6_그래프20.json", encoding="utf-8"))
def 갈래T(s):
    for k in ("뿔", "안테나", "차양", "돔", "아래 얼굴", "볼", "눈", "얼굴"):
        if k in s: return k
    if "옆" in s: return "돔"
    return None
nm = {d["id"]: 갈래T(d["이름(눈)"]) for d in G["노드"] if "지움" not in d["이름(눈)"]}
T = {}
for e in G["간선"]:
    a, b = nm.get(e["a"]), nm.get(e["b"])
    if a and b and a != b:
        k = tuple(sorted((a, b))); T[k] = T.get(k, 0) + e["경계"]
keys = sorted(set(C) | set(T))
rows = []
for k in keys:
    c, t = C.get(k, 0), T.get(k, 0)
    판 = "둘 다" if c and t else ("TripoSG 에만" if t else "우리에만")
    rows.append((k, round(t, 1), round(c, 1), 판)); print(f"{k[0]:>6} – {k[1]:<6} | TripoSG 경계 {t:7.1f} | 우리 맞닿음 {c:8.1f} | {판}")
json.dump([{"짝": list(k), "TripoSG": t, "우리": c, "판": p} for k, t, c, p in rows], open("G:/art2real/원화3d/out/오메가몬2/지표/트리포분할/그래프비교_v62_T6.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
