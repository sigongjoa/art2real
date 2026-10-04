# -*- coding: utf-8 -*-
"""B 계속 — 저폴리 부리 판 셋(코판 · 미늘2 · 턱판) (10-04 사용자 「니가 알아서」 → B 로 계속).
판 하나 = 정면 먹선 칸 묶음의 윤곽 다각형 + 가운데 능선 4 점. 깊이는 전부 잰 값:
  능선 = 옆 단면(옆 원화 앞 윤곽 · B 맞춤)
  윤곽 꼭짓점 = 코판: 창 입구 −17.2(창깊이) · 미늘2 · 턱판: 옆 원화의 같은 판 칸의 「뒤 끝」(그 높이에서 가장 뒤) — 옆에서 보이는 판 옆면이 끝나는 곳
칸 묶음(Claude 가 칸번호 그림에서 · 사람 확인 전): 정면 코판 25 · 26 / 미늘2 28~35 · 37 / 턱판 36 · 38~42 · 옆 코판 5 / 미늘2 14 · 15 · 16 / 턱판 20
v2(같은 날): 능선 깊이 = 그 판 옆 칸의 앞 끝(전체 실루엣 대신 · 판마다 기울기) · 능선 위끝 · 아래끝을 윤곽 끝까지(0 · 1) · 판 사이 이음 = 아래 판 꼭짓점이 위 판 꼭짓점 2.5 화소 안이면 그 위치 · 깊이로 붙임
v3(같은 날): 칸 마스크를 먹선 반 폭만큼 넓혀 판 경계를 먹선 가운데로 · 이음 거리 5 · 면 방향을 앞으로 고정
v5(같은 날 · 사용자 「위 머리를 저폴리로」): 이마판(정면 칸 14 · 16 · 두 눈 사이 · 코 능선이 위로 이어짐) — 윤곽 = 창 입구 −17 · 능선 = 옆 칸 5(코판 · 같은 능선) 앞 끝 · 위 판부터 지어 아래 판이 붙음
v8: 이마판 뺌(v4 로) + 옆판(옆 원화 칸 20 · 14~16 다각형 → x = 정면 부리 판 반폭)
출력 out/오메가몬2/블렌더/저폴리부리.ply · 저폴리부리_목록.png · 저폴리부리_비교.png(렌더는 win3)"""
import os, json, numpy as np, cv2, trimesh
from scipy.spatial import Delaunay
A = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
K = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "기준선.py")}; exec(open(K["__file__"], encoding="utf-8").read(), K); T = K["T"]
기준 = json.load(open(os.path.join(A, "기준선.json"), encoding="utf-8")); xa = 기준["정면 축(판 화소 열)"]["A 중심"]
깊 = json.load(open(os.path.join(A, "창깊이.json"), encoding="utf-8")); D = round((깊["창 깊이(옆 · 입구 → 눈)"] + 깊["창 깊이(3/4 · 옆벽 폭 / sin 35°)"]) / 2, 1)
def 칸지도(n):
    z = np.load(os.path.join(A, f"{n}.npz")); L = z["라벨"]; yy, xx = np.nonzero(L > 0); y0, x0 = yy.min(), xx.min()
    m = np.load(os.path.join(A, f"판_{n}_Z.npz"))["m"]; H, W = m.shape; py, px = np.mgrid[0:H, 0:W]
    return L[np.clip(y0 + 2 * py, 0, L.shape[0] - 1), np.clip(x0 + 2 * px, 0, L.shape[1] - 1)] * m, m
C1, m1 = 칸지도("1"); C2, m2 = 칸지도("2"); H, W = m1.shape; cu = (np.nonzero(m1)[1].min() + np.nonzero(m1)[1].max()) / 2
def 행표(mask2, 앞=True):
    ys, xs = np.nonzero(mask2); dd, rr = T(xs.astype(float), ys.astype(float)); out = {}
    for r_ in np.unique(np.round(rr).astype(int)):
        q = np.round(rr).astype(int) == r_; out[int(r_)] = float(dd[q].min() if 앞 else dd[q].max())
    return out
def 찾기(표, r):
    ks = np.array(sorted(표)); return 표[int(ks[np.argmin(np.abs(ks - r))])]
단면 = 행표(m2, True)
판정의 = {"코판": ([25, 26], [5], (236, 238, 246)), "미늘2": ([28, 29, 30, 31, 32, 33, 34, 35, 37], [14, 15, 16], (222, 226, 238)), "턱판": ([36, 38, 39, 40, 41, 42], [20], (208, 214, 230))}
meshes = []; 목록 = {}; 점그림 = []; 합 = np.zeros_like(m1, np.uint8)
for 이름, (fc, sc_, col) in 판정의.items():
    mk = cv2.morphologyEx(np.isin(C1, fc).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    mk = cv2.dilate(mk, np.ones((3, 3), np.uint8), iterations=2); 합 |= mk   # v3: 판 경계를 먹선 가운데로(먹선 폭 2~3 의 반씩)
    cs, _ = cv2.findContours(mk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); poly = cv2.approxPolyDP(max(cs, key=cv2.contourArea), 2.0, True).reshape(-1, 2).astype(float)
    mir = poly.copy(); mir[:, 0] = 2 * xa - mir[:, 0]; 짝 = [np.argmin(((mir - p) ** 2).sum(1)) for p in poly]
    sym = np.array([[(p[0] + (2 * xa - poly[j][0])) / 2, (p[1] + poly[j][1]) / 2] for p, j in zip(poly, 짝)])
    top, bot = sym[:, 1].min(), sym[:, 1].max(); 능선 = np.array([(xa, top + (bot - top) * f_) for f_ in (0.0, 0.33, 0.67, 1.0)])
    if 이름 in ("코판", "이마판"):   # v7: 눈구멍 옆 윤곽 = 옆 원화 눈구멍(칸 4 · 10) 앞 모서리(안쪽 테 · 축 B) ~ 뒤 모서리(바깥 테 · 축 C)를 정면 x 로 이음 · 눈구멍 높이 밖은 창 입구 −17
        구앞, 구뒤 = 행표(np.isin(C2, [4, 10]), True), 행표(np.isin(C2, [4, 10]), False); 구행 = (min(구앞), max(구앞))
        u = np.clip((np.abs(sym[:, 0] - xa) - 12) / (55 - 12), 0, 1)
        윤곽깊이 = np.array([찾기(구앞, r) + uu * (찾기(구뒤, r) - 찾기(구앞, r)) if 구행[0] <= r <= 구행[1] else -D for r, uu in zip(sym[:, 1], u)])
    else: 뒤 = 행표(np.isin(C2, sc_), False); 윤곽깊이 = np.array([찾기(뒤, r) for r in sym[:, 1]])
    앞칸 = 행표(np.isin(C2, sc_), True); 능깊 = [찾기(앞칸, r) for r in 능선[:, 1]]
    if 이름 == "이마판":   # v6: 옆 칸 5 는 코판이라 이마가 부리만큼 튀어나옴(v5) — 이마 능선 = 옆 원화의 직선(코판 위 앞 모서리 → 뿔 뿌리) 두 점 사이
        sp = json.load(open(os.path.join(A, "특징점.json"), encoding="utf-8"))["2"]["뿔 뿌리"]; dh, rh = T(float(sp[0]), float(sp[1]))
        r0, d0 = 능선[-1, 1], 찾기(앞칸, 능선[-1, 1]); 능깊 = [float(np.interp(r, [min(rh, r0), max(rh, r0)], [dh, d0] if rh < r0 else [d0, dh])) for r in 능선[:, 1]]
    V2 = np.r_[sym, 능선]; 깊이 = np.r_[윤곽깊이, 능깊]
    for (Vp, dp, _, _) in 점그림:   # 이음: 위 판 꼭짓점 2.5 화소 안이면 그 자리 · 깊이로
        for i in range(len(sym)):   # v4: 능선 점은 이음에서 뺀다(v3 턱판 능선이 미늘2 윤곽 −21 로 끌려 주름)
            dist = np.hypot(*(Vp - V2[i]).T); j = int(np.argmin(dist))
            if dist[j] < 5.0: V2[i] = Vp[j]; 깊이[i] = dp[j]
    tri = Delaunay(V2); inside = [t for t in tri.simplices if cv2.pointPolygonTest(sym.astype(np.float32), tuple(V2[t].mean(0)), False) >= 0 or mk[int(V2[t].mean(0)[1]), int(V2[t].mean(0)[0])]]
    me = trimesh.Trimesh(np.c_[V2[:, 0] - cu, 깊이, -V2[:, 1]], np.array(inside), process=False)
    nz = me.face_normals[:, 1] > 0; me.faces[nz] = me.faces[nz][:, ::-1]   # v3: 모든 면이 앞(−y)을 보게 · fix_normals 는 열린 판에서 일부를 뒤집었다
    me.visual.vertex_colors = np.tile(list(col) + [255], (len(V2), 1)).astype(np.uint8); meshes.append(me)
    목록[이름] = {"꼭짓점": len(V2), "면": len(inside), "윤곽 깊이 범위": [round(float(윤곽깊이.min()), 1), round(float(윤곽깊이.max()), 1)], "능선 깊이": [round(float(x), 1) for x in 깊이[len(sym):]]}
    점그림.append((V2, 깊이, len(sym), col))
# v8 옆판: 판은 앞만 보는 면이라 옆에서 종이 — 옆 원화 칸(턱 옆 20 · 미늘 옆 14~16)의 다각형을 그대로 옆벽으로.
#   꼭짓점 (깊이, 행) = 옆 칸 먹선 모서리를 T 로 · x = 그 행의 정면 부리 판 묶음 반폭(± · 좌우 대칭) — 둘 다 잰 값
반폭 = {r: (np.nonzero(합[r])[0].max() - np.nonzero(합[r])[0].min()) / 2 for r in range(H) if 합[r].any()}
for 이름, sc_, col in (("턱 옆", [20], (200, 206, 224)), ("미늘 옆", [14, 15, 16], (214, 218, 232))):   # v10(사용자 「그나마 B 가 비슷해」): 턱 옆 되살림 · 행을 정면 턱판 행 범위로 옮김
    mk2 = cv2.dilate(np.isin(C2, sc_).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=2)
    cs, _ = cv2.findContours(mk2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); pp = cv2.approxPolyDP(max(cs, key=cv2.contourArea), 2.0, True).reshape(-1, 2).astype(float)
    dd, rr = T(pp[:, 0], pp[:, 1]); Q = np.c_[dd, rr]
    if 이름 == "턱 옆":   # 옆 컷은 올려본 원근이라 아래턱이 길고 낮다 — 칸 20 의 위 · 아래 끝을 정면 턱판 위 · 아래 끝(턱 끝)에 맞춰 행만 선형으로 옮김(두 끝 = 잰 선)
        tr = [v for (V_, _, ns_, c_) in 점그림 if c_ == 판정의["턱판"][2] for v in (V_[:ns_, 1].min(), V_[:ns_, 1].max())]
        rr = tr[0] + (rr - rr.min()) / (rr.max() - rr.min()) * (tr[1] - tr[0]); Q = np.c_[dd, rr]
    tri = Delaunay(Q); inside = [t for t in tri.simplices if cv2.pointPolygonTest(Q.astype(np.float32), tuple(Q[t].mean(0)), False) >= 0]
    dr = np.array([찾기(단면, r) for r in rr]); f_ = np.clip((dd - dr) / (-D - dr), 0.15, 1)   # v10: 판이 V 단면이라 깊이 d 에서의 폭 = 반폭 × (d − 능선)/(테 − 능선) — v9 는 앞쪽까지 전체 폭이라 볼처럼 튀어나옴
    w = np.array([찾기(반폭, r) for r in rr]) * f_
    for sgn in (1, -1):
        me = trimesh.Trimesh(np.c_[xa + sgn * w - cu, dd, -rr], np.array(inside), process=False)
        bad = me.face_normals[:, 0] * sgn < 0; me.faces[bad] = me.faces[bad][:, ::-1]   # 바깥(±x)을 보게
        me.visual.vertex_colors = np.tile(list(col) + [255], (len(Q), 1)).astype(np.uint8); meshes.append(me)
    목록[이름] = {"꼭짓점": len(Q), "면": len(inside), "깊이 범위": [round(float(dd.min()), 1), round(float(dd.max()), 1)], "반폭 범위": [round(float(w.min()), 1), round(float(w.max()), 1)]}
창 = trimesh.load(os.path.join(B, "창모듈2.ply"), process=False); allm = trimesh.util.concatenate([창] + meshes)
trimesh.Trimesh(allm.vertices, allm.faces, vertex_colors=allm.visual.vertex_colors, process=False).export(os.path.join(B, "저폴리부리10" + ("A" if os.environ.get("PAIR") == "A" else "") + ".ply"), encoding="ascii")
json.dump(목록, open(os.path.join(B, "저폴리부리10" + ("A" if os.environ.get("PAIR") == "A" else "") + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(목록)
# 꼭짓점 목록 그림(정면 · 옆)
from PIL import Image, ImageDraw, ImageFont
F = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 16); Kz = 4; 색표 = [(255, 200, 0), (255, 80, 80), (80, 220, 120), (90, 160, 255)]
a = Image.open(os.path.join(A, "판_1_원화.png")).convert("RGB").crop((60, 160, 190, 301)); a = a.resize((a.width * Kz, a.height * Kz)); d1 = ImageDraw.Draw(a)
b = Image.open(os.path.join(A, "판_2_원화_밝게.png")).convert("RGB"); Ks = 2; b = b.resize((b.width * Ks, b.height * Ks)); d2 = ImageDraw.Draw(b)
k, t = K["k"], K["t"]; Ai = np.linalg.inv(np.array([[k * np.cos(t), -k * np.sin(t)], [k * np.sin(t), k * np.cos(t)]])); b0 = np.array([-k * (K["ex"] * np.cos(t) - K["ey"] * np.sin(t)), -k * K["xm"] * np.sin(t) + K["c"]])
for (V2, 깊이, ns, _), c_ in zip(점그림, 색표):
    for i, (v, dp) in enumerate(zip(V2, 깊이)):
        X_, Y_ = Kz * (v[0] - 60), Kz * (v[1] - 160); r_ = 6 if i >= ns else 4; d1.ellipse([X_ - r_, Y_ - r_, X_ + r_, Y_ + r_], fill=c_)
        sx, sy = Ai @ (np.array([dp, v[1]]) - b0); d2.ellipse([Ks * sx - r_, Ks * sy - r_, Ks * sx + r_, Ks * sy + r_], fill=c_)
b = b.crop((0, 120, 720, 600))
out = Image.new("RGB", (a.width + b.width + 20, max(a.height, b.height) + 50), "white"); out.paste(a, (0, 0)); out.paste(b, (a.width + 20, 0))
ImageDraw.Draw(out).text((8, max(a.height, b.height) + 10), "빨강 코판 · 초록 미늘2 · 파랑 턱판 — 큰 점 = 능선(옆 단면) · 작은 점 = 윤곽(코판 = 창 입구 · 아래 둘 = 옆 칸 뒤 끝) · 오른쪽 = 같은 점을 옆 원화 위에", font=F, fill="black")
out.save(os.path.join(B, "저폴리부리10" + ("A" if os.environ.get("PAIR") == "A" else "") + "_목록.png"))
