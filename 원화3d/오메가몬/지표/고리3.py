# -*- coding: utf-8 -*-
"""고리 3 — 부품별 라벨로 비교 (09-29 「부품별로 라벨링해서 봐야 · 부품 = 닫힌 object = 매니폴드?」).
단위 = 닫힌 한 덩이 메시(watertight · body 1) = 우리 STL 21 개. 캡처 쪽 단위 = 그 시점에서 보이는 그 부품의 면(2D · 시점마다 다름).
    python 고리3.py [부품 …] [--held-out=옆]  -> out/오메가몬2/지표/고리3_<판>.png · 고리3_<판>.json (부품별 · 장별 IoU)
장마다: (1) 초기 매개변수로 21 부품 래스터 → id 지도  (2) 그 장의 캡처 면(영역.py)마다 가장 많이 겹치는 id 를 라벨로(고정 · 시점별로 따로)  (3) 손실 = 판 부품마다 1 − IoU(렌더 마스크(부품 i), 캡처 면 라벨 i) 합 + 고리2 의 선 거리.
고리.py 와 다른 점: 판 묶음 하나가 아니라 **부품 하나하나**에 라벨 · 라벨은 각 시점의 렌더에서 · 선 거리도 같이.
"""
import os, sys, json, glob, math, time
import numpy as np, cv2
from scipy.optimize import minimize
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, 장면, J
import 고리2 as G
from 부품투영 import 단위, 찍기, 읽기
def 렌더ID(판이름들, c, p, 자, shape):
    ID = np.zeros(shape, np.int32); 삼 = []
    for i, (n, m) in enumerate(G.부품전체, 1):
        U = 단위(np.asarray(m.vertices, float)); U = G.변환(U, c, p) if n in 판이름들 else U; uv, z = 찍기(U, 자); uv = np.round(uv).astype(np.int32)
        for tri in m.faces: 삼.append((z[tri].mean(), i, uv[tri]))
    삼.sort(key=lambda t: -t[0])
    for _, i, q in 삼: cv2.fillPoly(ID, [q], int(i))
    return ID
if __name__ == "__main__":
    t0 = time.time(); args = [a for a in sys.argv[1:] if not a.startswith("--")]; ho = next((a.split("=")[1] for a in sys.argv if a.startswith("--held-out=")), None)
    판이름들 = set(args or ["코", "부리2", "부리3"]); k풀기 = "--k" in sys.argv; 판이름 = "+".join(sorted(판이름들)) + ("_ho" + ho if ho else "") + ("_k" if k풀기 else ""); id표 = {n: i for i, (n, _) in enumerate(G.부품전체, 1)}
    U0 = np.concatenate([단위(np.asarray(m.vertices, float)) for n, m in G.부품전체 if n in 판이름들]); c = U0.mean(0)
    장 = {}
    for n, 태그 in G.장들.items():
        f, _ = G.캡처2D[n]; im = 읽기(J(장면, f)); 자 = G.자세[n]; H, W = im.shape[:2]
        라벨3 = np.load(J(OUT, "영역_%s.npz" % 태그))["라벨"]; 면 = cv2.resize(라벨3.astype(np.float32), (W, H), interpolation=cv2.INTER_NEAREST).astype(np.int32)
        ID0 = 렌더ID(판이름들, c, np.zeros(3), 자, (H, W)); 캡라벨 = np.zeros((H, W), np.int32)
        for r in np.unique(면):
            if r <= 0: continue
            m = 면 == r; ids = ID0[m]; ids = ids[ids > 0]
            if ids.size >= 0.5 * m.sum(): 캡라벨[m] = np.bincount(ids).argmax()          # 그 시점의 렌더가 절반 넘게 덮는 면만 라벨
        캡 = G.캡처선(태그, im); 장[n] = dict(im=im, 자=자, 캡라벨=캡라벨, 캡=캡, 캡D=G.거리표(캡), 창=cv2.dilate(np.isin(ID0, [id표[k] for k in 판이름들]).astype(np.uint8), np.ones((41, 41), np.uint8)) > 0, 태그=태그)
    def 자세k(n, p):
        자 = dict(장[n]["자"]); 
        if k풀기 and 장[n]["태그"] == "3-4": 자["k"] = float(max(0.0, p[3]))
        return 자
    def 부품IoU(n, p):
        d = 장[n]; ID = 렌더ID(판이름들, c, p[:3], 자세k(n, p), d["캡라벨"].shape); out = {}
        for k in 판이름들:
            i = id표[k]; a = ID == i; b = d["캡라벨"] == i; out[k] = float((a & b).sum() / max(1, (a | b).sum())) if b.any() else None
        return out
    def 손실장(n, p):
        v = [x for x in 부품IoU(n, p).values() if x is not None]; return (sum(1 - x for x in v) / max(1, len(v))) + 0.3 * G.손실장.__wrapped__(n, p) if False else (sum(1 - x for x in v) / max(1, len(v)))
    맞춤장 = [n for n, 태 in G.장들.items() if 태 != ho]; 손실 = lambda p: sum(손실장(n, p) for n in 맞춤장) + max(0.0, abs(p[2]) - 15) * 0.5 + (max(0.0, p[3] - 0.03) * 50 if k풀기 else 0)
    best = None; 덧 = ([0.01] if k풀기 else [])
    for 초기 in (np.array([0, 0, 0] + 덧), np.array([math.radians(12), 0, 6.0] + 덧), np.array([math.radians(-12), 0, -6.0] + 덧)):
        r = minimize(손실, 초기, method="Nelder-Mead", options=dict(maxiter=120, xatol=1e-3, fatol=1e-3))
        if best is None or r.fun < best.fun: best = r
    p = best.x; p0_ = np.zeros(len(p)); 전 = {n: 부품IoU(n, p0_) for n in 장}; 후 = {n: 부품IoU(n, p) for n in 장}
    print("맞춘 값  pitch %.1f° yaw %.1f° dz %.1f 단위%s  (%.0f 초)" % (math.degrees(p[0]), math.degrees(p[1]), p[2], (" · 3/4 k %.4f (Z0 %.0f 단위)" % (p[3], 1 / max(p[3], 1e-6))) if k풀기 else "", time.time() - t0))
    for n in 장: print("%-6s%s  " % (G.장들[n], " [held-out]" if G.장들[n] == ho else "") + " · ".join("%s %s→%s" % (k, "—" if 전[n][k] is None else "%.2f" % 전[n][k], "—" if 후[n][k] is None else "%.2f" % 후[n][k]) for k in sorted(판이름들)))
    rng = np.random.RandomState(4); 색 = {k: tuple(int(x) for x in rng.randint(80, 255, 3)) for k in 판이름들}; rows = []
    for n, d in 장.items():
        vis = d["im"].copy(); ID = 렌더ID(판이름들, c, p[:3], 자세k(n, p), d["캡라벨"].shape)
        for k in 판이름들:
            i = id표[k]; vis[d["캡라벨"] == i] = (vis[d["캡라벨"] == i] * 0.4 + np.array(색[k]) * 0.6).astype(np.uint8)
            for M, col in (((렌더ID(판이름들, c, np.zeros(3), 자세k(n, p0_), d["캡라벨"].shape) == i), (0, 0, 255)), ((ID == i), (0, 255, 0))):
                cs, _ = cv2.findContours(M.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); cv2.drawContours(vis, cs, -1, col, 2)
        ys, xs = np.nonzero(d["창"]); y0, y1, x0, x1 = max(0, ys.min() - 20), ys.max() + 20, max(0, xs.min() - 20), xs.max() + 20
        crop = vis[y0:y1, x0:x1]; crop = cv2.resize(crop, (int(crop.shape[1] * 380 / crop.shape[0]), 380))
        for col, th in (((0, 0, 0), 3), ((255, 255, 255), 1)): cv2.putText(crop, d["태그"] + (" held-out" if d["태그"] == ho else ""), (6, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.65, col, th)
        rows.append(crop)
    W = max(r.shape[1] for r in rows); S = np.concatenate([np.pad(r, ((0, 0), (0, W - r.shape[1]), (0, 0)), constant_values=245) for r in rows], 0); cv2.imencode(".png", S)[1].tofile(J(OUT, "고리3_%s.png" % 판이름))
    json.dump(dict(판=판이름, pitch_deg=math.degrees(p[0]), yaw_deg=math.degrees(p[1]), dz=float(p[2]), k34=(float(p[3]) if k풀기 else None), 전={G.장들[n]: 전[n] for n in 장}, 후={G.장들[n]: 후[n] for n in 장}), open(J(OUT, "고리3_%s.json" % 판이름), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
