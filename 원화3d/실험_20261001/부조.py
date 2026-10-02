# -*- coding: utf-8 -*-
"""색 + 깊이로 세운 부조(2.5D) — 정면 · 좌 · 우 (10-02 사용자 「얼추 정보는 찾고 있네 · 이걸 바탕으로 좌우 · 정면 보여줘」).
정면 원화 한 장: 칸마다 깊이 = 먹선 굵게 판 DA V2 중앙(색깊이.json) · 칸 안은 DA 굴곡 0.35 배만 남김
색 규칙: 검정(속머리) 칸은 맞닿은 갑주 칸 중 가장 뒤보다 2 단위 더 뒤
눈금: DA 상대값 3~97 % → 0~25 머리 단위(옆 원화 머리 앞뒤 ≈ 75 옆 단위 × 0.658 ≈ 49 의 앞 절반 — 옆 원화에서 숫자 하나만)
뒤는 그림에 없음 → 앞면에서 6 단위 껍질만. 복셀 기둥 → 행진 입방체 → 색은 원화 화소. 출력 out/오메가몬2/지표/부조/"""
import os, json, numpy as np, cv2, trimesh
from skimage import measure
from scipy import ndimage
K = r"G:\art2real\원화3d\out\오메가몬2\지표"; G_ = os.path.join(K, "원화그림자"); O = os.path.join(K, "부조"); os.makedirs(O, exist_ok=True)
ART = r"G:\art2real\원화3d\out\번역\디지몬\장면\02_역습\yt_172.0_얼굴_정면.jpg"
x0, y0, x1, y1 = json.load(open(os.path.join(G_, "그림자.json"), encoding="utf-8"))["자르기"]
Lfull = np.load(os.path.join(K, "선파츠_정면.npz"))["라벨"]; top, bot = np.nonzero(Lfull > 0)[0].min(), np.nonzero(Lfull > 0)[0].max(); k = 100 / (bot - top)
L = Lfull[y0:y1, x0:x1]; img = cv2.imdecode(np.fromfile(ART, np.uint8), 1)[y0:y1, x0:x1]; D = np.load(os.path.join(G_, "먹선굵게_깊이.npy"))
칸 = {int(n): v for n, v in json.load(open(os.path.join(G_, "색깊이.json"), encoding="utf-8"))["칸"].items()}
# 먹선 벽(라벨 0)을 이웃 칸으로 채움 · 머리 밖은 비움
head = ndimage.binary_closing(L > 0, np.ones((7, 7))) | (L > 0)
idx = ndimage.distance_transform_edt(L == 0, return_distances=False, return_indices=True); Lf = L[idx[0], idx[1]]; Lf[~head] = 0
# 색 규칙: 검정 칸은 맞닿은 갑주 칸 중 가장 뒤보다 더 뒤
깊 = {n: v["깊이"] for n, v in 칸.items()}; 이웃 = {}
for dy, dx in ((0, 1), (1, 0)):
    p = Lf[: Lf.shape[0] - dy, : Lf.shape[1] - dx]; q = Lf[dy:, dx:]; ok = (p > 0) & (q > 0) & (p != q)
    for i, j in set(zip(p[ok].tolist(), q[ok].tolist())): 이웃.setdefault(i, set()).add(j); 이웃.setdefault(j, set()).add(i)
lo_, hi_ = np.percentile(list(깊.values()), 3), np.percentile(list(깊.values()), 97); 단위 = 25.0 / (hi_ - lo_)      # DA 값 → 머리 단위
고침 = []
for n, v in 칸.items():
    if v["색"].startswith("검정"):
        nb = [깊[j] for j in 이웃.get(n, []) if not 칸[j]["색"].startswith("검정")]
        if nb and 깊[n] > min(nb) - 2 / 단위: 고침.append((n, round(깊[n], 1), round(min(nb) - 2 / 단위, 1))); 깊[n] = min(nb) - 2 / 단위
# 화소 깊이 = 칸 깊이 + 칸 안 굴곡 0.35 배
Z = np.zeros(L.shape); cm = np.zeros(L.shape)
for n in np.unique(Lf):
    if n == 0: continue
    m = Lf == n; Z[m] = 깊[n] + 0.35 * (D[m] - np.median(D[m]))
Z = np.clip((Z - lo_) * 단위, -3, 28); Z[~head] = np.nan
# 부조 고체: 화소 기둥(뒷판 = 가장 뒤 − 4 ~ 앞면) → 0.5 단위 복셀 → 행진 입방체
px = k; nzb = float(np.nanmin(Z)) - 4; zz = np.arange(nzb, np.nanmax(Z) + 1, 0.5)
H, W = L.shape; V = np.zeros((W, H, len(zz)), bool)
for x in range(W):
    col = Z[:, x]; ok = ~np.isnan(col)
    V[x, ok, :] = (zz[None, :] <= col[ok, None]) & (zz[None, :] >= col[ok, None] - 6)   # 앞면 껍질 6 단위(뒷판까지 채우면 옆에서 사각 판에 묻힘)
v, f, _, _ = measure.marching_cubes(np.pad(V, 1).astype(np.float32), 0.5)
v -= 1; X = (v[:, 0] + x0 - (Lfull.shape[1] / 2)) * px; Yd = (v[:, 1]) * px; Zz = nzb + v[:, 2] * 0.5
mesh = trimesh.Trimesh(np.c_[X, -Zz, -Yd], f)                      # 블렌더: x 오른 · −y 앞(z 앞 → −y) · z 위(y 아래 → −z)
trimesh.smoothing.filter_taubin(mesh, iterations=6)
ci = np.clip(np.round(v[:, 0]).astype(int), 0, W - 1); cj = np.clip(np.round(v[:, 1]).astype(int), 0, H - 1)
col = (255 * (img[cj, ci][:, ::-1] / 255.0) ** 0.55).astype(np.uint8);   # 밝게(블렌더 꼭짓점색이 어둡게 보임)
mesh.visual.vertex_colors = np.c_[col, np.full(len(col), 255)].astype(np.uint8)
mesh.export(os.path.join(O, "부조.ply"))
json.dump({"색규칙으로뒤로보낸칸": 고침, "눈금": {"DA→단위": 단위, "앞뒤범위단위": 25, "근거": "옆 원화 머리 앞뒤 ≈ 49 단위의 앞 절반"}, "면": int(len(mesh.faces))},
          open(os.path.join(O, "부조.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("면", len(mesh.faces), "· 색 규칙으로 뒤로 보낸 칸", len(고침), 고침[:6])
