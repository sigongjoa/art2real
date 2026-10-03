# -*- coding: utf-8 -*-
"""블록아웃 B 위에 디테일 1 판 (10-03 사용자 「지금 원형만 한 거지 디테일 작업도 해 줘」).
머리 시작 카드대로 겹: 속머리(검정 · 눈이 달림) → 마스크(흰 · 미늘 3 장 계단) → 투구(흰 · 차양이 마스크 윗변을 덮음).
자리 · 크기는 정면 특징점(눈 · 눈구멍 안/바깥 · 차양 V/날개 · 번개)과 블록아웃 B 의 투구 타원체 겉면에서. 지어낸 값은 「가정」으로:
  눈구멍 = 검은 마름모 판(안 · 바깥 점 + 위아래 ±14 가정) · 눈 = 파란 원판(반지름 9 가정)
  차양 = 눈썹 날개 판 둘(V → 날개 끝 · 높이 16 · 투구 겉면보다 10 앞으로 = 처마 · 가정)
  마스크 = 부리 쐐기를 높이로 세 칸(미늘1 코판 · 미늘2 · 미늘3) · 아래 칸일수록 6 씩 뒤로(계단 · 가정)
  번개 = 투구 겉면 위 지그재그 판(파랑 · 높이 34 가정)
출력 out/오메가몬2/블렌더/디테일1.ply(색) · 디테일1_겹침.png"""
import os, json, numpy as np, trimesh, cv2
os.environ["PAIR"] = "B"
G = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "도형블록아웃.py")}
exec(open(G["__file__"], encoding="utf-8").read(), G)          # 블록아웃 B 의 cen · rad · beak · horn · ants · wings · f · s · X · Zr · T · 등
cen, rad, f, X, Zr, beak, B = G["cen"], G["rad"], G["f"], G["X"], G["Zr"], G["beak"], G["B"]
흰, 회, 검, 파, 금 = (225, 228, 238), (180, 184, 196), (25, 25, 32), (60, 120, 230), (210, 175, 60)
def 겉깊이(x, z, 앞=0.0):
    q = 1 - ((x - cen[0]) / rad[0]) ** 2 - ((z - cen[2]) / rad[2]) ** 2; return cen[1] - rad[1] * np.sqrt(max(q, 0.02)) - 앞
def 판(pts2, 두께, 앞, col, 겉=True):   # 정면 (x, 행) 다각형 → 투구 겉면에 붙인 얇은 판
    P = [];
    for x, r in pts2:
        d = 겉깊이(X(x), Zr(r), 앞) if 겉 else 앞; P += [[X(x), d, Zr(r)], [X(x), d + 두께, Zr(r)]]
    m = trimesh.convex.convex_hull(np.array(P)); m.visual.vertex_colors = np.tile(list(col) + [255], (len(m.vertices), 1)).astype(np.uint8); return m
parts = []
# 투구 · 뿔 · 안테나 · 볼날개는 블록아웃 그대로(색만)
# 2 판(눈으로 봄): 투구 타원체가 눈 높이 아래까지 내려와 얼굴을 덮음 · 눈구멍이 투구 속에 묻힘 → 카드대로 겹을 나눔
#   투구는 차양 아랫선에서 자르고(위만 남김) · 그 아래는 속머리(검정 타원체 · 투구보다 작음 · 가정 0.8)가 보이고 · 눈은 속머리 앞면에
zc = Zr(f["차양 V"][1] + 4); G["dome"] = G["dome"].slice_plane([0, 0, zc], [0, 0, 1], cap=True)
inner = trimesh.creation.icosphere(subdivisions=4); ic, ir = cen + np.array([0, 8, -30]), rad * np.array([0.78, 0.82, 0.8]); inner.vertices = inner.vertices * ir + ic
inner.visual.vertex_colors = np.tile(list(검) + [255], (len(inner.vertices), 1)).astype(np.uint8); parts.append(inner)
def 속깊이(x, z):
    q = 1 - ((x - ic[0]) / ir[0]) ** 2 - ((z - ic[2]) / ir[2]) ** 2; return ic[1] - ir[1] * np.sqrt(max(q, 0.02))
for nm, col in (("dome", 흰), ("horn", 회), ("wings", 흰)):
    ms = G[nm] if isinstance(G[nm], list) else [G[nm]]
    for m in ms: m = m.copy(); m.visual.vertex_colors = np.tile(list(col) + [255], (len(m.vertices), 1)).astype(np.uint8); parts.append(m)
for m in G["ants"]: m = m.copy(); m.visual.vertex_colors = np.tile(list(금) + [255], (len(m.vertices), 1)).astype(np.uint8); parts.append(m)
# 마스크 세 칸 계단
zt, zb = beak.bounds[0][2], beak.bounds[1][2]; cuts = np.linspace(zb, zt, 4)
for i in range(3):
    m = beak.slice_plane([0, 0, cuts[i + 1]], [0, 0, 1], cap=True).slice_plane([0, 0, cuts[i]], [0, 0, -1], cap=True)
    if len(m.faces) == 0: continue
    m.apply_translation([0, 6 * (2 - i), 0]); m.visual.vertex_colors = np.tile(list(흰 if i % 2 == 0 else 회) + [255], (len(m.vertices), 1)).astype(np.uint8); parts.append(m)
# 눈구멍 · 눈
for side in ("왼", "오른"):
    ai, ao = f[f"눈구멍 안/{side}"], f[f"눈구멍 바깥/{side}"]; mx, mr = (ai[0] + ao[0]) / 2, (ai[1] + ao[1]) / 2
    ex_, er_ = f[f"눈/{side}"]; d = 속깊이(X(ex_), Zr(er_)) - 2
    eye = trimesh.creation.cylinder(radius=11, height=2, sections=24); eye.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])); eye.apply_translation([X(ex_), d, Zr(er_)])
    eye.visual.vertex_colors = np.tile(list(파) + [255], (len(eye.vertices), 1)).astype(np.uint8); parts.append(eye)
# 차양 날개(처마)
V = f["차양 V"]
for side in ("왼", "오른"):
    w = f[f"차양 날개/{side}"]; parts.append(판([V, w, (w[0], w[1] - 18), (V[0], V[1] - 12)], 8, 12, 흰))
# 번개 무늬(지그재그)
for side in ("왼", "오른"):
    bx, br = f[f"번개/{side}"]; sg = 1 if side == "오른" else -1
    zig = [(a * 1.7, b * 1.7) for a, b in [(0, -17), (6 * sg, -3), (1 * sg, -3), (7 * sg, 17), (-2 * sg, 1), (3 * sg, 1)]]
    parts.append(판([(bx + a, br + b) for a, b in zig], 1.5, 1, 파))
all_ = trimesh.util.concatenate(parts); all_ = trimesh.Trimesh(all_.vertices, all_.faces, vertex_colors=all_.visual.vertex_colors, process=False)
all_.export(os.path.join(B, "디테일1.ply"), encoding="ascii")
# 겹침(정면 원화 위 · 블록아웃과 같은 식)
art1 = cv2.imdecode(np.fromfile(os.path.join(G["O"], "판_1_원화.png"), np.uint8), 1); cu = G["cu"]
sil = np.zeros(art1.shape[:2], np.uint8)
for m in parts:
    for tri in np.c_[m.vertices[:, 0] + cu, -m.vertices[:, 2]][m.faces]: cv2.fillConvexPoly(sil, np.round(tri).astype(np.int32), 1)
cs, _ = cv2.findContours(sil, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE); a = art1.copy(); cv2.drawContours(a, cs, -1, (60, 255, 60), 1)
cv2.imencode(".png", cv2.resize(a, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC))[1].tofile(os.path.join(B, "디테일1_겹침.png")); print("ok", len(parts))
