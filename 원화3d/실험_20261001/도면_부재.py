# -*- coding: utf-8 -*-
"""도면 v4 — 부재 여러 개를 한 좌표계 3D 로 정하고 같이 투영 (10-04 「다음 것도 만들어 줘」).
틀: x 오른 · y 앞이 − (눈 깊이 0) · z = −행(정면 판 화소). 부재는 메시로 정하고, 도면은 그 메시를 투영 · 절단해 그린다.
  H01 돔   : 비대칭 반타원체 + 껍질 — 앞 끝은 **옆 원화 돔 칸(1)만**으로(v3 은 차양 포함 실루엣이라 앞이 나옴) · 폭 · 높이는 정면 몸통
  H01 차양 : 정면 칸 14 · 16(차양 날개) 다각형(오른쪽 반 → 거울) · 깊이 = 행마다 옆 차양 칸(6) 앞 끝 → 뒤 끝 사이 판(앞면 = 앞 끝, 뒤면 = 앞 끝 + 두께)
            두께 = 옆 차양 칸 행 폭 중앙값(원화) · 꼭짓점은 다각형 단순화(eps 1.5)라 선이 곧음
출력 out/오메가몬2/블렌더/도면_부재_v4.png · 부재_v4.ply"""
import os, json, numpy as np, cv2, trimesh, contextlib, io
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import Delaunay
A = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
K = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "기준선.py")}
with contextlib.redirect_stdout(io.StringIO()): exec(open(K["__file__"], encoding="utf-8").read(), K)
J = json.load(open(os.path.join(A, "기준선.json"), encoding="utf-8")); 층, 축 = J["층(정면 판 화소 행)"], J["정면 축(판 화소 열)"]
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
# ── H01 돔 ──
r6 = int(round(층["L6 처마"])); xs = np.nonzero(Fa[r6])[0]; a = (xs.max() - xs.min()) / 2; cxi = (xs.max() + xs.min()) / 2
top = np.nonzero(Fa[:, int(xa)])[0].min(); h = r6 - top
돔칸 = cv2.dilate((C2 == 1).astype(np.uint8), np.ones((3, 3), np.uint8)); rows = [r for r in range(top, r6 + 1) if 돔칸[r].any()]
yf = min(np.nonzero(돔칸[r])[0].min() for r in rows) + D0; yb = np.nonzero(Sa[r6])[0].max() + D0
y0 = (yf + yb) / 2; f = b = (yb - yf) / 2; t = round(0.012 * (층["L2 턱 끝"] - 층["L7 뿔 뿌리"]), 2)
기록["H01 돔"] = {"폭": round(2 * a, 1), "높이": int(h), "앞 끝(돔 칸)": int(yf), "뒤 끝": int(yb), "껍질": t}
def 돔메시(sc=1.0):
    nu, nv = 48, 16; V = []; Fc = []
    for i in range(nv + 1):
        s = i / nv; k = np.sqrt(max(0, 1 - s * s))
        for j in range(nu):
            th = 2 * np.pi * j / nu; x = a * sc * k * np.cos(th); y = (b if np.sin(th) > 0 else f) * sc * k * np.sin(th)
            V.append((cxi - xa + x + (xa - xa), y0 + y, -(r6 - s * h * sc)))
    for i in range(nv):
        for j in range(nu):
            p, q = i * nu + j, i * nu + (j + 1) % nu; Fc += [(p, q, q + nu), (p, q + nu, p + nu)]
    return trimesh.Trimesh(np.array(V) + [0, 0, 0], np.array(Fc), process=False)
돔 = 돔메시(); 돔.vertices[:, 0] += xa - xa
# ── H01 차양 날개 ──
차정 = cv2.dilate(np.isin(C1, [14, 16]).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=2); 차정[:, :int(round(xa))] = 0   # 두 날개가 가운데서 붙어 한 윤곽 → 오른쪽 반만
차옆 = cv2.dilate((C2 == 6).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=1)
cs, _ = cv2.findContours(차정, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
옆행 = {r: (np.nonzero(차옆[r])[0].min() + D0, np.nonzero(차옆[r])[0].max() + D0) for r in range(H) if 차옆[r].any()}
두께 = float(np.median([q - p for p, q in 옆행.values()])) if 옆행 else 4.0
def 옆앞(r):
    ks = np.array(sorted(옆행)); return 옆행[int(ks[np.argmin(np.abs(ks - r))])][0]
판들 = []
for c in sorted(cs, key=cv2.contourArea, reverse=True)[:2]:
    P = cv2.approxPolyDP(c, 1.5, True).reshape(-1, 2).astype(float)
    tri = Delaunay(P); fc = [tt for tt in tri.simplices if cv2.pointPolygonTest(P.astype(np.float32), tuple(P[tt].mean(0)), False) >= 0]
    # 가로로 머리를 감싸게: 가운데 깊이는 옆 원화, 좌우로 갈수록 돔 바닥 타원 곡률만큼 뒤로(f · (1 − √(1 − (x/a)²)))
    xr = np.clip(np.abs(P[:, 0] - xa) / a, 0, 0.98); yfront = np.array([옆앞(r) for r in P[:, 1]]) + f * (1 - np.sqrt(1 - xr ** 2)); n = len(P)
    V = np.r_[np.c_[P[:, 0] - xa, yfront, -P[:, 1]], np.c_[P[:, 0] - xa, yfront + min(두께, 6), -P[:, 1]]]
    Fc = [list(tt) for tt in fc] + [[tt[0] + n, tt[2] + n, tt[1] + n] for tt in fc]
    for i in range(n): j = (i + 1) % n; Fc += [[i, j, j + n], [i, j + n, i + n]]
    m = trimesh.Trimesh(V, np.array(Fc), process=False); m.fix_normals(); 판들.append(m)
    mm = m.copy(); mm.vertices[:, 0] *= -1; mm.invert(); 판들.append(mm)
    기록["H01 차양"] = {"꼭짓점(한쪽)": n, "앞면 깊이 범위": [round(float(yfront.min()), 1), round(float(yfront.max()), 1)], "두께(옆 칸 폭 · 상한 6)": round(min(두께, 6), 1)}
돔.vertices[:, 0] += 0
부재 = [("H01 돔", 돔, (40, 110, 230)), ("H01 차양", trimesh.util.concatenate(판들) if 판들 else None, (230, 120, 0))]
for _, m, col in 부재:
    if m is not None: m.visual.vertex_colors = np.tile(list(col) + [255], (len(m.vertices), 1)).astype(np.uint8)
all_ = trimesh.util.concatenate([m for _, m, _ in 부재 if m is not None]); all_.export(os.path.join(B, "부재_v4.ply"), encoding="ascii")
# ── 그리기 ──
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
sheet = Image.new("RGB", (2400, 1600), "white"); d = ImageDraw.Draw(sheet)
d.text((30, 20), "머리 도면 v4 · 부재 둘(H01 돔 · H01 차양) 한 좌표계", font=F(40), fill="black")
d.text((30, 72), "부재마다 정한 메시를 투영 · 절단 · 선 = 투영 윤곽(굵게) + 판 모서리(가늘게) · 아래 = 원화 겹침 검증", font=F(22), fill=(80, 80, 80))
def 투영그림(view, x0, y0_, w, hh, sc, 제목, 오프셋):
    d.rectangle([x0, y0_, x0 + w, y0_ + hh], outline=(200, 200, 200)); d.text((x0 + 8, y0_ + 6), 제목, font=F(22), fill="black")
    uu = np.concatenate([view(m.vertices)[0] for _, m, _ in 부재 if m is not None]); vv = np.concatenate([view(m.vertices)[1] for _, m, _ in 부재 if m is not None])
    sc = min((w - 60) / max(1e-6, np.ptp(uu)), (hh - 80) / max(1e-6, np.ptp(vv)))   # 칸에 맞춤
    ox = x0 + w / 2 - (uu.min() + uu.max()) / 2 * sc; oy = y0_ + 50 + (hh - 80) / 2 - (vv.min() + vv.max()) / 2 * sc
    for nm, m, col in 부재:
        if m is None: continue
        u, v_ = view(m.vertices); U = ox + u * sc; Vv = oy + v_ * sc
        msk = np.zeros((hh + 400, w + 400), np.uint8)
        cv2.fillPoly(msk, [np.round(np.c_[U[t_] - x0 + 200, Vv[t_] - y0_ + 200]).astype(np.int32) for t_ in m.faces], 1)
        cn, _ = cv2.findContours(msk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in cn:
            c = cv2.approxPolyDP(c, 1.2, True).reshape(-1, 2); pts = [(p[0] + x0 - 200, p[1] + y0_ - 200) for p in c]; d.line(pts + [pts[0]], fill=col, width=3)
        e = m.face_adjacency_edges[m.face_adjacency_angles > np.radians(35)] if (len(m.faces) < 5000 and nm != "H01 돔") else []
        for p, q in e: d.line([(U[p], Vv[p]), (U[q], Vv[q])], fill=tuple(int(cc * 0.6 + 100) for cc in col), width=1)
정 = lambda v: (v[:, 0], v[:, 2] * -1); 옆 = lambda v: (v[:, 1], v[:, 2] * -1); 위 = lambda v: (v[:, 0], v[:, 1])
투영그림(정, 40, 120, 560, 420, 2.2, "① 정면", (280, -100 * 2.2 - 0 + 40 - 2.2 * 60 + 60))
투영그림(옆, 640, 120, 620, 420, 2.0, "② 옆 (왼쪽 = 앞)", (330, -2.0 * 60 + 20))
투영그림(위, 1300, 120, 520, 420, 1.8, "③ 평면 (위 = 앞)", (260, 230))
# 단면
def 자르기(m, z):
    T = m.triangles; dz = T[:, :, 2] - z; out = []
    for tri, dd in zip(T, dz):
        if dd.min() > 0 or dd.max() < 0: continue
        pts = [p + (q - p) * dp / (dp - dq) for p, q, dp, dq in ((tri[0], tri[1], dd[0], dd[1]), (tri[1], tri[2], dd[1], dd[2]), (tri[2], tri[0], dd[2], dd[0])) if dp * dq < 0]
        if len(pts) == 2: out.append(np.array(pts)[:, :2])
    return out
d.text((40, 570), "④ 단면 (한 몸을 같은 높이에서 자름)", font=F(24), fill="black")
for i, (nm, r) in enumerate((("L7 뿔 뿌리", 층["L7 뿔 뿌리"]), ("L6 처마", 층["L6 처마"] - 1), ("차양 가운데", float(-np.mean(부재[1][1].vertices[:, 2])) if 부재[1][1] is not None else 190.0))):
    x0 = 40 + i * 440; d.rectangle([x0, 610, x0 + 420, 610 + 400], outline=(200, 200, 200)); d.text((x0 + 8, 616), f"{nm} (행 {r:.0f})", font=F(20), fill="black")
    for _, m, col in 부재:
        if m is None: continue
        for s in 자르기(m, -r): d.line([(x0 + 210 + s[0][0] * 1.8, 610 + 230 + s[0][1] * 1.8), (x0 + 210 + s[1][0] * 1.8, 610 + 230 + s[1][1] * 1.8)], fill=col, width=2)
    d.text((x0 + 200, 640), "앞", font=F(16), fill=(0, 0, 200))
# 3/4
yaw, pit = np.radians(-35), np.radians(20); Rz = np.array([[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]]); Rx = np.array([[1, 0, 0], [0, np.cos(pit), -np.sin(pit)], [0, np.sin(pit), np.cos(pit)]])
def 삼사(v): w_ = v @ Rz.T @ Rx.T; return w_[:, 0], -w_[:, 2]
투영그림(삼사, 1360, 610, 460, 400, 1.8, "⑤ 3/4 (yaw -35° · pitch 20°)", (230, 330 - 1.8 * 0 - 1.8 * 200 + 200))
# 원화 겹침
art1 = Image.open(os.path.join(A, "판_1_원화.png")).convert("RGB"); d1 = ImageDraw.Draw(art1)
art2 = Image.fromarray(cv2.warpAffine(cv2.imdecode(np.fromfile(os.path.join(A, "판_2_원화_밝게.png"), np.uint8), 1), Ma, (ND, H), borderValue=(255, 255, 255))[:, :, ::-1]); d2 = ImageDraw.Draw(art2)
for _, m, col in 부재:
    if m is None: continue
    for img, dd, u in ((art1, d1, m.vertices[:, 0] + xa), (art2, d2, m.vertices[:, 1] - D0)):
        msk = np.zeros((img.height, img.width), np.uint8); cv2.fillPoly(msk, [np.round(np.c_[u[t_], -m.vertices[t_, 2]]).astype(np.int32) for t_ in m.faces], 1)
        for c in cv2.findContours(msk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]:
            pts = [tuple(p[0]) for p in c]; dd.line(pts + [pts[0]], fill=col, width=2)
d.text((40, 1040), "⑥ 검증: 부재 윤곽을 원화 위에 (파랑 = 돔 · 주황 = 차양)", font=F(24), fill="black")
g1 = art1.crop((0, 60, W, 240)).resize((int(W * 2.0), 360)); sheet.paste(g1, (40, 1080)); g2 = art2.crop((0, 60, ND, 240)).resize((int(ND * 1.5), 270)); sheet.paste(g2, (80 + g1.width, 1080))
d.text((1880, 120), "숫자 (원화)", font=F(24), fill="black"); yy_ = 160
for k, v in 기록.items():
    d.text((1880, yy_), k, font=F(20), fill="black"); yy_ += 28
    for kk, vv in v.items(): d.text((1900, yy_), f"{kk} = {vv}", font=F(17), fill=(40, 40, 40)); yy_ += 24
sheet.save(os.path.join(B, "도면_부재_v4.png")); print(기록)
