# -*- coding: utf-8 -*-
"""큰 덩어리를 도형으로 (10-03 사용자 「계속 고쳐」 · 도면헐은 위에서 보면 네모 기둥 → 현업처럼 도형 블록아웃).
틀 = 도면헐과 같음: 정면 화소 · x = px − cu(오른 +) · z = −행(위 +) · 깊이 d = 눈 = 0, 앞 −. 옆 점은 C(0.987 · −22.6° · 90.8)로 옮김.
크기는 전부 원화 두 장에서(특징점 · 도면헐 실루엣) — 지어낸 숫자는 「가정」으로 표시:
  투구 = 타원체: 눈 높이 위쪽 헐의 폭 · 앞뒤 · 높이 범위
  부리 = 쐐기(볼록 껍질): 눈구멍 바깥 폭(정면) · 부리 앞끝 · 턱 끝(옆 → C)
  볼날개 = 판: 정면 볼날개 끝(좌우) · 옆 볼날개 끝 깊이
  뿔 = 원뿔: 정면 뿔 뿌리 → 끝 · 깊이는 옆 뿔 뿌리(끝 깊이 = 뿌리와 같다고 가정)
  안테나 = 가는 원뿔: 정면 뿌리 → 끝 방향(위 · 바깥) + 옆 뿌리 → 뒤(옆 그림 끝에서 잘림 · 길이 가정)
검증 = 원화 두 장 위에 이 도형의 실루엣(초록 선)을 겹쳐 그린다(도형블록아웃_겹침.png).
출력 out/오메가몬2/블렌더/도형블록아웃.ply(부품 색) · 도형블록아웃.json"""
import os, json, numpy as np, trimesh, cv2
O = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
P = json.load(open(os.path.join(O, "특징점.json"), encoding="utf-8")); f, s = P["1"], P["2"]
PAIR = os.environ.get("PAIR", "A")   # A: 정면 턱 ↔ 옆 턱(부리 아래판 끝) · B: 정면 턱 ↔ 옆 부리 앞끝(정면에서 가장 아래는 앞으로 내민 부리 끝) — 사람 결정
def 맞춤(P, pair):
    from scipy.optimize import least_squares
    f, s = P["1"], P["2"]; avg = lambda a, b: (f[a][1] + f[b][1]) / 2; 턱 = s["턱 끝"] if pair == "A" else s["부리 앞끝"]
    쌍 = [(avg("눈/왼", "눈/오른"), s["눈/오른"]), (f["뿔 뿌리"][1], s["뿔 뿌리"]), (f["턱 끝"][1], 턱), (avg("번개/왼", "번개/오른"), s["번개/오른"]), (avg("안테나 뿌리/왼", "안테나 뿌리/오른"), s["안테나 뿌리/오른"])]
    yf = np.array([a for a, _ in 쌍]); xs = np.array([b[0] for _, b in 쌍], float); ys = np.array([b[1] for _, b in 쌍], float); xm = xs.mean()
    r = lambda q: q[0] * (ys * np.cos(q[1]) + (xs - xm) * np.sin(q[1])) + q[2] - yf
    q = least_squares(r, [0.9, 0, 0], bounds=([0.3, -0.6, -500], [2, 0.6, 500])).x; return q[0], q[1], q[2], xm
k, t, c, xm = 맞춤(P, PAIR); ct, st = np.cos(t), np.sin(t); ex, ey = s["눈/오른"]
def T(p):   # 옆 화소 → (깊이 d, 정면 행)
    x, y = p; return k * ((x - ex) * ct - (y - ey) * st), k * (y * ct + (x - xm) * st) + c
m1 = np.load(os.path.join(O, "판_1_Z.npz"))["m"]; ys, xs = np.nonzero(m1); cu = (xs.min() + xs.max()) / 2
X = lambda px: px - cu; Zr = lambda row: -row
eye_row = (f["눈/왼"][1] + f["눈/오른"][1]) / 2
V = trimesh.load(os.path.join(B, f"도면헐{PAIR}.ply")).vertices      # 도면헐(x, d, z)
up = V[V[:, 2] > Zr(eye_row)]
# 투구 타원체: 눈 위 헐 범위(앞쪽은 부리가 아니라 투구 앞면까지 — 눈 앞 0 에서 자름: 가정)
x0, x1 = np.percentile(up[:, 0], [2, 98]); d0, d1 = np.percentile(up[:, 1], [2, 98]); z0, z1 = Zr(eye_row + 25), np.percentile(up[:, 2], 99)
d0 = max(d0, -30.0)
cen = np.array([(x0 + x1) / 2, (d0 + d1) / 2, (z0 + z1) / 2]); rad = np.array([(x1 - x0) / 2, (d1 - d0) / 2, (z1 - z0) / 2])
dome = trimesh.creation.icosphere(subdivisions=4); dome.vertices = dome.vertices * rad + cen
# 부리 쐐기
tip_d, tip_r = T(s["부리 앞끝"]); chin_d, chin_r = T(s["턱 끝"]); tip_r = min(tip_r, f["턱 끝"][1])   # 기울기 맞춤이 먼 점(부리 끝)을 턱보다 47 아래로 보냄 — 정면에서 턱보다 아래는 없다 → 턱 높이로 자름(애니 원근 · 과장 목록 1)
w = (f["눈구멍 바깥/오른"][0] - f["눈구멍 바깥/왼"][0]) / 2
eye_d = 0.0; xc = X((f["차양 V"][0] + f["턱 끝"][0]) / 2)
beak_pts = np.array([[xc - w, eye_d + 10, Zr(eye_row)], [xc + w, eye_d + 10, Zr(eye_row)], [xc - w * 0.8, eye_d + 40, Zr(eye_row)], [xc + w * 0.8, eye_d + 40, Zr(eye_row)],
                     [xc, tip_d, Zr(tip_r)], [xc - w * 0.35, chin_d, Zr(chin_r)], [xc + w * 0.35, chin_d, Zr(chin_r)], [xc, chin_d + 30, Zr(chin_r)],
                     [xc - w * 0.6, (tip_d + eye_d) / 2, Zr(eye_row + 15)], [xc + w * 0.6, (tip_d + eye_d) / 2, Zr(eye_row + 15)]])
beak = trimesh.convex.convex_hull(beak_pts)
# 볼날개 판(좌우)
cw_d, cw_r = T(s["볼날개 끝/오른"]); wings = []
for side in ("왼", "오른"):
    tx, ty = f[f"볼날개 끝/{side}"]; sgn = 1 if side == "오른" else -1
    pts = np.array([[xc + sgn * w * 0.7, 0, Zr(eye_row + 10)], [xc + sgn * w * 0.7, 20, Zr(eye_row + 45)], [X(tx), cw_d, Zr(ty)], [X(tx), cw_d - 8, Zr(ty) + 6]])
    pts = np.r_[pts, pts + [sgn * 6, 0, 0]]; wings.append(trimesh.convex.convex_hull(pts))
# 뿔
bx, bz = X(f["뿔 뿌리"][0]), Zr(f["뿔 뿌리"][1]); q = 1 - ((bx - cen[0]) / rad[0]) ** 2 - ((bz - cen[2]) / rad[2]) ** 2
hr_d = cen[1] - rad[1] * np.sqrt(max(q, 0.0))   # 1 판: 옆 「뿔 뿌리」 점 깊이를 쓰니 뿔이 투구 앞에 떠 있음 → 투구 타원체 앞면 위 같은 높이로(가정)
base = np.array([bx, hr_d + 8, bz]); tipH = np.array([X(f["뿔 끝"][0]), hr_d + 8, Zr(f["뿔 끝"][1])])
def 원뿔(a, b, r):
    v = b - a; L = np.linalg.norm(v); m = trimesh.creation.cone(radius=r, height=L, sections=16)
    m.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], v / L)); m.apply_translation(a); return m
horn = 원뿔(base, tipH, 16)
# 안테나: 정면은 뿌리 → 화면 가장자리 쪽 방향(위 · 바깥) · 옆은 뒤로 — 끝은 두 그림에서 잘림 → 길이 = 정면 보이는 길이(가정)
ar_d, ar_r = T(s["안테나 뿌리/오른"]); ants = []
for side, tipxy in (("왼", (25, 12)), ("오른", (243, 128))):
    rx, ry = f[f"안테나 뿌리/{side}"]; a = np.array([X(rx), ar_d, Zr(ry)]); b = np.array([X(tipxy[0]), ar_d + 110, Zr(tipxy[1])]); ants.append(원뿔(a, b, 5))
parts = {"투구": (dome, (90, 170, 90)), "부리": (beak, (230, 200, 60)), "볼날개L": (wings[0], (80, 200, 220)), "볼날개R": (wings[1], (80, 200, 220)),
         "뿔": (horn, (200, 200, 120)), "안테나L": (ants[0], (230, 140, 50)), "안테나R": (ants[1], (230, 140, 50))}
ms = []
for nm, (m, col) in parts.items():
    m = m.copy(); m.vertices = np.c_[m.vertices[:, 0], m.vertices[:, 1], m.vertices[:, 2]]; m.visual.vertex_colors = np.tile(list(col) + [255], (len(m.vertices), 1)).astype(np.uint8); ms.append(m)
all_ = trimesh.util.concatenate(ms); all_ = trimesh.Trimesh(all_.vertices, all_.faces, vertex_colors=all_.visual.vertex_colors, process=False); all_.export(os.path.join(B, f"도형블록아웃{PAIR}.ply"), encoding="ascii")   # 블렌더 4.0 이 이 바이너리 PLY 를 못 읽음(unknown error)
# 겹침 검증: 정면(x, 행) · 옆(역 C)
art1 = cv2.imdecode(np.fromfile(os.path.join(O, "판_1_원화.png"), np.uint8), 1); art2 = cv2.imdecode(np.fromfile(os.path.join(O, "판_2_원화.png"), np.uint8), 1)
art2 = cv2.convertScaleAbs(art2, alpha=2.0, beta=10)
A = np.array([[k * ct, -k * st], [k * st, k * ct]]); Ai = np.linalg.inv(A); b0 = np.array([-k * (ex * ct - ey * st), -k * xm * st + c])
def 실루엣(m, to2d, shape):
    img = np.zeros(shape[:2], np.uint8); P2 = to2d(m.vertices)
    for tri in P2[m.faces]: cv2.fillConvexPoly(img, np.round(tri).astype(np.int32), 1)
    return img
fr = 실루엣(all_, lambda v: np.c_[v[:, 0] + cu, -v[:, 2]], art1.shape)
sd = 실루엣(all_, lambda v: (Ai @ np.stack([v[:, 1] - b0[0], -v[:, 2] - b0[1]])).T, art2.shape)
out = []
for art, sil in ((art1, fr), (art2, sd)):
    a = art.copy(); cs, _ = cv2.findContours(sil, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); cv2.drawContours(a, cs, -1, (60, 255, 60), 2)
    a = cv2.resize(a, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC); out.append(a)
H = max(o.shape[0] for o in out); out = [cv2.copyMakeBorder(o, 0, H - o.shape[0], 0, 10, cv2.BORDER_CONSTANT, value=(255, 255, 255)) for o in out]
cv2.imencode(".png", np.hstack(out))[1].tofile(os.path.join(B, f"도형블록아웃{PAIR}_겹침.png"))
r = {"투구 중심 · 반지름": [cen.round(1).tolist(), rad.round(1).tolist()], "부리 앞끝 (d, 행)": [round(tip_d, 1), round(tip_r, 1)], "턱 끝": [round(chin_d, 1), round(chin_r, 1)],
     "과장 목록": ["옆 컷 부리 끝이 기울기 맞춤 뒤 턱보다 47 아래 → 턱 높이로"], "가정": ["투구 앞면을 눈 앞 30 에서 자름", "뿔 끝 깊이 = 뿌리 깊이", "안테나 뒤로 110 · 끝은 정면 보이는 끝"]}
json.dump(r, open(os.path.join(B, f"도형블록아웃{PAIR}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(r)
