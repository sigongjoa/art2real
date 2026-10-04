# -*- coding: utf-8 -*-
"""저폴리 눈 (10-04 사용자 「눈쪽 해볼래? 눈도 깊이감 있잖아」).
창 모듈 3 판의 눈구멍은 화소 높이장이라 계단 · 눈은 납작한 파란 원판이었다 → 부리와 같은 저폴리 방식으로 다시:
  앞 윤곽(테 포함 창 입구) · 안 윤곽(검은 눈구멍) = 창모듈2.py 와 같은 먹선 규칙 → 다각형 근사(꼭짓점 몇 개)
  앞 윤곽 꼭짓점 깊이 = 그 자리 둘레 벽(창 모듈 판)의 깊이 — 벽에 붙음은 구성상
  안 윤곽 = 눈 깊이 0(창 깊이 17.2 = 입구 → 눈 앞 · 옆 · 3/4 일치) · 그 사이 = 옆벽(경사 문설주) 삼각형 고리
  눈구멍 바닥 = 안 윤곽을 +4 뒤에(가정 · 검은 칠이라 안 보임)
  눈알 = 낮은 구면 모자: 반지름 = 눈동자(검은 구멍 안 밝은 덩어리) 넓이 환산 · 앞 꼭대기 = 0(잰 눈 앞) · 가장자리 +반지름×0.4(가정) · 색 = 정면 원화를 그대로 투영(칠)
저폴리부리10.ply 에서 창 모듈의 눈구멍 · 파란 원판 면을 지우고 끼움 → out/오메가몬2/블렌더/저폴리눈.ply"""
import os, json, numpy as np, cv2, trimesh
from scipy import ndimage
from scipy.spatial import Delaunay
O = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
기준 = json.load(open(os.path.join(O, "기준선.json"), encoding="utf-8")); 축 = 기준["정면 축(판 화소 열)"]; xa = 축["A 중심"]
m = np.load(os.path.join(O, "판_1_Z.npz"))["m"]; H, W = m.shape; py, px = np.mgrid[0:H, 0:W]; cu = (np.nonzero(m)[1].min() + np.nonzero(m)[1].max()) / 2
art = cv2.imdecode(np.fromfile(os.path.join(O, "판_1_원화.png"), np.uint8), 1); Lum = cv2.cvtColor(art, cv2.COLOR_BGR2LAB)[:, :, 0]; rgb = art[:, :, ::-1]
P0 = json.load(open(os.path.join(O, "특징점.json"), encoding="utf-8"))["1"]
base = trimesh.load(os.path.join(B, "저폴리부리10.ply"), process=False); 창 = trimesh.load(os.path.join(B, "창모듈2.ply"), process=False); f0 = len(창.faces)
wall_v = 창.vertices; 벽깊이 = lambda x, y: float(wall_v[np.argmin((wall_v[:, 0] + cu - x) ** 2 + (-wall_v[:, 2] - y) ** 2), 1])
def 다각(mask, eps):
    cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); return cv2.approxPolyDP(max(cs, key=cv2.contourArea), eps, True).reshape(-1, 2).astype(float)
def 안쪽(poly, pts): return np.array([cv2.pointPolygonTest(poly.astype(np.float32), (float(p[0]), float(p[1])), False) >= 0 for p in pts])
지울 = np.zeros(len(base.faces), bool); parts = []; 기록 = {}
for side in ("왼", "오른"):
    ex, ey = [int(v) for v in P0[f"눈/{side}"]]; 반 = (px < xa - 3) if ex < xa else (px > xa + 3)
    n_, lab = cv2.connectedComponents((Lum < 45).astype(np.uint8)); ys_, xs_ = np.nonzero(lab > 0); j = np.argmin((xs_ - ex) ** 2 + (ys_ - ey) ** 2)
    blk = (lab == lab[ys_[j], xs_[j]]) & 반; blk = ndimage.binary_fill_holes(cv2.morphologyEx(blk.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)) > 0)
    near = (cv2.dilate(blk.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13))) > 0) & 반
    n2, lab2 = cv2.connectedComponents(((Lum >= 90) & near & ~blk).astype(np.uint8), connectivity=4)
    touch = set(np.unique(lab2[(cv2.dilate(blk.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & (lab2 > 0)])) - {0}
    out_ = ndimage.binary_fill_holes(cv2.morphologyEx((blk | np.isin(lab2, list(touch))).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) > 0)
    Po, Pi = 다각(out_, 2.5), 다각(blk, 2.0)
    # 창 모듈의 이 창 안 면(계단 옆벽 · 파란 원판) 지우기
    cen = base.triangles_center[:f0]; 지울[:f0] |= 안쪽(Po, np.c_[cen[:, 0] + cu, -cen[:, 2]])
    blue = base.visual.vertex_colors[base.faces[:, 0], 2] > 200; blue &= base.visual.vertex_colors[base.faces[:, 0], 0] < 100
    지울 |= blue & 안쪽(Po, np.c_[base.triangles_center[:, 0] + cu, -base.triangles_center[:, 2]])
    # 옆벽 고리
    do = np.array([벽깊이(x, y) for x, y in Po]); Q = np.r_[Po, Pi]; dq = np.r_[do, np.zeros(len(Pi))]
    tri = Delaunay(Q); c2 = Q[tri.simplices].mean(1); ring = tri.simplices[안쪽(Po, c2) & ~안쪽(Pi, c2)]
    r_ = trimesh.Trimesh(np.c_[Q[:, 0] - cu, dq, -Q[:, 1]], ring, process=False); r_.visual.vertex_colors = np.tile([238, 240, 248, 255], (len(Q), 1)).astype(np.uint8); parts.append(r_)
    # 바닥
    tb = Delaunay(Pi); fb = tb.simplices[안쪽(Pi, Pi[tb.simplices].mean(1))]
    b_ = trimesh.Trimesh(np.c_[Pi[:, 0] - cu, np.full(len(Pi), 4.0), -Pi[:, 1]], fb, process=False); b_.visual.vertex_colors = np.tile([20, 20, 26, 255], (len(Pi), 1)).astype(np.uint8); parts.append(b_)
    # 눈알: 검은 구멍 안 밝은 덩어리(눈동자) 넓이 → 반지름
    n3, lab3 = cv2.connectedComponents((blk & (Lum >= 45)).astype(np.uint8)); 크기 = np.bincount(lab3.ravel())[1:]
    k = 1 + int(np.argmax(크기)); yy, xx = np.nonzero(lab3 == k); cx, cy = xx.mean(), yy.mean(); R = float(np.sqrt(len(xx) / np.pi))
    링, 둘레 = 5, 20; V = [(cx, cy, 0.0)]
    for i in range(1, 링 + 1):
        rr = R * i / 링
        for a in np.linspace(0, 2 * np.pi, 둘레, endpoint=False): V.append((cx + rr * np.cos(a), cy + rr * np.sin(a), 0.4 * R * (i / 링) ** 2))
    V = np.array(V); F = [(0, 1 + (a + 1) % 둘레, 1 + a) for a in range(둘레)]
    for i in range(1, 링):
        s0, s1 = 1 + (i - 1) * 둘레, 1 + i * 둘레
        for a in range(둘레):
            b_ = (a + 1) % 둘레; F += [(s0 + a, s0 + b_, s1 + b_), (s0 + a, s1 + b_, s1 + a)]
    e_ = trimesh.Trimesh(np.c_[V[:, 0] - cu, V[:, 2], -V[:, 1]], np.array(F), process=False)
    bad = e_.face_normals[:, 1] > 0; e_.faces[bad] = e_.faces[bad][:, ::-1]
    cc = rgb[np.clip(V[:, 1].round().astype(int), 0, H - 1), np.clip(V[:, 0].round().astype(int), 0, W - 1)]
    e_.visual.vertex_colors = np.c_[cc, np.full(len(V), 255)].astype(np.uint8); parts.append(e_)
    기록[side] = {"앞 윤곽 꼭짓점": len(Po), "안 윤곽 꼭짓점": len(Pi), "앞 윤곽 깊이": [round(float(do.min()), 1), round(float(do.max()), 1)], "눈알 반지름": round(R, 1)}
keep = base.copy(); keep.update_faces(~지울); keep.remove_unreferenced_vertices()
allm = trimesh.util.concatenate([keep] + parts)
trimesh.Trimesh(allm.vertices, allm.faces, vertex_colors=allm.visual.vertex_colors, process=False).export(os.path.join(B, "저폴리눈.ply"), encoding="ascii")
print(기록, {"지운 면": int(지울.sum())})
