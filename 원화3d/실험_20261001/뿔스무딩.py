# -*- coding: utf-8 -*-
"""뿔 스무딩 — 이름이 정한 꼴로 끌어당기기 (10-02 사용자 「뿔이라고 하면 뿔을 스무딩해서」 · 기준: 이름이 꼴 · 먹선이 남길 곳 · 문턱이 멈출 때).
꼴 = 마름모 단면 각뿔(지온: 각진 단면 · 곧은 축 · 좁아짐 · 뾰족 끝). 왼면 · 오른면 사이 먹선 = 앞 능선(지킴).
정면 칸 1(왼면) · 2(끝) · 3(오른면) → 뿌리 폭 · 능선 자리 · 길이 · 정면 기울기(주축) / 옆 칸 2 · 3 → 축이 뒤로 눕는 각 · 뿌리 앞뒤 두께 비율(숫자 둘)
붙는 자리 = 뿌리 가운데의 부조 앞면(이마판 · 끝-가운데). 깊이 AI 의 「뿔이 앞으로 누움」은 근거가 한 출처뿐이라 버림.
문턱(먼저 적음): 정면 윤곽 IoU ≥ 0.9 · 옆 축 각 차 ≤ 10°. 출력 out/오메가몬2/지표/부조/뿔.ply · 뿔스무딩.json"""
import os, json, numpy as np, cv2, trimesh
K = r"G:\art2real\원화3d\out\오메가몬2\지표"; O = os.path.join(K, "부조")
Lf = np.load(os.path.join(K, "선파츠_정면.npz"))["라벨"]; ys, xs = np.nonzero(Lf > 0); top, bot = ys.min(), ys.max(); k = 100 / (bot - top)
x0, y0, x1, y1 = json.load(open(os.path.join(K, "원화그림자", "그림자.json"), encoding="utf-8"))["자르기"]
def bx(px): return (px - Lf.shape[1] / 2) * k
def bz(py): return -(py - y0) * k
horn = np.isin(Lf, [1, 2, 3]); hy, hx = np.nonzero(horn)
# 정면 주축(뿌리 → 끝): 픽셀 PCA
P = np.c_[hx, hy].astype(float); c0 = P.mean(0); ax = np.linalg.svd(P - c0, full_matrices=False)[2][0]; ax = ax if ax[1] < 0 else -ax   # 위쪽(끝) 방향
t = (P - c0) @ ax; tip2 = c0 + ax * t.max(); root2 = c0 + ax * t.min()
perp = np.array([-ax[1], ax[0]])
def 폭(tt, band=4):
    m = np.abs(t - tt) < band; s = (P[m] - c0) @ perp; return (s.min(), s.max()) if m.sum() > 3 else (0, 0)
ts = np.arange(t.min() + 2, t.max() - 2, 1.0); ws = [np.subtract(*폭(q)[::-1]) for q in ts]
t_root = float(ts[int(np.argmax(ws))]); root2 = c0 + ax * t_root                      # 뿌리 = 단면 폭이 가장 넓은 자리(맨 아래 끝은 이마로 좁아지는 꼬리)
w_lo, w_hi = 폭(t_root)
# 앞 능선: 칸 1(왼면)과 3(오른면) 경계(먹선) — 뿌리 쪽 능선 자리
L13 = (cv2.dilate((Lf == 1).astype(np.uint8), np.ones((5, 5))) > 0) & (cv2.dilate((Lf == 3).astype(np.uint8), np.ones((5, 5))) > 0)
ry, rx = np.nonzero(L13); ridge_s = float(np.median((np.c_[rx, ry] - c0) @ perp)) if len(rx) else (w_lo + w_hi) / 2
# 옆: 축 각 · 두께 비율
Ls = np.load(os.path.join(K, "선파츠_옆.npz"))["라벨"]; sy, sx = np.nonzero(np.isin(Ls, [2, 3])); S = np.c_[sx, sy].astype(float); sc0 = S.mean(0)
sax = np.linalg.svd(S - sc0, full_matrices=False)[2][0]; sax = sax if sax[1] < 0 else -sax
옆각 = float(np.degrees(np.arctan2(sax[0], -sax[1])))                                # 수직에서 기운 각(+ = 그림 오른쪽 = 뒤 · 옆 원화는 얼굴이 왼쪽)
st = (S - sc0) @ sax; sperp = np.array([-sax[1], sax[0]]); sm = np.abs(st - (st.min() + 6)) < 4; 옆두께 = float(np.ptp((S[sm] - sc0) @ sperp))
sm2 = np.abs(t - t_root) < 4; 정면폭 = float(np.ptp((P[sm2] - c0) @ perp)); 두께비 = 옆두께 / max(정면폭, 1e-6)
# 3D 꼴: 블렌더 좌표(x 오른 · −y 앞 · z 위) · 단위 = 머리 단위
rel = trimesh.load(os.path.join(O, "부조_뿔뺌.ply"), process=False); V = rel.vertices
root_x, root_z = bx(root2[0]), bz(root2[1]); near = np.hypot(V[:, 0] - root_x, V[:, 2] - root_z) < 4; root_y = float(np.percentile(V[near, 1], 20)) if near.any() else 0.0   # 이마판 앞면
L_ = float(np.hypot(*(tip2 - root2))) * k
fdir = np.array([ax[0], 0.0, -ax[1]]); fdir /= np.linalg.norm(fdir)                   # 정면 기울기(x, z)
back = np.radians(옆각); d = fdir * np.cos(back) + np.array([0, 1.0, 0]) * np.sin(back); d /= np.linalg.norm(d)   # +y = 뒤
side = np.cross(d, [0, -1.0, 0]); side /= np.linalg.norm(side); fwd = np.cross(side, d)   # fwd ≈ −y(앞)
tt_ = np.array([q for q in ts if q >= t_root]); ww_ = np.array([np.subtract(*폭(q)[::-1]) for q in tt_])
slope = float(np.sum(ww_ * (t.max() - tt_)) / np.sum((t.max() - tt_) ** 2))         # 끝에서 0 인 직선 w = slope · (끝 − t) 최소제곱
W = slope * (t.max() - t_root) * k; Dp = W * 두께비; r_off = (ridge_s - (w_lo + w_hi) / 2) * k
base = np.array([root_x, root_y + Dp * 0.35, root_z])
quad = [base - side * W / 2, base + side * r_off + fwd * Dp * 0.35, base + side * W / 2, base - fwd * Dp * 0.65]   # 왼 · 앞 능선 · 오른 · 뒤
tip = base + d * L_
v = np.array(quad + [tip]); f = np.array([[0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4], [0, 3, 2], [0, 2, 1]])
m = trimesh.Trimesh(v, f); m.fix_normals()
# 남은 차이 = 뿌리 아래 둥근 판(먹선이 둘러쌈 → 디테일) → 작은 꼴 하나: 그 윤곽을 뿌리 깊이에서 앞뒤 두께 Dp 로 민 판
below = horn & (((np.c_[np.nonzero(horn)[1], np.nonzero(horn)[0]] - c0) @ ax <= t_root + 2).reshape(-1) if False else horn)
hy2, hx2 = np.nonzero(horn); tt2 = (np.c_[hx2, hy2] - c0) @ ax; mk = np.zeros(Lf.shape, np.uint8); mk[hy2[tt2 <= t_root + 2], hx2[tt2 <= t_root + 2]] = 1
cs, _ = cv2.findContours(mk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
if cs:
    cc = max(cs, key=cv2.contourArea).reshape(-1, 2); poly = np.c_[bx(cc[:, 0]), bz(cc[:, 1])]
    pl = trimesh.creation.extrude_polygon(__import__("shapely.geometry", fromlist=["Polygon"]).Polygon(poly).buffer(0), Dp)   # x-y 평면 윤곽을 z 로 민다
    pl.vertices = np.c_[pl.vertices[:, 0], root_y - Dp * 0.35 + pl.vertices[:, 2], pl.vertices[:, 1]]                       # (x, z) 윤곽 · 앞뒤 = y
    pl.fix_normals(); m = trimesh.util.concatenate([m, pl])
m.visual.vertex_colors = np.tile([215, 220, 235, 255], (len(m.vertices), 1)); m.export(os.path.join(O, "뿔.ply"))
# 채점: 정면 윤곽(투영) vs 원화 뿔 칸 · 옆 축 각
def 투영(mesh):
    img = np.zeros(Lf.shape, np.uint8); pts = mesh.vertices; px = pts[:, 0] / k + Lf.shape[1] / 2; py = -pts[:, 2] / k + y0
    for t_ in np.c_[px, py].astype(np.int32)[mesh.faces]: cv2.fillConvexPoly(img, t_, 1)   # 한꺼번에 fillPoly 는 겹친 삼각형을 홀짝으로 지움
    return img > 0
pm = 투영(m); iou = float((pm & horn).sum() / (pm | horn).sum())
옆각_우리 = float(np.degrees(np.arctan2(d[1], d[2])))
결과 = {"꼴": "마름모 단면 각뿔 + 뿌리 판(디테일 1)", "뿌리폭": round(W, 1), "길이": round(L_, 1), "앞뒤두께비(옆)": round(두께비, 2), "능선자리(폭 가운데에서)": round(r_off, 1),
        "옆축각_원화": round(옆각, 1), "옆축각_우리": round(옆각_우리, 1), "정면윤곽IoU": round(iou, 3), "통과": bool(iou >= 0.9 and abs(옆각 - 옆각_우리) <= 10)}
json.dump(결과, open(os.path.join(O, "뿔스무딩.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(결과)
