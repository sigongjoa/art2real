# -*- coding: utf-8 -*-
"""창 모듈 2 판 (10-04 「그 다음 ㄱㄱ」 · 창 모듈 1 판의 남은 것 셋을 고침).
① 창 모양: 원화의 밝은 테 = 비스듬히 벌어진 창 옆벽(건축: 경사 문설주 · splayed reveal) — 앞(벽 면)의 창 윤곽 = 눈구멍 + 테 · 안(깊이 17)의 윤곽 = 검은 눈구멍
   → 그 사이를 거리 비례로 이음(옆벽이 앞으로 벌어짐). 1 판은 테를 빼서 창이 작고 둥글었다.
② 벽: 평판 대신 정면 접힌 판(판_1_Z · 셀 그림자로 세운 면)의 상대 높이 — 창 둘레 고리 평균을 0 으로, 앞 = −. 배율 1(같은 화소 단위) · ±25 로 자름(가정)
③ 립: 창 앞 윤곽 위쪽 3 화소 띠를 2 앞으로(옆에서 잰 두께 3.7 · 내민 길이는 옆에서 거의 0 → 2 가정)
한 장의 높이장 → 한 메시라 벽 · 옆벽 · 안쪽이 붙어 있음은 구성상. 출력 out/오메가몬2/블렌더/창모듈2.ply · 창모듈2_비교.png"""
import os, json, numpy as np, cv2, trimesh
from scipy import ndimage
O = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
기준 = json.load(open(os.path.join(O, "기준선.json"), encoding="utf-8")); 층, 축 = 기준["층(정면 판 화소 행)"], 기준["정면 축(판 화소 열)"]
깊 = json.load(open(os.path.join(O, "창깊이.json"), encoding="utf-8")); D = (깊["창 깊이(옆 · 입구 → 눈)"] + 깊["창 깊이(3/4 · 옆벽 폭 / sin 35°)"]) / 2
대응 = json.load(open(os.path.join(O, "부품ID.json"), encoding="utf-8"))["대응표"]["1"]
z = np.load(os.path.join(O, "1.npz")); L = z["라벨"]; yy, xx = np.nonzero(L > 0); y0, x0 = yy.min(), xx.min()
zz = np.load(os.path.join(O, "판_1_Z.npz")); m, Z = zz["m"], zz["Z"]; H, W = m.shape; py, px = np.mgrid[0:H, 0:W]
cell = L[np.clip(y0 + 2 * py, 0, L.shape[0] - 1), np.clip(x0 + 2 * px, 0, L.shape[1] - 1)] * m
칸 = lambda 표면들: [c for e in 대응 if e.get("부품") == "H03 눈 조립" and e.get("표면") in 표면들 for c in e["칸"]]
닫기 = lambda a: cv2.morphologyEx(a.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) > 0
안 = 닫기(np.isin(cell, 칸(("눈구멍", "눈")))); 앞 = 닫기(np.isin(cell, 칸(("눈구멍", "눈", "테")))) | 안
xl, xr = sorted([축["E' 볼날개 끝 L"], 축["E 볼날개 끝 R"]]); top, bot = 층["L7 뿔 뿌리"] - 10, 층["L4 코판 끝"]
판 = m & (py >= top) & (py <= bot) & (px >= xl) & (px <= xr)
# ② 벽 높이: 접힌 판 상대값
Zf = np.where(np.isfinite(Z), Z, np.nanmean(Z[m])); 고리 = (cv2.dilate(앞.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0) & ~앞 & 판
rel = -(Zf - np.median(Zf[고리]))                  # 접힌 판 Z 는 보는 쪽 + → 앞 = − 로
dep = np.clip(rel, -25, 25) - D
# ① 경사 옆벽
d_in = ndimage.distance_transform_edt(~안); d_out = ndimage.distance_transform_edt(앞)
reveal = 앞 & ~안; t = d_in / np.maximum(1e-6, d_in + d_out)        # 안 경계 0 → 앞 경계 1
dep[reveal] = (-D * t)[reveal] + (dep[reveal] + D) * t[reveal]        # 앞 경계에서 벽 높이와 이어짐
dep[안] = 0.0
# ③ 립
위띠 = (cv2.dilate(앞.astype(np.uint8), np.ones((7, 1), np.uint8)) > 0) & ~앞 & np.roll(앞, 3, axis=0) & 판
dep[위띠] -= 2.0
쓸 = 판 | 앞
cu = (np.nonzero(m)[1].min() + np.nonzero(m)[1].max()) / 2
ys, xs = np.nonzero(쓸); vid = -np.ones((H, W), int); vid[ys, xs] = np.arange(len(ys)); n = len(ys)
V = np.c_[xs - cu, dep[ys, xs], -ys.astype(float)]
a, b, c, d = vid[:-1, :-1], vid[:-1, 1:], vid[1:, :-1], vid[1:, 1:]; ok = (a >= 0) & (b >= 0) & (c >= 0) & (d >= 0)
F = np.r_[np.c_[a[ok], b[ok], c[ok]], np.c_[b[ok], d[ok], c[ok]]]
art = cv2.imdecode(np.fromfile(os.path.join(O, "판_1_원화.png"), np.uint8), 1)[:, :, ::-1]
col = np.full((n, 3), (225, 228, 238), np.uint8); col[안[ys, xs]] = (25, 25, 32); col[reveal[ys, xs]] = (240, 242, 250); col[위띠[ys, xs]] = (250, 250, 255)
me = trimesh.Trimesh(V, F, process=False); me.visual.vertex_colors = np.c_[col, np.full(n, 255)].astype(np.uint8)
parts = [me]
P = json.load(open(os.path.join(O, "특징점.json"), encoding="utf-8"))["1"]
for side in ("왼", "오른"):
    ex, ey = P[f"눈/{side}"]; e = trimesh.creation.cylinder(radius=9, height=1.5, sections=24); e.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    e.apply_translation([ex - cu, -1.0, -ey]); e.visual.vertex_colors = np.tile([70, 130, 230, 255], (len(e.vertices), 1)).astype(np.uint8); parts.append(e)
allm = trimesh.util.concatenate(parts); allm = trimesh.Trimesh(allm.vertices, allm.faces, vertex_colors=allm.visual.vertex_colors, process=False)
allm.export(os.path.join(B, "창모듈2.ply"), encoding="ascii")
print({"창 깊이": round(D, 1), "안 화소": int(안.sum()), "앞 화소": int(앞.sum()), "옆벽 화소": int(reveal.sum()), "립 화소": int(위띠.sum()), "벽 상대 높이 범위": [round(float(np.percentile(rel[판], 5)), 1), round(float(np.percentile(rel[판], 95)), 1)]})
