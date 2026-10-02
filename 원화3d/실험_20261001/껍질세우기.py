# -*- coding: utf-8 -*-
"""여섯 장 껍질을 그대로 한 자리에 세우기 (10-02 사용자 「이것부터 시작하고」 — 판_시트의 장별 껍질).
쪼개지도 · 투표로 깎지도 않는다(부품헐 · 장합치기 기각). 껍질 하나 = 그 장 카메라에서 본 앞면 → 그 카메라 각도로 돌려 놓기만.
  껍질 좌표(각도접힌판.py): 오른 u = px·k · 위 = −py·k · 카메라 쪽 깊이 = Z·k (k = 100 / 머리 높이 화소)
  가운데 = 마스크 상자 가운데 · 깊이 0 점은 모르니 껍질 가장 앞 = 머리 반지름 D(정면 깊이/높이로 잡음)
  틀(블렌더): x = 인물 왼쪽 · y = 정면 카메라 반대(앞 = −y) · z = 위. 장 각도(yaw θ · pitch φ)는 이름표에서 읽은 눈짐작 — 찾기(장합치기의 각 비틀기)는 안 씀.
출력 out/오메가몬2/지표/각도데이터/껍질세우기.ply(장마다 색) · 껍질세우기.json"""
import os, json, numpy as np, trimesh
O = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"
각 = {"1": (0, 0), "2": (90, -10), "3": (35, 5), "4": (40, 15), "5": (55, 0), "6": (180, 5)}
색 = {"1": (230, 25, 75), "2": (60, 180, 75), "3": (255, 225, 25), "4": (67, 99, 216), "5": (245, 130, 49), "6": (145, 30, 180)}
D = 40.0
meshes = []
for n, (th, ph) in 각.items():
    z = np.load(os.path.join(O, f"판_{n}_Z.npz")); m = z["m"]; Z = z["Z"]; ys, xs = np.nonzero(m); H = ys.max() - ys.min(); k = 100.0 / H
    cu, cv = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2; vid = -np.ones(m.shape, int); vid[ys, xs] = np.arange(len(ys))
    u = (xs - cu) * k; up = -(ys - cv) * k; dep = Z[ys, xs] * k; dep = dep - np.nanmax(dep) + D
    t, p = np.radians(th), np.radians(ph); dh = dep * np.cos(p) - up * np.sin(p); zz = up * np.cos(p) + dep * np.sin(p)
    x = u * np.cos(t) + dh * np.sin(t); y = -u * np.sin(t) + dh * np.cos(t)          # y = 정면 카메라 쪽
    a, b, c, d = vid[:-1, :-1], vid[:-1, 1:], vid[1:, :-1], vid[1:, 1:]; ok = (a >= 0) & (b >= 0) & (c >= 0) & (d >= 0)
    F = np.r_[np.c_[a[ok], c[ok], b[ok]], np.c_[b[ok], c[ok], d[ok]]]
    me = trimesh.Trimesh(np.c_[x, -y, zz], F, process=False); me.visual.vertex_colors = np.tile(list(색[n]) + [255], (len(x), 1)).astype(np.uint8); meshes.append(me)
trimesh.util.concatenate(meshes).export(os.path.join(O, "껍질세우기.ply"))
json.dump({"각(yaw, pitch)": 각, "앞 반지름 D": D, "색": {"1 정면": "빨강", "2 옆": "초록", "3 3/4": "노랑", "4 위에서": "파랑", "5 tri": "주황", "6 뒤": "보라"}},
          open(os.path.join(O, "껍질세우기.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok")

# ── 2 단계: 이름을 맞춤점으로 껍질마다 정면 껍질에 통째로 맞추기(크기 · 이동만 · 쪼개지 않음) ──
# 회전까지 풀면(움베야마) 정면 껍질 이름점이 거의 한 평면이라 크기 0.4~0.5 · 40~106° 를 더 돌려 버렸다 → 회전은 눈짐작 각 그대로.
# 맞춤점 = 두 껍질에 다 있는 이름(좌우 붙은 그대로 · 「?」 뺌)의 무게중심. 3 개 이상일 때만. 정면 껍질은 그대로(바탕).
이름 = json.load(open(os.path.join(O, "이름.json"), encoding="utf-8"))
def 이름점(n, me):
    z = np.load(os.path.join(O, f"{n}.npz")); L = z["라벨"]; ys, xs = np.nonzero(L > 0); y0, x0 = ys.min(), xs.min()
    m = np.load(os.path.join(O, f"판_{n}_Z.npz"))["m"]; py, px = np.nonzero(m); lab = L[np.clip(y0 + 2 * py, 0, L.shape[0] - 1), np.clip(x0 + 2 * px, 0, L.shape[1] - 1)]
    out = {}
    for nm, cs in 이름[n].items():
        if "?" in nm: continue
        q = np.isin(lab, cs)
        if q.sum() >= 5: out[nm] = me.vertices[q].mean(0)
    return out
def 움베야마(A, B):   # B ≈ s R A + t
    ma, mb = A.mean(0), B.mean(0); a, b = A - ma, B - mb; U, S, Vt = np.linalg.svd(b.T @ a); d = np.sign(np.linalg.det(U @ Vt)); Dg = np.diag([1, 1, d])
    R = U @ Dg @ Vt; s = (S * np.diag(Dg)).sum() / (a ** 2).sum(); return s, R, mb - s * R @ ma
기준 = 이름점("1", meshes[0]); 맞춤 = {}; 맞춘 = [meshes[0]]
for i, n in enumerate(list(각)[1:], 1):
    p = 이름점(n, meshes[i]); 공통 = [k_ for k_ in p if k_ in 기준]
    if len(공통) < 3: 맞춤[n] = {"공통 이름": 공통, "맞춤": "못 함(3 개 미만) · 세운 그대로"}; 맞춘.append(meshes[i]); continue
    A = np.array([p[k_] for k_ in 공통]); B = np.array([기준[k_] for k_ in 공통]); R = np.eye(3); a_, b_ = A - A.mean(0), B - B.mean(0); s = float((a_ * b_).sum() / (a_ ** 2).sum()); t = B.mean(0) - s * A.mean(0)
    me = meshes[i].copy(); me.vertices = (s * (R @ me.vertices.T)).T + t; 맞춘.append(me)
    잔차 = float(np.sqrt((((s * (R @ A.T)).T + t - B) ** 2).sum(1)).mean()); ang = float(np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))))
    맞춤[n] = {"공통 이름": 공통, "크기": round(float(s), 2), "더 돌린 각": round(ang, 1), "평균 잔차(머리=100)": round(잔차, 1)}
trimesh.util.concatenate(맞춘).export(os.path.join(O, "껍질맞춤.ply"))
json.dump(맞춤, open(os.path.join(O, "껍질맞춤.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(맞춤, ensure_ascii=False))
