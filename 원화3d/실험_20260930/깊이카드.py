# -*- coding: utf-8 -*-
"""깊이 카드 — 음영 있는 02 캡처에서 단안 깊이 모델이 깊이를 읽나 (2026-09-30 · 계획 claudedocs/plan_깊이카드_20260930.md · 문턱은 미리).
    python 깊이카드.py [모델]   모델 = da2b(기본 · Depth-Anything-V2-Base · 캐시) | 상수 | 타원체
    -> out/깊이카드/<모델>_정면.npy · 깊이카드_<모델>.json(ρ · 3/4 부품 IoU · 오목 부호) · 깊이카드_<모델>.png(깊이맵 · 능선 비교 · 3/4 재투영)
자 1 가운데 능선 ρ(정면 깊이 중앙 열 vs 옆 실루엣 맨 앞 · 같은 y) · 자 2 3/4 재투영 부품 IoU(대조 = 껍질 0.21) · 자 3 눈구멍 오목 부호."""
import os, sys, json
import numpy as np, cv2
from scipy.stats import spearmanr
from PIL import Image, ImageDraw, ImageFont
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(R, "오메가몬", "지표")); from 집합 import OUT, J
from 부품투영 import 찍기
D = J(OUT, "..", "자료"); B = J(OUT, "..", "블렌더"); K = J(R, "out", "깊이카드"); os.makedirs(K, exist_ok=True); S = 3
모델 = sys.argv[1] if len(sys.argv) > 1 else "da2b"
기록 = json.load(open(J(D, "자료.json"), encoding="utf-8")); 자세 = json.load(open(J(OUT, "자세3.json"), encoding="utf-8")); F = 자세["정면 yt_172"]; Rf = cv2.Rodrigues(np.asarray(F["r"], float))[0]
선택 = json.load(open(J(D, "면대응_선택.json"), encoding="utf-8"))["짝"]; L정 = np.load(J(D, "02_정면_영역.npz"))["라벨"]; L34 = np.load(J(D, "02_3-4_영역.npz"))["라벨"]
스펙 = json.load(open(J(B, "블록아웃.json"), encoding="utf-8")); 카 = {c["이름"]: c for c in 스펙["카메라"]}
읽 = lambda p, f=cv2.IMREAD_COLOR: cv2.imdecode(np.fromfile(p, np.uint8), f)
im = 읽(기록["02_정면"]["파일"]); x0, y0, x1, y1 = 기록["02_정면"]["상자"]; sil = 읽(J(D, "02_정면_실루엣.png"), 0) > 127
# ── 정면 깊이맵(캡처 해상도 · 상자 안) ──
def 깊이_da2b():
    from transformers import pipeline
    crop = Image.fromarray(im[y0:y1, x0:x1, ::-1]); s = 1008 / max(crop.size); big = crop.resize((int(crop.width * s), int(crop.height * s)), Image.BICUBIC)
    p = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Base-hf", device=-1); out = p(big)["predicted_depth"]; d = np.asarray(out, np.float32)
    d = cv2.resize(d, (x1 - x0, y1 - y0), interpolation=cv2.INTER_CUBIC); full = np.zeros(im.shape[:2], np.float32); full[y0:y1, x0:x1] = d; return full     # 값 클수록 가깝다(역깊이 계열)
def 단위xy(u, v): return (u - F["t"][0]) / F["s"], (v - F["t"][1]) / F["s"]
def 깊이_타원체():
    vs, us = np.nonzero(sil); x, y = 단위xy(us.astype(float), vs.astype(float)); full = np.zeros(im.shape[:2], np.float32); full[vs, us] = np.sqrt(np.clip(1 - (x / 40) ** 2 - ((y - 40) / 50) ** 2, 0, 1)) * 45; return full
if 모델 == "da2b": d = 깊이_da2b()
elif 모델 == "타원체": d = 깊이_타원체()
elif 모델 == "시차": d = np.load(J(K, "시차_정면.npy"))                                   # 시차깊이.py 결과(이미 z 단위 · 값 클수록 앞)
else: d = np.where(sil, 1.0, 0.0).astype(np.float32)
np.save(J(K, "%s_정면.npy" % 모델), d)
# ── 옆 실루엣 맨 앞 z(y) (자세5 옆 카메라 · x = 0 평면) ──
c = 카["02_옆"]; M = np.array(c["행렬"]); Rm, loc = M[:3, :3], M[:3, 3]; s_ = c["W"] / c["ortho_scale"]
def 옆에서(u, v):
    cx, cy = (u - c["W"] / 2) / s_, -(v - c["H"] / 2) / s_; base = loc + Rm[:, 0] * cx + Rm[:, 1] * cy; cz = -base[0] / Rm[0, 2]; b = base + Rm[:, 2] * cz; return (float(b[0]), float(-b[2]), float(-b[1]))
sil옆 = 읽(J(D, "02_옆_실루엣.png"), 0) > 127; L옆 = np.load(J(D, "02_옆_영역.npz"))["라벨"]; 턱옆 = np.nonzero(L옆 == 15)[0].max() // S
능선 = []                                                                                            # (y, z앞) — 행마다 맨 왼쪽(앞) 화소
for v in range(20, 턱옆 + 1):
    xs = np.nonzero(sil옆[v])[0]
    if len(xs): _, yy, zz = 옆에서(xs.min(), v); 능선.append((yy, zz))
능선 = np.array(sorted(능선));
# ── 자 1: 정면 중앙 열 깊이 vs 능선 ──
cx_px = F["t"][0] + 0 * F["s"]; 열 = []
for yy, zz in 능선:
    v = int(round(F["t"][1] + yy * F["s"])); u = int(round(cx_px))
    if 0 <= v < d.shape[0] and sil[v, u]: 열.append((yy, zz, float(d[v, max(u - 2, 0):u + 3].mean())))
열 = np.array(열); ρ = float(spearmanr(열[:, 1], 열[:, 2]).correlation) if len(열) > 5 else float("nan")
a, b = np.polyfit(열[:, 2], 열[:, 1], 1) if len(열) > 5 else (0, 0)                                  # 눈금: 능선으로 상대 깊이 → z 단위
# ── 자 2: 정면 화소 → 3D → 3/4 로 찍어 부품 IoU ──
vs, us = np.nonzero(sil & (np.arange(im.shape[0])[:, None] >= y0)); x, y = 단위xy(us.astype(float), vs.astype(float)); z = a * d[vs, us] + b
U = (np.stack([x, y, -z], 1) @ Rf) * (1, 1, -1); uv, cz = 찍기(U, 자세["3/4 M04"]); H34, W34 = L34.shape[0] // S, L34.shape[1] // S; L34s = cv2.resize(L34, (W34, H34), interpolation=cv2.INTER_NEAREST)
p = np.round(uv).astype(int); ok = (p[:, 0] >= 0) & (p[:, 0] < W34) & (p[:, 1] >= 0) & (p[:, 1] < H34)
# 가림: 같은 픽셀엔 카메라에 가까운 것만
lab정 = cv2.resize(L정, (im.shape[1], im.shape[0]), interpolation=cv2.INTER_NEAREST)[vs, us]; 순 = np.argsort(-cz); 보임 = np.zeros((H34, W34), np.int32) - 1
for i in 순[ok[순]]: 보임[p[i, 1], p[i, 0]] = i
결과 = {}
for n, 짝 in 선택.items():
    if not 짝.get("정면") or not 짝.get("3-4"): continue
    m = np.zeros((H34, W34), np.uint8); idx = 보임[보임 >= 0]; sel = idx[np.isin(lab정[idx], 짝["정면"])]; m[p[sel, 1], p[sel, 0]] = 1; m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)) > 0
    t = np.isin(L34s, 짝["3-4"]); 결과[n] = round(float((m & t).sum() / max(1, (m | t).sum())), 3)
껍질 = {"눈구멍L": 0.19, "볼L": 0.20, "부리1": 0.43, "부리2": 0.07, "부리3": 0.40, "투구이마": 0.23}
# ── 자 3: 눈구멍 오목 부호 (z 작을수록 뒤) ──
눈 = np.isin(L정, [13, 10]); 눈s = cv2.resize(눈.astype(np.uint8), (im.shape[1], im.shape[0]), interpolation=cv2.INTER_NEAREST) > 0; 둘레 = (cv2.dilate(눈s.astype(np.uint8), np.ones((15, 15), np.uint8)) > 0) & ~눈s & sil
z눈, z둘 = float(np.median(a * d[눈s] + b)), float(np.median(a * d[둘레] + b)); 오목 = z눈 < z둘
중앙 = float(np.median([결과[k] for k in 결과])) if 결과 else float("nan")
판정 = "쓸 수 있다" if (ρ >= 0.7 and 중앙 > 0.21 and 오목) else ("일부" if sum([ρ >= 0.7, 중앙 > 0.21, 오목]) == 2 else "못 쓴다")
out = dict(모델=모델, 능선ρ=round(ρ, 3), 눈금=[round(float(a), 4), round(float(b), 2)], 부품IoU=결과, 부품IoU중앙=round(중앙, 3), 껍질중앙=0.21, 눈구멍z=round(z눈, 1), 둘레z=round(z둘, 1), 오목=bool(오목), 판정=판정)
json.dump(out, open(J(K, "깊이카드_%s.json" % 모델), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(out, ensure_ascii=False))
# ── 그림 ──
ft = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 20); dn = d[y0:y1, x0:x1]; dn = (255 * (dn - dn[sil[y0:y1, x0:x1]].min()) / max(1e-6, np.ptp(dn[sil[y0:y1, x0:x1]]))).clip(0, 255).astype(np.uint8); dn[~sil[y0:y1, x0:x1]] = 0
A = Image.fromarray(cv2.applyColorMap(dn, cv2.COLORMAP_TURBO)[:, :, ::-1]); A = A.resize((int(A.width * 500 / A.height), 500)); ImageDraw.Draw(A).text((6, 6), "%s 정면 깊이(밝을수록 가까움)" % 모델, font=ft, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
Bp = Image.new("RGB", (400, 500), (250, 250, 248)); dr = ImageDraw.Draw(Bp)
for yy, zz, dd in 열: dr.ellipse((200 + zz * 2 - 3, yy * 4.5 - 3, 200 + zz * 2 + 3, yy * 4.5 + 3), fill=(220, 40, 40)); zp = a * dd + b; dr.ellipse((200 + zp * 2 - 3, yy * 4.5 - 3, 200 + zp * 2 + 3, yy * 4.5 + 3), fill=(40, 120, 220))
dr.text((6, 6), "능선 z(y): 빨 옆 캡처 · 파 예측  ρ %.2f" % ρ, font=ft, fill=(0, 0, 0))
im34 = 읽(기록["02_3-4"]["파일"]); ov = cv2.resize(im34, (W34, H34)).copy(); rng = np.random.RandomState(5)
for n, 짝 in 선택.items():
    if not 짝.get("정면") or not 짝.get("3-4"): continue
    idx = 보임[보임 >= 0]; sel = idx[np.isin(lab정[idx], 짝["정면"])]; col = tuple(int(c_) for c_ in rng.randint(60, 230, 3)); ov[p[sel, 1], p[sel, 0]] = col
C = Image.fromarray(cv2.addWeighted(cv2.resize(im34, (W34, H34)), 0.4, ov, 0.6, 0)[:, :, ::-1]); xb0, yb0, xb1, yb1 = [v // S for v in (830 * S, 0, 1440 * S, 700 * S)]; C = C.crop((830, 0, 1440, 700)); C = C.resize((int(C.width * 500 / C.height), 500)); ImageDraw.Draw(C).text((6, 6), "3/4 재투영 · 부품 IoU 중앙 %.2f (껍질 0.21)" % 중앙, font=ft, fill=(0, 0, 0), stroke_width=2, stroke_fill=(255, 255, 255))
시트 = Image.new("RGB", (A.width + Bp.width + C.width + 20, 500), (250, 250, 248)); 시트.paste(A, (0, 0)); 시트.paste(Bp, (A.width + 10, 0)); 시트.paste(C, (A.width + Bp.width + 20, 0)); 시트.save(J(K, "깊이카드_%s.png" % 모델)); print(J(K, "깊이카드_%s.png" % 모델))
