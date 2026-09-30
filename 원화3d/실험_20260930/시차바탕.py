# -*- coding: utf-8 -*-
"""시차 깊이 → 바탕 메시(정면 실루엣 격자를 z 로 들어 올림 · 블렌더 좌표) -> out/오메가몬2/블렌더/시차바탕.npz"""
import os, sys, json, numpy as np, cv2
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(R, "오메가몬", "지표")); from 집합 import OUT, J
D = J(OUT, "..", "자료"); K = J(R, "out", "깊이카드"); B = J(OUT, "..", "블렌더")
기록 = json.load(open(J(D, "자료.json"), encoding="utf-8")); 자세 = json.load(open(J(OUT, "자세3.json"), encoding="utf-8")); F = 자세["정면 yt_172"]; Rf = cv2.Rodrigues(np.asarray(F["r"], float))[0]
sil = cv2.imdecode(np.fromfile(J(D, "02_정면_실루엣.png"), np.uint8), 0) > 127; d = np.load(J(K, "시차_정면.npy")); x0, y0, x1, y1 = 기록["02_정면"]["상자"]
m = cv2.morphologyEx(sil.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (19, 19))) > 0; m[:int(F["t"][1] - 2)] = False; m[int(F["t"][1] + 100 * F["s"] + 3):] = False   # 뿔 · 안테나 뗌 · 돔 위 · 턱 밑 자름
r0 = int(F["t"][1] + 60 * F["s"]); xl, xr = int(F["t"][0] - 36 * F["s"]), int(F["t"][0] + 36 * F["s"]); m[r0:, :xl] = False; m[r0:, xr:] = False
step = 3; ys = np.arange(y0, y1, step); xs = np.arange(x0, x1, step); gv, gu = np.meshgrid(ys, xs, indexing="ij"); inside = m[gv, gu]
idx = -np.ones(gv.shape, int); idx[inside] = np.arange(inside.sum()); u = gu[inside].astype(float); v = gv[inside].astype(float); x = (u - F["t"][0]) / F["s"]; y = (v - F["t"][1]) / F["s"]; z = d[gv[inside], gu[inside]]
U = (np.stack([x, y, -z], 1) @ Rf) * (1, 1, -1); Vb = np.stack([U[:, 0], -U[:, 2], -U[:, 1]], 1); Fs = []
for i in range(gv.shape[0] - 1):
    for j in range(gv.shape[1] - 1):
        a, b, c, e = idx[i, j], idx[i, j + 1], idx[i + 1, j + 1], idx[i + 1, j]
        if a >= 0 and b >= 0 and c >= 0: Fs.append((a, b, c))
        if a >= 0 and c >= 0 and e >= 0: Fs.append((a, c, e))
np.savez(J(B, "시차바탕.npz"), V=Vb.astype(np.float32), F=np.array(Fs, np.int32)); print("정점", len(Vb), "삼각형", len(Fs), "z 범위 %.0f..%.0f" % (z.min(), z.max()))
