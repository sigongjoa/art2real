# -*- coding: utf-8 -*-
"""자동 대응점 — Sobel 선 접점(junction)을 장마다 뽑고, 풀린 자세(랜드마크3D.json)로 에피폴라 선을 그어 짝지은 뒤 삼각측량 (09-29 「일단 해보자」).
    python 접점.py -> out/오메가몬2/지표/접점_<장>.png (접점 흰 · 짝지어진 것 색 + 번호) · 접점.json (3D 점 · 재투영 잔차) · 표: 손 랜드마크 15 개와의 거리
약원근: u = s·(R·X̃)[:2] + t, X̃ = X·(1,1,−1). A 장의 점 u_A 는 3D 직선 X̃ = R_Aᵀ[a, w] (a = (u_A − t_A)/s_A) → B 장에서 직선 p0 + w·d. 그 직선 가까이(ε 단위) 있는 B 접점이 후보.
짝: 상호 최근접(A→B, B→A 둘 다) + 좌우 거울 점도 두 장에서 접점 근처에 있으면 가산. 삼각측량 = 두 장 4 식 · 3 미지수 최소제곱.
검산: 손으로 읽은 랜드마크 15 종(맞춤값) 마다 가장 가까운 자동 3D 점까지 거리(단위). 이 거리가 판독 오차(≈3) 안이면 자동 점이 손 점을 대신할 수 있다.
"""
import os, sys, json
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, 장면, J
from 소벨 import 소벨선, 읽기
F = json.load(open(J(OUT, "랜드마크3D.json"), encoding="utf-8")); 자세 = F["자세"]; LM = {**F["반쪽"], **F["가운데"]}
장 = {"정면 yt_172": ("yt_172.0_얼굴_정면.jpg", (690, 10, 1180, 505)), "3/4 M04": ("wk_Omegamon_M04.jpg", (830, 0, 1440, 700)), "옆 yt_235": ("yt_235.0_머리_옆.jpg", (400, 0, 990, 305))}
S = 3; ε = 4.0; 뭉침 = 5
def 접점찾기(f, box):
    im = 읽기(J(장면, f)); x0, y0, x1, y1 = box; c = im[y0:y1, x0:x1]; c3 = cv2.bilateralFilter(cv2.resize(c, None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC), 7, 30, 7)
    _, e = 소벨선(c3); sk = (e > 0).astype(np.uint8); nb = cv2.filter2D(sk, -1, np.ones((3, 3), np.float32)) - sk
    jn = ((sk > 0) & (nb >= 3)).astype(np.uint8); n, lab, st, cen = cv2.connectedComponentsWithStats(cv2.dilate(jn, np.ones((뭉침, 뭉침), np.uint8)))
    pts = np.array([[cen[i][0] / S + x0, cen[i][1] / S + y0] for i in range(1, n)], float); return im, pts, e
def R_(n): return cv2.Rodrigues(np.asarray(자세[n]["r"], float))[0]
def 찍기(X, n): c = R_(n) @ (np.asarray(X, float) * (1, 1, -1)); return 자세[n]["s"] * c[:2] + np.asarray(자세[n]["t"])
def 직선(uA, A, B):
    """A 장의 점 → B 장에서의 에피폴라 직선 (p0, d) · w 는 A 카메라 깊이(단위)."""
    a = (np.asarray(uA) - np.asarray(자세[A]["t"])) / 자세[A]["s"]; M = R_(B) @ R_(A).T
    p0 = 자세[B]["s"] * (M[:2, :2] @ a) + np.asarray(자세[B]["t"]); d = 자세[B]["s"] * M[:2, 2]; return p0, d
def 거리(u, p0, d):
    dn = d / (np.linalg.norm(d) + 1e-9); v = u - p0; w = v @ dn; return np.abs(v[:, 0] * dn[1] - v[:, 1] * dn[0]), w / (np.linalg.norm(d) + 1e-9)
def 삼각(uA, A, uB, B):
    rows, rhs = [], []
    for u, n in ((uA, A), (uB, B)):
        R = R_(n); s = 자세[n]["s"]; t = np.asarray(자세[n]["t"]); rows += [s * R[0], s * R[1]]; rhs += [u[0] - t[0], u[1] - t[1]]
    Xt, res, *_ = np.linalg.lstsq(np.array(rows), np.array(rhs), rcond=None); return Xt * (1, 1, -1)
def 짝짓기(PA, A, PB, B):
    sB, sA = 자세[B]["s"], 자세[A]["s"]; near = {}
    for i, u in enumerate(PA):
        p0, d = 직선(u, A, B); dist, w = 거리(PB, p0, d); ok = (dist < ε * sB) & (np.abs(w) < 130)
        if ok.any(): j = int(np.argmin(np.where(ok, dist, 1e9))); near[i] = j
    back = {}
    for j, u in enumerate(PB):
        p0, d = 직선(u, B, A); dist, w = 거리(PA, p0, d); ok = (dist < ε * sA) & (np.abs(w) < 130)
        if ok.any(): back[j] = int(np.argmin(np.where(ok, dist, 1e9)))
    return [(i, j) for i, j in near.items() if back.get(j) == i]
if __name__ == "__main__":
    이름 = list(장); D = {n: 접점찾기(*장[n]) for n in 이름}; print({n: len(D[n][1]) for n in 이름})
    점3D = []; 색표 = {}
    for A, B in (("정면 yt_172", "3/4 M04"), ("정면 yt_172", "옆 yt_235"), ("3/4 M04", "옆 yt_235")):
        PA, PB = D[A][1], D[B][1]; 짝 = 짝짓기(PA, A, PB, B)
        for i, j in 짝:
            X = 삼각(PA[i], A, PB[j], B); eA = np.linalg.norm(찍기(X, A) - PA[i]) / 자세[A]["s"]; eB = np.linalg.norm(찍기(X, B) - PB[j]) / 자세[B]["s"]
            if max(eA, eB) > ε: continue
            k = len(점3D); 점3D.append(dict(X=[round(float(v), 1) for v in X], 장=[A, B], 잔차=round(float(max(eA, eB)), 2))); 색표.setdefault(A, {})[i] = k; 색표.setdefault(B, {})[j] = k
        print("%s ↔ %s: 짝 %d" % (A, B, len(짝)))
    # 검산: 손 랜드마크와의 거리
    P = np.array([p["X"] for p in 점3D]) if 점3D else np.zeros((0, 3)); 표 = {}
    for k, v in LM.items():
        for s, nm in ((1, k + ("R" if k in F["반쪽"] else "")), (-1, k + "L")):
            if k in F["가운데"] and s < 0: continue
            X = np.array(v) * (s, 1, 1); d = np.linalg.norm(P - X, axis=1).min() if len(P) else np.nan; 표[nm] = round(float(d), 1)
    print("자동 3D 점", len(점3D), "· 손 랜드마크 → 가장 가까운 자동 점 거리(단위): 중앙값 %.1f" % np.nanmedian(list(표.values())))
    for nm, d in sorted(표.items(), key=lambda kv: kv[1]): print("  %-14s %5.1f" % (nm, d))
    rng = np.random.RandomState(3); 색 = rng.randint(60, 255, (max(1, len(점3D)), 3))
    for n in 이름:
        im, pts, e = D[n]; vis = im.copy()
        for i, (x, y) in enumerate(pts):
            k = 색표.get(n, {}).get(i)
            if k is None: cv2.circle(vis, (int(x), int(y)), 3, (255, 255, 255), 1)
            else: cv2.circle(vis, (int(x), int(y)), 5, tuple(int(c) for c in 색[k]), -1); cv2.putText(vis, str(k), (int(x) + 5, int(y) - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 2); cv2.putText(vis, str(k), (int(x) + 5, int(y) - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        cv2.imencode(".png", vis)[1].tofile(J(OUT, "접점_%s.png" % n.replace("/", "-").replace(" ", "_")))
    json.dump(dict(점=점3D, 검산=표), open(J(OUT, "접점.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
