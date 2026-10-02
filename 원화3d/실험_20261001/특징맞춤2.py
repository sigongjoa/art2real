# -*- coding: utf-8 -*-
"""특징맞춤 2 판 — 대칭 평면 고정 + 특징점 늘림 (10-03 · Gemini 의견 「대칭 평면 먼저 · 특징점 15~20」 → 사용자 「ㄱㄱ」).
특징점 = 각도데이터/특징점.json 2 판(정면 19 · 옆 9 · 3/4 12 · 위 7 · tri 6 · 「턱 끝」과 「부리 앞끝」을 나눔).
특징점 3D(정면 틀 · x 오른 · y 정면 카메라 쪽 · z 위)는 대칭으로만 둔다: 대칭 평면 x = x0(하나) — 짝 이름(…/왼 · …/오른)은 (x0 ± dx, y, z) · 가운데 이름은 (x0, y, z).
카메라: 정면 고정(그림 x = X · 그림 y = −Z) · 나머지 정사영(yaw · pitch · roll · 크기 · 이동) · 각 사전 W(10° 벗어나면 W·10 화소).
나머지(껍질 세우기 · 이름마다 주인 장 하나 · 원화 색)는 특징맞춤.py 와 같다. 출력 각도데이터/특징맞춤2.ply · 특징맞춤2.json"""
import os, sys, json, numpy as np, trimesh
from scipy.optimize import least_squares
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
O = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; P = json.load(open(os.path.join(O, "특징점.json"), encoding="utf-8"))
W_사전 = float(os.environ.get("W_PRIOR", 1.0)); 장 = list(os.environ.get("VIEWS", "12345")); 처음 = {"2": (90, -10), "3": (35, 5), "4": (40, 15), "5": (55, 0)}
def 껍질(n):
    z = np.load(os.path.join(O, f"판_{n}_Z.npz")); m, Z = z["m"], z["Z"]; ys, xs = np.nonzero(m); return m, Z, (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
def 깊이(Z, x, y):
    for rr in (3, 6, 10, 16, 25):
        q = Z[max(0, y - rr):y + rr + 1, max(0, x - rr):x + rr + 1]
        if np.isfinite(q).any(): return float(np.nanmedian(q))
    raise ValueError(f"특징점 ({x},{y}) 주변에 껍질이 없음")
def R_of(yaw, pitch, roll):
    t, p, r = np.radians([yaw, pitch, roll]); right = np.array([np.cos(t), -np.sin(t), 0]); toward = np.array([np.sin(t), np.cos(t), 0]); up0 = np.array([0, 0, 1.0])
    up = up0 * np.cos(p) - toward * np.sin(p); tw = toward * np.cos(p) + up0 * np.sin(p)
    r1 = right * np.cos(r) + up * np.sin(r); u1 = -right * np.sin(r) + up * np.cos(r); return np.array([r1, u1, tw])
m1, Z1, cu, cv = 껍질("1")
이름들 = sorted({k for n in 장 for k in P[n]}); 바탕들 = sorted({k.split("/")[0] for k in 이름들}); 짝 = {b for b in 바탕들 if any(k.startswith(b + "/") for k in 이름들)}
idx = {}; i = 1
for b in 바탕들: idx[b] = i; i += 3 if b in 짝 else 2           # 짝: dx · y · z / 가운데: y · z (x0 은 q[0])
NP = i
def 점들(q):
    out = {}
    for b in 바탕들:
        j = idx[b]
        if b in 짝: dx, y, z = q[j:j + 3]; out[b + "/오른"] = np.array([q[0] + dx, y, z]); out[b + "/왼"] = np.array([q[0] - dx, y, z])
        else: y, z = q[j:j + 2]; out[b] = np.array([q[0], y, z])
    return out
def cam(q, n): k = 장.index(n) - 1; return q[NP + 6 * k:NP + 6 * k + 6]
def 투영(n, X, q):
    if n == "1": return np.array([X[0] + cu, -X[2] + cv])
    c = cam(q, n); R = R_of(*c[:3]); v = R @ X; return np.array([c[3] * v[0] + c[4], -c[3] * v[1] + c[5]])
def 잔차(q):
    pts = 점들(q); r = []
    for n in 장:
        for k, xy in P[n].items(): r.extend(투영(n, pts[k], q) - np.array(xy, float))
        if n != "1": c = cam(q, n); y0, p0 = 처음[n]; r.extend([W_사전 * (c[0] - y0), W_사전 * (c[1] - p0), 2 * W_사전 * c[2]])
    return np.array(r)
# 처음 값: 정면 2D 에서 x · z(없으면 0), 깊이 0
f1 = P["1"]; q0 = np.zeros(NP); q0[0] = np.mean([(f1[b + "/오른"][0] + f1[b + "/왼"][0]) / 2 for b in 짝 if b + "/오른" in f1 and b + "/왼" in f1]) - cu
for b in 바탕들:
    j = idx[b]
    if b in 짝:
        if b + "/오른" in f1: q0[j] = abs(f1[b + "/오른"][0] - cu - q0[0]); q0[j + 2] = -(f1[b + "/오른"][1] - cv)
        else: q0[j] = 30
    elif b in f1: q0[j + 1] = -(f1[b][1] - cv)
q0 = list(q0); lo = [-np.inf] * NP; hi = [np.inf] * NP
for n in 장[1:]:
    B = np.array(list(P[n].values()), float); q0 += [처음[n][0], 처음[n][1], 0, 1.5, B[:, 0].mean(), B[:, 1].mean()]
    lo += [처음[n][0] - 70, -70, -40, 0.3, -1e4, -1e4]; hi += [처음[n][0] + 70, 70, 40, 5, 1e4, 1e4]
for b in 짝: lo[idx[b]] = 0                                       # dx ≥ 0 (오른이 오른쪽)
sol = least_squares(잔차, q0, bounds=(lo, hi), loss="soft_l1", f_scale=8.0); q = sol.x; pts = 점들(q)
결과 = {"W_사전": W_사전, "장": 장, "대칭 평면 x0(정면 화소, 가운데 기준)": round(float(q[0]), 1), "특징점 3D": {k: [round(float(v), 1) for v in X] for k, X in pts.items()}, "장별": {}}
# 껍질 세우기 · 주인 하나 · 원화 색 (특징맞춤.py 와 같은 규칙)
이름표 = json.load(open(os.path.join(O, "이름.json"), encoding="utf-8")); 넓이 = json.load(open(os.path.join(O, "주뷰.json"), encoding="utf-8"))["넓이비"]
바탕 = lambda t: t.split("/")[0].replace("?", "").replace("(뒤)", "").replace("(뒤에서)", "").replace(" 뒤끝", "").strip()
주인 = {b: max(((k.split()[0], v) for k, v in d.items() if k.split()[0] in 장), key=lambda t: t[1])[0] for b, d in 넓이.items() if any(k.split()[0] in 장 for k in d)}
from PIL import Image
def 메시(n, Mw):
    m, Z, _, _ = 껍질(n); z = np.load(os.path.join(O, f"{n}.npz")); L = z["라벨"]; ys_, xs_ = np.nonzero(L > 0); y0, x0_ = ys_.min(), xs_.min()
    py, px = np.nonzero(m); lab = L[np.clip(y0 + 2 * py, 0, L.shape[0] - 1), np.clip(x0_ + 2 * px, 0, L.shape[1] - 1)]
    c2n = {c: 바탕(nm) for nm, cs in 이름표[n].items() for c in cs}; nm = [c2n.get(int(c), "") for c in lab]
    keep = np.array([(주인.get(t) == n) if t else (n == "1") for t in nm]); mm = np.zeros_like(m); mm[py[keep], px[keep]] = True
    ys, xs = np.nonzero(mm); vid = -np.ones(m.shape, int); vid[ys, xs] = np.arange(len(ys)); W = Mw(xs.astype(float), ys.astype(float), Z[ys, xs])
    a, b_, c, d = vid[:-1, :-1], vid[:-1, 1:], vid[1:, :-1], vid[1:, 1:]; ok = (a >= 0) & (b_ >= 0) & (c >= 0) & (d >= 0); F = np.r_[np.c_[a[ok], c[ok], b_[ok]], np.c_[b_[ok], c[ok], d[ok]]]
    me = trimesh.Trimesh(np.c_[W[:, 0], -W[:, 1], W[:, 2]], F, process=False)
    art = np.asarray(Image.open(os.path.join(O, f"판_{n}_원화.png")).convert("RGB")).astype(float); sel = art[ys, xs]
    sel = np.clip(sel * (200.0 / max(1.0, np.percentile(art[m].mean(1), 90))), 0, 255)   # 장마다 밝기 맞춤(흰 갑주 90 백분위 = 200) — 옆 밤 장면이 어둡던 것
    me.visual.vertex_colors = np.c_[sel.astype(np.uint8), np.full(len(W), 255)].astype(np.uint8); return me
meshes = []
for n in 장:
    m, Z, _, _ = 껍질(n); ks = list(P[n])
    if n == "1": R = np.eye(3)[[0, 2, 1]]; s, tx, ty = 1.0, cu, cv; ang = (0, 0, 0)
    else: c = cam(q, n); R = R_of(*c[:3]); s, tx, ty = c[3:]; ang = tuple(c[:3])
    want = np.array([R[2] @ pts[k] for k in ks]); have = np.array([깊이(Z, *P[n][k]) / s for k in ks])
    a, b0 = np.polyfit(have, want, 1) if np.ptp(have) > 1e-3 else (1.0, float(np.median(want - have)))
    if a <= 0 or a > 8: a, b0 = 1.0, float(np.median(want - have))
    meshes.append(메시(n, lambda x, y, Zv, R=R, s=s, tx=tx, ty=ty, a=a, b0=b0: np.c_[(x - tx) / s, -(y - ty) / s, a * Zv / s + b0] @ R))
    e = np.sqrt(((np.array([투영(n, pts[k], q) for k in ks]) - np.array([P[n][k] for k in ks])) ** 2).sum(1))
    결과["장별"][n] = {"yaw · pitch · roll": [round(float(v), 1) for v in ang], "크기": round(float(s), 3), "깊이 배율 a": round(float(a), 2), "점": len(ks), "잔차 중앙(그 장 화소)": round(float(np.median(e)), 1), "잔차 최대": round(float(e.max()), 1)}
    print(n, 결과["장별"][n])
trimesh.util.concatenate(meshes).export(os.path.join(O, "특징맞춤2.ply")); 결과["주인"] = 주인
json.dump(결과, open(os.path.join(O, "특징맞춤2.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("x0", 결과["대칭 평면 x0(정면 화소, 가운데 기준)"], "부리 앞끝", 결과["특징점 3D"].get("부리 앞끝"), "턱 끝", 결과["특징점 3D"].get("턱 끝"), "눈/오른", 결과["특징점 3D"].get("눈/오른"))
