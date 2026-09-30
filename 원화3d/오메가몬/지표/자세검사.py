# -*- coding: utf-8 -*-
"""자세 검사 — 세 시점 자세가 서로 맞는가 (2026-09-30 「개판이야 고쳐 봐」 → 근본 원인부터).
    python 자세검사.py [자세 파일 이름 …]  -> 부품마다: 정면 무게중심 광선(z 훑기)이 옆 · 3/4 의 짝 면에 닿는 z 구간 · 두 구간이 겹치면 ○
자세 파일: 자세2.json(실루엣 맞춤 · 기본) · 랜드마크3D.json 의 "자세"(맞춤.py 손 랜드마크 동시 맞춤)"""
import os, sys, json
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, J
from 부품투영 import 찍기
D = J(OUT, "..", "자료"); S = 3; 선택 = json.load(open(J(D, "면대응_선택.json"), encoding="utf-8"))["짝"]
라벨 = {t: np.load(J(D, t + "_영역.npz"))["라벨"] for t in ("02_정면", "02_3-4", "02_옆")}
def 검사(자세, 이름):
    F = 자세["정면 yt_172"]; Rf = cv2.Rodrigues(np.asarray(F["r"], float))[0]; zs = np.arange(-60, 71, 1.0); 점수 = []
    print("── %s ──" % 이름)
    for n, 짝 in 선택.items():
        if not 짝.get("정면") or not (짝.get("옆") or 짝.get("3-4")): continue
        ys, xs = np.nonzero(np.isin(라벨["02_정면"], 짝["정면"])); u, v = xs.mean() / S, ys.mean() / S; x, y = (u - F["t"][0]) / F["s"], (v - F["t"][1]) / F["s"]
        C = np.stack([np.full_like(zs, x), np.full_like(zs, y), -zs], 1); U = (C @ Rf) * (1, 1, -1); 구간 = {}
        for t, key, 자이름 in (("02_옆", "옆", "옆 yt_235"), ("02_3-4", "3-4", "3/4 M04")):
            if not 짝.get(key): continue
            m = cv2.dilate(np.isin(라벨[t], 짝[key]).astype(np.uint8), np.ones((9, 9), np.uint8)) > 0; uv, _ = 찍기(U, 자세[자이름]); p = np.round(uv * S).astype(int)
            ok = (p[:, 0] >= 0) & (p[:, 0] < m.shape[1]) & (p[:, 1] >= 0) & (p[:, 1] < m.shape[0]); hit = np.zeros(len(zs), bool); hit[ok] = m[p[ok, 1], p[ok, 0]]
            구간[key] = (float(zs[hit].min()), float(zs[hit].max())) if hit.any() else None
        a, b = 구간.get("옆"), 구간.get("3-4"); 겹 = (a and b and max(a[0], b[0]) <= min(a[1], b[1]))
        if a and b: 점수.append(1 if 겹 else 0)
        print("  %-6s 옆 z %-14s 3/4 z %-14s %s" % (n, a, b, "○ 겹침" if 겹 else ("× 안 겹침" if a and b else "—")))
    print("  겹침 %d / %d" % (sum(점수), len(점수)))
자세2 = json.load(open(J(OUT, "자세2.json"), encoding="utf-8")); 검사(자세2, "자세2 (실루엣 · 옛 6판 모델에 각각)")
L3 = json.load(open(J(OUT, "랜드마크3D.json"), encoding="utf-8"))["자세"]; 검사({k: dict(v, k=0.0) for k, v in L3.items()}, "맞춤.py (손 랜드마크 3 시점 동시)")
if os.path.exists(J(OUT, "자세3.json")): 검사(json.load(open(J(OUT, "자세3.json"), encoding="utf-8")), "자세3 (② 면 짝 동시 맞춤)")
