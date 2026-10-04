# -*- coding: utf-8 -*-
"""B 계속 — 저폴리 부리 판 셋(코판 · 미늘2 · 턱판) (10-04 사용자 「니가 알아서」 → B 로 계속).
판 하나 = 정면 먹선 칸 묶음의 윤곽 다각형 + 가운데 능선 4 점. 깊이는 전부 잰 값:
  능선 = 옆 단면(옆 원화 앞 윤곽 · B 맞춤)
  윤곽 꼭짓점 = 코판: 창 입구 −17.2(창깊이) · 미늘2 · 턱판: 옆 원화의 같은 판 칸의 「뒤 끝」(그 높이에서 가장 뒤) — 옆에서 보이는 판 옆면이 끝나는 곳
칸 묶음(Claude 가 칸번호 그림에서 · 사람 확인 전): 정면 코판 25 · 26 / 미늘2 28~35 · 37 / 턱판 36 · 38~42 · 옆 코판 5 / 미늘2 14 · 15 · 16 / 턱판 20
v2(같은 날): 능선 깊이 = 그 판 옆 칸의 앞 끝(전체 실루엣 대신 · 판마다 기울기) · 능선 위끝 · 아래끝을 윤곽 끝까지(0 · 1) · 판 사이 이음 = 아래 판 꼭짓점이 위 판 꼭짓점 2.5 화소 안이면 그 위치 · 깊이로 붙임
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
meshes = []; 목록 = {}; 점그림 = []
for 이름, (fc, sc_, col) in 판정의.items():
    mk = cv2.morphologyEx(np.isin(C1, fc).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    cs, _ = cv2.findContours(mk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); poly = cv2.approxPolyDP(max(cs, key=cv2.contourArea), 2.0, True).reshape(-1, 2).astype(float)
    mir = poly.copy(); mir[:, 0] = 2 * xa - mir[:, 0]; 짝 = [np.argmin(((mir - p) ** 2).sum(1)) for p in poly]
    sym = np.array([[(p[0] + (2 * xa - poly[j][0])) / 2, (p[1] + poly[j][1]) / 2] for p, j in zip(poly, 짝)])
    top, bot = sym[:, 1].min(), sym[:, 1].max(); 능선 = np.array([(xa, top + (bot - top) * f_) for f_ in (0.0, 0.33, 0.67, 1.0)])
    if 이름 == "코판": 윤곽깊이 = np.full(len(sym), -D)
    else: 뒤 = 행표(np.isin(C2, sc_), False); 윤곽깊이 = np.array([찾기(뒤, r) for r in sym[:, 1]])
    앞칸 = 행표(np.isin(C2, sc_), True); 능깊 = [찾기(앞칸, r) for r in 능선[:, 1]]
    V2 = np.r_[sym, 능선]; 깊이 = np.r_[윤곽깊이, 능깊]
    for (Vp, dp, _, _) in 점그림:   # 이음: 위 판 꼭짓점 2.5 화소 안이면 그 자리 · 깊이로
        for i in range(len(V2)):
            dist = np.hypot(*(Vp - V2[i]).T); j = int(np.argmin(dist))
            if dist[j] < 2.5: V2[i] = Vp[j]; 깊이[i] = dp[j]
    tri = Delaunay(V2); inside = [t for t in tri.simplices if cv2.pointPolygonTest(sym.astype(np.float32), tuple(V2[t].mean(0)), False) >= 0]
    me = trimesh.Trimesh(np.c_[V2[:, 0] - cu, 깊이, -V2[:, 1]], np.array(inside), process=False); me.fix_normals()
    me.visual.vertex_colors = np.tile(list(col) + [255], (len(V2), 1)).astype(np.uint8); meshes.append(me)
    목록[이름] = {"꼭짓점": len(V2), "면": len(inside), "윤곽 깊이 범위": [round(float(윤곽깊이.min()), 1), round(float(윤곽깊이.max()), 1)], "능선 깊이": [round(float(x), 1) for x in 깊이[len(sym):]]}
    점그림.append((V2, 깊이, len(sym), col))
창 = trimesh.load(os.path.join(B, "창모듈2.ply"), process=False); allm = trimesh.util.concatenate([창] + meshes)
trimesh.Trimesh(allm.vertices, allm.faces, vertex_colors=allm.visual.vertex_colors, process=False).export(os.path.join(B, "저폴리부리2.ply"), encoding="ascii")
json.dump(목록, open(os.path.join(B, "저폴리부리2.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(목록)
# 꼭짓점 목록 그림(정면 · 옆)
from PIL import Image, ImageDraw, ImageFont
F = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 16); Kz = 4; 색표 = [(255, 80, 80), (80, 220, 120), (90, 160, 255)]
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
out.save(os.path.join(B, "저폴리부리2_목록.png"))
