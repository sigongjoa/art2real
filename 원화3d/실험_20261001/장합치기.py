# -*- coding: utf-8 -*-
"""장마다 통째 껍질을 한 머리로 (10-02 사용자 「각 화면에는 잘 보였는데 쪼개 놓으니깐 개판이네」 → 부품헐 기각, 쪼개지 않는다).
입력: 각도접힌판.py 의 장별 앞면 깊이 Z · 머리 마스크(반 해상도 · 머리 높이 = 100 단위로 맞춤 · 가운데 = 마스크 상자 가운데).
틀: x = 인물 왼쪽(정면 그림 오른쪽) · y = 정면 카메라 쪽 · z = 위. 장 i 의 카메라 = (yaw θ, pitch φ) · 정사영:
    d = x sinθ + y cosθ (수평 카메라 쪽) · u = x cosθ − y sinθ (그림 오른쪽) · 위 = z cosφ − d sinφ · 깊이 = d cosφ + z sinφ
합치기: ① 실루엣 투표 — N 장 중 (N − 1) 장 이상이(화면 밖 = 머리 밖) 「머리 안」이면 남김(한 장의 과장 · 원근은 넘어감)
        ② 앞면 깎기 — 장마다 껍질 앞면보다 카메라 쪽에 있는 복셀을 지움(장 깊이의 0 점은 모르니, 남은 부피의 가장 앞에 껍질 꼭대기를 맞춤)
각도: 눈짐작에서 시작 → 장마다 「나를 뺀 다섯 장 부피」를 그 장에 투영한 실루엣과 IoU 가 가장 큰 (θ, φ) 를 ±20° 안에서 찾음(두 바퀴).
판정(정답 없이): 나를 뺀 IoU(LOO) — 그 장을 쓰지 않고 만든 머리가 그 장 원화 실루엣과 얼마나 맞나. 답지(피규어)는 안 씀.
출력 out/오메가몬2/지표/각도데이터/합친머리.ply · 합친머리.json"""
import os, json, numpy as np, cv2, trimesh
from skimage import measure
O = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"
J = json.load(open(os.path.join(O, "각도데이터.json"), encoding="utf-8")); 장 = [k.split()[0] for k in J]
각 = {"1": [0, 0], "2": [90, -10], "3": [35, 5], "4": [40, 15], "5": [55, 0], "6": [180, 5]}
V = {}
for n in 장:
    z = np.load(os.path.join(O, f"판_{n}_Z.npz")); m = z["m"]; Z = z["Z"]; ys, xs = np.nonzero(m)
    k = 100.0 / (ys.max() - ys.min()); cu, cv = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    V[n] = dict(m=m, Z=np.where(m, Z, np.nan) * k, k=k, cu=cu, cv=cv)
G = 112; R = 75; a = np.linspace(-R, R, G); X, Y, Zz = np.meshgrid(a, a, a, indexing="ij"); P = np.c_[X.ravel(), Y.ravel(), Zz.ravel()]
def 투영(n, th, ph):
    t, p = np.radians(th), np.radians(ph); d = P[:, 0] * np.sin(t) + P[:, 1] * np.cos(t); u = P[:, 0] * np.cos(t) - P[:, 1] * np.sin(t)
    up = P[:, 2] * np.cos(p) - d * np.sin(p); dep = d * np.cos(p) + P[:, 2] * np.sin(p); v = V[n]
    c = np.round(u / v["k"] + v["cu"]).astype(int); r = np.round(-up / v["k"] + v["cv"]).astype(int); H, W = v["m"].shape
    ok = (r >= 0) & (r < H) & (c >= 0) & (c < W); inside = np.zeros(len(P), bool); inside[ok] = v["m"][r[ok], c[ok]]
    return ok, inside, r, c, dep
def 부피(쓸, 깎기=True):
    proj = {n: 투영(n, *각[n]) for n in 쓸}; 표 = sum(pr[1].astype(int) for pr in proj.values()); 보임 = sum(pr[0].astype(int) for pr in proj.values())
    keep = 표 >= len(쓸) - 1   # 화면 밖 = 머리 밖(머리는 장마다 화면 안에 다 있다)
    if 깎기:
        for n in 쓸:
            ok, ins, r, c, dep = proj[n]; v = V[n]; s = np.full(len(P), np.nan); q = ok & ins; s[q] = v["Z"][r[q], c[q]]
            sel = keep & q & ~np.isnan(s)
            if sel.sum() < 50: continue
            off = np.nanpercentile(dep[sel], 99) - np.nanpercentile(s[sel], 99)   # 껍질 꼭대기 = 남은 부피의 가장 앞
            keep &= ~(sel & (dep > s + off + 3))
    return keep
def iou_장(n, keep):
    ok, ins, r, c, dep = 투영(n, *각[n]); img = np.zeros(V[n]["m"].shape, bool); q = keep & ok; img[r[q], c[q]] = True
    kk = int(np.ceil((2 * R / (G - 1)) / V[n]["k"])) + 1; img = cv2.dilate(img.astype(np.uint8), np.ones((kk, kk), np.uint8)) > 0; m = V[n]["m"]   # 복셀 하나 = 화소 kk 개
    return float((img & m).sum() / max(1, (img | m).sum()))
처음 = {n: list(각[n]) for n in 장}
for 바퀴 in range(2):
    for n in 장:
        if n == "1": continue   # 정면이 틀의 기준
        남 = [q for q in 장 if q != n]; keep = 부피(남, 깎기=False); best = (iou_장(n, keep), 각[n][:])
        th0, ph0 = 각[n]
        for th in range(th0 - 20, th0 + 21, 5):
            for ph in range(ph0 - 15, ph0 + 16, 5):
                각[n] = [th, ph]; s = iou_장(n, keep)
                if s > best[0]: best = (s, [th, ph])
        각[n] = best[1]; print(바퀴, n, 각[n], round(best[0], 3))
LOO = {n: round(iou_장(n, 부피([q for q in 장 if q != n])), 3) for n in 장}
keep = 부피(장); Vg = keep.reshape(G, G, G)
vt, fc, _, _ = measure.marching_cubes(np.pad(Vg, 1).astype(np.float32), 0.5); vt = (vt - 1) * (2 * R / (G - 1)) - R
mesh = trimesh.Trimesh(np.c_[vt[:, 0], -vt[:, 1], vt[:, 2]], fc); trimesh.smoothing.filter_taubin(mesh, iterations=8)   # 블렌더: 앞(정면 카메라 쪽) = −y
mesh.export(os.path.join(O, "합친머리.ply"))
결과 = {"처음 각(yaw, pitch)": 처음, "찾은 각": 각, "나를 뺀 IoU": LOO, "복셀": int(keep.sum())}
json.dump(결과, open(os.path.join(O, "합친머리.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(결과)
