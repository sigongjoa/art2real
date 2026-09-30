# -*- coding: utf-8 -*-
"""자세 4 — 옆 · 3/4 카메라를 블록아웃(블렌더 부품 STL)에 맞춘다: 실루엣 IoU + 눈 하나(앞뒤 뒤집힘을 끊는 점) · 두 시작(R · 네커 반전 DRD) 중 좋은 쪽 (2026-09-30).
    python 자세4.py -> 자세3.json 갱신(옆 yt_235 · 3/4 M04) · 정면은 그대로(기준 틀)"""
import os, sys, json
import numpy as np, cv2, trimesh
from scipy.optimize import minimize
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, J
from 부품투영 import 찍기
D = J(OUT, "..", "자료"); B = J(OUT, "..", "블렌더"); S = 3; 자세3 = json.load(open(J(OUT, "자세3.json"), encoding="utf-8")); 자세2 = json.load(open(J(OUT, "자세2.json"), encoding="utf-8"))
mesh = trimesh.load(J(B, "블록아웃.stl"), force="mesh"); Vb = np.asarray(mesh.vertices, float); U = np.stack([Vb[:, 0], -Vb[:, 2], -Vb[:, 1]], 1); F = np.asarray(mesh.faces)
눈L = np.array([[11.5, 50.0, 2.7]])                                                                  # 홍채중심(랜드마크3D · +x = 옆 · 3/4 에 보이는 눈)
설정 = {"02_옆": ("옆 yt_235", [3, 4, 6, 7, 8, 9], (400, 0, 990, 305), None), "02_3-4": ("3/4 M04", [7, 8], (830, 0, 1440, 700), "눈위모름")}
축 = 4
for t, (자이름, 눈ids, 상자, 모름) in 설정.items():
    sil = cv2.imdecode(np.fromfile(J(D, t + "_실루엣.png"), np.uint8), 0) > 127; L = np.load(J(D, t + "_영역.npz"))["라벨"]; H, W = sil.shape
    roi = np.zeros_like(sil); x0, y0, x1, y1 = 상자; roi[y0:y1, x0:x1] = True
    if 모름: roi[:np.nonzero(np.isin(L, 눈ids).any(1))[0].min() // S] = False
    ys, xs = np.nonzero(np.isin(L, 눈ids)); 눈px = np.array([xs.mean(), ys.mean()]) / S
    sil4 = cv2.resize(sil.astype(np.uint8), (W // 축, H // 축)) > 0; roi4 = cv2.resize(roi.astype(np.uint8), (W // 축, H // 축)) > 0
    def 마스크(p):
        uv, _ = 찍기(U, dict(r=p[:3], s=p[3], t=p[4:6], k=0.0)); m = np.zeros((H // 축, W // 축), np.uint8); q = np.round(uv / 축).astype(np.int32)
        for f in F: cv2.fillPoly(m, [q[f]], 1)
        return m > 0
    def 비용(p):
        m = 마스크(p) & roi4; tt = sil4 & roi4; iou = (m & tt).sum() / max(1, (m | tt).sum()); uv, _ = 찍기(눈L, dict(r=p[:3], s=p[3], t=p[4:6], k=0.0)); d = np.linalg.norm(uv[0] - 눈px) / p[3]
        return -iou + 0.01 * d, iou, d
    후보 = []
    for 이름, 자 in (("자세3", 자세3[자이름]), ("자세2", 자세2[자이름])):
        for 뒤집 in (False, True):
            R = cv2.Rodrigues(np.asarray(자["r"], float))[0]
            if 뒤집: Dm = np.diag([1.0, 1.0, -1.0]); R = Dm @ R @ Dm
            p0 = np.r_[cv2.Rodrigues(R)[0].ravel(), 자["s"], 자["t"]]
            best = minimize(lambda p: 비용(p)[0], p0, method="Nelder-Mead", options=dict(maxiter=400, xatol=1e-3, fatol=1e-4, initial_simplex=np.r_[[p0], p0 + np.diag([0.05, 0.05, 0.05, 0.2, 15, 15])]))
            c, iou, d = 비용(best.x); 후보.append((c, iou, d, 이름, 뒤집, best.x)); print("  %s %s 시작 %s%s → IoU %.3f · 눈 거리 %.1f 단위" % (t, 이름, "반전" if 뒤집 else "그대로", "", iou, d))
    c, iou, d, 이름, 뒤집, p = min(후보, key=lambda a: a[0]); Rn = cv2.Rodrigues(p[:3])[0]; 앞 = Rn @ np.array([0, 0, -1.0])
    자세3[자이름] = dict(자세3[자이름], r=p[:3].tolist(), s=float(p[3]), t=p[4:6].tolist(), 비고="자세4: 블록아웃 실루엣 + 눈 한 점 · 시작 %s %s · IoU %.3f · 눈 %.1f" % (이름, "반전" if 뒤집 else "그대로", iou, d))
    print("%s ← %s %s · IoU %.3f · 눈 거리 %.1f · yaw %.1f°" % (자이름, 이름, "반전" if 뒤집 else "그대로", iou, d, np.degrees(np.arctan2(앞[0], -앞[2]))))
json.dump(자세3, open(J(OUT, "자세3.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
