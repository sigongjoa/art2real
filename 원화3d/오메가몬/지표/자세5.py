# -*- coding: utf-8 -*-
"""자세 5 — 원형사 식: 옆은 옆(yaw −90°) · 3/4 는 3/4(yaw −30°)로 **정해 두고**, 크기 · 위치만 두 랜드마크(눈 높이 · 턱 끝)로 (2026-09-30 · 맞춤은 앞뒤 뒤집힌 해 사이를 오갔다).
    python 자세5.py -> 자세3.json 갱신(옆 yt_235 · 3/4 M04). 가까운 쪽 = +x(정면 그림 오른쪽 = 캐릭터 왼쪽 · 옆 · 3/4 캡처는 코가 그림 왼쪽)."""
import os, sys, json
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, J
from 부품투영 import 찍기
from 자세2 import R_of, 각
D = J(OUT, "..", "자료"); S = 3; 자세3 = json.load(open(J(OUT, "자세3.json"), encoding="utf-8")); 자세2 = json.load(open(J(OUT, "자세2.json"), encoding="utf-8"))
눈 = np.array([11.5, 50.0, 2.7]); 턱 = np.array([0.0, 100.0, 18.4])                                    # 랜드마크3D(측정) · y 는 정면에서 확실 · z 는 대략
설정 = {"02_옆": ("옆 yt_235", -90.0, [3, 4, 6, 7, 8, 9], [15]), "02_3-4": ("3/4 M04", -30.0, [7, 8], [20])}
for t, (자이름, yaw, 눈ids, 턱ids) in 설정.items():
    L = np.load(J(D, t + "_영역.npz"))["라벨"]; ys, xs = np.nonzero(np.isin(L, 눈ids)); 눈px = np.array([xs.mean(), ys.mean()]) / S
    ys, xs = np.nonzero(np.isin(L, 턱ids)); 턱px = np.array([xs[ys == ys.max()].mean(), ys.max()]) / S
    yaw0, pitch0, roll0 = 각(cv2.Rodrigues(np.asarray(자세2[자이름]["r"], float))[0])
    후보 = []
    for 부호 in (1, -1):
        R = R_of(np.radians(부호 * abs(yaw)), pitch0 if t == "02_3-4" else 0.0, roll0)
        C눈, C턱 = R @ (눈 * (1, 1, -1)), R @ (턱 * (1, 1, -1)); s = (턱px[1] - 눈px[1]) / (C턱[1] - C눈[1]); tt = 눈px - s * C눈[:2]
        자 = dict(r=cv2.Rodrigues(R)[0].ravel().tolist(), s=float(s), t=tt.tolist(), k=0.0)
        _, cz = 찍기(np.array([[20.0, 50, 0], [-20.0, 50, 0]]), 자); 후보.append((cz[0] < cz[1], 부호, 자))          # +x 가 가까운 쪽인 부호를 고른다
    ok, 부호, 자 = [c for c in 후보 if c[0]][0]; 자세3[자이름] = dict(자세3[자이름], **자, 비고="자세5: yaw %.0f° 고정 · pitch %.1f · roll %.1f(자세2) · s·t = 눈 · 턱" % (부호 * abs(yaw), np.degrees(pitch0 if t == "02_3-4" else 0), np.degrees(roll0)))
    uv, _ = 찍기(np.array([눈, 턱]), 자); print("%s yaw %+.0f° · s %.2f · 눈 px %s → %s · 턱 px %s → %s" % (자이름, 부호 * abs(yaw), 자["s"], np.round(눈px), np.round(uv[0]), np.round(턱px), np.round(uv[1])))
json.dump(자세3, open(J(OUT, "자세3.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
