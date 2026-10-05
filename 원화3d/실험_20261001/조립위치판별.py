# -*- coding: utf-8 -*-
"""사람이 나눈 출력용 모델이 「조립 위치로 저장됐나」 판별 (2026-10-05)
출력용 STL 은 부품마다 출력판 자세로 옮겨 저장되는 경우가 많다(RX78 머리: 얼굴 · 속판은 제자리, V 안테나 · 받침 · 볼판은 옆으로 눕힘).
부품마다: 바닥 z=0 에 눕혀졌나(출력 자세) · 다른 부품과 경계 상자가 닿나(조립) → 모델 점수 = 닿는 부품 비율
python 조립위치판별.py → out/레퍼런스/사람분할/조립판별.json · 표 출력"""
import os, glob, json, numpy as np, trimesh
R = "G:/art2real/원화3d/out/레퍼런스/사람분할/"
out = {}
for d in sorted(glob.glob(R + "*/")):
    fs = [f for f in glob.glob(d + "**/*", recursive=True) if f.lower().endswith((".stl", ".obj", ".3mf"))]
    B = []
    for f in fs[:120]:
        try:
            m = trimesh.load(f, force="mesh")
            if len(m.faces): B.append((os.path.basename(f), m.bounds))
        except Exception: pass
    if not B: out[os.path.basename(d[:-1])] = {"부품": 0}; continue
    lo = np.array([b[1][0] for b in B]); hi = np.array([b[1][1] for b in B]); n = len(B)
    tol = 1.0; touch = np.zeros(n, bool)
    for i in range(n):
        for j in range(n):
            if i != j and np.all(lo[i] - tol <= hi[j]) and np.all(lo[j] - tol <= hi[i]): touch[i] = True; break
    바닥 = np.mean(np.abs(lo[:, 2]) < 0.05)
    머리 = [b[0] for b in B if any(k in b[0].lower() for k in ("head", "helmet", "face", "visor", "horn", "antenna", "fin", "eye", "mask", "chin", "jaw", "forehead"))]
    out[os.path.basename(d[:-1])] = {"부품": n, "닿는비율": round(float(touch.mean()), 2), "바닥z0비율": round(float(바닥), 2), "머리파일": len(머리),
                                     "판정": "조립 위치" if touch.mean() >= 0.8 else ("일부 조립" if touch.mean() >= 0.4 else "출력 자세")}
    print(os.path.basename(d[:-1])[:28].ljust(28), out[os.path.basename(d[:-1])])
json.dump(out, open(R + "조립판별.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
