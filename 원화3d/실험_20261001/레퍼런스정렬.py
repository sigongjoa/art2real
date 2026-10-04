# -*- coding: utf-8 -*-
"""레퍼런스 변형 1 단계 — 정렬 (10-04 사용자 「레퍼런스를 변형」 · 메모 deform-reference-not-build-from-art).
엑시아 머리(Printables 870763 · Power Jojo · CC BY)를 원화 틀(x = 정면 화소 − cu · y 깊이 앞 − · z = −행)에 **균일 배율 + 이동만**으로 맞춘다(휘기는 2 단계).
  엑시아 기준점(정면 격자에서 읽음 · 깊이는 앞 겉에 광선): 두 눈 (±28, −15) · 이마 볼록 = 뿔 뿌리 대응 (0, 15) · 턱 아래 끝 z −75
  원화 기준점(특징점.json 정면): 눈/왼 · 눈/오른 · 뿔 뿌리 · 턱 끝 행
  배율 = 원화 (뿔 뿌리 → 턱 끝) 높이 / 엑시아 (이마 → 턱) 높이 · 가로는 두 눈 가운데를 축 A 에 · 깊이는 엑시아 눈 겉 = 원화 눈 깊이 0
출력 out/오메가몬2/블렌더/엑시아_정렬.ply · 정렬 숫자 출력"""
import os, json, numpy as np, trimesh
A = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
m = trimesh.load(os.path.join(B, "엑시아원본.ply"), process=False)
f1 = json.load(open(os.path.join(A, "특징점.json"), encoding="utf-8"))["1"]
m1 = np.load(os.path.join(A, "판_1_Z.npz"))["m"]; cu = (np.nonzero(m1)[1].min() + np.nonzero(m1)[1].max()) / 2
def 앞겉(x, z):
    loc, _, _ = m.ray.intersects_location([[x, -500, z]], [[0, 1, 0]], multiple_hits=False)
    return float(loc[0, 1]) if len(loc) else np.nan
E = {"눈왼": (-28, -15), "눈오른": (28, -15), "이마": (0, 15), "턱": (0, -75)}
Ey = {k: 앞겉(*v) for k, v in E.items()}
눈y = np.nanmean([Ey["눈왼"], Ey["눈오른"]])
# 원화(정면 화소 · 판 좌표) — z = −행
눈x = (f1["눈/왼"][0] + f1["눈/오른"][0]) / 2 - cu; 눈z = -(f1["눈/왼"][1] + f1["눈/오른"][1]) / 2
뿔z = -f1["뿔 뿌리"][1]; 턱z = -f1["턱 끝"][1]
s = (뿔z - 턱z) / (E["이마"][1] - E["턱"][1])
v = m.vertices * s
v[:, 0] += 눈x - 0 * s; v[:, 2] += 눈z - E["눈왼"][1] * s; v[:, 1] += 0 - 눈y * s
# 2 판: 기준점 눈대중(이마 · 턱)이 틀려 너무 크고 높았다 → 정면 실루엣 IoU 로 배율 · x · z 찾기(턱 끝 아래 = 목 제외) · 깊이는 눈 겉 고정
import cv2
H_, W_ = m1.shape; 아래 = int(-턱z) + 3; F = m1.astype(np.uint8).copy(); F[아래:] = 0
# 실루엣은 한 번만 그리고(모델 단위 2 px) 배율 · 이동은 어파인으로 — 면 단순화가 2500 면까지 안 줄어 한 번 평가 2.3 초였다
R0 = 2.0; mn = m.vertices.min(0); Sx = int((m.vertices[:, 0].max() - mn[0]) * R0) + 4; Sz = int((m.vertices[:, 2].max() - mn[2]) * R0) + 4
base = np.zeros((Sz, Sx), np.uint8); U = (m.vertices[:, 0] - mn[0]) * R0; Z = (m.vertices[:, 2].max() - m.vertices[:, 2]) * R0
cv2.fillPoly(base, [np.round(np.c_[U[f], Z[f]]).astype(np.int32) for f in m.faces], 1); zmax = m.vertices[:, 2].max()
def iou(s_, tx, tz):
    # 화면 u = (X·s + tx + cu) , 행 = −(Z·s + tz) ; X = U/R0 + mn0 , Z = zmax − Zp/R0
    M_ = np.float32([[s_ / R0, 0, mn[0] * s_ + tx + cu], [0, s_ / R0, -(zmax * s_ + tz)]])
    img = cv2.warpAffine(base, M_, (W_, H_), flags=cv2.INTER_NEAREST); img[아래:] = 0
    return (img & F).sum() / max(1, (img | F).sum())
best = (0, s, 눈x, 0)
for s_ in np.arange(0.8, 1.8, 0.04):
    for tx in np.arange(-20, 21, 4):
        for tz in np.arange(-260, -150, 4):
            q = iou(s_, tx, tz)
            if q > best[0]: best = (q, s_, tx, tz)
q0, s, tx, tz = best
for s_ in np.arange(s - 0.03, s + 0.031, 0.01):
    for tx_ in np.arange(tx - 3, tx + 4, 1):
        for tz_ in np.arange(tz - 3, tz + 4, 1):
            q = iou(s_, tx_, tz_)
            if q > best[0]: best = (q, s_, tx_, tz_)
q0, s, tx, tz = best
v = m.vertices * s; v[:, 0] += tx; v[:, 2] += tz; v[:, 1] += 0 - 눈y * s
print({"정면 IoU": round(q0, 3), "배율": round(s, 3), "x": tx, "z": tz})
out = trimesh.Trimesh(v, m.faces, vertex_colors=m.visual.vertex_colors, process=False); out.export(os.path.join(B, "엑시아_정렬.ply"))
print({"배율": round(s, 3), "엑시아 눈 깊이": round(눈y, 1), "원화 눈 x · z": (round(눈x, 1), round(눈z, 1)), "뿔 뿌리 z": 뿔z, "턱 z": 턱z, "정렬 뒤 범위": [v.min(0).round(1).tolist(), v.max(0).round(1).tolist()]})
