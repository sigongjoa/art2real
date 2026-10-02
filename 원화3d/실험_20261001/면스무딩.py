# -*- coding: utf-8 -*-
"""면 여러 개 스무딩 (10-02 사용자 「스무딩을 하면 패널라인이나 그림자 정보가 약해진다가 문제」).
부품스무딩.py(판마다 평면 하나)와 다른 점: 부품 안을 **부품 안 먹선 + 원화 그림자 경계**로 면(패싯)들로 나누고, 면마다 평면을 둔다.
  면 방향: 깊이(부조_Z)에 맞춘 평면에서 시작 → 원화가 밝다고 한 면은 빛을 향하게(n·L ≥ 0.55), 그림자라고 한 면은 등지게(n·L ≤ 0.25) 가장 적게 돌림
  윤곽: 면마다 곧은 변 · IoU ≥ 0.93 에서 멈춤(부품스무딩과 같음) · 두께 2
눈 · 뿔 · 투구 돔은 그대로(부품스무딩 · 뿔스무딩 · 투구돔). 출력 out/오메가몬2/지표/부조/면스무딩/*.ply"""
import os, json, numpy as np, cv2, trimesh
from shapely.geometry import Polygon
import 면정보자 as M
K = M.K; O = os.path.join(K, "부조"); S = os.path.join(O, os.environ.get("FACET_OUT", "면스무딩")); os.makedirs(S, exist_ok=True)
z = np.load(os.path.join(O, "부조_Z.npz")); Z = z["Z"]; Lc = z["Lf"]; x0, y0, x1, y1 = z["자르기"]; k = float(z["k"]); W_full = M.Lf.shape[1]
그래프 = json.load(open(os.path.join(K, "연결그래프", "그래프.json"), encoding="utf-8"))
sv = cv2.imdecode(np.fromfile(os.path.join(M.G_, "그림자찾기.png"), np.uint8), 1); SH = (sv[:, :, 2] > 120) & (sv[:, :, 1] < 100)
Lum = cv2.cvtColor(cv2.imdecode(np.fromfile(M.ART, np.uint8), 1)[y0:y1, x0:x1], cv2.COLOR_BGR2LAB)[:, :, 0]
INK = cv2.dilate((cv2.morphologyEx(Lum, cv2.MORPH_BLACKHAT, np.ones((7, 7), np.uint8)) > 28).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
L_b = M.L_b
def bx(px): return (px + x0 - W_full / 2) * k
def bz(py): return -py * k
def 돌림(n, 밝음):
    """n(앞 = −y 쪽)을 L 쪽으로 가장 적게 돌려 n·L 조건을 맞춤."""
    n = n / np.linalg.norm(n); want_lo, want_hi = (0.55, 1.0) if 밝음 else (-1.0, 0.25); d = n @ L_b
    if want_lo <= d <= want_hi: return n
    target = want_lo if d < want_lo else want_hi; best = n
    for a in np.linspace(0, 3, 301):
        q = n + (a if d < want_lo else -a) * L_b; q /= np.linalg.norm(q)
        if q[1] > -0.15: break                                     # 카메라를 등지면 멈춤
        best = q
        if (q @ L_b >= target) if d < want_lo else (q @ L_b <= target): break
    return best
for f in os.listdir(S): os.remove(os.path.join(S, f))
판이름 = ("차양", "이마판", "눈구멍", "눈 둘레 테", "미늘", "마스크 볼판", "볼날개", "번개", "안테나") + (("투구 돔", "뿔", "눈") if os.environ.get("FACET_ALL") else ())   # 10-02 그림자만 목표: 돔 · 뿔 · 눈 칸도 면으로
결과 = {}
for p in 그래프["부품"]:
    nm = p["이름"]; base = nm.split("/")[0]
    if not base.startswith(판이름): continue
    m = cv2.morphologyEx(np.isin(Lc, p["칸"]).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) > 0
    if m.sum() < 30: continue
    # 면 나누기: (부품 − 부품 안 먹선)의 연결 성분 × 밝음/그림자
    inner = m & INK & (cv2.erode(m.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0)
    n_lab, lab = cv2.connectedComponents((m & ~inner).astype(np.uint8))
    면들 = []
    for i in range(1, n_lab):
        r = lab == i
        for 밝음 in (True, False):
            q = r & (~SH if 밝음 else SH)
            if q.sum() >= 25: 면들.append((q, 밝음))
    if not 면들: 면들 = [(m, not SH[m].mean() > 0.5)]
    nf = 0
    for j, (q, 밝음) in enumerate(면들):
        q = cv2.morphologyEx(q.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        cs, _ = cv2.findContours(q, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not cs: continue
        c = max(cs, key=cv2.contourArea)
        if cv2.contourArea(c) < 20: continue
        for eps in (9, 7, 5, 4, 3, 2.5, 2, 1.5, 1.0):
            ap = cv2.approxPolyDP(c, eps, True).reshape(-1, 2)
            if len(ap) < 3: continue
            rast = np.zeros(q.shape, np.uint8); cv2.fillPoly(rast, [ap.astype(np.int32)], 1)
            if (rast & q).sum() / ((rast | q) > 0).sum() >= 0.93: break
        ys, xs = np.nonzero(q); zz = Z[ys, xs]; ok = ~np.isnan(zz)
        if ok.sum() < 5: continue
        A = np.c_[bx(xs[ok]), bz(ys[ok]), np.ones(ok.sum())]; a_, b_, c_ = np.linalg.lstsq(A, zz[ok], rcond=None)[0]   # 앞 = a x + b z + c
        n0 = np.array([a_, -1.0, b_]); n0 /= np.linalg.norm(n0)                # 앞(−y)을 보는 법선: 블렌더 y = −앞
        n1 = 돌림(n0, 밝음)
        P0 = np.array([bx(xs[ok].mean()), -np.median(zz[ok]), bz(ys[ok].mean())])
        poly = Polygon(np.c_[bx(ap[:, 0]), bz(ap[:, 1])]).buffer(0)
        if poly.is_empty or poly.geom_type != "Polygon": continue
        pl = trimesh.creation.extrude_polygon(poly, 2.0); V = pl.vertices
        yfront = P0[1] - (n1[0] * (V[:, 0] - P0[0]) + n1[2] * (V[:, 1] - P0[2])) / n1[1]
        pl.vertices = np.c_[V[:, 0], yfront + V[:, 2], V[:, 1]]
        pl.visual.vertex_colors = np.tile([50, 52, 60, 255] if base.startswith("눈구멍") else [215, 220, 235, 255], (len(V), 1))
        pl.export(os.path.join(S, f"{nm.replace('/', '_').replace(' ', '')}_{j:02d}.ply")); nf += 1
    결과[nm] = {"면": nf}
json.dump(결과, open(os.path.join(S, "면스무딩.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("부품", len(결과), "· 면 합계", sum(v["면"] for v in 결과.values()))
