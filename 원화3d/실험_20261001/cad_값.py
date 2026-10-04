# -*- coding: utf-8 -*-
"""CAD v1 입력값 — 원화에서 숫자 · 윤곽만 뽑아 JSON (10-04 사용자 「CAD 도안을 바탕으로 가자」).
좌표: x = 정면 판 화소 − 축 A · y 깊이(눈 0 · 앞 −) · z = −행. FreeCAD 는 이 값만 읽어 솔리드를 짓는다(cad_짓기.py).
  속 타원체 E: 머리판.py 와 같은 맞춤(정면 몸통 반폭 최소제곱 · 옆 돔 칸 앞 끝 · 처마 높이 뒤 끝)
  얼굴 구멍: 정면 칸(눈 조립 · 마스크 · 볼날개) 합집합 윤곽 — 투구 앞쪽을 이 윤곽대로 뚫음
  차양: 정면 칸 14 · 16 오른쪽 반 다각형(9 점) → 거울
출력 out/오메가몬2/cad/값_v1.json"""
import os, json, numpy as np, cv2, contextlib, io
A = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; O = r"G:\art2real\원화3d\out\오메가몬2\cad"; os.makedirs(O, exist_ok=True)
K = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "기준선.py")}
with contextlib.redirect_stdout(io.StringIO()): exec(open(K["__file__"], encoding="utf-8").read(), K)
J = json.load(open(os.path.join(A, "기준선.json"), encoding="utf-8")); 층, 축 = J["층(정면 판 화소 행)"], J["정면 축(판 화소 열)"]; xa = 축["A 중심"]
m1 = np.load(os.path.join(A, "판_1_Z.npz"))["m"]; H, W = m1.shape
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
rows = np.array([r for r in range(H) if Fa[r].any()]); hw = np.array([(np.nonzero(Fa[r])[0].max() - np.nonzero(Fa[r])[0].min()) / 2 for r in rows])
top = rows.min(); 턱 = 층["L2 턱 끝"]; best = None
for c in np.arange(60, 160, 2):
    for zc in np.arange(top + 40, 턱, 2):
        q = 1 - ((rows - zc) / c) ** 2; ok = (q > 0.05) & (rows <= 턱)
        if ok.sum() < 30: continue
        s = np.sqrt(q[ok]); a = float((hw[ok] * s).sum() / (s * s).sum()); e = ((hw[ok] - a * s) ** 2).mean()
        if best is None or e < best[0]: best = (e, a, c, zc)
_, a, c, zc = best
r6 = 층["L6 처마"]; 돔칸 = cv2.dilate((C2 == 1).astype(np.uint8), np.ones((3, 3), np.uint8)); dr = [r for r in range(int(top), int(r6) + 1) if 돔칸[r].any()]
yf6 = min(np.nonzero(돔칸[r])[0].min() for r in dr) + D0; yb6 = np.nonzero(Sa[int(r6)])[0].max() + D0
s6 = np.sqrt(max(0.05, 1 - ((r6 - zc) / c) ** 2)); y0 = (yf6 + yb6) / 2; f = (yb6 - yf6) / 2 / s6
def 윤곽(mask, eps=1.5, 오른쪽=False):
    m = mask.astype(np.uint8).copy()
    if 오른쪽: m[:, :int(round(xa))] = 0
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    return [[[float(p[0] - xa), float(-p[1])] for p in cv2.approxPolyDP(cn, eps, True).reshape(-1, 2)] for cn in cs if cv2.contourArea(cn) > 30]
칸 = lambda cs: cv2.dilate(np.isin(C1, cs).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=2)
얼굴 = 칸([11, 12, 13, 15, 17, 18, 19, 20, 21, 22, 23, 24, 27] + list(range(29, 43)) + [7, 10, 25, 26, 28]) & m1.astype(np.uint8)
얼굴 = cv2.morphologyEx(얼굴, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
값 = {"E": {"a": float(a), "c": float(c), "zc": float(-zc), "y0": float(y0), "f": float(f)}, "껍질": 1.8, "턱 z": float(-턱),
     "얼굴 구멍": 윤곽(얼굴, 2.0), "차양 오른쪽": 윤곽(칸([14, 16]) & m1.astype(np.uint8), 1.5, True), "차양 두께": 6.0}
json.dump(값, open(os.path.join(O, "값_v1.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print({k: (v if not isinstance(v, list) else f"{len(v)} 윤곽 · {[len(p) for p in v]} 점") for k, v in 값.items()})
