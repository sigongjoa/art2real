# -*- coding: utf-8 -*-
"""자세 2 — 손 랜드마크 대신 **실루엣**으로 카메라 자세를 잡는다 (09-29 「3/4 에서 전혀 못 잡고 있지? 다시 잡아봐」).
    python 자세2.py [장 …] -> out/오메가몬2/지표/자세2_<장>.png (왼쪽 실루엣 씨앗 · 오른쪽 맞춘 6 판 실루엣(초록) vs 캡처 실루엣(빨강)) · 자세2.json
1 캡처 실루엣: 현재 자세로 찍은 6 판 부품 투영을 씨앗으로(안쪽 침식 = 확실한 앞 · 바깥 띠 = 아마 앞 · 그 밖 = 뒤) GrabCut → 가장 큰 성분.  (3/4 M04 는 흰 깃 · 팔과 맞닿아 상자만으로는 샜다)
2 자세 맞춤: (yaw · pitch · roll · s · tx · ty) 를 Nelder-Mead 로 — 6 판 부품(볼록 껍질 합 · 안테나는 뺌)의 투영 실루엣과 캡처 실루엣의 IoU 최대. 랜드마크는 안 쓴다.
"""
import os, sys, json, glob, math
import numpy as np, cv2, trimesh
from scipy.optimize import minimize
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, 장면, J
from 부품투영 import 단위, 읽기
from 자세 import 캡처 as 캡처2D
F = json.load(open(J(OUT, "랜드마크3D.json"), encoding="utf-8")); 자세0 = F["자세"]
D6 = J(OUT, "..", "머리", "단계4"); 부품 = [(os.path.basename(f)[:-4], np.asarray(trimesh.load(f, process=False, force="mesh").vertices, float)) for f in sorted(glob.glob(J(D6, "*.stl"))) if os.path.basename(f) not in ("프레임.stl",)]
껍질 = [(n, 단위(V)) for n, V in 부품 if not n.startswith("안테나")]
def R_of(yaw, pitch, roll):
    Ry = cv2.Rodrigues(np.array([0, -yaw, 0.0]))[0]; Rx = cv2.Rodrigues(np.array([pitch, 0, 0.0]))[0]; Rz = cv2.Rodrigues(np.array([0, 0, roll]))[0]; return Rz @ Rx @ Ry
def 각(R):
    앞 = R @ np.array([0, 0, -1.0]); 위 = R @ np.array([0, -1.0, 0])
    return math.atan2(앞[0], -앞[2]), math.asin(max(-1, min(1, -앞[1]))), math.atan2(위[0], -위[1])
def 실루엣(p, shape, 축소=4):
    yaw, pitch, roll, s, tx, ty = p[:6]; k = float(p[6]) if len(p) > 6 else 0.0; R = R_of(yaw, pitch, roll); H, W = shape[0] // 축소, shape[1] // 축소; m = np.zeros((H, W), np.uint8)
    for n, U in 껍질:
        C = (U * (1, 1, -1)) @ R.T; uv = (s * C[:, :2] / (1 + k * C[:, 2])[:, None] + (tx, ty)) / 축소; h = cv2.convexHull(np.round(uv).astype(np.int32)); cv2.fillPoly(m, [h], 1)   # 원근 k (09-29)
    return m
def iou(a, b): return (a & b).sum() / max(1, (a | b).sum())
def 씨앗실루엣(im, p):
    m = cv2.resize(실루엣(p, im.shape[:2], 1), (im.shape[1], im.shape[0]), interpolation=cv2.INTER_NEAREST)
    앞 = cv2.erode(m, np.ones((25, 25), np.uint8)) > 0; 아마 = cv2.dilate(m, np.ones((41, 41), np.uint8)) > 0
    mask = np.full(im.shape[:2], cv2.GC_BGD, np.uint8); mask[아마] = cv2.GC_PR_BGD; mask[m > 0] = cv2.GC_PR_FGD; mask[앞] = cv2.GC_FGD
    cv2.grabCut(im, mask, None, np.zeros((1, 65)), np.zeros((1, 65)), 6, cv2.GC_INIT_WITH_MASK)
    mk = ((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD)).astype(np.uint8); mk = cv2.morphologyEx(mk, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(mk); i = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); return (lab == i).astype(np.uint8)
def 초기(n):
    자 = 자세0[n]; R = cv2.Rodrigues(np.asarray(자["r"], float))[0]; y, p, r = 각(R); return np.array([y, p, r, 자["s"], 자["t"][0], 자["t"][1], 0.0], float)
if __name__ == "__main__":
    결과 = {}
    for n in (sys.argv[1:] or ["3/4 M04"]):
        f, _ = 캡처2D[n]; im = 읽기(J(장면, f)); p0 = 초기(n); 캡 = 씨앗실루엣(im, p0); 캡4 = cv2.resize(캡, (im.shape[1] // 4, im.shape[0] // 4), interpolation=cv2.INTER_NEAREST) > 0
        손실 = lambda p: 1 - iou(실루엣(p, im.shape[:2]) > 0, 캡4) + (0.0 if -0.002 <= p[6] <= 0.02 else 1.0)      # k: 0 ~ 0.02 (Z0 ≥ 50 단위 = 머리 반 개 거리) 밖은 벌점
        best = None
        for dy in (0, 0.35, -0.35):                                              # yaw 초기값 셋(국소해 대비)
            q = p0.copy(); q[0] += dy; r = minimize(손실, q, method="Nelder-Mead", options=dict(maxiter=600, xatol=1e-3, fatol=1e-4))
            if best is None or r.fun < best.fun: best = r
        p = best.x; R = R_of(*p[:3]); rvec = cv2.Rodrigues(R)[0].ravel()
        결과[n] = dict(r=list(map(float, rvec)), t=[float(p[4]), float(p[5])], s=float(p[3]), k=float(p[6]), iou=round(1 - best.fun, 3), iou0=round(1 - 손실(p0), 3), yaw=round(math.degrees(p[0]), 1), pitch=round(math.degrees(p[1]), 1), roll=round(math.degrees(p[2]), 1))
        print(n, "IoU %.3f → %.3f" % (1 - 손실(p0), 1 - best.fun), "yaw %.1f pitch %.1f roll %.1f s %.2f k %.4f (Z0 %s 단위)" % (math.degrees(p[0]), math.degrees(p[1]), math.degrees(p[2]), p[3], p[6], ("%.0f" % (1 / p[6])) if p[6] > 1e-6 else "∞"))
        m1 = cv2.resize(실루엣(p, im.shape[:2], 1), (im.shape[1], im.shape[0]), interpolation=cv2.INTER_NEAREST); L = im.copy(); L[캡 > 0] = (L[캡 > 0] * 0.4 + np.array((0, 0, 255)) * 0.6).astype(np.uint8)
        Rr = im.copy(); c1, _ = cv2.findContours(캡, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); c2, _ = cv2.findContours(m1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); cv2.drawContours(Rr, c1, -1, (0, 0, 255), 3); cv2.drawContours(Rr, c2, -1, (0, 255, 0), 3)
        p_ = J(OUT, "자세2_%s.png" % n.replace("/", "-").replace(" ", "_")); cv2.imencode(".png", np.concatenate([L, Rr], 1))[1].tofile(p_)
    old = json.load(open(J(OUT, "자세2.json"), encoding="utf-8")) if os.path.exists(J(OUT, "자세2.json")) else {}; old.update(결과); json.dump(old, open(J(OUT, "자세2.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
