# -*- coding: utf-8 -*-
"""분할 데이터로 부리 판 짓기 (10-03 사용자 「분할 데이터는 참고해야지?」).
부리학습은 판 모양을 정면 칸 하나로만 정하고 옆 칸은 점수에만 썼다 → 옆 분할의 모양이 판에 안 들어감.
이번엔 판마다 두 장의 분할을 다 모양으로: 판 = {정면 칸 안} ∩ {옆 칸 안}(같은 이름 · 옆 카메라 = 블록아웃 B 맞춤 0.745 · −22.3°).
부품헐(10-02 실패)과 다른 점: 그때는 장끼리 크기 · 높이를 부품마다 억지로 늘렸다 → 지금은 다섯 점으로 맞춘 카메라 하나를 모든 판이 같이 씀.
단계 그림: ① 정면 칸 ② 옆 칸 ③ 두 칸의 교집합 판(정면 · 옆 · 3/4 · 위 렌더)."""
import os, json, numpy as np, cv2, trimesh
from skimage import measure
os.environ["PAIR"] = "B"
G = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "도형블록아웃.py")}
exec(open(G["__file__"], encoding="utf-8").read(), G)
O, B, cu = G["O"], G["B"], G["cu"]; k, t_, c_, xm, ex, ey = G["k"], G["t"], G["c"], G["xm"], G["ex"], G["ey"]
ct, st = np.cos(t_), np.sin(t_); Ai = np.linalg.inv(np.array([[k * ct, -k * st], [k * st, k * ct]])); b0 = np.array([-k * (ex * ct - ey * st), -k * xm * st + c_])
대응 = json.load(open(os.path.join(O, "부품ID.json"), encoding="utf-8"))["대응표"]
def 칸지도(n):
    z = np.load(os.path.join(O, f"{n}.npz")); L = z["라벨"]; ys, xs = np.nonzero(L > 0); y0, x0_ = ys.min(), xs.min()
    m = np.load(os.path.join(O, f"판_{n}_Z.npz"))["m"]; H, W = m.shape; py, px = np.mgrid[0:H, 0:W]
    return L[np.clip(y0 + 2 * py, 0, L.shape[0] - 1), np.clip(x0_ + 2 * px, 0, L.shape[1] - 1)] * m
def 표면칸(n, 표면):
    cs = [c for e in 대응[n] if e.get("부품") == "H02 마스크" and e.get("표면") == 표면 for c in e["칸"]]; return np.isin(칸지도(n), cs)
판들 = {"코판": (230, 70, 70), "미늘2": (70, 200, 70), "턱판": (70, 110, 230)}
st_ = 1.0; xs = np.arange(-130, 130, st_); ds = np.arange(-160, 120, st_); zs = np.arange(-320, -150, st_)
GX, GD, GZ = np.meshgrid(xs, ds, zs, indexing="ij")
fx = np.round(GX + cu).astype(int); fy = np.round(-GZ).astype(int)
sxy = np.einsum("ij,j...->i...", Ai, np.stack([GD - b0[0], -GZ - b0[1]])); sx, sy = np.round(sxy[0]).astype(int), np.round(sxy[1]).astype(int)
meshes = []; 결과 = {}
for p, col in 판들.items():
    F = 표면칸("1", p); S = cv2.dilate(표면칸("2", p).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    ok1 = (fx >= 0) & (fx < F.shape[1]) & (fy >= 0) & (fy < F.shape[0]); ok2 = (sx >= 0) & (sx < S.shape[1]) & (sy >= 0) & (sy < S.shape[0])
    V = np.zeros(GX.shape, bool); V[ok1 & ok2] = F[fy[ok1 & ok2], fx[ok1 & ok2]] & S[sy[ok1 & ok2], sx[ok1 & ok2]]
    결과[p] = {"복셀": int(V.sum())}
    if V.sum() < 30: continue
    vt, fc, _, _ = measure.marching_cubes(np.pad(V, 1).astype(np.float32), 0.5); vt = (vt - 1) * st_ + np.array([xs[0], ds[0], zs[0]])
    m = trimesh.Trimesh(vt, fc); trimesh.smoothing.filter_taubin(m, iterations=4); m.visual.vertex_colors = np.tile(list(col) + [255], (len(m.vertices), 1)).astype(np.uint8); meshes.append(m)
    결과[p]["깊이 범위"] = [round(float(vt[:, 1].min()), 1), round(float(vt[:, 1].max()), 1)]
# 바탕(디테일 1 판의 투구 · 속머리 · 뿔 · 안테나 · 눈)은 회색으로 같이
D = trimesh.load(os.path.join(B, "디테일1.ply"), process=False)
D.visual.vertex_colors = np.tile([150, 150, 160, 255], (len(D.vertices), 1)).astype(np.uint8)
allm = trimesh.util.concatenate(meshes + [D]); allm = trimesh.Trimesh(allm.vertices, allm.faces, vertex_colors=allm.visual.vertex_colors, process=False)
allm.export(os.path.join(B, "부리판헐.ply"), encoding="ascii")
# 단계 ①②: 두 장 분할 위 판 칸
a1 = cv2.imdecode(np.fromfile(os.path.join(O, "판_1_원화.png"), np.uint8), 1); a2 = cv2.convertScaleAbs(cv2.imdecode(np.fromfile(os.path.join(O, "판_2_원화.png"), np.uint8), 1), alpha=2, beta=10)
for p, col in 판들.items():
    for a, n in ((a1, "1"), (a2, "2")):
        cs, _ = cv2.findContours(표면칸(n, p).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); cv2.drawContours(a, cs, -1, col[::-1], 2)
cv2.imencode(".png", cv2.resize(a1, None, fx=2, fy=2))[1].tofile(os.path.join(B, "부리판헐_1정면칸.png")); cv2.imencode(".png", cv2.resize(a2, None, fx=2, fy=2))[1].tofile(os.path.join(B, "부리판헐_2옆칸.png"))
print(결과)
