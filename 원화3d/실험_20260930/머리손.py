# -*- coding: utf-8 -*-
"""머리 손 — 부품을 만들어 합친다 (2026-09-30 「부품을 만들어서 합쳐야지」). 부리손과 같은 손: 줄마다 점 몇 개 · 값은 측정(정면 폭 · 옆 앞뒤 · 시차) + 손 · 각진 낱말.
    python 머리손.py -> out/오메가몬2/블렌더/머리손/<부품>.npz · 머리손.json(부품 · 값 · 출처)
낱말: 투구(단면 쌓기 · 초타원) · 부리(부리손 그대로) · 눈구멍 판 L/R(정면 면 다각형 · 얼굴면보다 뒤) · 뿔(원뿔) · 안테나 L/R(원뿔 · 뒤로 쓸림) · 볼날개 L/R(판).
틀: 모델 틀(정면 카메라 · 3/4 · 옆은 09-30 앞뒤 눈금 뒤). 블렌더 좌표 = (x, −z, −y)."""
import os, sys, json
import numpy as np, cv2
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(R, "오메가몬", "지표")); from 집합 import OUT, J
D = J(OUT, "..", "자료"); B = J(OUT, "..", "블렌더"); K = J(R, "out", "깊이카드"); P = J(B, "머리손"); os.makedirs(P, exist_ok=True); S = 3
기록 = json.load(open(J(D, "자료.json"), encoding="utf-8")); 자세 = json.load(open(J(OUT, "자세3.json"), encoding="utf-8")); F = 자세["정면 yt_172"]
스펙 = json.load(open(J(B, "블록아웃.json"), encoding="utf-8")); 카 = {c["이름"]: c for c in 스펙["카메라"]}
읽 = lambda p, f=cv2.IMREAD_COLOR: cv2.imdecode(np.fromfile(p, np.uint8), f)
c = 카["02_옆"]; M = np.array(c["행렬"]); Rm, loc = M[:3, :3], M[:3, 3]; s_ = c["W"] / c["ortho_scale"]
def 옆에서(u, v):
    cx, cy = (u - c["W"] / 2) / s_, -(v - c["H"] / 2) / s_; base = loc + Rm[:, 0] * cx + Rm[:, 1] * cy; cz = -base[0] / Rm[0, 2]; b = base + Rm[:, 2] * cz; return float(-b[2]), float(-b[1])   # (y, z)
def 옆행(y): Ub = np.array([0.0, -20.0, -y]); C = Rm.T @ (Ub - loc); return int(round(-C[1] * s_ + c["H"] / 2))
sil옆 = 읽(J(D, "02_옆_실루엣.png"), 0) > 127; sil정 = 읽(J(D, "02_정면_실루엣.png"), 0) > 127; L정 = np.load(J(D, "02_정면_영역.npz"))["라벨"]; L정s = cv2.resize(L정, (sil정.shape[1], sil정.shape[0]), interpolation=cv2.INTER_NEAREST)
머리정 = cv2.morphologyEx(sil정.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (19, 19))) > 0      # 뿔 · 안테나 뗀 머리 덩어리
def 정행(y): return int(round(F["t"][1] + y * F["s"]))
def 정면폭(y, m=머리정, 최대=40.0):
    xs = np.nonzero(m[정행(y)])[0]; xs = xs[np.abs((xs - F["t"][0]) / F["s"]) < 최대]
    return (float((xs.min() - F["t"][0]) / F["s"]), float((xs.max() - F["t"][0]) / F["s"])) if len(xs) else None
def 옆앞뒤(y):
    v = 옆행(y); xs = np.nonzero(sil옆[v])[0] if 0 <= v < sil옆.shape[0] else []
    return (옆에서(xs.min(), v)[1], 옆에서(xs.max(), v)[1]) if len(xs) else None
B점 = lambda x, y, z: (float(x), float(-z), float(-y))
def 켜(y, xl, xr, zf, zb, 각=0.8, n=24):
    cx, rx, cz, rz = (xl + xr) / 2, max(0.5, (xr - xl) / 2), (zf + zb) / 2, max(0.5, (zf - zb) / 2)
    return [B점(cx + rx * np.sign(np.cos(t)) * abs(np.cos(t)) ** 각, y, cz + rz * np.sign(np.sin(t)) * abs(np.sin(t)) ** 각) for t in np.linspace(0, 2 * np.pi, n, endpoint=False)]
def 쌓기(켜들):
    V, Fs = [], []; n = len(켜들[0])
    for k in 켜들: V += k
    for i in range(len(켜들) - 1):
        for j in range(n): a, b_ = i * n + j, i * n + (j + 1) % n; Fs += [(a, b_, b_ + n), (a, b_ + n, a + n)]
    for i, k in ((0, 0), (len(켜들) - 1, 1)):                                                        # 뚜껑
        cidx = len(V); V.append(tuple(np.mean(np.array(켜들[i]), 0)))
        for j in range(n): a, b_ = i * n + j, i * n + (j + 1) % n; Fs.append((a, cidx, b_) if k == 0 else (a, b_, cidx))
    return np.array(V, np.float32), np.array(Fs, np.int32)
def 원뿔(밑, 끝, r, n=12):
    a, b_ = np.array(밑, float), np.array(끝, float); d = b_ - a; d /= np.linalg.norm(d); u = np.cross(d, [0, 0, 1.0]); u = u / np.linalg.norm(u) if np.linalg.norm(u) > 1e-6 else np.array([1.0, 0, 0]); w = np.cross(d, u)
    V = [tuple(a + r * (np.cos(t) * u + np.sin(t) * w)) for t in np.linspace(0, 2 * np.pi, n, endpoint=False)] + [tuple(b_), tuple(a)]
    Fs = [(i, (i + 1) % n, n) for i in range(n)] + [((i + 1) % n, i, n + 1) for i in range(n)]; return np.array(V, np.float32), np.array(Fs, np.int32)
def 판(다각B, 두께, 법선=(0, 1, 0)):
    n = len(다각B); nv = np.array(법선, float) * 두께; V = [tuple(p) for p in 다각B] + [tuple(np.array(p) + nv) for p in 다각B]; Fs = []
    for i in range(1, n - 1): Fs += [(0, i, i + 1), (n, n + i + 1, n + i)]
    for i in range(n): a, b_ = i, (i + 1) % n; Fs += [(a, a + n, b_ + n), (a, b_ + n, b_)]
    return np.array(V, np.float32), np.array(Fs, np.int32)
부품 = {}; 기록값 = {}
# ── 부리(부리손 그대로) ──
z = np.load(J(B, "부리손.npz")); Vb_ = z["V"].copy(); Vb_[:6, 1] += 6.0; 부품["부리"] = (Vb_, z["F"]); 부리점 = json.load(open(J(B, "부리점.json"), encoding="utf-8"))["줄"]; 부리뒤 = {p["y"]: p["z뒤"] for p in 부리점}   # 위 두 줄(점 6)을 투구 속으로 6; 부리점 = json.load(open(J(B, "부리점.json"), encoding="utf-8"))["줄"]; 부리뒤 = {p["y"]: p["z뒤"] for p in 부리점}
# ── 투구(소체 겸): 줄마다 정면 폭(측정) · 옆 앞(측정 · 부리 줄은 부리 뒤 − 2) · 옆 뒤(측정) ──
켜들 = []; 표 = []
for y in [2, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 95]:
    w = 정면폭(y); ab = 옆앞뒤(y)
    if w is None or ab is None: continue
    xl, xr = w; zf, zb = ab
    if y >= 56: zf = np.interp(y, list(부리뒤), list(부리뒤.values())) - 2.0                                # 부리 아래 얼굴면
    hw = min(30.0, max(abs(xl), abs(xr))) if y >= 56 else max(abs(xl), abs(xr)); xl, xr = -hw, hw                   # 좌우 대칭(손) · 턱 쪽 ±30
    if False: xl, xr = max(xl, -30.0), min(xr, 30.0)                                                 # 턱 쪽은 볼 날개를 뺀 얼굴 폭(손)
    zb = max(zf - (xr - xl) * 1.0, -62.0)                                                              # 옆 실루엣 뒤끝은 안테나 · 깃이 섞여 못 쓴다 → 머리 깊이 = 폭 × 1.0(art-to-3d-maps 측정값 · 손)
    표.append((y, round(xl, 1), round(xr, 1), round(zf, 1), round(zb, 1))); 켜들.append(켜(y, xl, xr, zf, zb, 각=0.8 if y < 56 else 0.6))
부품["투구"] = 쌓기(켜들); 기록값["투구"] = dict(표=표, 출처="정면 머리 실루엣 폭(측정) · 옆 실루엣 앞(측정 · 눈금 뒤) · 뒤 = 앞 − 폭(손 · 깊이/폭 ≈ 1.0) · 부리 줄 앞 = 부리 뒤 − 2(손) · 턱 폭 ±30(손)")
# ── 눈구멍 판 L/R: 정면 면 다각형 · 얼굴면보다 6 뒤 · 두께 2 ──
def 얼굴z(y): return float(np.interp(y, [r[0] for r in 표], [r[3] for r in 표]))
for 이름, ids in (("눈L", [13]), ("눈R", [10, 15])):
    m = np.isin(L정s, ids).astype(np.uint8); cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); cnt = max(cs, key=cv2.contourArea); poly = cv2.approxPolyDP(cnt, 3.0, True)[:, 0, :]
    pts = [B점((u - F["t"][0]) / F["s"], (v - F["t"][1]) / F["s"], 얼굴z((v - F["t"][1]) / F["s"]) - 6.0) for u, v in poly]; 부품[이름] = 판(pts, 2.0, (0, 1, 0)); 기록값[이름] = dict(출처="정면 면 %s 다각형(측정) · 깊이 얼굴면 − 6(손 · 오목)" % ids)
# ── 뿔: 정면 면 1 (밑 폭 · 위아래) · 밑 z = 이마 앞(측정) · 끝 z 손 ──
m1 = (L정s == 1); ys1, xs1 = np.nonzero(m1); y밑, y끝 = (ys1.max() - F["t"][1]) / F["s"], (ys1.min() - F["t"][1]) / F["s"]; row = xs1[ys1 == ys1.max()]; r뿔 = (row.max() - row.min()) / 2 / F["s"]; x뿔 = ((row.max() + row.min()) / 2 - F["t"][0]) / F["s"]
zf이마 = 옆앞뒤(min(40, y밑 + 8))[0] if 옆앞뒤(min(40, y밑 + 8)) else 20.0
부품["뿔"] = 원뿔(B점(x뿔, y밑, zf이마 - 4), B점(x뿔, y끝, zf이마 + 6), max(3.0, r뿔)); 기록값["뿔"] = dict(밑=[round(x뿔, 1), round(y밑, 1)], 끝y=round(y끝, 1), 반지름=round(float(r뿔), 1), 출처="정면 면 1(측정) · z 이마 앞(측정) · 끝 앞으로 +10(손)")
# ── 안테나 L/R: 정면 실루엣 맨 바깥 점(측정) → 뿌리(투구 옆 · 손) · 뒤로 쓸림(손 · 키트) ──
ys0, xs0 = np.nonzero(sil정[:정행(15)]); X0 = (xs0 - F["t"][0]) / F["s"]; Y0 = (ys0 - F["t"][1]) / F["s"]; iR, iL = np.argmax(X0), np.argmin(X0); xr_, yr_, xl_, yl_ = X0[iR], Y0[iR], X0[iL], Y0[iL]
if xr_ < 50: xr_, yr_, xl_, yl_ = 60.0, -25.0, -60.0, -25.0                                              # 정면 실루엣이 가는 안테나를 잘랐다 → 끝은 손(캡처에서 읽음 ±60 · −25)
for 이름, (xt, yt), sgn in (("안테나L", (xr_, yr_), 1), ("안테나R", (xl_, yl_), -1)):
    w = 정면폭(20) or (-35, 35); 뿌리 = (sgn * abs(w[1] if sgn > 0 else w[0]) * 0.85, 22.0, -12.0); 부품[이름] = 원뿔(B점(*뿌리), B점(xt, yt, -45.0), 4.5); 기록값[이름] = dict(끝=[round(xt, 1), round(yt, 1)], 출처="끝 xy 정면 실루엣(측정) · 뿌리 · 뒤 쓸림 −40(손 · 키트 옆 사진)")
# ── 볼 날개 L/R: 정면 면 14 · 11 다각형(측정) · z 는 머리 옆(손: 앞 −5 · 뒤로 기울어 −25) ──
for 이름, ids in (("볼날개L", [14]), ("볼날개R", [11])):
    m = np.isin(L정s, ids).astype(np.uint8); cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); cnt = max(cs, key=cv2.contourArea); poly = cv2.approxPolyDP(cnt, 4.0, True)[:, 0, :]
    xs_ = (poly[:, 0] - F["t"][0]) / F["s"]; x안 = xs_.min() if 이름.endswith("L") else xs_.max()
    pts = [B점((u - F["t"][0]) / F["s"], (v - F["t"][1]) / F["s"], 얼굴z((v - F["t"][1]) / F["s"]) - 4.0 - 1.0 * abs((u - F["t"][0]) / F["s"] - x안)) for u, v in poly]; 부품[이름] = 판(pts, 3.0, (0, 1, 0)); 기록값[이름] = dict(출처="정면 면 %s(측정) · z 안쪽 −5 → 바깥 뒤로(손)" % ids)
for n_, (V, Fs) in 부품.items(): np.savez(J(P, n_ + ".npz"), V=V, F=Fs)
json.dump(dict(부품=list(부품), 값=기록값, 승인="Claude(사용자 미확인)"), open(J(B, "머리손.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("부품", {n_: (len(V), len(Fs)) for n_, (V, Fs) in 부품.items()}); print("투구 표", 표)
