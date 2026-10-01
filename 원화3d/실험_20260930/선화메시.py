# -*- coding: utf-8 -*-
"""선화 = 와이어프레임 (2026-10-01 「과격하고 획기적인 방법 · 패널라인을 바탕으로」).
02 정면 영역 경계를 꼭짓점·면(영역) 그래프로 뽑고, x·y 는 그림 그대로, **z 만 최소제곱**으로 푼다.
    python 선화메시.py -> out/오메가몬2/블렌더/머리손/선화.npz · 선화.json
조건(전부 선형): ① 영역은 평면(z = a x + b y + c · 면마다 a b c) ② 좌우 대칭 ③ 중심선 z = 머리손 표 앞z(y) ④ 시차 깊이(표로 눈금 맞춤 · 상관 낮으면 뺌) ⑤ 투구 겉 z 약한 사전
손으로 z 를 찍는 칸이 없다 — 여섯 판이 실패한 자리를 비운다."""
import os, sys, json
import numpy as np, cv2
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(R, "오메가몬", "지표")); from 집합 import OUT, J
D = J(OUT, "..", "자료"); B = J(OUT, "..", "블렌더"); P = J(B, "머리손")
F = json.load(open(J(OUT, "자세3.json"), encoding="utf-8"))["정면 yt_172"]; s, t = F["s"], F["t"]
표 = json.load(open(J(B, "머리손.json"), encoding="utf-8"))["값"]["투구"]["표"]
앞z = lambda y: float(np.interp(y, [r[0] for r in 표], [r[3] for r in 표])); 뒤z = lambda y: float(np.interp(y, [r[0] for r in 표], [r[4] for r in 표])); 반폭 = lambda y: float(np.interp(y, [r[0] for r in 표], [r[2] for r in 표]))
def 겉z(x, y):
    hw = max(1.0, 반폭(y)); zf, zb = 앞z(y), 뒤z(y); cz, rz = (zf + zb) / 2, (zf - zb) / 2; c = min(1.0, abs(x) / hw); return cz + rz * ((1 - c ** 2.5) ** 0.4 if c < 1 else 0.0)
L = np.load(J(D, "02_정면_영역.npz"))["라벨"]; sil = cv2.imdecode(np.fromfile(J(D, "02_정면_실루엣.png"), np.uint8), 0) > 127
Ls = cv2.resize(L, (sil.shape[1], sil.shape[0]), interpolation=cv2.INTER_NEAREST)
머리 = [i for i in range(1, 32) if i not in (22, 23, 27, 28, 29)]                                   # 깃 · 어깨 영역은 뺀다
눈구멍 = {10, 15, 13, 16}
# ① 영역 다각형(그림 좌표 → 모델 x y)
다각 = {}
for i in 머리:
    m = (Ls == i).astype(np.uint8); m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)); cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cs: continue
    c = max(cs, key=cv2.contourArea)
    if cv2.contourArea(c) < 150: continue
    p = cv2.approxPolyDP(c, 2.5, True)[:, 0, :].astype(float); 다각[i] = np.column_stack([(p[:, 0] - t[0]) / s, (p[:, 1] - t[1]) / s])
# ② 꼭짓점 공유: 반지름 R 안의 점은 한 꼭짓점
RAD = 3.0; V = []; 면 = {}
def vid(q):
    for k, v in enumerate(V):
        if np.hypot(*(v - q)) < RAD: V[k] = (v + q) / 2; return k
    V.append(q.copy()); return len(V) - 1
for i, xy in 다각.items():
    ids = []
    for q in xy:
        k = vid(q)
        if not ids or ids[-1] != k: ids.append(k)
    if len(ids) > 2 and ids[0] == ids[-1]: ids.pop()
    if len(ids) >= 3: 면[i] = ids
V = np.array(V); n = len(V); fids = list(면)
# ③ 시차 깊이 눈금: 중심선에서 표 앞z 와 맞춤
시차 = np.load(J(OUT, "..", "..", "깊이카드", "시차_정면.npy"))
ys = np.arange(2, 95, 2.0); raw = np.array([시차[int(t[1] + y * s), int(t[0])] for y in ys]); ref = np.array([앞z(y) for y in ys]); ok = np.isfinite(raw)
r = np.corrcoef(raw[ok], ref[ok])[0, 1]; a, b = np.polyfit(raw[ok], ref[ok], 1) if abs(r) > 0.8 else (0.0, 0.0)
def 시차z(x, y):
    px, py = int(t[0] + x * s), int(t[1] + y * s)
    if not (0 <= py < 시차.shape[0] and 0 <= px < 시차.shape[1]) or not sil[py, px]: return None
    v = 시차[py, px]; return None if not np.isfinite(v) else a * v + b
# ④ 최소제곱: 미지수 = z_v (n) + 면마다 (a b c) (3 F)
rows, rhs, w = [], [], []
def eq(coef, val, wt):
    rows.append(coef); rhs.append(val); w.append(wt)
N = n + 3 * len(fids)
for fi, i in enumerate(fids):
    for k in 면[i]:
        c = np.zeros(N); c[k] = 1; c[n + 3 * fi:n + 3 * fi + 3] = -np.array([V[k, 0], V[k, 1], 1.0]); eq(c, 0.0, 3.0)      # 평면
거울 = {}
for k in range(n):
    q = np.array([-V[k, 0], V[k, 1]]); d = np.hypot(*(V - q).T); m = int(np.argmin(d))
    if d[m] < 4.0 and m != k: 거울[k] = m; c = np.zeros(N); c[k] = 1; c[m] = -1; eq(c, 0.0, 2.0)                             # 대칭
n중심 = n시차 = 0
for k in range(n):
    x, y = V[k]
    if abs(x) < 2.5: c = np.zeros(N); c[k] = 1; eq(c, 앞z(y), 2.0); n중심 += 1                                                   # 중심선 프로필(옆 캡처에서 잰 것)
    z = 시차z(x, y) if a else None
    if z is not None: c = np.zeros(N); c[k] = 1; eq(c, z, 0.7); n시차 += 1                                                        # 시차 깊이
    c = np.zeros(N); c[k] = 1; eq(c, 겉z(x, y), 0.08)                                                                             # 약한 사전
A = np.array(rows) * np.array(w)[:, None]; bvec = np.array(rhs) * np.array(w); sol = np.linalg.lstsq(A, bvec, rcond=None)[0]; z = sol[:n]
# ⑤ 메시: 면마다 귀 자르기 · 눈구멍 면은 재질 1
from trimesh.creation import triangulate_polygon
from shapely.geometry import Polygon
B점 = lambda x, y, zz: (float(x), float(-zz), float(-y))
VV, FF, MM = [], [], []
for i in fids:
    ids = 면[i]; xy = V[ids]
    try: v2, f2 = triangulate_polygon(Polygon(xy).buffer(0))
    except Exception: continue
    # 삼각형 꼭짓점을 원래 꼭짓점 z 로(새 점이 생기면 평면식으로)
    fi = fids.index(i); pa, pb, pc = sol[n + 3 * fi:n + 3 * fi + 3]; base = len(VV)
    for x, y in v2:
        d = np.hypot(*(V[ids] - [x, y]).T); k = ids[int(np.argmin(d))]; zz = z[k] if d.min() < 1e-6 else pa * x + pb * y + pc
        VV.append(B점(x, y, zz))
    for tri in f2: FF.append([base + int(t_) for t_ in tri]); MM.append(1 if i in 눈구멍 else 0)

# ⑥ 뒤 껍질: 머리손 투구 꼭짓점 중 선화 앞면 안에 드는 것은 선화 z 보다 2 뒤로 — 돔 · 옆 · 뒤는 그대로, 앞은 선화가 맡는다
from shapely.geometry import Point
식 = {i: sol[n + 3 * fids.index(i):n + 3 * fids.index(i) + 3] for i in fids}; 폴 = {i: Polygon(V[면[i]]).buffer(0) for i in fids}
def 선화z(x, y):
    for i, pg in 폴.items():
        if pg.contains(Point(x, y)): pa, pb, pc = 식[i]; return pa * x + pb * y + pc
    return None
h = np.load(J(P, "투구.npz")); HV = h["V"].astype(np.float64).copy(); 밀림 = 0
for k in range(len(HV)):
    x, y, zz = HV[k, 0], -HV[k, 2], -HV[k, 1]; w = 선화z(x, y)
    if w is not None and zz > w - 2.0: HV[k, 1] = -(w - 2.0); 밀림 += 1
np.savez(J(P, "투구뒤.npz"), V=HV.astype(np.float32), F=h["F"]); print("투구뒤: 밀린 꼭짓점", 밀림, "/", len(HV))
np.savez(J(P, "선화.npz"), V=np.array(VV, np.float32), F=np.array(FF, np.int32), M=np.array(MM, np.int32))
json.dump(dict(꼭짓점=n, 면=len(fids), 거울=len(거울), 중심=n중심, 시차=n시차, 시차상관=round(float(r), 3), 시차눈금=[round(float(a), 4), round(float(b), 2)], z범위=[round(float(z.min()), 1), round(float(z.max()), 1)],
               조건="평면 3 · 대칭 2 · 중심선 2 · 시차 0.7 · 겉 사전 0.08", 승인="Claude(사용자 미확인)"), open(J(B, "선화.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(dict(꼭짓점=n, 면=len(fids), 거울=len(거울), 중심=n중심, 시차=n시차, 시차상관=round(float(r), 3), z범위=(round(float(z.min()), 1), round(float(z.max()), 1))))
