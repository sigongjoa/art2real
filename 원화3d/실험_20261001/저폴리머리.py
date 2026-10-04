# -*- coding: utf-8 -*-
"""저폴리 머리 나머지 (10-04 사용자 「나머지 부분도 해봐봐」).
부리 · 눈 밖의 정면 칸(투구 · 이마 · 볼날개 · 뿔 · 번개 …)을 칸 하나 = 평평한 면 몇 개로:
  꼭짓점 = 칸 먹선 다각형(먹선 가운데까지 넓힘) · 깊이 = 그 자리 창 모듈 벽(정면 접힌 판 상대 높이 − 17 · 이미 쓰던 잰 면)을 찍기만
  → 새 모양을 짓지 않고 계단 벽을 먹선 따라 납작면으로 다시 깎는 것
  이음: 꼭짓점이 앞서 놓인 꼭짓점(부리 판 · 눈구멍 앞 윤곽 · 먼저 지은 칸) 4 화소 안이면 그 자리 · 깊이로
  색: 원화 칸 평균이 채도 높으면(노랑 뿔 · 파랑 번개) 그 색, 아니면 흰 갑주색
출력 out/오메가몬2/블렌더/저폴리머리.ply"""
import os, json, numpy as np, cv2, trimesh
from scipy.spatial import Delaunay
A = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
z = np.load(os.path.join(A, "1.npz")); L = z["라벨"]; yy, xx = np.nonzero(L > 0); y0, x0 = yy.min(), xx.min()
m1 = np.load(os.path.join(A, "판_1_Z.npz"))["m"]; H, W = m1.shape; py, px = np.mgrid[0:H, 0:W]; cu = (np.nonzero(m1)[1].min() + np.nonzero(m1)[1].max()) / 2
C1 = L[np.clip(y0 + 2 * py, 0, L.shape[0] - 1), np.clip(x0 + 2 * px, 0, L.shape[1] - 1)] * m1
art = cv2.imdecode(np.fromfile(os.path.join(A, "판_1_원화.png"), np.uint8), 1); hsv = cv2.cvtColor(art, cv2.COLOR_BGR2HSV); rgb = art[:, :, ::-1]
창 = trimesh.load(os.path.join(B, "창모듈2.ply"), process=False); wv = 창.vertices
벽 = lambda x, y: float(wv[np.argmin((wv[:, 0] + cu - x) ** 2 + (-wv[:, 2] - y) ** 2), 1])
base = trimesh.load(os.path.join(B, "저폴리눈_벽없음.ply"), process=False)
앞윤곽 = {k: np.array(v) for k, v in json.load(open(os.path.join(B, "저폴리눈_앞윤곽.json"), encoding="utf-8")).items()}
안쪽 = lambda poly, p: cv2.pointPolygonTest(poly.astype(np.float32), (float(p[0]), float(p[1])), False) >= 0
부리칸 = {25, 26, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42}
pool = np.c_[base.vertices[:, 0] + cu, -base.vertices[:, 2]]; pool_d = base.vertices[:, 1].copy()   # 이음 후보(2D, 깊이)
parts = [base]; 기록 = []
ids, cnt = np.unique(C1[C1 > 0], return_counts=True)
for c in [int(i) for i, n in sorted(zip(ids, cnt), key=lambda t: -t[1]) if n >= 20]:
    if c in 부리칸 or c in (1, 2): continue   # 루프 1: 뿔(1 · 2)은 아래에서 따로
    mk = cv2.dilate((C1 == c).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=2)
    yy_, xx_ = np.nonzero(C1 == c); cen = (xx_.mean(), yy_.mean())
    if any(안쪽(P, cen) for P in 앞윤곽.values()): continue          # 눈구멍 안 칸(눈동자 · 검은 칠)은 눈 모듈 몫
    cs, _ = cv2.findContours(mk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); poly = cv2.approxPolyDP(max(cs, key=cv2.contourArea), 2.0, True).reshape(-1, 2).astype(float)
    if len(poly) < 3: continue
    d = np.array([벽(x, y) for x, y in poly])
    for i in range(len(poly)):
        dist = np.hypot(*(pool - poly[i]).T); j = int(np.argmin(dist))
        if dist[j] < 4.0: poly[i] = pool[j]; d[i] = pool_d[j]
    tri = Delaunay(poly); fc = [t for t in tri.simplices if 안쪽(poly, poly[t].mean(0))]
    if not fc: continue
    me = trimesh.Trimesh(np.c_[poly[:, 0] - cu, d, -poly[:, 1]], np.array(fc), process=False)
    bad = me.face_normals[:, 1] > 0; me.faces[bad] = me.faces[bad][:, ::-1]
    hs = hsv[yy_, xx_].mean(0); col = rgb[yy_, xx_].mean(0) if hs[1] > 70 else np.array([232, 234, 244])
    me.visual.vertex_colors = np.tile(list(col.astype(int)) + [255], (len(poly), 1)).astype(np.uint8); parts.append(me)
    pool = np.r_[pool, poly]; pool_d = np.r_[pool_d, d]; 기록.append((c, len(poly), round(float(d.min()), 1), round(float(d.max()), 1)))
# ── 피드백 루프 1 (채점: 정면 0.864 · 옆 0.275 — 옆 빨강 = 투구 뒤 · 볼 · 뿔이 종이) ──
import contextlib, io
K = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "기준선.py")}
with contextlib.redirect_stdout(io.StringIO()): exec(open(K["__file__"], encoding="utf-8").read(), K)
T = K["T"]; z2 = np.load(os.path.join(A, "2.npz")); L2 = z2["라벨"]; yy2, xx2 = np.nonzero(L2 > 0)
m2 = np.load(os.path.join(A, "판_2_Z.npz"))["m"]; H2, W2 = m2.shape; py2, px2 = np.mgrid[0:H2, 0:W2]
C2 = L2[np.clip(yy2.min() + 2 * py2, 0, L2.shape[0] - 1), np.clip(xx2.min() + 2 * px2, 0, L2.shape[1] - 1)] * m2
def 행표(mask2, 앞=True):
    ys, xs = np.nonzero(mask2); dd, rr = T(xs.astype(float), ys.astype(float)); o = {}
    for r_ in np.unique(np.round(rr).astype(int)):
        q = np.round(rr).astype(int) == r_; o[int(r_)] = float(dd[q].min() if 앞 else dd[q].max())
    return o
def 찾기(표, r):
    ks = np.array(sorted(표)); return 표[int(ks[np.argmin(np.abs(ks - r))])]
def 다각(mask, eps=2.0):
    cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); return cv2.approxPolyDP(max(cs, key=cv2.contourArea), eps, True).reshape(-1, 2).astype(float)
def 면(V3, F, col, 바깥):
    me = trimesh.Trimesh(V3, np.array(F), process=False); n = me.face_normals @ np.array(바깥, float); me.faces[n < 0] = me.faces[n < 0][:, ::-1]
    me.visual.vertex_colors = np.tile(list(col) + [255], (len(V3), 1)).astype(np.uint8); return me
# 1-a 뿔: 정면 칸 1(밝은 면) · 2(그늘 면) = 능선에서 만나는 두 면. 옆 원화 뿔 칸 2 의 앞 모서리 = 능선 깊이 · 뒤 모서리 = 뒷등 깊이(잰 값) · 바깥 모서리 = 둘의 가운데(가정)
뿔앞, 뿔뒤 = 행표(C2 == 2, True), 행표(C2 == 2, False); 뿔합 = np.zeros((H, W), np.uint8)
for c in (1, 2):
    mk = cv2.dilate((C1 == c).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=2); 뿔합 |= mk
뿔P = {c: 다각(cv2.dilate((C1 == c).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=2)) for c in (1, 2)}
cs2, _ = cv2.findContours(cv2.dilate((C1 == 2).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=2), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); 둘2 = max(cs2, key=cv2.contourArea)
cs1, _ = cv2.findContours(cv2.dilate((C1 == 1).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=2), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); 둘1 = max(cs1, key=cv2.contourArea)
for c, other in ((1, 둘2), (2, 둘1)):
    P = 뿔P[c]; 능 = np.array([abs(cv2.pointPolygonTest(other, (float(x), float(y)), True)) <= 3 for x, y in P])
    d = np.array([찾기(뿔앞, y) if f else (찾기(뿔앞, y) + 찾기(뿔뒤, y)) / 2 for (x, y), f in zip(P, 능)])
    for i in range(len(P)):
        dist = np.hypot(*(pool - P[i]).T); j = int(np.argmin(dist))
        if dist[j] < 4.0: P[i] = pool[j]; d[i] = pool_d[j]
    tri = Delaunay(P); fc = [t for t in tri.simplices if 안쪽(P, P[t].mean(0))]
    parts.append(면(np.c_[P[:, 0] - cu, d, -P[:, 1]], fc, (230, 232, 242) if c == 1 else (200, 204, 222), (0, -1, 0)))
    pool = np.r_[pool, P]; pool_d = np.r_[pool_d, d]
Pu = 다각(뿔합); 행 = np.unique(np.round(Pu[:, 1]).astype(int)); 등 = []
for r_ in np.linspace(Pu[:, 1].min(), Pu[:, 1].max(), 6):
    xs_ = np.nonzero(뿔합[int(np.clip(round(r_), 0, H - 1))])[0]
    if len(xs_): 등.append(((xs_.min() + xs_.max()) / 2, r_))
Q = np.r_[Pu, np.array(등)]; dq = np.r_[[(찾기(뿔앞, y) + 찾기(뿔뒤, y)) / 2 for y in Pu[:, 1]], [찾기(뿔뒤, y) for _, y in 등]]
tri = Delaunay(Q); fc = [t for t in tri.simplices if 안쪽(Pu, Q[t].mean(0))]
parts.append(면(np.c_[Q[:, 0] - cu, dq, -Q[:, 1]], fc, (190, 194, 212), (0, 1, 0)))   # 뿔 뒷면(뒷등)
# 1-b 투구 · 볼 옆벽: 옆 원화 칸(투구 1 · 볼 17) 다각형 → (깊이, 행) · x = 그 행 정면 머리 반폭(곧은 옆벽 · 둥근 단면은 다음 루프)
# 루프 2: 반폭을 정면 마스크 그대로 재면 볼날개 · 안테나 가시가 든 행에서 옆벽이 지느러미로 튐(정면 IoU 0.864 → 0.771) → 지름 25 원으로 열어 가시를 뗀 몸통 폭
몸 = cv2.morphologyEx(m1.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
반폭 = {r: (np.nonzero(몸[r])[0].max() - np.nonzero(몸[r])[0].min()) / 2 for r in range(H) if 몸[r].any()}; xc = (np.nonzero(m1)[1].min() + np.nonzero(m1)[1].max()) / 2
for sc_, col in (([1, 3, 4, 6, 7, 8, 10, 11, 13, 18], (226, 228, 240)), ([17], (214, 218, 232))):   # 루프 4: 투구 옆벽에 옆 원화 눈 둘레 칸(3 · 4 · 6 · 7 · 8 · 10 · 11 · 13 · 18)을 합쳐 옆 · 3/4 의 눈자리 구멍을 막음
    Pp = 다각(cv2.dilate(np.isin(C2, sc_).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=2)); dd, rr = T(Pp[:, 0], Pp[:, 1]); Q = np.c_[dd, rr]
    tri = Delaunay(Q); fc = [t for t in tri.simplices if 안쪽(Q, Q[t].mean(0))]; w = np.array([찾기(반폭, r) for r in rr])
    중 = {r: (np.nonzero(몸[r])[0].max() + np.nonzero(몸[r])[0].min()) / 2 for r in 반폭}; xr_ = np.array([찾기(중, r) for r in rr])   # 루프 3: 행마다 몸통 가운데(전체 마스크 가운데는 볼날개 탓에 왼쪽으로 쏠려 왼쪽만 지느러미)
    for sgn in (1, -1): parts.append(면(np.c_[xr_ + sgn * w - cu, dd, -rr], fc, col, (sgn, 0, 0)))
OPT = os.environ.get("OPT", "")   # 10-04 「둘 다 비교해보자고」: A = 정면 판 ↔ 옆벽 잇기 · B = 안테나 · 코판 옆 채우기
if OPT == "A":   # 행마다 정면 몸통 가장자리(x · 깊이 = 그 자리 벽)와 옆벽 앞 모서리(같은 x · 깊이 = 옆 투구 칸 앞 끝)를 띠로 이음
    투앞 = 행표(np.isin(C2, [1, 3, 4, 6, 7, 8, 10, 11, 13, 18]), True); rs = [r for r in range(0, H, 6) if r in 반폭 and r in 중 and min(투앞) <= r <= max(투앞)]
    for sgn in (1, -1):
        V3 = []; F = []
        for r in rs:
            x = 중[r] + sgn * 반폭[r]; V3 += [(x - cu, 벽(x, r), -r), (x - cu, 찾기(투앞, r), -r)]
        for i in range(len(rs) - 1):
            a = 2 * i; F += [(a, a + 1, a + 3), (a, a + 3, a + 2)]
        if F: parts.append(면(np.array(V3), F, (220, 223, 236), (sgn, 0, 0)))
if OPT == "B":
    xa = json.load(open(os.path.join(A, "기준선.json"), encoding="utf-8"))["정면 축(판 화소 열)"]["A 중심"]
    # 안테나 = 가는 막대: 정면 노랑 가지(먹 판 밖) 의 (x, 행) + 옆 노랑 칸 9 의 깊이 — 뿌리 → 끝 길이 비율 t 로 짝(행은 컷마다 원근이 달라 정면 행을 씀)
    노 = ((hsv[:, :, 0] > 15) & (hsv[:, :, 0] < 40) & (hsv[:, :, 1] > 60)).astype(np.uint8); n_, lab = cv2.connectedComponents(노)
    ys9, xs9 = np.nonzero(C2 == 9); d9, r9 = T(xs9.astype(float), ys9.astype(float)); 옆선 = np.c_[d9, r9]
    def 끝점(pts, 뿌리쪽):   # 첫 주성분 양끝, 뿌리 = 뿌리쪽 점에 가까운 끝
        c = pts.mean(0); u = np.linalg.svd(pts - c)[2][0]; t_ = (pts - c) @ u; a, b = c + u * t_.min(), c + u * t_.max()
        return (a, b) if np.hypot(*(a - 뿌리쪽)) < np.hypot(*(b - 뿌리쪽)) else (b, a)
    s0, s1 = 끝점(옆선, np.array([0.0, 옆선[:, 1].mean()]))
    for k in range(1, n_):
        yy_, xx_ = np.nonzero(lab == k)
        if len(xx_) < 40: continue
        f0, f1 = 끝점(np.c_[xx_, yy_].astype(float), np.array([xa, 150.0])); 반경 = max(1.5, len(xx_) / np.hypot(*(f1 - f0)) / 2)
        V3 = []; F = []
        for i, t_ in enumerate(np.linspace(0, 1, 6)):
            x, r = f0 + (f1 - f0) * t_; d = (s0 + (s1 - s0) * t_)[0]; rad = 반경 * (1 - 0.8 * t_)
            for a in range(3): V3.append((x - cu + rad * np.cos(a * 2.094), d + rad * np.sin(a * 2.094), -r))
        for i in range(5):
            for a in range(3):
                b = (a + 1) % 3; F += [(3 * i + a, 3 * i + b, 3 * i + 3 + b), (3 * i + a, 3 * i + 3 + b, 3 * i + 3 + a)]
        me = trimesh.Trimesh(np.array(V3), np.array(F), process=False); me.fix_normals(); me.visual.vertex_colors = np.tile([200, 180, 60, 255], (len(V3), 1)).astype(np.uint8); parts.append(me)
    # 코판 옆: 옆 원화 칸 5 · 6 · 12 → 부리 옆판과 같은 V 단면 폭(저폴리부리 v10 규칙)
    부리합 = cv2.dilate(np.isin(C1, list(부리칸)).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=2)
    부반 = {r: (np.nonzero(부리합[r])[0].max() - np.nonzero(부리합[r])[0].min()) / 2 for r in range(H) if 부리합[r].any()}; 단면 = 행표(m2, True); D = 17.2
    Pp = 다각(cv2.dilate(np.isin(C2, [5, 6, 12]).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=2)); dd, rr = T(Pp[:, 0], Pp[:, 1]); Q = np.c_[dd, rr]
    tri = Delaunay(Q); fc = [t for t in tri.simplices if 안쪽(Q, Q[t].mean(0))]
    dr = np.array([찾기(단면, r) for r in rr]); w = np.array([찾기(부반, r) for r in rr]) * np.clip((dd - dr) / (-D - dr), 0.15, 1)
    for sgn in (1, -1): parts.append(면(np.c_[xa + sgn * w - cu, dd, -rr], fc, (230, 232, 244), (sgn, 0, 0)))
allm = trimesh.util.concatenate(parts)
trimesh.Trimesh(allm.vertices, allm.faces, vertex_colors=allm.visual.vertex_colors, process=False).export(os.path.join(B, "저폴리머리" + os.environ.get("PAN", "") + ".ply"), encoding="ascii")
print({"칸": len(기록), "꼭짓점 합": sum(r[1] for r in 기록)}, 기록[:12])
