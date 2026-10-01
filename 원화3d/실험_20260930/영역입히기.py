# -*- coding: utf-8 -*-
"""영역 분할만 (10-01 「영역 분할은 잘 된 거니까 영역 분할만 만들어볼래?」).
정면 영역 라벨(02_정면_영역.npz)을 투구 바탕(머리손/투구.npz) 앞면에 정면 투영으로 입힌다 — 모양은 그대로, 면마다 영역 번호만.
    python 영역입히기.py -> out/오메가몬2/블렌더/머리손/투구영역.npz (V F M=영역번호) · 영역팔레트.json"""
import os, sys, json
import numpy as np, cv2
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(R, "오메가몬", "지표")); from 집합 import OUT, J
D = J(OUT, "..", "자료"); B = J(OUT, "..", "블렌더"); P = J(B, "머리손")
F = json.load(open(J(OUT, "자세3.json"), encoding="utf-8"))["정면 yt_172"]; s, t = F["s"], F["t"]
L = np.load(J(D, "02_정면_영역.npz"))["라벨"]; sil = cv2.imdecode(np.fromfile(J(D, "02_정면_실루엣.png"), np.uint8), 0) > 127
Ls = cv2.resize(L, (sil.shape[1], sil.shape[0]), interpolation=cv2.INTER_NEAREST)
머리 = [i for i in range(1, 32) if i not in (22, 23, 27, 28, 29)]
h = np.load(J(P, "투구.npz")); V, Fc = h["V"].astype(np.float64), h["F"]
import trimesh
for _ in range(3): V, Fc = trimesh.remesh.subdivide(V, Fc)                                           # 672 면 → 43k: 경계가 선으로 보이게
V = V.astype(np.float32); Fc = np.asarray(Fc, np.int32)
M = np.zeros(len(Fc), np.int32)
for k, f in enumerate(Fc):
    c = V[f].mean(0); x, y = c[0], -c[2]                                                             # Blender (x, -z, -y) → 모델 x y
    nrm = np.cross(V[f[1]] - V[f[0]], V[f[2]] - V[f[0]])
    if nrm[1] > 0: continue                                                                          # 뒤를 보는 면(Blender +y = 모델 −z)은 안 입힌다
    px, py = int(round(t[0] + x * s)), int(round(t[1] + y * s))
    if 0 <= py < Ls.shape[0] and 0 <= px < Ls.shape[1] and sil[py, px] and Ls[py, px] in 머리: M[k] = int(Ls[py, px])
# 경계면: 이웃 면과 영역이 다르면 −1(검정) — 패널라인
tm = trimesh.Trimesh(V, Fc, process=False); adj = tm.face_adjacency; Mb = M.copy()
diff = (M[adj[:, 0]] != M[adj[:, 1]]) & (M[adj[:, 0]] > 0) & (M[adj[:, 1]] > 0)
Mb[adj[diff, 0]] = -1; Mb[adj[diff, 1]] = -1; M = Mb
np.savez(J(P, "투구영역.npz"), V=V, F=Fc, M=M)
사용 = sorted(set(M.tolist()) - {0, -1}); print("입힌 영역", len(사용), "면", int((M > 0).sum()), "/", len(Fc))
# 팔레트: 영역 번호마다 고정 색(번호 지도와 같이 보려고 번호 → 색 표를 남긴다)
rng = np.random.RandomState(7); import colorsys
pal = {int(i): [float(v) for v in colorsys.hsv_to_rgb((k * 0.618) % 1.0, 0.55, 0.95)] for k, i in enumerate(머리)}; pal[-1] = [0.05, 0.05, 0.06]
json.dump(dict(팔레트=pal, 입힌영역=사용, 투영="정면 · 면 무게중심 · 앞을 보는 면만", 승인="Claude(사용자 미확인)"), open(J(B, "영역팔레트.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
