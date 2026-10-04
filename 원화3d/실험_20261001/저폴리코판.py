# -*- coding: utf-8 -*-
"""B 시험 — 저폴리 박스 모델링: 꼭짓점을 도면 선 위에 (10-04 「둘 다 테스트」 · 패널 권고 2-B).
부재 하나 = 코판(두 창 사이 · 정면 칸 25 · 26). 꼭짓점 = 원화 먹선 모서리, 깊이 = 잰 값뿐:
  정면 윤곽 꼭짓점(먹선 다각형 근사 · 판 화소) — 깊이 = 창 입구 −17.2(창깊이 · 옆 · 3/4 일치값) · 코판 테두리가 창 둘레 벽에 붙음
  가운데 능선 꼭짓점(축 A · 윤곽 위끝 ~ 아래끝 4 점) — 깊이 = 옆 단면(옆 원화 앞 윤곽 · B 맞춤)
  면 = 정면 (x, z) 들로니 삼각형 중 윤곽 안 · 좌우 대칭(중심축 기준 평균)
① 꼭짓점 목록 그림(정면 · 옆 원화 위 번호 · 깊이) = 승인용 ② 메시 → 도안 장면 렌더
출력 out/오메가몬2/블렌더/저폴리코판.ply · 저폴리코판_목록.png · 저폴리코판.json"""
import os, json, numpy as np, cv2, trimesh
from scipy.spatial import Delaunay
A = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
K = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "기준선.py")}; exec(open(K["__file__"], encoding="utf-8").read(), K); T = K["T"]
기준 = json.load(open(os.path.join(A, "기준선.json"), encoding="utf-8")); 축 = 기준["정면 축(판 화소 열)"]; xa = 축["A 중심"]
깊 = json.load(open(os.path.join(A, "창깊이.json"), encoding="utf-8")); D = round((깊["창 깊이(옆 · 입구 → 눈)"] + 깊["창 깊이(3/4 · 옆벽 폭 / sin 35°)"]) / 2, 1)
z = np.load(os.path.join(A, "1.npz")); L = z["라벨"]; yy, xx = np.nonzero(L > 0); y0, x0 = yy.min(), xx.min()
m1 = np.load(os.path.join(A, "판_1_Z.npz"))["m"]; H, W = m1.shape; py, px = np.mgrid[0:H, 0:W]
cell = L[np.clip(y0 + 2 * py, 0, L.shape[0] - 1), np.clip(x0 + 2 * px, 0, L.shape[1] - 1)] * m1
코판 = cv2.morphologyEx(np.isin(cell, [25, 26]).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
cs, _ = cv2.findContours(코판, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); poly = cv2.approxPolyDP(max(cs, key=cv2.contourArea), 2.0, True).reshape(-1, 2).astype(float)
# 좌우 대칭: 각 꼭짓점의 거울 짝과 평균(가장 가까운 거울 꼭짓점)
mir = poly.copy(); mir[:, 0] = 2 * xa - mir[:, 0]; 짝 = [np.argmin(((mir - p) ** 2).sum(1)) for p in poly]
sym = np.array([[(p[0] + (2 * xa - poly[j][0])) / 2, (p[1] + poly[j][1]) / 2] for p, j in zip(poly, 짝)])
# 옆 단면(행마다 가장 앞)
m2 = np.load(os.path.join(A, "판_2_Z.npz"))["m"]; ys2, xs2 = np.nonzero(m2); dd, rr = T(xs2.astype(float), ys2.astype(float))
단면 = {}
for r_ in range(H):
    q = np.round(rr).astype(int) == r_
    if q.any(): 단면[r_] = float(dd[q].min())
top, bot = sym[:, 1].min(), sym[:, 1].max(); 능선 = [(xa, top + (bot - top) * f_) for f_ in (0.05, 0.35, 0.65, 0.95)]
V2 = np.r_[sym, np.array(능선)]; 깊이 = np.r_[np.full(len(sym), -D), [단면.get(int(round(r)), -D) for _, r in 능선]]
tri = Delaunay(V2); inside = [t for t in tri.simplices if cv2.pointPolygonTest(sym.astype(np.float32), tuple(V2[t].mean(0)), False) >= 0]
cu = (np.nonzero(m1)[1].min() + np.nonzero(m1)[1].max()) / 2
V3 = np.c_[V2[:, 0] - cu, 깊이, -V2[:, 1]]
me = trimesh.Trimesh(V3, np.array(inside), process=False); me.fix_normals()
me.visual.vertex_colors = np.tile([236, 238, 246, 255], (len(V3), 1)).astype(np.uint8)
창 = trimesh.load(os.path.join(B, "창모듈2.ply"), process=False); allm = trimesh.util.concatenate([창, me])
trimesh.Trimesh(allm.vertices, allm.faces, vertex_colors=allm.visual.vertex_colors, process=False).export(os.path.join(B, "저폴리코판.ply"), encoding="ascii")
목록 = [{"번호": i, "정면 x": round(float(v[0]), 1), "정면 행": round(float(v[1]), 1), "깊이": round(float(d), 1), "출처": "창 입구 −17.2" if i < len(sym) else "옆 단면"} for i, (v, d) in enumerate(zip(V2, 깊이))]
json.dump({"꼭짓점": 목록, "면": len(inside)}, open(os.path.join(B, "저폴리코판.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
# ① 승인용 그림
from PIL import Image, ImageDraw, ImageFont
F = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 18); Kz = 4
a = Image.open(os.path.join(A, "판_1_원화.png")).convert("RGB").crop((60, 120, 190, 260)); a = a.resize((a.width * Kz, a.height * Kz)); d1 = ImageDraw.Draw(a)
for t_ in inside: d1.polygon([(Kz * (V2[i][0] - 60), Kz * (V2[i][1] - 120)) for i in t_], outline=(255, 230, 0))
for i, (v, dpt) in enumerate(zip(V2, 깊이)):
    X_, Y_ = Kz * (v[0] - 60), Kz * (v[1] - 120); col = (255, 80, 80) if i < len(sym) else (80, 255, 120); d1.ellipse([X_ - 6, Y_ - 6, X_ + 6, Y_ + 6], fill=col); d1.text((X_ + 7, Y_ - 9), f"{i}:{dpt:.0f}", font=F, fill=col, stroke_width=2, stroke_fill=(0, 0, 0))
b = Image.open(os.path.join(A, "판_2_원화_밝게.png")).convert("RGB"); Ks = 2; b = b.resize((b.width * Ks, b.height * Ks)); d2 = ImageDraw.Draw(b)
Ai = np.linalg.inv(np.array([[K["k"] * np.cos(K["t"]), -K["k"] * np.sin(K["t"])], [K["k"] * np.sin(K["t"]), K["k"] * np.cos(K["t"])]])); b0 = np.array([-K["k"] * (K["ex"] * np.cos(K["t"]) - K["ey"] * np.sin(K["t"])), -K["k"] * K["xm"] * np.sin(K["t"]) + K["c"]])
for i, (v, dpt) in enumerate(zip(V2, 깊이)):
    sx, sy = Ai @ (np.array([dpt, v[1]]) - b0); col = (255, 80, 80) if i < len(sym) else (80, 255, 120); d2.ellipse([Ks * sx - 5, Ks * sy - 5, Ks * sx + 5, Ks * sy + 5], fill=col); d2.text((Ks * sx + 6, Ks * sy - 8), str(i), font=F, fill=col, stroke_width=2, stroke_fill=(0, 0, 0))
b = b.crop((0, 0, 700, 420))
out = Image.new("RGB", (a.width + b.width + 20, max(a.height, b.height) + 60), "white"); out.paste(a, (0, 0)); out.paste(b, (a.width + 20, 0))
ImageDraw.Draw(out).text((8, max(a.height, b.height) + 10), f"코판 꼭짓점 {len(V2)} 개 · 면 {len(inside)} — 빨강 = 정면 먹선 모서리(깊이 −{D} 창 입구) · 초록 = 가운데 능선(깊이 = 옆 단면) · 오른쪽 = 같은 점을 옆 원화 위에", font=F, fill="black")
out.save(os.path.join(B, "저폴리코판_목록.png")); print({"꼭짓점": len(V2), "면": len(inside), "능선 깊이": [round(float(x), 1) for x in 깊이[len(sym):]]})
