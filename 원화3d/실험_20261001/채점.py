# -*- coding: utf-8 -*-
"""채점 — 지은 머리를 정면 · 옆 원화 실루엣에 겹쳐 IoU (10-04 피드백 루프 · 패널 권고 3 「채점 도구」).
python 채점.py <ply 이름(확장자 없이)> [...]
정면: 메시 (x, 행) 투영 대 정면 마스크(판_1) · 옆: 메시 (깊이, 행) 투영 대 옆 마스크(판_2 를 B 맞춤 T 로 옮긴 것)
머리 띠만(뿔 끝 ~ 턱 끝 · 정면 층 L2 아래는 목이라 뺌). 출력: 숫자 + 채점_<이름>.png(초록 = 겹침 · 빨강 = 원화에만 · 파랑 = 모델에만)"""
import os, sys, json, numpy as np, cv2, trimesh
A = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
K = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "기준선.py")}
import contextlib, io
with contextlib.redirect_stdout(io.StringIO()): exec(open(K["__file__"], encoding="utf-8").read(), K)
T = K["T"]; 층 = json.load(open(os.path.join(A, "기준선.json"), encoding="utf-8"))["층(정면 판 화소 행)"]; 아래 = int(층["L2 턱 끝"] + 3)
m1 = np.load(os.path.join(A, "판_1_Z.npz"))["m"]; H, W = m1.shape; cu = (np.nonzero(m1)[1].min() + np.nonzero(m1)[1].max()) / 2
m2 = np.load(os.path.join(A, "판_2_Z.npz"))["m"]; ys, xs = np.nonzero(m2); dd, rr = T(xs.astype(float), ys.astype(float))
OX = 200; S2 = np.zeros((H, 400), np.uint8); ok = (rr >= 0) & (rr < H) & (dd + OX >= 0) & (dd + OX < 400)
S2[np.round(rr[ok]).astype(int).clip(0, H - 1), np.round(dd[ok] + OX).astype(int).clip(0, 399)] = 1; S2 = cv2.morphologyEx(S2, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
F1 = m1.astype(np.uint8).copy(); F1[아래:] = 0; S2[아래:] = 0
def 투영(me, u, shape):
    img = np.zeros(shape, np.uint8); r = -me.vertices[:, 2]
    for f in me.faces: cv2.fillConvexPoly(img, np.round(np.c_[u[f], r[f]]).astype(np.int32), 1)
    img[아래:] = 0; return img
def iou(a, b): return float((a & b).sum() / max(1, (a | b).sum()))
out = {}
for nm in sys.argv[1:]:
    me = trimesh.load(os.path.join(B, nm + ".ply"), process=False)
    P1 = 투영(me, me.vertices[:, 0] + cu, (H, W)); P2 = 투영(me, me.vertices[:, 1] + OX, (H, 400))
    out[nm] = {"정면 IoU": round(iou(P1, F1), 3), "옆 IoU": round(iou(P2, S2), 3)}
    def 색(p, g):
        c = np.full(p.shape + (3,), 255, np.uint8); c[(p & g) > 0] = (60, 180, 80); c[(g & ~p) > 0] = (230, 80, 80); c[(p & ~g) > 0] = (80, 120, 230); return c
    sheet = np.concatenate([색(P1, F1), np.full((H, 10, 3), 0, np.uint8), 색(P2, S2)], 1)
    cv2.imencode(".png", cv2.resize(sheet, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)[:, :, ::-1])[1].tofile(os.path.join(B, f"채점_{nm}.png"))
print(json.dumps(out, ensure_ascii=False))
