# -*- coding: utf-8 -*-
"""원화의 셀 그림자를 찾아 과장 (10-02 사용자 「AI 는 쓰지 않을 거야 · 그림자를 인식하고 더 과장만 해 보자」).
생성 AI 로 그림자를 입히지 않는다 — 원화(02 정면 캡처)에 애니메이터가 그린 그림자만 쓴다.
  그림자 찾기: 연결그래프 부품(정면 칸 묶음)마다 밝기를 두 무리로(오츠) 나눠 어두운 무리 = 그림자(밝기 차가 작으면 그림자 없음)
  과장: 그림자 × 0.35 · 밝은 면 × 1.18 · 이름 묶음(좌우 합쳐) 단위로 찾음 · 먹선(벽) 2 px 굵게
  세 판(원본 · 먹선 굵게 · 먹선 + 그림자 과장) → 깊이 추정(재는 자로만 · 형태엔 안 씀) → TripoSG 앞면 깊이(따로 만든 3D · 참고 기준)와 순위 상관
출력 out/오메가몬2/지표/원화그림자/"""
import os, json, numpy as np, cv2, trimesh
from PIL import Image
R = r"G:\art2real\원화3d\out"; K = os.path.join(R, "오메가몬2", "지표"); O = os.path.join(K, "원화그림자"); os.makedirs(O, exist_ok=True)
ART = os.path.join(R, "번역", "디지몬", "장면", "02_역습", "yt_172.0_얼굴_정면.jpg")
L = np.load(os.path.join(K, "선파츠_정면.npz"))["라벨"]; 그래프 = json.load(open(os.path.join(K, "연결그래프", "그래프.json"), encoding="utf-8"))
img = cv2.imdecode(np.fromfile(ART, np.uint8), cv2.IMREAD_COLOR); lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(float); Lum = lab[:, :, 0]
head = L > 0; ys, xs = np.nonzero(head); top, bot = ys.min(), ys.max(); k = 100 / (bot - top)
# 그림자 찾기
shadow = np.zeros(L.shape, bool); 표 = {}
묶음 = {}
for p in 그래프["부품"]: 묶음.setdefault(p["이름"].split("/")[0], []).extend(p["칸"])   # 좌우 합쳐서(뿔 = 밝은 왼면 + 그늘진 오른면 · 반쪽이면 한 톤뿐)
for 이름_, 칸 in 묶음.items():
    p = {"이름": 이름_}; m = np.isin(L, 칸) & ~(cv2.morphologyEx(Lum.astype(np.uint8), cv2.MORPH_BLACKHAT, np.ones((7, 7), np.uint8)) > 28); v = Lum[m].astype(np.uint8)
    if v.size < 50: continue
    t, _ = cv2.threshold(v.reshape(-1, 1), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU); dark = Lum[m] < t
    gap = Lum[m][~dark].mean() - Lum[m][dark].mean() if dark.any() and (~dark).any() else 0
    if gap > 18 and 0.1 < dark.mean() < 0.9: shadow[m] = dark; 표[p["이름"]] = {"그림자비": round(float(dark.mean()), 2), "밝기차": round(float(gap), 1)}
wall = head.copy(); wall[:] = False
ink = cv2.morphologyEx(Lum.astype(np.uint8), cv2.MORPH_BLACKHAT, np.ones((7, 7), np.uint8)) > 28
ink &= cv2.dilate(head.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
판 = {"원본": img.copy()}
a = img.copy(); a[cv2.dilate(ink.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0] = (20, 20, 25); 판["먹선굵게"] = a
b = a.astype(float); b[shadow & ~ink] *= 0.35; lit = head & ~shadow & ~ink; b[lit] = np.clip(b[lit] * 1.18, 0, 255); b = b.astype(np.uint8)
b[cv2.dilate(ink.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0] = (20, 20, 25); 판["먹선굵게_그림자과장"] = b
x0, x1 = max(0, xs.min() - 40), min(L.shape[1], xs.max() + 40); y0, y1 = max(0, top - 20), min(L.shape[0], bot + 30)
for nm, im in 판.items(): cv2.imencode(".png", cv2.resize(im[y0:y1, x0:x1], None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC))[1].tofile(os.path.join(O, f"{nm}.png"))
sv = np.zeros_like(img); sv[head] = (200, 200, 200); sv[shadow] = (90, 60, 160); cv2.imencode(".png", sv[y0:y1, x0:x1])[1].tofile(os.path.join(O, "그림자찾기.png"))
# TripoSG 앞면 깊이를 원화 화소에(머리 단위 사상 · 부피칸.py 와 같은 틀)
m3 = trimesh.load(os.path.join(K, "부피칸", "h_remesh.obj"), process=False); vg = m3.voxelized(0.5).fill(); V = vg.matrix; lo = vg.transform[:3, 3]
has = V.any(2); nz = V.shape[2]; zi = np.where(has, nz - 1 - np.argmax(V[:, :, ::-1], 2), -1)
dome = np.isin(L, [n for p in 그래프["부품"] if p["이름"].startswith("투구 돔") for n in p["칸"]]); dx_ = np.nonzero(dome)[1]; cx = (dx_.min() + dx_.max()) / 2
YY, XX = np.mgrid[y0:y1, x0:x1]; gi = np.round(((XX - cx) * k - lo[0]) / 0.5).astype(int); gj = np.round(((YY - top) * k - lo[1]) / 0.5).astype(int)
ok = (gi >= 0) & (gi < V.shape[0]) & (gj >= 0) & (gj < V.shape[1]); trip = np.full(YY.shape, np.nan); z = np.full(YY.shape, -1); z[ok] = zi[gi[ok], gj[ok]]
trip[z >= 0] = lo[2] + z[z >= 0] * 0.5          # 클수록 앞
np.save(os.path.join(O, "트리포_앞면깊이.npy"), trip); np.save(os.path.join(O, "머리마스크.npy"), head[y0:y1, x0:x1])
json.dump({"그림자부품": 표, "자르기": [int(x0), int(y0), int(x1), int(y1)]}, open(os.path.join(O, "그림자.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("그림자 찾은 부품", len(표), "/", len(그래프["부품"]), "· 그림자 화소", int(shadow.sum()), "/", int(head.sum()))
