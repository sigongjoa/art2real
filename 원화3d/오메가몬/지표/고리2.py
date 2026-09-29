# -*- coding: utf-8 -*-
"""고리 2 — 시점마다 **렌더에서 새로 뽑은** 선(실루엣 테두리 · 부품 이음선)을 **그 시점의** 캡처 선(실루엣 컨투어 · Sobel)과 비교한다.
(09-29 「시점이 바뀌면 새로운 컨투어랑 소벨을 봐야지 왜 다른 거를 같다고 보나」 — 고리.py 는 정면에서 고른 면을 다른 장에도 같은 것으로 썼다. 여기서는 3D 라벨을 장 사이로 옮기지 않는다.)
    python 고리2.py [부품 …] [--held-out=옆]  -> out/오메가몬2/지표/고리2_<판>.png · 고리2_<판>.json
장마다: 머리 부품 21 개 전부(판은 매개변수로 옮긴 채) 래스터 → 부품 id 지도 → 렌더 선 = id 경계(이음선 + 실루엣 테두리).  캡처 선 = 실루엣 컨투어 ∪ 실루엣 안 Sobel(그 장에서 새로).
손실(장) = 판 둘레 창 안에서 렌더 선 → 캡처 선 평균 거리 + 캡처 선 → 렌더 선 평균 거리 (머리 단위). 세 장 합. --held-out=옆 이면 옆은 맞춤에서 빼고 심판만.
"""
import os, sys, json, glob, math, time
import numpy as np, cv2, trimesh
from scipy.optimize import minimize
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, 장면, J
from 부품투영 import 단위, 찍기, 읽기, 머리mm, cx_mm, top_mm
from 자세 import 캡처 as 캡처2D
from 소벨 import 소벨선
자세 = json.load(open(J(OUT, "자세2.json"), encoding="utf-8")); D6 = J(OUT, "..", "머리", "단계4")
장들 = {"정면 yt_172": "정면", "3/4 M04": "3-4", "옆 yt_235": "옆"}
부품전체 = [(os.path.basename(f)[:-4], trimesh.load(f, process=False, force="mesh")) for f in sorted(glob.glob(J(D6, "*.stl"))) if os.path.basename(f) != "프레임.stl"]
def 변환(U, c, p):
    pitch, yaw, dz = p; R = cv2.Rodrigues(np.array([pitch, 0, 0.0]))[0] @ cv2.Rodrigues(np.array([0, yaw, 0.0]))[0]; return (U - c) @ R.T + c + np.array([0, 0, dz])
def 렌더선(판이름들, c, p, 자, shape):
    """부품 21 개 래스터(화가 알고리즘) → id 지도 → 경계 = 그 시점의 이음선 + 실루엣 테두리. 판에 든 부품만 변환."""
    ID = np.zeros(shape, np.int32); 삼 = []
    for i, (n, m) in enumerate(부품전체, 1):
        U = 단위(np.asarray(m.vertices, float)); U = 변환(U, c, p) if n in 판이름들 else U; uv, z = 찍기(U, 자); uv = np.round(uv).astype(np.int32)
        for tri in m.faces: 삼.append((z[tri].mean(), i, uv[tri]))
    삼.sort(key=lambda t: -t[0])
    for _, i, q in 삼: cv2.fillPoly(ID, [q], int(i))
    e = (cv2.Laplacian(ID.astype(np.float32), cv2.CV_32F) != 0); 판마스크 = np.isin(ID, [i for i, (n, _) in enumerate(부품전체, 1) if n in 판이름들]); return e, 판마스크
def 캡처선(태그, im):
    c_ = np.load(J(OUT, "윤곽2_%s_전체.npy" % 태그)); sil = np.zeros(im.shape[:2], np.uint8); cv2.fillPoly(sil, [c_.astype(np.int32)], 1)
    테 = cv2.Laplacian(sil.astype(np.float32), cv2.CV_32F) != 0; _, sob = 소벨선(cv2.bilateralFilter(im, 7, 30, 7)); 안 = cv2.erode(sil, np.ones((5, 5), np.uint8)) > 0
    return 테 | ((sob > 0) & 안)
def 거리표(e): return cv2.distanceTransform((~e).astype(np.uint8), cv2.DIST_L2, 3)
if __name__ == "__main__":
    t0 = time.time(); args = [a for a in sys.argv[1:] if not a.startswith("--")]; ho = next((a.split("=")[1] for a in sys.argv if a.startswith("--held-out=")), None)
    판이름들 = set(args or ["코", "부리2", "부리3"]); 판이름 = "+".join(sorted(판이름들)) + ("_ho" + ho if ho else "")
    U0 = np.concatenate([단위(np.asarray(m.vertices, float)) for n, m in 부품전체 if n in 판이름들]); c = U0.mean(0)
    장 = {}
    for n, 태그 in 장들.items():
        f, _ = 캡처2D[n]; im = 읽기(J(장면, f)); 자 = 자세[n]; 캡 = 캡처선(태그, im); e0, 판0 = 렌더선(판이름들, c, np.zeros(3), 자, im.shape[:2])
        창 = cv2.dilate(판0.astype(np.uint8), np.ones((41, 41), np.uint8)) > 0; 장[n] = dict(im=im, 자=자, 캡=캡, 캡D=거리표(캡), 창=창, 태그=태그)
    def 손실장(n, p):
        d = 장[n]; e, 판 = 렌더선(판이름들, c, p, d["자"], d["캡"].shape); 창 = d["창"] & cv2.dilate(판.astype(np.uint8), np.ones((41, 41), np.uint8)).astype(bool)
        rE = e & 창; rC = d["캡"] & 창; u = d["자"]["s"]
        if rE.sum() == 0 or rC.sum() == 0: return 10.0
        return float(d["캡D"][rE].mean() + 거리표(e)[rC].mean()) / u / 2
    맞춤장 = [n for n, 태 in 장들.items() if 태 != ho]; 손실 = lambda p: sum(손실장(n, p) for n in 맞춤장) + max(0.0, abs(p[2]) - 15) * 0.5
    best = None
    for 초기 in (np.zeros(3), np.array([math.radians(12), 0, 6.0]), np.array([math.radians(-12), 0, -6.0])):
        r = minimize(손실, 초기, method="Nelder-Mead", options=dict(maxiter=120, xatol=1e-3, fatol=1e-3))
        if best is None or r.fun < best.fun: best = r
    p = best.x; 전 = {n: round(손실장(n, np.zeros(3)), 2) for n in 장}; 후 = {n: round(손실장(n, p), 2) for n in 장}
    print("맞춘 값  pitch %.1f° yaw %.1f° dz %.1f 단위  (%.0f 초)" % (math.degrees(p[0]), math.degrees(p[1]), p[2], time.time() - t0))
    print("점수판(선 거리 · 단위 · 낮을수록)  " + " · ".join("%s %.2f→%.2f%s" % (장들[n], 전[n], 후[n], " [held-out]" if 장들[n] == ho else "") for n in 장))
    rows = []
    for n, d in 장.items():
        vis = d["im"].copy(); vis[d["캡"]] = (255, 120, 0)
        for pp, col in ((np.zeros(3), (0, 0, 255)), (p, (0, 255, 0))):
            e, 판 = 렌더선(판이름들, c, pp, d["자"], d["캡"].shape); vis[e & d["창"]] = col
        ys, xs = np.nonzero(d["창"]); y0, y1, x0, x1 = max(0, ys.min() - 20), ys.max() + 20, max(0, xs.min() - 20), xs.max() + 20
        crop = vis[y0:y1, x0:x1]; crop = cv2.resize(crop, (int(crop.shape[1] * 380 / crop.shape[0]), 380))
        for col, th in (((0, 0, 0), 3), ((255, 255, 255), 1)): cv2.putText(crop, "%s %.2f->%.2f%s" % (d["태그"], 전[n], 후[n], " held-out" if d["태그"] == ho else ""), (6, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.65, col, th)
        rows.append(crop)
    W = max(r.shape[1] for r in rows); S = np.concatenate([np.pad(r, ((0, 0), (0, W - r.shape[1]), (0, 0)), constant_values=245) for r in rows], 0); cv2.imencode(".png", S)[1].tofile(J(OUT, "고리2_%s.png" % 판이름))
    json.dump(dict(판=판이름, pitch_deg=math.degrees(p[0]), yaw_deg=math.degrees(p[1]), dz=float(p[2]), 전=전, 후=후, 초=round(time.time() - t0)), open(J(OUT, "고리2_%s.json" % 판이름), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
