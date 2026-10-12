# -*- coding: utf-8 -*-
"""정답 부품 라벨 — 사람 부품 메시만 보고 규칙으로 단다(우리 결과는 안 봄) · 판정 뒤 라벨별 통과율로 「잘하는 것 · 못하는 것」 · 10-11
python runs/기능0/라벨.py  →  라벨.json {"시험/NN" | "검증/NN": {부품, 모델, 이름, 수치, 라벨[]}}
문턱은 판정 전에 얼린다(판정기준12 와 같은 커밋 다음엔 안 바꾼다)."""
import os, sys, json, numpy as np, trimesh
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R)
sys.path[:0] = [os.path.join(T0, "s0"), os.path.join(T0, "s0", "stub")]
from s0 import unit
from 모양자 import _occ, _거친위상, _닫힘
RR = "G:/art2real/원화3d/out/레퍼런스/사람분할/"
문턱 = {"상자형_평면비": 0.75, "곡면_평면비": 0.45, "얇음_두께비": 0.08, "속빔_볼록비": 0.45, "막대_길이비": 3.0, "디테일_평면수": 25}
def 재(m):
    m = unit(m); e = np.sort(m.extents)
    def 판판(f):   # trimesh facets 는 이웃 면 각만 봐서 잘게 나눈 곡면도 한 판으로 묶는다 → 꼭짓점이 실제로 한 평면 위(0.3 %)인 것만
        v = m.vertices[np.unique(m.faces[f])]; n = m.face_normals[f[0]]; d = (v - v.mean(0)) @ n; return np.abs(d).max() < 0.003
    판 = [f for f in m.facets if 판판(f)]   # 곡면을 나눈 작은 네모(삼각형 둘)도 판판하다 → 넓이 0.5 % 넘는 판만 「평면」 (ponytail: 반지름 큰 완만한 곡면 #23 은 평면으로 샘)
    큰판 = [f for f in 판 if m.area_faces[f].sum() >= 0.005 * m.area]; 평면비 = float(sum(m.area_faces[f].sum() for f in 큰판) / m.area)
    닫힘 = _닫힘(m); V = abs(m.volume) if 닫힘 else float("nan")
    두께비 = 2 * V / m.area / e[2] if 닫힘 else float("nan"); 볼록비 = V / m.convex_hull.volume if 닫힘 else float("nan")
    n = 96; g = (np.indices((n, n, n)).reshape(3, -1).T + 0.5) / n; b0, 구멍 = _거친위상(_occ(m, g).reshape(n, n, n), k=3) if 닫힘 else (len(m.split(only_watertight=False)), -1)
    return {"평면비": round(평면비, 3), "두께비": round(두께비, 3), "볼록비": round(볼록비, 3), "길이비": round(float(e[2] / max(e[1], 1e-6)), 2), "평면수": len(큰판), "덩이": int(b0), "구멍": int(구멍), "닫힘": bool(닫힘)}
def 라벨(x):
    t = 문턱; L = []
    L.append("상자형" if x["평면비"] >= t["상자형_평면비"] else "곡면" if x["평면비"] < t["곡면_평면비"] else "섞임")
    if x["두께비"] == x["두께비"] and x["두께비"] < t["얇음_두께비"]: L.append("얇은 판·껍질")
    if x["볼록비"] == x["볼록비"] and x["볼록비"] < t["속빔_볼록비"]: L.append("속 빔·오목")
    if x["길이비"] >= t["막대_길이비"]: L.append("막대")
    if x["구멍"] > 0: L.append("관통 구멍")
    if x["덩이"] > 1: L.append("여러 덩이")
    if x["평면수"] >= t["디테일_평면수"]: L.append("디테일 많음")
    if not x["닫힘"]: L.append("열린 메시")
    return L
if __name__ == "__main__":
    세트들 = sys.argv[1:] or ["시험", "검증"]; LP = os.path.join(H, "라벨.json")
    out = json.load(open(LP, encoding="utf-8"))["부품"] if os.path.exists(LP) and sys.argv[1:] else {}   # 세트를 주면 있던 라벨에 덧붙임
    for 세트 in 세트들:
        부 = np.load(os.path.join(R, "깊이학습", 세트 + ".npz"))["부품"]
        for i, p in enumerate(부):
            if 세트 == "시험" and i == 30: continue   # 30 은 처음부터 뺀 부품
            x = 재(trimesh.load(RR + str(p), force="mesh")); 모델, 이름 = str(p).split("/")[0], os.path.splitext(os.path.basename(str(p)))[0]
            out["%s/%02d" % (세트, i)] = {"부품": str(p), "모델": 모델, "이름": 이름, "수치": x, "라벨": 라벨(x)}; print(세트, i, 이름, 라벨(x), flush=True)
    json.dump({"문턱": 문턱, "부품": out}, open(os.path.join(H, "라벨.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    from collections import Counter
    for 세트 in 세트들: print(세트, dict(Counter(l for k, v in out.items() if k.startswith(세트) for l in v["라벨"])))
