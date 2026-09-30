# -*- coding: utf-8 -*-
"""소체 조각 — 원형사 블록인(Spencer 1장 · GSC 「실루엣으로 뼈대를 세우고 볼륨을 조금씩」): 구 하나에서 시작해 **실루엣부터** 맞춘다 (2026-09-30).
    python 소체조각.py -> out/오메가몬2/블렌더/소체.stl (블렌더 좌표) · 소체조각.png (세 시점 실루엣 겹침: 빨 캡처 · 초 소체) · 소체조각.json(시점별 실루엣 IoU)
붓 = Grab 의 뜻 그대로: 시점마다 그 그림 평면 안에서만 점을 옮긴다(옆 뷰 = z 만 · 정면 = x·y 만 · 교본 「옆모습에서 z 로만 점을 옮긴다」) · 사이사이 라플라시안 스무딩(볼륨을 조금씩).
대상 = 머리 덩어리(투구 + 얼굴) 실루엣: 뿔 · 안테나는 열기(opening)로 지움(따로 만드는 겹) · 3/4 는 눈 위(뿔 잘린 띠) 안 씀 · 카메라는 블록아웃.json(자세5) 그대로."""
import os, sys, json
import numpy as np, cv2, trimesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, J
D = J(OUT, "..", "자료"); B = J(OUT, "..", "블렌더"); S = 3
스펙 = json.load(open(J(B, "블록아웃.json"), encoding="utf-8")); 카 = {c["이름"]: c for c in 스펙["카메라"]}
읽 = lambda p: cv2.imdecode(np.fromfile(p, np.uint8), 0) > 127
자세정면 = json.load(open(J(OUT, "자세3.json"), encoding="utf-8"))["정면 yt_172"]; L옆 = np.load(J(D, "02_옆_영역.npz"))["라벨"]; 턱옆 = np.nonzero(L옆 == 15)[0].max() // S
def 머리덩어리(t):
    sil = 읽(J(D, t + "_실루엣.png")).astype(np.uint8); x0, y0, x1, y1 = 기록[t]["상자"]; m = np.zeros_like(sil); m[y0:y1, x0:x1] = 1; sil &= m
    sil = cv2.morphologyEx(sil, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (19, 19)))                 # 뿔 · 안테나(가는 것) 지움
    if t == "02_3-4": L = np.load(J(D, t + "_영역.npz"))["라벨"]; r = np.nonzero(np.isin(L, [7, 8]).any(1))[0].min() // S; sil[:r] = 0     # 눈 위 = 모름(뿔이 잘려 실루엣이 틀림)
    if t == "02_정면": F_ = 자세정면; sil[:int(F_["t"][1] - 2)] = 0; sil[int(F_["t"][1] + 100 * F_["s"] + 3):] = 0      # 돔 꼭대기(y 0) 위 = 뿔뿐 · 턱(y 100) 아래 = 목 · 깃
    if t == "02_옆": sil[int(턱옆 + 6):] = 0
    if t == "02_정면":
        F_ = 자세정면; r0 = int(F_["t"][1] + 60 * F_["s"]); xl, xr = int(F_["t"][0] - 36 * F_["s"]), int(F_["t"][0] + 36 * F_["s"]); sil[r0:, :xl] = 0; sil[r0:, xr:] = 0   # 어깨 갑주 뗌                                                                              # 턱 밑 = 목
    cs, _ = cv2.findContours(sil, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); big = max(cs, key=cv2.contourArea); out = np.zeros_like(sil); cv2.drawContours(out, [big], -1, 1, -1); return out > 0
기록 = json.load(open(J(D, "자료.json"), encoding="utf-8"))
시점 = ["02_정면", "02_옆", "02_3-4"]; 표적 = {t: 머리덩어리(t) for t in 시점}
쓰는행 = {t: None for t in 시점};
if True: L = np.load(J(D, "02_3-4_영역.npz"))["라벨"]; 쓰는행["02_3-4"] = np.nonzero(np.isin(L, [7, 8]).any(1))[0].min() // S
# 카메라: 픽셀 ↔ 블렌더 세계
def 투영(t, Vb):
    c = 카[t]; M = np.array(c["행렬"]); s = c["W"] / c["ortho_scale"]; Rm = M[:3, :3]; loc = M[:3, 3]; C = (Vb - loc) @ Rm            # 카메라 틀 (x 오른쪽 · y 위 · −z 앞)
    return np.stack([C[:, 0] * s + c["W"] / 2, -C[:, 1] * s + c["H"] / 2], 1), Rm, s
# 시작: 타원체(블록아웃 소체) — 밑 메시는 단순하게
소 = next(p for p in 스펙["부품"] if p["이름"] == "소체"); 구 = trimesh.creation.icosphere(subdivisions=4, radius=1.0); Vb = np.asarray(구.vertices) * np.array([38.8, 40.0, 36.0]) + np.array([0.0, 15.0, -34.0]); F = np.asarray(구.faces)
이웃 = [[] for _ in range(len(Vb))]
for a, b, c in F: 이웃[a] += [b, c]; 이웃[b] += [a, c]; 이웃[c] += [a, b]
이웃 = [np.unique(n) for n in 이웃]
def 스무딩(V, 람다=0.5, n=2):
    for _ in range(n): V = V + 람다 * (np.array([V[nb].mean(0) for nb in 이웃]) - V)
    return V
def 실루엣맞춤(t, V, 세기=0.7):
    """그림 평면에서: 표적 밖 점은 경계로 · 소체 테두리(투영 마스크 경계) 점은 표적 경계로 — 거리장 기울기 방향"""
    tg = 표적[t]; H, W = tg.shape; uv, Rm, s = 투영(t, V); ok = (uv[:, 0] >= 0) & (uv[:, 0] < W - 1) & (uv[:, 1] >= 0) & (uv[:, 1] < H - 1)
    if 쓰는행[t] is not None: ok &= uv[:, 1] >= 쓰는행[t]
    din = cv2.distanceTransform(tg.astype(np.uint8), cv2.DIST_L2, 5); dout = cv2.distanceTransform((~tg).astype(np.uint8), cv2.DIST_L2, 5); sd = din - dout      # 안 + · 밖 −
    gy, gx = np.gradient(sd)
    m = np.zeros((H, W), np.uint8); q = np.round(uv).astype(np.int32)
    for f in F: cv2.fillPoly(m, [q[f]], 1)
    테두리 = (cv2.dilate(m, np.ones((5, 5), np.uint8)) > 0) & ~(cv2.erode(m, np.ones((5, 5), np.uint8)) > 0)
    d = np.zeros((len(V), 2))
    for i in np.nonzero(ok)[0]:
        x, y = q[i]; v = sd[y, x]; g = np.array([gx[y, x], gy[y, x]]); n = np.linalg.norm(g)
        if n < 1e-6: continue
        if v < 0: d[i] = -v * g / n                                                                  # 밖 → 안으로 경계까지
        elif 테두리[y, x] and v > 2: d[i] = -v * g / n * 0.8                                          # 테두리인데 표적 안쪽 깊숙이 → 밖으로
    d *= 세기 / s                                                                                     # px → 단위
    D3 = d[:, 0:1] * Rm[:, 0] - d[:, 1:2] * Rm[:, 1]; 고정 = np.linalg.norm(D3, axis=1) > 1e-9        # 그림 평면 안에서만(정면 x·y · 옆 z·y)
    for _ in range(12):                                                                              # Grab: 잡은 점 둘레도 같이 딸려온다(이동장을 이웃으로 퍼뜨림 · 잡은 점은 고정)
        D3n = np.array([D3[nb].mean(0) for nb in 이웃]); D3 = np.where(고정[:, None], D3, 0.5 * D3 + 0.5 * D3n)
    return V + D3
def IoU(t, V):
    tg = 표적[t]; H, W = tg.shape; uv, _, _ = 투영(t, V); m = np.zeros((H, W), np.uint8); q = np.round(uv).astype(np.int32)
    for f in F: cv2.fillPoly(m, [q[f]], 1)
    m = m > 0; roi = np.ones_like(m)
    if 쓰는행[t] is not None: roi[:쓰는행[t]] = False
    a, b = m & roi, tg & roi; return float((a & b).sum() / max(1, (a | b).sum())), m
B점 = lambda u: np.array([u[0], -u[2], -u[1]], float)                                                # U(x 오른쪽 · y 아래 · z 앞) → 블렌더
def 잡기(V, 중심, 목표, 반지름):
    """Grab 붓: 중심에서 반지름 안 점을 (목표 − 중심) 만큼, 매끈한 감쇠로 끌어온다"""
    d = np.linalg.norm(V - 중심, axis=1) / 반지름; w = np.clip(1 - d, 0, 1) ** 2 * (3 - 2 * np.clip(1 - d, 0, 1)); return V + w[:, None] * (목표 - 중심)
def 옆에서(u, v):
    c = 카["02_옆"]; M = np.array(c["행렬"]); Rm, loc = M[:3, :3], M[:3, 3]; s_ = c["W"] / c["ortho_scale"]; cx, cy = (u - c["W"] / 2) / s_, -(v - c["H"] / 2) / s_
    base = loc + Rm[:, 0] * cx + Rm[:, 1] * cy; cz = -base[0] / Rm[0, 2] if abs(Rm[0, 2]) > 1e-6 else 0.0; b = base + Rm[:, 2] * cz; return (float(b[0]), float(-b[2]), float(-b[1]))     # → U
tg = 표적["02_옆"]; ys, xs = np.nonzero(tg); i0 = np.argmin(xs); 부리끝 = 옆에서(xs[i0], ys[i0]); i1 = np.argmax(ys); 턱끝옆 = 옆에서(xs[i1], ys[i1]); 
print("옆에서 읽은 부리 끝 U", np.round(부리끝, 1), "· 턱 끝 U", np.round(턱끝옆, 1), "(랜드마크: 코끝 (0,75,51) · 턱끝 (0,100,18))")
V = Vb.copy(); U_ = np.stack([V[:, 0], -V[:, 2], -V[:, 1]], 1)                                        # 블록인 첫 손: 제스처 · 비례 — 코끝 · 턱끝 · 콧대를 잰 자리로 잡아당긴다(랜드마크3D · 측정)
for 이름, (y0_, y1_), 목표, r in (("콧대", (30, 48), (0, 39.1, 33.2), 22), ("코끝", (60, 90), (0, 부리끝[1], 부리끝[2]), 28), ("턱끝", (60, 200), (0, 턱끝옆[1], 턱끝옆[2]), 24)):
    U_ = np.stack([V[:, 0], -V[:, 2], -V[:, 1]], 1); 후보 = np.nonzero((U_[:, 1] >= y0_) & (U_[:, 1] <= y1_) & (np.abs(U_[:, 0]) < 12))[0]
    i = 후보[np.argmax(U_[후보, 2])] if 이름 != "턱끝" else 후보[np.argmax(U_[후보, 1])]; V = 잡기(V, V[i], B점(목표), r); print("잡기 %s: (%.0f,%.0f,%.0f) → %s" % (이름, *U_[i], 목표))
print("시작 IoU", {t: round(IoU(t, V)[0], 3) for t in 시점})
for 바퀴 in range(30):
    for t in 시점: V = 실루엣맞춤(t, V, 1.0); V = 스무딩(V, 0.25, 1)
    if 바퀴 % 10 == 9: print("바퀴", 바퀴 + 1, {t: round(IoU(t, V)[0], 3) for t in 시점})
V = 스무딩(V, 0.3, 1); 점수 = {t: round(IoU(t, V)[0], 3) for t in 시점}; print("끝 IoU", 점수)
trimesh.Trimesh(V, F, process=False).export(J(B, "소체.stl")); json.dump(dict(IoU=점수, 바퀴=10, 시작="타원체 38.8×40×36 · 중심 (0,15,−34)"), open(J(B, "소체조각.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
# 그림: 실루엣만(셰이딩 끄고 본다)
from PIL import Image, ImageDraw, ImageFont
ft = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 20); 판 = []
for t in 시점:
    tg = 표적[t]; _, m = IoU(t, V); H, W = tg.shape; im = np.full((H, W, 3), 245, np.uint8); im[tg] = (120, 120, 255); im[m & tg] = (160, 160, 160); im[m & ~tg] = (120, 220, 120); im[tg & ~m] = (255, 120, 120)
    x0, y0, x1, y1 = 기록[t]["상자"]; p = Image.fromarray(im[y0:y1, x0:x1]); p = p.resize((int(p.width * 500 / p.height), 500)); ImageDraw.Draw(p).text((6, 6), "%s IoU %.2f (회 겹침 · 빨 캡처만 · 초 소체만)" % (t, 점수[t]), font=ft, fill=(0, 0, 0)); 판.append(p)
시트 = Image.new("RGB", (sum(p.width for p in 판) + 20, 500), (250, 250, 248)); x = 0
for p in 판: 시트.paste(p, (x, 0)); x += p.width + 10
시트.save(J(B, "sculpt_silhouette.jpg"), quality=85); print(J(B, "sculpt_silhouette.jpg"))
