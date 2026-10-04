# -*- coding: utf-8 -*-
"""겹쳐보기 — 메시 실루엣 윤곽(빨강)을 정면 원화 · 옆 원화(B 맞춤으로 옮긴 것) 위에 (10-04 레퍼런스 변형 판정용).
python 겹쳐보기.py <ply 이름> → 겹쳐_<이름>.png"""
import os, sys, numpy as np, cv2, trimesh, contextlib, io
A = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
K = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "기준선.py")}
with contextlib.redirect_stdout(io.StringIO()): exec(open(K["__file__"], encoding="utf-8").read(), K)
m1 = np.load(os.path.join(A, "판_1_Z.npz"))["m"]; H, W = m1.shape; cu = (np.nonzero(m1)[1].min() + np.nonzero(m1)[1].max()) / 2
art1 = cv2.imdecode(np.fromfile(os.path.join(A, "판_1_원화.png"), np.uint8), 1)
art2 = cv2.imdecode(np.fromfile(os.path.join(A, "판_2_원화_밝게.png"), np.uint8), 1)
D0, ND = -200, 400; k_, t_ = K["k"], K["t"]; ct, st_ = np.cos(t_), np.sin(t_)
M = np.array([[k_ * ct, -k_ * st_, -k_ * K["ex"] * ct + k_ * K["ey"] * st_ - D0], [k_ * st_, k_ * ct, K["c"] - k_ * K["xm"] * st_]], np.float32)
side = cv2.warpAffine(art2, M, (ND, H), borderValue=(255, 255, 255))
me = trimesh.load(os.path.join(B, sys.argv[1] + ".ply"), process=False)
def sil(u, shape):
    img = np.zeros(shape, np.uint8); r = -me.vertices[:, 2]
    cv2.fillPoly(img, [np.round(np.c_[u[f], r[f]]).astype(np.int32) for f in me.faces], 1); return img
def 그림(art, s):
    o = art.copy(); cs, _ = cv2.findContours(s, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); cv2.drawContours(o, cs, -1, (0, 0, 255), 1)
    o[s > 0] = (0.6 * o[s > 0] + 0.4 * np.array([90, 90, 255])).astype(np.uint8); return o
a = 그림(art1, sil(me.vertices[:, 0] + cu, (H, W))); b = 그림(side, sil(me.vertices[:, 1] - D0, (H, ND)))
out = np.concatenate([a, np.full((H, 10, 3), 255, np.uint8), b], 1); out = cv2.resize(out, None, fx=2, fy=2)
cv2.imencode(".png", out)[1].tofile(os.path.join(B, f"겹쳐_{sys.argv[1]}.png")); print("ok")
