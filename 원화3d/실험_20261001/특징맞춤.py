# -*- coding: utf-8 -*-
"""특징점으로 카메라와 특징점 깊이를 같이 풀고, 껍질을 통째로 세운다 (10-02 사용자 「차양 기반으로 위치 잘 맞추면 · 특징적인 것들 잘 가져다 붙이면」).
특징점(차양 V · 눈 · 턱 끝 · 뿔 뿌리 · 번개) = 각도데이터/특징점.json(Claude 가 격자 보고 찍음 · 사람이 고칠 것). 칸 무게중심(범위가 장마다 다름)은 안 쓴다.
1 판(정면 껍질 깊이를 특징점 3D 로 믿고 장마다 카메라만): 카메라가 범위 끝(pitch −60 · roll 45)에 붙음 — 정면 껍질은 턱 · 눈 깊이가 거의 같은데 옆 원화는 부리가 훨씬 앞.
2 판(지금) = 묶음 조정: 특징점 3D 와 카메라 넷을 같이 푼다. 정면 카메라 고정(그림 x = X · 그림 y = −Z · 깊이 = Y).
  특징점 대칭: 눈 · 번개는 좌우 짝(가운데 x0 기준 거울) · 차양 V · 턱 끝 · 뿔 뿌리는 가운데 → 미지수 13.
  카메라(정사영) 장마다 yaw · pitch · roll · 크기 s · 이동 t → 24. 관측 44 + 약한 사전(각은 눈짐작 ± · roll 0 쪽).
껍질 세우기: 장마다 껍질 깊이 Z 를 풀린 특징점 깊이에 1 차로 맞춤(a·Z + b · 껍질 깊이 배율이 장마다 다르니) → 카메라 역투영.
뒤(설정화)는 공통 특징점이 없어 뺌. 출력 각도데이터/특징맞춤.ply(장마다 색) · 특징맞춤.json"""
import os, json, numpy as np, trimesh
from scipy.optimize import least_squares
O = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; P = json.load(open(os.path.join(O, "특징점.json"), encoding="utf-8"))
W_사전 = float(os.environ.get("W_PRIOR", 0.5)); 장 = ["1", "2", "3", "4", "5"]; 처음 = {"2": (90, -10), "3": (35, 5), "4": (40, 15), "5": (55, 0)}
색 = {"1": (230, 25, 75), "2": (60, 180, 75), "3": (255, 225, 25), "4": (67, 99, 216), "5": (245, 130, 49)}
def 껍질(n):
    z = np.load(os.path.join(O, f"판_{n}_Z.npz")); m, Z = z["m"], z["Z"]; ys, xs = np.nonzero(m); return m, Z, (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
def 깊이(Z, x, y):
    for rr in (3, 6, 10, 16, 25):   # 특징점이 껍질 가장자리 · 밖이면 넓혀서 가장 가까운 껍질 깊이
        q = Z[max(0, y - rr):y + rr + 1, max(0, x - rr):x + rr + 1]
        if np.isfinite(q).any(): return float(np.nanmedian(q))
    raise ValueError(f"특징점 ({x},{y}) 주변에 껍질이 없음")
def R_of(yaw, pitch, roll):
    t, p, r = np.radians([yaw, pitch, roll]); right = np.array([np.cos(t), -np.sin(t), 0]); toward = np.array([np.sin(t), np.cos(t), 0]); up0 = np.array([0, 0, 1.0])
    up = up0 * np.cos(p) - toward * np.sin(p); tw = toward * np.cos(p) + up0 * np.sin(p)
    r1 = right * np.cos(r) + up * np.sin(r); u1 = -right * np.sin(r) + up * np.cos(r); return np.array([r1, u1, tw])   # 행: 오른 · 위 · 카메라 쪽
m1, Z1, cu, cv = 껍질("1")
def 점들(q):   # q[:13] → 특징점 3D (정면 틀 · x 오른 · y 카메라 쪽 · z 위)
    x0, ex, ey, ez, bx, by, bz, vy, vz, cy, cz, hy, hz = q[:13]
    return {"눈/오른": [x0 + ex, ey, ez], "눈/왼": [x0 - ex, ey, ez], "번개/오른": [x0 + bx, by, bz], "번개/왼": [x0 - bx, by, bz],
            "차양 V": [x0, vy, vz], "턱 끝": [x0, cy, cz], "뿔 뿌리": [x0, hy, hz]}
def 투영(n, X, c):
    if n == "1": return np.array([X[0] + cu, -X[2] + cv])
    R = R_of(*c[:3]); s, tx, ty = c[3:]; v = R @ np.array(X); return np.array([s * v[0] + tx, -s * v[1] + ty])
def 잔차(q):
    pts = 점들(q); r = []
    for i, n in enumerate(장):
        c = None if n == "1" else q[13 + 6 * (i - 1):13 + 6 * i]
        for k, xy in P[n].items():
            if k in pts: r.extend(투영(n, pts[k], c) - np.array(xy, float))
        if c is not None: y0, p0 = 처음[n]; r.extend([W_사전 * (c[0] - y0), W_사전 * (c[1] - p0), 2 * W_사전 * c[2]])   # 각 사전(10° 벗어나면 W·10 화소)
    return np.array(r)
# 처음 값: 정면 2D 에서 x · z, 깊이는 0
f = P["1"]; e = (np.array(f["눈/오른"]) - np.array(f["눈/왼"])) / 2; b = (np.array(f["번개/오른"]) - np.array(f["번개/왼"])) / 2
x0 = (f["눈/오른"][0] + f["눈/왼"][0]) / 2 - cu
q0 = [x0, e[0], 0, -((f["눈/오른"][1] + f["눈/왼"][1]) / 2 - cv), b[0], 0, -((f["번개/오른"][1] + f["번개/왼"][1]) / 2 - cv), 0, -(f["차양 V"][1] - cv), 0, -(f["턱 끝"][1] - cv), 0, -(f["뿔 뿌리"][1] - cv)]
for n in 장[1:]: B = np.array(list(P[n].values()), float); q0 += [처음[n][0], 처음[n][1], 0, 2.0, B[:, 0].mean(), B[:, 1].mean()]
lo = [-np.inf] * 13; hi = [np.inf] * 13
for n in 장[1:]: lo += [처음[n][0] - 70, -70, -40, 0.2, -1e4, -1e4]; hi += [처음[n][0] + 70, 70, 40, 6, 1e4, 1e4]
sol = least_squares(잔차, q0, bounds=(lo, hi)); q = sol.x; pts = 점들(q)
결과 = {"특징점 3D(정면 화소 · y = 카메라 쪽)": {k: [round(float(v), 1) for v in X] for k, X in pts.items()}, "장": {}}
meshes = []
def 메시(n, Mw):
    m, Z, _, _ = 껍질(n); ys, xs = np.nonzero(m); vid = -np.ones(m.shape, int); vid[ys, xs] = np.arange(len(ys)); W = Mw(xs.astype(float), ys.astype(float), Z[ys, xs])
    a, b_, c, d = vid[:-1, :-1], vid[:-1, 1:], vid[1:, :-1], vid[1:, 1:]; ok = (a >= 0) & (b_ >= 0) & (c >= 0) & (d >= 0); F = np.r_[np.c_[a[ok], c[ok], b_[ok]], np.c_[b_[ok], c[ok], d[ok]]]
    me = trimesh.Trimesh(np.c_[W[:, 0], -W[:, 1], W[:, 2]], F, process=False); me.visual.vertex_colors = np.tile(list(색[n]) + [255], (len(W), 1)).astype(np.uint8); return me   # 블렌더: 앞 = −y
for i, n in enumerate(장):
    m, Z, _, _ = 껍질(n); ks = [k for k in P[n] if k in pts]
    if n == "1": R = np.eye(3)[[0, 2, 1]]; s, tx, ty = 1.0, cu, cv; ang = (0, 0, 0)   # 행: 오른 = x · 위 = z · 카메라 쪽 = y
    else: c = q[13 + 6 * (i - 1):13 + 6 * i]; R = R_of(*c[:3]); s, tx, ty = c[3:]; ang = tuple(c[:3])
    want = np.array([R[2] @ np.array(pts[k]) for k in ks]); have = np.array([깊이(Z, *P[n][k]) / s for k in ks])
    a, b0 = np.polyfit(have, want, 1) if len(ks) >= 3 and np.ptp(have) > 1e-3 else (1.0, float(np.median(want - have)))
    if a <= 0: a, b0 = 1.0, float(np.median(want - have))   # 뒤집힌 깊이는 안 씀
    meshes.append(메시(n, lambda x, y, Zv, R=R, s=s, tx=tx, ty=ty, a=a, b0=b0: np.c_[(x - tx) / s, -(y - ty) / s, a * Zv / s + b0] @ R))
    e2 = np.sqrt(((np.array([투영(n, pts[k], None if n == "1" else q[13 + 6 * (i - 1):13 + 6 * i]) for k in ks]) - np.array([P[n][k] for k in ks])) ** 2).sum(1)).mean() / s
    결과["장"][n] = {"yaw · pitch · roll": [round(float(v), 1) for v in ang], "크기": round(float(s), 3), "깊이 배율 a": round(float(a), 2), "특징점": ks, "평균 잔차(정면 화소)": round(float(e2), 1)}
    print(n, 결과["장"][n])
trimesh.util.concatenate(meshes).export(os.path.join(O, "특징맞춤.ply"))
json.dump(결과, open(os.path.join(O, "특징맞춤.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(결과["특징점 3D(정면 화소 · y = 카메라 쪽)"])
