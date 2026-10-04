# -*- coding: utf-8 -*-
"""머리판 v5 ~ v10 — 도면 → 짓기 → 판정 (10-04 사용자 「알아서 v10 까지 해봐봐」).
v4 를 지어 보고 드러난 것: 반구 돔은 그릇 · 부재가 서로 안 닿음 · 밑이 뚫림 → **속(머리 타원체) 하나를 먼저 정하고 모든 부재를 그 표면에서 짓는다**(붙음은 구성상).
  속 E: 가운데 x = 축 A · 세로 반축 c · 가운데 행 zc · 좌우 반축 a = 정면 몸통 반폭에 최소제곱 · 앞뒤 = 옆 돔 칸 앞 끝 · 처마 높이 뒤 끝(f = b)
  v5 투구 H01 = E 표면 중 정면 칸(돔 · 이마 · 차양 밑) 영역 + 뒤 반 전체 → 아래 테두리가 원화 칸 윤곽을 그대로 따름
  v6 마스크 H02 = 정면 마스크 칸 영역 · 앞면 = min(E 앞, V 쐐기) · 쐐기 = 행마다 옆 마스크 칸 가장 앞 + 기울기(테두리에서 E 와 만나게)
  v7 창 H03 = 저폴리눈 앞 윤곽 둘(원화) · 표면에서 +17.2 뒤로 옆벽 · 바닥(검정) · 눈알(파랑)
  v8 차양 = 정면 칸 14 · 16 판 · 뒷면 = 그 자리 표면 · 두께 4
  v9 뿔 H09 = 정면 칸 1 · 2 폭 + 옆 뿔 칸(2) 앞 · 뒤로 마름모 단면 로프트 · 안테나 H04 = 원화 노랑 가지 끝 + 옆 안테나 칸(9) 깊이 막대
  v10 볼날개 H06 = 정면 칸 7 · 10 · 25 · 26 · 28 판(표면 위 두께 4) + 색(흰 · 검정 속 · 파랑 눈 · 노랑)
python 머리판.py <V> → out/오메가몬2/블렌더/머리판_v<V>.ply · 도면_머리판_v<V>.png"""
import os, sys, json, numpy as np, cv2, trimesh, contextlib, io
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import Delaunay
VER = int(sys.argv[1])
A = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
K = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "기준선.py")}
with contextlib.redirect_stdout(io.StringIO()): exec(open(K["__file__"], encoding="utf-8").read(), K)
J = json.load(open(os.path.join(A, "기준선.json"), encoding="utf-8")); 층, 축, 옆축 = J["층(정면 판 화소 행)"], J["정면 축(판 화소 열)"], J["옆 축(눈 = 0 · 정면 화소 · 앞 −)"]
깊 = json.load(open(os.path.join(A, "창깊이.json"), encoding="utf-8")); DW = round((깊["창 깊이(옆 · 입구 → 눈)"] + 깊["창 깊이(3/4 · 옆벽 폭 / sin 35°)"]) / 2, 1)
m1 = np.load(os.path.join(A, "판_1_Z.npz"))["m"]; H, W = m1.shape; xa = 축["A 중심"]
m2 = np.load(os.path.join(A, "판_2_Z.npz"))["m"]; D0, ND = -200, 400; k_, t_ = K["k"], K["t"]; ct, st_ = np.cos(t_), np.sin(t_)
Ma = np.array([[k_ * ct, -k_ * st_, -k_ * K["ex"] * ct + k_ * K["ey"] * st_ - D0], [k_ * st_, k_ * ct, K["c"] - k_ * K["xm"] * st_]], np.float32)
def 칸지도(n):
    z = np.load(os.path.join(A, f"{n}.npz")); L = z["라벨"]; yy, xx = np.nonzero(L > 0); y0, x0 = yy.min(), xx.min()
    m = np.load(os.path.join(A, f"판_{n}_Z.npz"))["m"]; h, w = m.shape; py, px = np.mgrid[0:h, 0:w]
    return L[np.clip(y0 + 2 * py, 0, L.shape[0] - 1), np.clip(x0 + 2 * px, 0, L.shape[1] - 1)] * m
C1 = 칸지도("1"); C2 = cv2.warpAffine(칸지도("2").astype(np.float32), Ma, (ND, H), flags=cv2.INTER_NEAREST).astype(int)
S2 = cv2.warpAffine(m2.astype(np.uint8), Ma, (ND, H), flags=cv2.INTER_NEAREST)
몸 = lambda m: cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
Fa, Sa = 몸(m1), 몸(S2)
기록 = {}
# ── 속 E ──
rows = [r for r in range(H) if Fa[r].any()]; hw = np.array([(np.nonzero(Fa[r])[0].max() - np.nonzero(Fa[r])[0].min()) / 2 for r in rows]); rows = np.array(rows)
top = rows.min(); 턱 = 층["L2 턱 끝"]; best = None
for c in np.arange(60, 160, 2):
    for zc in np.arange(top + 40, 턱, 2):
        q = 1 - ((rows - zc) / c) ** 2; ok = (q > 0.05) & (rows <= 턱)
        if ok.sum() < 30: continue
        s = np.sqrt(q[ok]); a = float((hw[ok] * s).sum() / (s * s).sum()); e = ((hw[ok] - a * s) ** 2).mean()
        if best is None or e < best[0]: best = (e, a, c, zc)
_, a, c, zc = best
r6 = 층["L6 처마"]; 돔칸 = cv2.dilate((C2 == 1).astype(np.uint8), np.ones((3, 3), np.uint8)); dr = [r for r in range(int(top), int(r6) + 1) if 돔칸[r].any()]
yf6 = min(np.nonzero(돔칸[r])[0].min() for r in dr) + D0; yb6 = np.nonzero(Sa[int(r6)])[0].max() + D0
s6 = np.sqrt(max(0.05, 1 - ((r6 - zc) / c) ** 2)); y0 = (yf6 + yb6) / 2; f = b = (yb6 - yf6) / 2 / s6
기록["속 E"] = {"a": round(a, 1), "c": round(float(c), 1), "zc 행": round(float(zc), 1), "y0": round(float(y0), 1), "f=b": round(float(f), 1)}
def q_(x, r): return np.clip(1 - ((x - xa) / a) ** 2 - ((r - zc) / c) ** 2, 0, None)
앞E = lambda x, r: y0 - f * np.sqrt(q_(x, r)); 뒤E = lambda x, r: y0 + b * np.sqrt(q_(x, r))
# ── 영역 → 조각(정면 투영 다각형 + 격자 · 깊이 함수) ──
def 조각(mask, 깊이, step=3, eps=1.0):
    mask = mask.astype(np.uint8); cs, _ = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    P = [cv2.approxPolyDP(cn, eps, True).reshape(-1, 2) for cn in cs if len(cn) >= 3]
    if not P: return None
    P = np.concatenate(P).astype(float); gy, gx = np.mgrid[0:H:step, 0:W:step]; g = np.c_[gx.ravel(), gy.ravel()][mask[gy.ravel(), gx.ravel()] > 0]
    pts = np.unique(np.r_[P, g].round(1), axis=0)
    if len(pts) < 3: return None
    tri = Delaunay(pts); cen = pts[tri.simplices].mean(1); keep = mask[np.clip(cen[:, 1].round().astype(int), 0, H - 1), np.clip(cen[:, 0].round().astype(int), 0, W - 1)] > 0
    V = np.c_[pts[:, 0] - xa, 깊이(pts[:, 0], pts[:, 1]), -pts[:, 1]]
    m = trimesh.Trimesh(V, tri.simplices[keep], process=False); m.remove_unreferenced_vertices(); return m
def 판(mask, 앞깊이, 두께):   # 정면 다각형 판 — 앞면 = 앞깊이, 뒷면 = 앞깊이 + 두께, 옆벽
    m = 조각(mask, 앞깊이, step=4, eps=1.0)
    if m is None: return None
    back = m.copy(); back.vertices[:, 1] += 두께; back.invert()
    e = m.edges_sorted[trimesh.grouping.group_rows(m.edges_sorted, require_count=1)]; n = len(m.vertices); Fs = []   # 경계 모서리(한 면에만)
    for p, q in e: Fs += [[p, q, q + n], [p, q + n, p + n]]
    V = np.r_[m.vertices, back.vertices]; Fc = np.r_[m.faces, back.faces + n, np.array(Fs).reshape(-1, 3)] if Fs else np.r_[m.faces, back.faces + n]
    return trimesh.Trimesh(V, Fc, process=False)
칸 = lambda cs: cv2.dilate(np.isin(C1, cs).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=2)
몸정 = m1.astype(np.uint8)
창들 = [np.array(v, np.float32) for v in json.load(open(os.path.join(B, "저폴리눈_앞윤곽.json"), encoding="utf-8")).values()]
창판 = np.zeros((H, W), np.uint8)
for P_ in 창들: cv2.fillPoly(창판, [P_.round().astype(np.int32)], 1)
부재 = []
투구영역 = 칸([3, 4, 6, 8, 9, 14, 16, 5, 11, 13, 19]) & 몸정 & (1 - 창판) if VER >= 7 else 칸([3, 4, 6, 8, 9, 14, 16, 5, 11, 13, 19]) & 몸정
if VER < 6: 투구영역 = 투구영역 | (칸(list(range(17, 43))) & 몸정)    # v5: 얼굴 아래도 일단 속 표면(마스크 전)
if VER >= 11:   # v11: 칸 사이 틈(먹선 · 빠진 칸)으로 검은 속이 얼룩 → 투구 = 몸 실루엣에서 마스크 · 창 · 뿔만 뺀 나머지 전부
    투구영역 = 몸정 & (1 - 칸([29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42])) & (1 - 창판) & (1 - np.isin(C1, [1, 2]).astype(np.uint8))
투구 = 조각(투구영역, 앞E); 뒤반 = 조각((np.abs(np.arange(W)[None, :] - xa) <= a) & (np.arange(H)[:, None] >= zc - c) & (np.arange(H)[:, None] <= 턱) & (q_(np.arange(W)[None, :], np.arange(H)[:, None]) > 0), 뒤E, step=4)
if 뒤반 is not None: 뒤반.invert()
부재 += [("H01 투구", trimesh.util.concatenate([m for m in (투구, 뒤반) if m is not None]), (232, 234, 244))]
if VER >= 6:
    마스크칸 = 칸([29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42]) & 몸정
    if VER >= 12: 마스크칸 = cv2.morphologyEx(마스크칸, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))   # 미늘 사이 먹선 틈 메움
    if VER >= 7: 마스크칸 &= (1 - 창판)
    옆마 = cv2.dilate(np.isin(C2, [5, 12, 14, 15, 16, 19, 20]).astype(np.uint8), np.ones((3, 3), np.uint8))
    부앞 = {r: np.nonzero(옆마[r])[0].min() + D0 for r in range(H) if 옆마[r].any()}; ks = np.array(sorted(부앞))
    if VER >= 12:   # v12: 행마다 깊이라 계단 → 행 방향 가우시안 σ 4 · 빈 행은 보간
        from scipy import ndimage as _nd
        rr_ = np.arange(ks.min(), ks.max() + 1); vv_ = np.interp(rr_, ks, [부앞[k] for k in ks]); vv_ = _nd.gaussian_filter1d(vv_, 4)
        부앞 = dict(zip(rr_.tolist(), vv_.tolist())); ks = np.array(sorted(부앞))
    xs_ = {r: (np.nonzero(마스크칸[r])[0].min(), np.nonzero(마스크칸[r])[0].max()) for r in range(H) if 마스크칸[r].any()}
    def 마스크깊이(x, r):
        out = []
        for xx, rr in zip(np.atleast_1d(x), np.atleast_1d(r)):
            ri = int(round(rr)); e = 앞E(xx, rr); 끝 = 부앞[int(ks[np.argmin(np.abs(ks - ri))])]
            if ri in xs_: hwm = max(1.0, max(xa - xs_[ri][0], xs_[ri][1] - xa))
            else: hwm = 30.0
            테 = 앞E(xa + hwm, rr); s = (테 - 끝) / hwm; out.append(min(e, 끝 + s * abs(xx - xa)))
        return np.array(out)
    부재 += [("H02 마스크", 조각(마스크칸, 마스크깊이, step=3), (222, 226, 238))]
    기록["H02 마스크"] = {"부리 앞 최소": round(float(min(부앞.values())), 1)}
if VER >= 7:
    socks = []
    for P_ in 창들:
        n = len(P_); 입 = np.array([[p[0] - xa, (부재[1][1] if False else None) or 0, -p[1]] for p in P_], float)
        입[:, 1] = [min(앞E(p[0], p[1]), 마스크깊이(p[0], p[1])[0]) if VER >= 6 else 앞E(p[0], p[1]) for p in P_]
        cen = P_.mean(0); 속P = cen + (P_ - cen) * 0.8; 바 = np.c_[속P[:, 0] - xa, 입[:, 1] + DW, -속P[:, 1]]
        V = np.r_[입, 바]; Fs = []
        for i in range(n): j = (i + 1) % n; Fs += [[i, j, j + n], [i, j + n, i + n]]
        tri = Delaunay(속P); Fs += [list(np.array(t_) + n) for t_ in tri.simplices if cv2.pointPolygonTest(속P.astype(np.float32), tuple(속P[t_].mean(0)), False) >= 0]
        socks.append(trimesh.Trimesh(V, np.array(Fs), process=False))
        eye = trimesh.creation.icosphere(2, radius=9.0); eye.vertices[:, 1] *= 0.5; eye.apply_translation([cen[0] - xa, 바[:, 1].mean() - 2, -cen[1]]); 부재.append(("H03 눈", eye, (90, 150, 230)))
    부재.append(("H03 창", trimesh.util.concatenate(socks), (25, 25, 32)))
    기록["H03 창"] = {"깊이": DW}
def 표면(x, r):
    e = 앞E(x, r)
    return np.minimum(e, 마스크깊이(x, r)) if VER >= 6 else e
if VER >= 8:
    부재.append(("H01 차양", 판(칸([14, 16]) & 몸정, lambda x, r: 표면(x, r) - 4.0, 4.0), (240, 242, 250)))
if VER >= 9:
    # 뿔: 정면 폭(칸 1 · 2) + 옆 뿔 칸(2) 앞 · 뒤 → 행마다 마름모
    뿔정 = np.isin(C1, [1, 2]); 뿔옆 = cv2.dilate((C2 == 2).astype(np.uint8), np.ones((3, 3), np.uint8))
    정행 = [r for r in range(H) if 뿔정[r].any()]; 옆행 = [r for r in range(H) if 뿔옆[r].any()]
    대응행 = (lambda r: int(round(옆행[0] + (r - 정행[0]) * (옆행[-1] - 옆행[0]) / max(1, 정행[-1] - 정행[0])))) if (VER >= 13 and 정행 and 옆행) else (lambda r: r)   # v13: 두 장의 뿔 행 범위가 안 겹쳐 뿔이 안 나옴 → 끝끼리 맞춤
    rs = [r for r in 정행 if 뿔옆[min(H - 1, max(0, 대응행(r)))].any()][::2] if VER >= 13 else [r for r in range(H) if 뿔정[r].any() and 뿔옆[r].any()][::2]; V = []; Fc = []
    for i, r in enumerate(rs):
        xs = np.nonzero(뿔정[r])[0]; ys = np.nonzero(뿔옆[min(H - 1, max(0, 대응행(r)))])[0] + D0; cx_ = (xs.min() + xs.max()) / 2 - xa; hw_ = (xs.max() - xs.min()) / 2; ym = (ys.min() + ys.max()) / 2
        V += [(cx_, ys.min(), -r), (cx_ + hw_, ym, -r), (cx_, ys.max(), -r), (cx_ - hw_, ym, -r)]
        if i:
            o = 4 * (i - 1)
            for k in range(4): Fc += [[o + k, o + (k + 1) % 4, o + 4 + (k + 1) % 4], [o + k, o + 4 + (k + 1) % 4, o + 4 + k]]
    if VER >= 15 and len(V) >= 8:   # v15: 행마다 단면이라 계단 → 마름모 네 꼭짓점 궤적을 행 방향 σ 3 으로 고르게
        from scipy import ndimage as _nd
        VV = np.array(V).reshape(-1, 4, 3); VV[:, :, :2] = _nd.gaussian_filter1d(VV[:, :, :2], 3, axis=0, mode="nearest"); V = VV.reshape(-1, 3).tolist()
    if len(rs) > 1: 뿔 = trimesh.Trimesh(np.array(V), np.array(Fc), process=False); 뿔.fix_normals(); 부재.append(("H09 뿔", 뿔, (236, 238, 248)))
    # 안테나: 정면 노랑 가지(채도 · 색상) 뿌리 → 끝 · 깊이 = 옆 안테나 칸 9 의 앞 → 뒤
    art = cv2.imdecode(np.fromfile(os.path.join(A, "판_1_원화.png"), np.uint8), 1); hsv = cv2.cvtColor(art, cv2.COLOR_BGR2HSV)
    노 = ((hsv[:, :, 0] > 15) & (hsv[:, :, 0] < 40) & (hsv[:, :, 1] > 60)).astype(np.uint8); n_, lab = cv2.connectedComponents(노)
    ys9, xs9 = np.nonzero(C2 == 9); 앞9, 뒤9 = (xs9.min() + D0, xs9.max() + D0) if len(xs9) else (0, 60)
    for k in range(1, n_):
        yy, xx = np.nonzero(lab == k)
        if len(xx) < 40: continue
        pts = np.c_[xx, yy].astype(float); cc = pts.mean(0); u = np.linalg.svd(pts - cc)[2][0]; t = (pts - cc) @ u; p0, p1 = cc + u * t.min(), cc + u * t.max()
        if np.hypot(*(p0 - [xa, 150])) > np.hypot(*(p1 - [xa, 150])): p0, p1 = p1, p0
        a3 = np.array([p0[0] - xa, float(np.ravel(표면(p0[0], p0[1]))[0]), -p0[1]]); b3 = np.array([p1[0] - xa, 뒤9, -p1[1]])
        if VER >= 14:   # v14: 옆 칸 9 깊이가 엉뚱해 3 배 길이 → 3D 길이 = 정면 길이 / cos(30°) (뒤로 30° 젖힘 · 원화 옆 안테나 기울기 가정)
            L2 = np.hypot(*(p1 - p0)); b3[1] = a3[1] + L2 * np.tan(np.radians(30))
        cyl = trimesh.creation.cylinder(radius=2.0, segment=[a3, b3], sections=6); 부재.append(("H04 안테나", cyl, (210, 175, 60)))
if VER >= 10:
    부재.append(("H06 볼날개", 판(칸([7, 10, 25, 26, 28]) & 몸정 & (1 - 창판), lambda x, r: 표면(x, r) - 3.0, 3.0), (226, 230, 242)))
core = trimesh.creation.icosphere(3); core.vertices *= [a * 0.97, f * 0.97, c * 0.97]; core.apply_translation([0, y0, -zc]); 부재.append(("속(검정)", core, (30, 30, 36)))   # v5 2 판: 속을 처음부터 — 판 사이로 보이는 곳은 원화의 검은 속머리(겹 순서)
부재 = [(n_, m, col) for n_, m, col in 부재 if m is not None]
for _, m, col in 부재: m.visual.vertex_colors = np.tile(list(col) + [255], (len(m.vertices), 1)).astype(np.uint8)
allm = trimesh.util.concatenate([m for _, m, _ in 부재]); allm = trimesh.Trimesh(allm.vertices, allm.faces, vertex_colors=allm.visual.vertex_colors, process=False)
allm.export(os.path.join(B, f"머리판_v{VER}.ply"), encoding="ascii")
# ── 도면 ──
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
sheet = Image.new("RGB", (2400, 1600), "white"); d = ImageDraw.Draw(sheet)
d.text((30, 20), f"머리 도면 v{VER} · 속(타원체) 하나에서 모든 부재", font=F(40), fill="black")
d.text((30, 72), "부재마다 색 · 굵은 선 = 투영 윤곽 · 아래 = 원화 겹침 · 단위 = 정면 판 화소", font=F(22), fill=(80, 80, 80))
선색 = lambda col: tuple(int(cc * 0.55) for cc in col) if sum(col) > 400 else col
def 투영그림(view, x0, y0_, w, hh, 제목):
    d.rectangle([x0, y0_, x0 + w, y0_ + hh], outline=(200, 200, 200)); d.text((x0 + 8, y0_ + 6), 제목, font=F(22), fill="black")
    uu = np.concatenate([view(m.vertices)[0] for _, m, _ in 부재]); vv = np.concatenate([view(m.vertices)[1] for _, m, _ in 부재])
    sc = min((w - 60) / max(1e-6, np.ptp(uu)), (hh - 80) / max(1e-6, np.ptp(vv)))
    ox = x0 + w / 2 - (uu.min() + uu.max()) / 2 * sc; oy = y0_ + 50 + (hh - 80) / 2 - (vv.min() + vv.max()) / 2 * sc
    for nm, m, col in 부재:
        u, v_ = view(m.vertices); U = ox + u * sc; Vv = oy + v_ * sc
        msk = np.zeros((hh + 600, w + 600), np.uint8); cv2.fillPoly(msk, [np.round(np.c_[U[t_] - x0 + 300, Vv[t_] - y0_ + 300]).astype(np.int32) for t_ in m.faces], 1)
        for cn in cv2.findContours(msk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]:
            cn = cv2.approxPolyDP(cn, 1.2, True).reshape(-1, 2); pts = [(p[0] + x0 - 300, p[1] + y0_ - 300) for p in cn]
            if len(pts) > 2: d.line(pts + [pts[0]], fill=선색(col), width=2)
정 = lambda v: (v[:, 0], -v[:, 2]); 옆 = lambda v: (v[:, 1], -v[:, 2]); 위 = lambda v: (v[:, 0], v[:, 1])
yaw, pit = np.radians(-35), np.radians(20); Rz = np.array([[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]]); Rx = np.array([[1, 0, 0], [0, np.cos(pit), -np.sin(pit)], [0, np.sin(pit), np.cos(pit)]])
삼사 = lambda v: ((v @ Rz.T @ Rx.T)[:, 0], -(v @ Rz.T @ Rx.T)[:, 2])
투영그림(정, 40, 110, 500, 460, "① 정면"); 투영그림(옆, 570, 110, 560, 460, "② 옆 (왼쪽 = 앞)"); 투영그림(위, 1160, 110, 460, 460, "③ 평면 (위 = 앞)"); 투영그림(삼사, 1650, 110, 460, 460, "⑤ 3/4")
def 자르기(m, z):
    T = m.triangles; dz = T[:, :, 2] - z; sel = (dz.min(1) <= 0) & (dz.max(1) >= 0); out = []
    for tri, dd in zip(T[sel], dz[sel]):
        pts = [p + (q - p) * dp / (dp - dq) for p, q, dp, dq in ((tri[0], tri[1], dd[0], dd[1]), (tri[1], tri[2], dd[1], dd[2]), (tri[2], tri[0], dd[2], dd[0])) if dp * dq < 0]
        if len(pts) == 2: out.append(np.array(pts)[:, :2])
    return out
d.text((40, 600), "④ 단면", font=F(24), fill="black")
for i, (nm, r) in enumerate((("L6 처마", 층["L6 처마"]), ("L5 눈", 층["L5 눈"]), ("L4 코판 끝", 층["L4 코판 끝"]), ("L3 미늘2 아래", 층["L3 미늘2 아래"]))):
    x0 = 40 + i * 400; d.rectangle([x0, 640, x0 + 380, 640 + 380], outline=(200, 200, 200)); d.text((x0 + 8, 646), f"{nm} (행 {r:.0f})", font=F(20), fill="black"); d.text((x0 + 180, 672), "앞", font=F(16), fill=(0, 0, 200))
    for _, m, col in 부재:
        for s in 자르기(m, -r): d.line([(x0 + 190 + s[0][0] * 1.3, 640 + 210 + (s[0][1] - y0) * 1.3), (x0 + 190 + s[1][0] * 1.3, 640 + 210 + (s[1][1] - y0) * 1.3)], fill=선색(col), width=2)
art1 = Image.open(os.path.join(A, "판_1_원화.png")).convert("RGB"); d1 = ImageDraw.Draw(art1)
art2 = Image.fromarray(cv2.warpAffine(cv2.imdecode(np.fromfile(os.path.join(A, "판_2_원화_밝게.png"), np.uint8), 1), Ma, (ND, H), borderValue=(255, 255, 255))[:, :, ::-1]); d2 = ImageDraw.Draw(art2)
for _, m, col in 부재:
    for img, dd, u in ((art1, d1, m.vertices[:, 0] + xa), (art2, d2, m.vertices[:, 1] - D0)):
        msk = np.zeros((img.height, img.width), np.uint8); cv2.fillPoly(msk, [np.round(np.c_[u[t_], -m.vertices[t_, 2]]).astype(np.int32) for t_ in m.faces], 1)
        for cn in cv2.findContours(msk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]:
            pts = [tuple(p[0]) for p in cn]
            if len(pts) > 2: dd.line(pts + [pts[0]], fill=(255, 60, 60) if sum(col) > 400 else col, width=1)
d.text((40, 1050), "⑥ 원화 겹침 (부재 윤곽)", font=F(24), fill="black")
g1 = art1.crop((0, 80, W, 306)).resize((int(W * 1.9), int(226 * 1.9))); sheet.paste(g1, (40, 1090)); g2 = art2.crop((0, 80, ND, 306)).resize((int(ND * 1.4), int(226 * 1.4))); sheet.paste(g2, (80 + g1.width, 1090))
tx = 1700; d.text((tx, 620), "숫자 (원화 · 창 깊이 두 장 일치)", font=F(22), fill="black"); yy_ = 656
for k, v in 기록.items():
    d.text((tx, yy_), k, font=F(19), fill="black"); yy_ += 26
    for kk, vv in v.items(): d.text((tx + 20, yy_), f"{kk} = {vv}", font=F(17), fill=(40, 40, 40)); yy_ += 23
d.text((tx, yy_ + 10), "부재: " + " · ".join(dict.fromkeys(n_ for n_, _, _ in 부재)), font=F(17), fill=(40, 40, 40))
sheet.save(os.path.join(B, f"도면_머리판_v{VER}.png")); print(VER, 기록)
