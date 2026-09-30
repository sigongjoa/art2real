# -*- coding: utf-8 -*-
"""머리 디테일 — 머리손 2판 위에 정면 영역(정면_영역번호.png)대로 판 부품을 더한다 (2026-09-30 「시작으로 나쁘지 않아 · 디테일하게」).
    python 머리디테일.py -> out/오메가몬2/블렌더/머리손/<부품>.npz (덮어쓰기 · 추가) · 눈구멍 칼(<칼>.npz) · 머리디테일.json
판 부품 = 정면 영역 다각형(측정) × z 함수(손: 투구 앞면 + 돌출 · 가운데 용골 기울기). 좌우 중 잘 그려진 쪽을 거울로.
영역: 3 · 4 돔 · 5 · 8 이마판 · 6 · 7 관자판 · 9 · 12 눈썹 차양 · 10+15 · 13+16 눈 · 11 · 14 볼 날개 · 17 · 18 윗부리 · 19+21 · 20+26 송곳니 · 24 · 25 아랫부리 · 30 · 31 턱."""
import os, sys, json
import numpy as np, cv2
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(R, "오메가몬", "지표")); from 집합 import OUT, J
D = J(OUT, "..", "자료"); B = J(OUT, "..", "블렌더"); P = J(B, "머리손"); S = 3
자세 = json.load(open(J(OUT, "자세3.json"), encoding="utf-8")); F = 자세["정면 yt_172"]; 표 = json.load(open(J(B, "머리손.json"), encoding="utf-8"))["값"]["투구"]["표"]
L = np.load(J(D, "02_정면_영역.npz"))["라벨"]; sil = cv2.imdecode(np.fromfile(J(D, "02_정면_실루엣.png"), np.uint8), 0) > 127; Ls = cv2.resize(L, (sil.shape[1], sil.shape[0]), interpolation=cv2.INTER_NEAREST)
B점 = lambda x, y, z: (float(x), float(-z), float(-y))
def 앞z(y): return float(np.interp(y, [r[0] for r in 표], [r[3] for r in 표]))                          # 투구 앞면(가운데)
def 반폭(y): return float(np.interp(y, [r[0] for r in 표], [r[2] for r in 표]))
def 투구겉z(x, y):                                                                                    # 투구 초타원 켜의 겉(각 0.8) z — 판을 겉에 붙이려고
    hw = max(1.0, 반폭(y)); zf = 앞z(y); zb = float(np.interp(y, [r[0] for r in 표], [r[4] for r in 표])); cz, rz = (zf + zb) / 2, (zf - zb) / 2
    c = min(1.0, abs(x) / hw); s = (1 - c ** (2 / 0.8)) ** (0.8 / 2) if c < 1 else 0.0; return cz + rz * s
def 다각(ids, eps=2.5, 거울=False, 껍질=False):
    m = np.isin(Ls, ids).astype(np.uint8); m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)); cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnt = max(cs, key=cv2.contourArea); cnt = cv2.convexHull(cnt) if 껍질 else cnt; p = cv2.approxPolyDP(cnt, eps, True)[:, 0, :].astype(float); xy = np.column_stack([(p[:, 0] - F["t"][0]) / F["s"], (p[:, 1] - F["t"][1]) / F["s"]])
    if 거울: xy[:, 0] = -xy[:, 0]; xy = xy[::-1]
    return xy
def 판(xy, zf, 두께):
    """정면 다각형 xy · 점마다 앞 z(zf 함수) · 뒤로 두께 — 볼록이 아니어도 되게 부채꼴 대신 귀 자르기(earcut)"""
    from trimesh.creation import triangulate_polygon
    from shapely.geometry import Polygon
    v2, f2 = triangulate_polygon(Polygon(xy).buffer(0)); n = len(v2)
    top = [B점(x, y, zf(x, y)) for x, y in v2]; bot = [B점(x, y, zf(x, y) - 두께) for x, y in v2]; V = top + bot
    Fs = [tuple(f) for f in f2] + [(a + n, c + n, b + n) for a, b, c in f2]
    ring = Polygon(v2).exterior.coords[:-1]; idx = [int(np.argmin(np.linalg.norm(v2 - np.array(q), axis=1))) for q in ring]
    for i in range(len(idx)): a, b = idx[i], idx[(i + 1) % len(idx)]; Fs += [(a, b, b + n), (a, b + n, a + n)]
    return np.array(V, np.float32), np.array(Fs, np.int32)
def 양쪽(이름, xy, zf, 두께, 부품):
    부품[이름 + "L"] = 판(xy, zf, 두께); xm = xy.copy(); xm[:, 0] = -xm[:, 0]; 부품[이름 + "R"] = 판(xm[::-1], zf, 두께)
부품 = {}; 기록 = {}
# 이마판(5 · 8): 뿔 밑에서 눈썹까지 V — 가운데 용골 +3 · 옆으로 갈수록 투구 겉
# 이마(5+8+9+12 한 판): 뿔 밑에서 눈 사이까지 V — 가운데 용골 · 1판의 조각을 하나로
xy = 다각([5, 9], 3.0, 껍질=True); xy = xy[xy[:, 0] <= 0.5] if (xy[:, 0] <= 0.5).sum() >= 3 else xy; xy[:, 0] = np.minimum(xy[:, 0], 0.0)      # 왼쪽 반(가운데까지) 껍질
양쪽("이마", xy, lambda x, y: 앞z(y) + 4.0 - 0.3 * abs(x), 3.0, 부품); 기록["이마"] = "영역 5+8+9+12 · 앞 +4 − 0.3|x|(손)"
# 눈썹 차양(9 · 12): 눈 위로 튀어나온 V 판 — 앞 +6(눈을 덮는 그늘)

# 관자판(6 → 거울): 투구 겉 +1.5
부리 = json.load(open(J(B, "부리점.json"), encoding="utf-8"))["줄"]; 능선 = lambda y: float(np.interp(y, [p["y"] for p in 부리], [p["z앞"] for p in 부리]))
주둥이 = np.isin(Ls, [17, 18, 24, 25, 30, 31]); 줄 = []
for y in np.arange(50, 101, 3.0):
    v = int(round(F["t"][1] + y * F["s"])); xs = np.nonzero(주둥이[v])[0]
    if len(xs) < 3: continue
    xl, xr = (xs.min() - F["t"][0]) / F["s"], (xs.max() - F["t"][0]) / F["s"]; 줄.append((y, xl, xr, 능선(y)))
Vs = []
for y, xl, xr, zr in 줄:
    xc = 0.0 if y < 75 else (xl + xr) / 2 * 0.5; hw = (xr - xl) / 2; Vs += [B점(xc - hw, y, zr - 0.75 * hw), B점(xc, y, zr), B점(xc + hw, y, zr - 0.75 * hw), B점(xc, y, zr - 0.75 * hw - 4)]
Fs = []
for i in range(len(줄) - 1):
    for j in range(4): a, b = i * 4 + j, i * 4 + (j + 1) % 4; Fs += [(a, b, b + 4), (a, b + 4, a + 4)]
n = len(줄) * 4; Fs += [(0, 2, 1), (0, 3, 2), (n - 4, n - 3, n - 2), (n - 4, n - 2, n - 1)]
부품["주둥이"] = (np.array(Vs, np.float32), np.array(Fs, np.int32)); 기록["주둥이"] = "줄마다 폭(영역 17 18 24 25 30 31 · 측정) · 능선(시차 · 측정) · 옆 = 능선 − 0.75 반폭(손)"
# 돔 옆판(3 → 거울): 안테나 뿌리 둘레 판 — 겉 +1
# 돔판 · 관자판은 떠서 조각이 됐다(1판) — 판이 아니라 패널 선이라 뒤로 미룸
# 볼 날개(14 → 거울): 얼굴 옆에서 바깥으로 뒤로 누움 — 머리손 볼날개 대체
xy14 = 다각([14], 3.0); x안 = xy14[:, 0].min()
부품["볼날개R"] = 판(xy14, lambda x, y: 앞z(y) - 6.0 - 0.45 * abs(x - x안), 3.0); xm = xy14.copy(); xm[:, 0] = -xm[:, 0]; 부품["볼날개L"] = 판(xm[::-1], lambda x, y: 앞z(y) - 6.0 - 0.45 * abs(-x - x안), 3.0); 기록["볼날개"] = "영역 14(오른 · 잘 그려진 쪽) 거울 · 얼굴 −6 에서 바깥으로 뒤로 0.9(손)"
# 송곳니(19+21 → 거울): 부리 옆 아래로 늘어진 판 — 얼굴 −1
양쪽("송곳니", 다각([19, 21]), lambda x, y: 능선(min(y, 88)) - 0.75 * abs(x) - 1.0, 2.5, 부품); 기록["송곳니"] = "영역 19+21(왼) 거울 · 얼굴 −1(손)"
# 턱(30+31): 부리 아래 쐐기 — 가운데 앞
# 눈: 소켓(10 → 거울) 바닥 판(어두움) · 칼(투구를 파낼 기둥) · 홍채(15 → 거울) 파란 판
xy10 = 다각([10, 15], 2.0)
양쪽("눈바닥", xy10, lambda x, y: 앞z(y) - 9.0, 1.5, 부품)
양쪽("눈칼", xy10, lambda x, y: 앞z(y) + 20.0, 28.5, 부품)                                              # 앞 +20 에서 앞 −8.5 까지
양쪽("홍채", 다각([15], 1.5), lambda x, y: 앞z(y) - 7.0, 1.0, 부품); 기록["눈"] = "영역 10+15(왼) 거울 · 소켓 깊이 9 · 홍채 앞 −7(손 · 오목)"
뿔 = (Ls == 1); 줄 = []
for y in np.arange(-56, 36, 4.0):
    v = int(round(F["t"][1] + y * F["s"])); xs = np.nonzero(뿔[v])[0]
    if len(xs) >= 2: 줄.append((y, (xs.min() - F["t"][0]) / F["s"], (xs.max() - F["t"][0]) / F["s"]))
z밑 = 앞z(30) + 2.0; Vs = []
for y, xl, xr in 줄:
    t = (y - 줄[-1][0]) / (줄[0][0] - 줄[-1][0]); zc = z밑 + 14.0 * t; hw = max(0.6, (xr - xl) / 2); xc = (xl + xr) / 2; d_ = max(0.6, hw * 0.8)
    Vs += [B점(xc - hw, y, zc), B점(xc, y, zc + d_), B점(xc + hw, y, zc), B점(xc, y, zc - d_)]
Fs = []
for i in range(len(줄) - 1):
    for j in range(4): a, b = i * 4 + j, i * 4 + (j + 1) % 4; Fs += [(a, b, b + 4), (a, b + 4, a + 4)]
n = len(줄) * 4; Fs += [(0, 2, 1), (0, 3, 2), (n - 4, n - 3, n - 2), (n - 4, n - 2, n - 1)]
부품["뿔"] = (np.array(Vs, np.float32), np.array(Fs, np.int32)); 기록["뿔"] = "줄마다 폭(영역 1 · 측정) · 마름모 칼날 · 밑 z 이마 앞 · 끝 +14 앞으로(손)"
for n, (V, Fs) in 부품.items(): np.savez(J(P, n + ".npz"), V=V, F=Fs)
json.dump(dict(부품=list(부품), 값=기록, 승인="Claude(사용자 미확인)"), open(J(B, "머리디테일.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print({n: len(V) for n, (V, _) in 부품.items()})
