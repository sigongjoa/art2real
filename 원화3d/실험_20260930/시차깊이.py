# -*- coding: utf-8 -*-
"""시차 깊이 — 정면 ↔ 3/4(30°) 두 장의 **시차**로 깊이를 잰다 (2026-09-30 · 학습 깊이 모델은 셀화에서 얼굴을 평면으로 읽었다 · 옆 캡처는 검산용으로 남긴다).
    python 시차깊이.py -> out/깊이카드/시차_정면.npy (정면 캡처 해상도 · z 단위) · 시차깊이.png (앵커 점 · 채운 깊이)
② 짝 면(정면 ids ↔ 3/4 ids)의 **경계** 화소마다: 정면 (x,y) 를 z 로 훑어 3/4 카메라(자세5)로 찍어 3/4 짝 면 경계에 닿는 z (거리 변환 · 허용 6 px) — 경계가 세로 성분이 있을 때만(가로 경계는 시차를 못 준다).
바깥 실루엣도 같은 식(정면 실루엣 경계 ↔ 3/4 실루엣 경계 · 눈 위 띠 제외). 앵커를 실루엣 안에 라플라시안으로 채운다(면 안은 매끈 · 경계는 앵커)."""
import os, sys, json
import numpy as np, cv2
from scipy.sparse import lil_matrix, csr_matrix
from scipy.sparse.linalg import spsolve
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(R, "오메가몬", "지표")); from 집합 import OUT, J
from 부품투영 import 찍기
D = J(OUT, "..", "자료"); K = J(R, "out", "깊이카드"); os.makedirs(K, exist_ok=True); S = 3
기록 = json.load(open(J(D, "자료.json"), encoding="utf-8")); 자세 = json.load(open(J(OUT, "자세3.json"), encoding="utf-8")); F = 자세["정면 yt_172"]; Rf = cv2.Rodrigues(np.asarray(F["r"], float))[0]; Q = 자세["3/4 M04"]
선택 = json.load(open(J(D, "면대응_선택.json"), encoding="utf-8"))["짝"]; L정 = np.load(J(D, "02_정면_영역.npz"))["라벨"]; L34 = np.load(J(D, "02_3-4_영역.npz"))["라벨"]
읽 = lambda p, f=cv2.IMREAD_COLOR: cv2.imdecode(np.fromfile(p, np.uint8), f)
im = 읽(기록["02_정면"]["파일"]); H, W = im.shape[:2]; x0, y0, x1, y1 = 기록["02_정면"]["상자"]; sil = 읽(J(D, "02_정면_실루엣.png"), 0) > 127
sil34 = 읽(J(D, "02_3-4_실루엣.png"), 0) > 127; H34, W34 = sil34.shape; L34s = cv2.resize(L34, (W34, H34), interpolation=cv2.INTER_NEAREST); L정s = cv2.resize(L정, (W, H), interpolation=cv2.INTER_NEAREST)
눈위 = np.nonzero(np.isin(L34s, [7, 8]).any(1))[0].min()                                             # 3/4 는 뿔이 잘려 눈 위 띠는 모름
def 단위xy(u, v): return (u - F["t"][0]) / F["s"], (v - F["t"][1]) / F["s"]
zs = np.arange(-40, 121, 1.0)
def 경계화소(m): return np.column_stack(np.nonzero(m & ~(cv2.erode(m.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0)))     # (v, u)
def 거리장(m):
    e = m & ~(cv2.erode(m.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0); return cv2.distanceTransform((~e).astype(np.uint8), cv2.DIST_L2, 3), e
def 세로성분(e):
    gy = cv2.Sobel(e.astype(np.float32), cv2.CV_32F, 0, 1, ksize=5); gx = cv2.Sobel(e.astype(np.float32), cv2.CV_32F, 1, 0, ksize=5); return np.abs(gx) / (np.abs(gx) + np.abs(gy) + 1e-6)   # 경계가 세로일수록 1 (x 방향 기울기)
앵커 = []                                                                                            # (v, u, z, 출처)
def 맞추기(m정, m34, 이름, 허용=6.0, 간격=3):
    dist, e34 = 거리장(m34); 세로 = 세로성분(e34); pts = 경계화소(m정)[::간격]; n = 0
    for v, u in pts:
        if not sil[v, u]: continue
        x, y = 단위xy(float(u), float(v)); C = np.stack([np.full_like(zs, x), np.full_like(zs, y), -zs], 1); U = (C @ Rf) * (1, 1, -1); uv, _ = 찍기(U, Q); p = np.round(uv).astype(int)
        ok = (p[:, 0] >= 0) & (p[:, 0] < W34) & (p[:, 1] >= 눈위) & (p[:, 1] < H34); d = np.full(len(zs), 1e9); d[ok] = dist[p[ok, 1], p[ok, 0]]
        i = int(np.argmin(d))
        if d[i] > 허용: continue
        if 세로[p[i, 1], p[i, 0]] < 0.5: continue                                                   # 가로 경계는 z 를 못 가른다
        near = np.nonzero(d <= d[i] + 1.0)[0]
        if zs[near].max() - zs[near].min() > 25: continue                                             # 여러 z 가 다 닿으면(경계가 시선과 나란) 버린다
        앵커.append((v, u, float(zs[near].mean()), 이름)); n += 1
    return n
for n_, 짝 in 선택.items():
    if 짝.get("정면") and 짝.get("3-4"): print("%-6s 앵커 %d" % (n_, 맞추기(np.isin(L정s, 짝["정면"]), np.isin(L34s, 짝["3-4"]), n_)))
print("실루엣 앵커 %d" % 맞추기(sil, sil34, "실루엣", 허용=5.0, 간격=4))
A = np.array([(a[0], a[1], a[2]) for a in 앵커]); print("앵커 총 %d · z 범위 %.0f..%.0f · 중앙 %.0f" % (len(A), A[:, 2].min(), A[:, 2].max(), np.median(A[:, 2])))
# 상자 안 · 실루엣 안을 라플라시안으로 채운다(앵커 고정) — 4 배 축소 격자
축 = 4; h, w = (y1 - y0) // 축, (x1 - x0) // 축; m = cv2.resize(sil[y0:y1, x0:x1].astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST) > 0
고정 = {}
for v, u, z in A:
    gv, gu = int((v - y0) / 축), int((u - x0) / 축)
    if 0 <= gv < h and 0 <= gu < w: 고정.setdefault((gv, gu), []).append(z)
idx = -np.ones((h, w), int); ii = np.nonzero(m); idx[ii] = np.arange(len(ii[0])); N = len(ii[0]); Amat = lil_matrix((N, N)); b = np.zeros(N)
for k, (gv, gu) in enumerate(zip(*ii)):
    if (gv, gu) in 고정: Amat[k, k] = 1; b[k] = np.median(고정[(gv, gu)]); continue
    nb = [idx[gv + dv, gu + du] for dv, du in ((-1, 0), (1, 0), (0, -1), (0, 1)) if 0 <= gv + dv < h and 0 <= gu + du < w and idx[gv + dv, gu + du] >= 0]
    Amat[k, k] = len(nb)
    for j in nb: Amat[k, j] = -1
z = spsolve(csr_matrix(Amat), b); Z = np.zeros((h, w), np.float32); Z[ii] = z
full = np.zeros((H, W), np.float32); full[y0:y0 + h * 축, x0:x0 + w * 축] = cv2.resize(Z, (w * 축, h * 축), interpolation=cv2.INTER_LINEAR); np.save(J(K, "시차_정면.npy"), full)
json.dump(dict(앵커수=len(A), 출처별={k: int(sum(1 for a in 앵커 if a[3] == k)) for k in set(a[3] for a in 앵커)}, z중앙=float(np.median(A[:, 2]))), open(J(K, "시차깊이.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
# 그림: 앵커(색 = z) · 채운 깊이
from PIL import Image, ImageDraw, ImageFont
ft = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 20); vis = im.copy(); zmin, zmax = np.percentile(A[:, 2], 5), np.percentile(A[:, 2], 95)
for v, u, z_ in A: c = cv2.applyColorMap(np.array([[int(255 * np.clip((z_ - zmin) / max(1e-6, zmax - zmin), 0, 1))]], np.uint8), cv2.COLORMAP_TURBO)[0, 0]; cv2.circle(vis, (int(u), int(v)), 3, tuple(int(x) for x in c), -1)
P1 = Image.fromarray(vis[y0:y1, x0:x1, ::-1]); P1 = P1.resize((int(P1.width * 500 / P1.height), 500)); ImageDraw.Draw(P1).text((6, 6), "시차 앵커 %d (빨 가까움 → 파 멀리)" % len(A), font=ft, fill=(0, 0, 0), stroke_width=2, stroke_fill=(255, 255, 255))
dn = full[y0:y1, x0:x1]; dn = (255 * (dn - zmin) / max(1e-6, zmax - zmin)).clip(0, 255).astype(np.uint8); dn[~sil[y0:y1, x0:x1]] = 0
P2 = Image.fromarray(cv2.applyColorMap(dn, cv2.COLORMAP_TURBO)[:, :, ::-1]); P2 = P2.resize((int(P2.width * 500 / P2.height), 500)); ImageDraw.Draw(P2).text((6, 6), "채운 깊이", font=ft, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
시트 = Image.new("RGB", (P1.width + P2.width + 10, 500), (250, 250, 248)); 시트.paste(P1, (0, 0)); 시트.paste(P2, (P1.width + 10, 0)); 시트.save(J(K, "시차깊이.png")); print(J(K, "시차깊이.png"))
