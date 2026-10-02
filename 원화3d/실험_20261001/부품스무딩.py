# -*- coding: utf-8 -*-
"""부품별 스무딩 (10-02 사용자 「각 부품별로 이렇게 스무딩해 봐」) — 뿔스무딩.py 의 기준을 모든 부품에.
기준: 이름이 꼴 · 먹선이 남길 곳 · 문턱이 멈출 때.
  판(차양 · 이마판 · 눈구멍 · 눈 둘레 테 · 미늘 · 마스크 볼판 · 볼날개 · 번개 · 안테나 뿌리): 윤곽을 곧은 변으로 줄이되 칸과 IoU ≥ 0.93 인 가장 적은 꼭짓점에서 멈춤
     · 면 = 부품 깊이(부조_Z · 색 규칙 적용됨)에 평면 맞춤(기울기만) · 두께 2(사전 기본)
  눈: 타원 맞춤 → 납작 타원체   뿔: 뿔스무딩.py 결과   투구 돔: 투구돔.py 결과(소체 자리)
출력 out/오메가몬2/지표/부조/스무딩/<부품>.ply · 스무딩.json(부품마다 꼭짓점 수 · IoU · 기울기)"""
import os, json, numpy as np, cv2, trimesh
from shapely.geometry import Polygon
K = r"G:\art2real\원화3d\out\오메가몬2\지표"; O = os.path.join(K, "부조"); S = os.path.join(O, "스무딩"); os.makedirs(S, exist_ok=True)
z = np.load(os.path.join(O, "부조_Z.npz")); Z = z["Z"]; Lc = z["Lf"]; x0, y0, x1, y1 = z["자르기"]; k = float(z["k"])
Lfull = np.load(os.path.join(K, "선파츠_정면.npz"))["라벨"]; W_full = Lfull.shape[1]
그래프 = json.load(open(os.path.join(K, "연결그래프", "그래프.json"), encoding="utf-8"))
def bx(px): return (px + x0 - W_full / 2) * k          # 자른 그림 화소 → 블렌더 x
def bz(py): return -(py) * k                           # 부조와 같은 틀(y0 = 0)
판이름 = ("차양", "이마판", "눈구멍", "눈 둘레 테", "미늘", "마스크 볼판", "볼날개", "번개", "안테나")
for f in os.listdir(S): os.remove(os.path.join(S, f))
결과 = {}; 메시들 = []
for p in 그래프["부품"]:
    nm = p["이름"]; base = nm.split("/")[0]
    if base.startswith(("뿔", "투구 돔")): continue
    m = np.isin(Lc, p["칸"]); m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) > 0
    if m.sum() < 30: continue
    cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); c = max(cs, key=cv2.contourArea)
    ys, xs = np.nonzero(m); zz = Z[ys, xs]; ok = ~np.isnan(zz)
    A = np.c_[bx(xs[ok]), bz(ys[ok]), np.ones(ok.sum())]; coef = np.linalg.lstsq(A, zz[ok], rcond=None)[0]   # 앞 = a·x + b·z + c (평면으로 스무딩)
    def 앞(xb, zb): return coef[0] * xb + coef[1] * zb + coef[2]
    if base == "눈":
        (cx_, cy_), (ma, mi), ang = cv2.fitEllipse(c); e = trimesh.creation.icosphere(3); r = np.array([ma / 2 * k, mi / 4 * k, mi / 2 * k])
        R = trimesh.transformations.rotation_matrix(np.radians(-ang), [0, 1, 0]); e.vertices = e.vertices * r; e.apply_transform(R)
        cxb, czb = bx(cx_), bz(cy_); e.apply_translation([cxb, -앞(cxb, czb) + r[1] * 0.3, czb]); mesh = e
        rast = np.zeros(m.shape, np.uint8); cv2.ellipse(rast, ((cx_, cy_), (ma, mi), ang), 1, -1); iou = float((rast & m).sum() / ((rast | m) > 0).sum()); nv = "타원"
    elif base.startswith(판이름):
        best = None
        for eps in (12, 9, 7, 5, 4, 3, 2.5, 2, 1.5, 1.0):        # 큰 것부터 — 문턱을 처음 넘는(가장 거친) 단순화에서 멈춤
            ap = cv2.approxPolyDP(c, eps, True).reshape(-1, 2)
            if len(ap) < 3: continue
            rast = np.zeros(m.shape, np.uint8); cv2.fillPoly(rast, [ap.astype(np.int32)], 1); iou = float((rast & m).sum() / ((rast | m) > 0).sum())
            best = (eps, ap, iou)
            if iou >= 0.93: break
        eps, ap, iou = best; nv = len(ap)
        poly = Polygon(np.c_[bx(ap[:, 0]), bz(ap[:, 1])]).buffer(0)
        if poly.is_empty or poly.geom_type != "Polygon": continue
        pl = trimesh.creation.extrude_polygon(poly, 2.0)                                   # (x, z 자리) 윤곽 · 두께 2
        V = pl.vertices; fr = 앞(V[:, 0], V[:, 1]); pl.vertices = np.c_[V[:, 0], -(fr - V[:, 2]), V[:, 1]]   # 앞면이 평면 위 · 뒤로 2
        mesh = pl
    else: continue
    mesh.visual.vertex_colors = np.tile([215, 220, 235, 255] if not base.startswith("눈구멍") else [50, 52, 60, 255], (len(mesh.vertices), 1))
    mesh.export(os.path.join(S, nm.replace("/", "_").replace(" ", "") + ".ply")); 메시들.append(mesh)
    결과[nm] = {"꼴": "타원체" if base == "눈" else "각진 판", "꼭짓점": nv, "IoU": round(iou, 3), "기울기(좌우·위아래)": [round(float(coef[0]), 2), round(float(coef[1]), 2)], "통과": iou >= 0.93}
json.dump(결과, open(os.path.join(S, "스무딩.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
n_ok = sum(v["통과"] for v in 결과.values()); print("부품", len(결과), "· 문턱 0.93 통과", n_ok)
for k_, v in 결과.items(): print(k_, v)
