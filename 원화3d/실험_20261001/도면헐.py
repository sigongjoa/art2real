# -*- coding: utf-8 -*-
"""정면 · 옆 도면 블록아웃 1 단계 — 큰 덩어리 (10-03 · 조사 「원화는 안내 · 정면 기준 옆으로 균형 · 큰 덩어리 먼저」 → 「원래 하던 거 하자」).
쓰는 것은 두 장뿐: 정면 머리 마스크(판_1) · 옆 머리 마스크(판_2) · 옆 → 정면 맞춤 C(배율 0.987 · 기울기 −22.6° · 세로 이동 90.8 ·
다섯 점 눈 · 뿔 뿌리 · 턱 끝 · 번개 · 안테나 뿌리로 풂 · 배율고르기2.png). 숫자는 전부 원화에서 — 지어낸 치수 없음.
덩어리 = {정면 실루엣 안} ∩ {옆 실루엣 안} (도면 두 장의 헐). 깊이 원점 = 눈(옆 그림 눈 = 0), 앞 = −.
부품은 아직 안 나눈다(다음 단계: 이 덩어리 위에 투구 · 마스크 · 뿔 · 안테나 · 볼날개).
출력 out/오메가몬2/블렌더/도면헐.ply · 도면헐.json"""
import os, json, numpy as np, trimesh
from skimage import measure
O = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
P = json.load(open(os.path.join(O, "특징점.json"), encoding="utf-8")); s = P["2"]
k, t, c = 0.987, np.radians(-22.6), 90.8
xm = np.mean([s[n][0] for n in ("눈/오른", "뿔 뿌리", "턱 끝", "번개/오른", "안테나 뿌리/오른")]); ex, ey = s["눈/오른"]
m1 = np.load(os.path.join(O, "판_1_Z.npz"))["m"]; m2 = np.load(os.path.join(O, "판_2_Z.npz"))["m"]
# 1 판: 옆 마스크의 안테나(가는 가시)가 깊이를 260 까지 끌고 가 상자가 됨 → 가는 것(안테나 · 뿔 끝)은 열림으로 떼어 낸다 — 큰 덩어리만(가는 부품은 다음 단계에 따로)
import cv2
m1 = cv2.morphologyEx(m1.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13))) > 0
m2 = cv2.morphologyEx(m2.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))) > 0
ys, xs = np.nonzero(m1); cu = (xs.min() + xs.max()) / 2
ct, st = np.cos(t), np.sin(t); A = np.array([[k * ct, -k * st], [k * st, k * ct]]); Ai = np.linalg.inv(A); b0 = np.array([-k * (ex * ct - ey * st), -k * xm * st + c])
st_ = 1.0; X = np.arange(0, m1.shape[1], st_); Zf = np.arange(0, m1.shape[0], st_); D = np.arange(-260, 260, st_)
GX, GD, GZ = np.meshgrid(X, D, Zf, indexing="ij")
f_in = m1[GZ.astype(int), GX.astype(int)]
sx, sy = np.einsum("ij,j...->i...", Ai, np.stack([GD - b0[0], GZ - b0[1]]))
sxi, syi = np.round(sx).astype(int), np.round(sy).astype(int); ok = (sxi >= 0) & (sxi < m2.shape[1]) & (syi >= 0) & (syi < m2.shape[0])
s_in = np.zeros_like(ok); s_in[ok] = m2[syi[ok], sxi[ok]]
V = f_in & s_in
vt, fc, _, _ = measure.marching_cubes(np.pad(V, 1).astype(np.float32), 0.5); vt -= 1
P3 = np.c_[vt[:, 0] * st_ + X[0] - cu, vt[:, 1] * st_ + D[0], -(vt[:, 2] * st_ + Zf[0])]
mesh = trimesh.Trimesh(np.c_[P3[:, 0], P3[:, 1], P3[:, 2]], fc); trimesh.smoothing.filter_taubin(mesh, iterations=6)   # 블렌더: x 오른 · y 앞이 − · z 위
mesh.export(os.path.join(B, "도면헐.ply"))
dz = P3[:, 1]; r = {"복셀": int(V.sum()), "깊이 범위(눈 = 0, 앞 −)": [round(float(dz.min()), 1), round(float(dz.max()), 1)], "폭": round(float(np.ptp(P3[:, 0])), 1), "높이": round(float(np.ptp(P3[:, 2])), 1)}
json.dump(r, open(os.path.join(B, "도면헐.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(r)
