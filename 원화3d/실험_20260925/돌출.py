# -*- coding: utf-8 -*-
"""소형 돌출 부품 — 원화 실루엣에는 있고 모델에는 없는 튀어나온 조각(뿔 · 칼날 · 발톱 · 가시)을 꽂는 부품으로 (2026-09-26).

    python 돌출.py
      -> out/출력/오메가몬_PG/디자인/돌출/*.stl · 부품.json · 빠진실루엣.png
      디테일대조.py --색분할 --돌출 로 잰다.

  (x, z) 모양 = 정면 빠짐 ∩ 뒤 빠짐 (두 원화가 모두 그린 것 — 정사영 실루엣은 앞뒤가 같다, 뒤는 「거울 뒤」라 좌표 그대로).
  돌출 판정 = 모델 실루엣에서 가장 먼 점 ≥ 3 mm · 넓이 ≥ 15 mm² (가장자리를 따라 난 얇은 띠는 모양 차이 · 정렬 — 여기서 안 다룸).
  y = 주인 부품(가장 가까운 모델 부품)이 뿌리 둘레에서 차지하는 y 의 가운데. 두께는 원화에 없다 → 주인 두께 안에서
      뿌리 min(주인 두께, 6) → 끝 0.3 배로 얇아지는 쐐기(모델 실루엣에서 먼 만큼). 윤곽은 격자 계단을 펴고(열기 0.6 · 단순화 0.3).
      옆 원화 실루엣을 x 로 민 기둥과 교집합(옆에서 보이는 범위 밖으로 안 나가게).
  붙이기 = 조각을 모델 실루엣 안으로 1 mm 늘리고 곁 부품(실루엣 안 2.5 mm 둘레)을 뺀다 → 주인 겉면에 맞닿는 면으로 붙임(접착).
      주인은 안 판다 — 2 mm 껍질 가장자리에 홈을 파면 주인이 20 조각 넘게 쪼개졌다(09-26 첫 판).
  색 = 조각 원화에서 먹선(검)을 뺀 가장 많은 부류의 RGB 중앙값."""
import os, sys, json, time, importlib.util as IU
import numpy as np, trimesh, manifold3d as M
from scipy import ndimage
from skimage import measure
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 디테일대조 as DD
from 메시출력 import 부채나누기
_sp = IU.spec_from_file_location("색분할25", os.path.join(os.path.dirname(os.path.abspath(__file__)), "색분할.py"))
C = IU.module_from_spec(_sp); _sp.loader.exec_module(C)      # 이름 「색분할」 이 다른 실험 폴더와 겹쳐 경로로 읽는다

OUT = os.path.join(DD.D, "돌출"); os.makedirs(OUT, exist_ok=True)
해상, X0, X1, Z0, Z1 = 0.25, -140.0, 140.0, -15.0, 330.0          # mm 격자
최소거리, 최소넓이, 뿌리, 끝비율, 최대두께 = 3.0, 15.0, 2.5, 0.3, 6.0
t_ = time.time()
def log(*a): print("[%4.0fs]" % (time.time() - t_), *a, flush=True)

gx = np.arange(X0, X1, 해상) + 해상 / 2; gz = np.arange(Z1, Z0, -해상) - 해상 / 2       # 행 = z 위→아래, 열 = x
def 격자로(mask, 보기):
    """보기 화소 마스크 → mm 격자 (가장 가까운 화소)."""
    f, cx, r0, s, R, sg = DD.보기[보기]
    u = np.rint((sg * gx) / s + cx - 0.5).astype(int); v = np.rint(r0 - gz / s - 0.5).astype(int)
    ok = (u >= 0) & (u < mask.shape[1]); okv = (v >= 0) & (v < mask.shape[0])
    out = np.zeros((len(gz), len(gx)) + mask.shape[2:], mask.dtype)
    out[np.ix_(okv, ok)] = mask[np.ix_(v[okv], u[ok])]
    return out
def 격자단면(mask):
    polys = [np.c_[X0 + (c[:, 1] - 1 + 0.5) * 해상, Z1 - (c[:, 0] - 1 + 0.5) * 해상] for c in measure.find_contours(np.pad(mask, 1).astype(float), 0.5) if len(c) >= 4]
    return M.CrossSection(polys, M.FillRule.EvenOdd).simplify(0.05) if polys else M.CrossSection()
def 판(cs, y0, y1):
    """(x, z) 단면을 y ∈ [y0, y1] 로."""
    return cs.extrude(y1 - y0).transform(np.array([[1, 0, 0, 0], [0, 0, 1, y0], [0, 1, 0, 0]], float))
def 옆기둥():
    f, cx, r0, s, R, sg = DD.보기["옆"]; A = DD.원화선("옆")["A"]
    polys = [np.c_[(c[:, 1] - 1 + 0.5 - cx) * s, (r0 - (c[:, 0] - 1 + 0.5)) * s] for c in measure.find_contours(np.pad(A, 1).astype(float), 0.5) if len(c) >= 4]
    cs = M.CrossSection(polys, M.FillRule.EvenOdd).offset(0.5, M.JoinType.Round)     # (y, z) · 0.5 mm 여유
    return cs.extrude(400.0).transform(np.array([[0, 0, 1, -200.0], [1, 0, 0, 0], [0, 1, 0, 0]], float))
def 만폴드(tm):
    m = M.Manifold(M.Mesh(vert_properties=np.asarray(tm.vertices, np.float32), tri_verts=np.asarray(tm.faces, np.uint32)))
    assert m.status() == M.Error.NoError, m.status()
    return m

def main():
    부품 = DD.부품읽기(색분할=True)
    원f, 원b = DD.원화선("정면"), DD.원화선("뒤")
    앞, 이름들 = C.앞부품지도("정면", 부품)
    Mo = 격자로(앞 >= 0, "정면"); 주인지도 = 격자로(앞, "정면"); 주인지도[~Mo] = -1; rgb = 격자로(원f["rgb"], "정면")
    빠 = 격자로(원f["A"], "정면") & 격자로(원b["A"], "뒤") & ~Mo
    빠 = ndimage.binary_opening(빠, iterations=2)
    거리 = ndimage.distance_transform_edt(~Mo) * 해상
    가까 = ndimage.distance_transform_edt(~Mo, return_distances=False, return_indices=True)
    옆 = 옆기둥(); lab, n = ndimage.label(빠)
    디스크 = lambda r: np.hypot(*np.mgrid[-r:r + 1, -r:r + 1]) <= r
    결과 = {"설명": __doc__, "부품": {}}; 목록 = []
    for i in range(1, n + 1):
        r = lab == i; 넓 = r.sum() * 해상 ** 2; 멀 = 거리[r].max()
        if 넓 < 최소넓이 or 멀 < 최소거리: continue
        근 = ndimage.binary_dilation(r, 디스크(int(뿌리 / 해상))) & Mo           # 주인 찾는 자리(모델 실루엣 안 2.5 mm)
        겹 = ndimage.binary_dilation(r, 디스크(int(1.0 / 해상))) & Mo             # 부품이 실루엣 안으로 들어가는 폭 1 mm — 곁 부품에 맞닿게 깎인다
        주 = 주인지도[근]; 주 = 주[주 >= 0]
        if not len(주): continue
        주인 = 이름들[np.bincount(주).argmax()]; tm = 부품[주인][0]
        ys, xs = np.nonzero(근 | r); xmm, zmm = gx[xs], gz[ys]
        V = np.asarray(tm.vertices); 곁 = (V[:, 0] >= xmm.min() - 3) & (V[:, 0] <= xmm.max() + 3) & (V[:, 2] >= zmm.min() - 3) & (V[:, 2] <= zmm.max() + 3)
        if 곁.sum() < 3: continue
        ya, yb = np.percentile(V[곁, 1], [5, 95]); yc = (ya + yb) / 2; T = min(yb - ya, 최대두께)
        cs = 격자단면(r | 겹).offset(0.6, M.JoinType.Round).offset(-0.6, M.JoinType.Round).simplify(0.3)   # 격자 계단 펴기
        # 두께: 뿌리 T → 끝 끝비율·T (모델 실루엣에서 먼 만큼 얇게). 윤곽 정점만 옮겨도 윗면 삼각형이 뿌리→끝 쐐기가 된다.
        Tr = max(T, 1.2 / 끝비율)
        def 쐐기(P):
            i_ = np.clip(np.rint((Z1 - P[:, 2]) / 해상 - 0.5).astype(int), 0, len(gz) - 1); j_ = np.clip(np.rint((P[:, 0] - X0) / 해상 - 0.5).astype(int), 0, len(gx) - 1)
            f = 1.0 - (1.0 - 끝비율) * np.clip(거리[i_, j_] / 멀, 0, 1)
            return np.c_[P[:, 0], yc + (P[:, 1] - yc) * f, P[:, 2]]
        층 = [판(cs, yc - Tr / 2, yc + Tr / 2).warp_batch(쐐기)]
        곁부품 = set(이름들[j] for j in np.unique(주인지도[ndimage.binary_dilation(근, iterations=8)]) if j >= 0)
        m = (M.Manifold.batch_boolean(층, M.OpType.Add) ^ 옆) - M.Manifold.batch_boolean([만폴드(부품[q][0]) for q in 곁부품], M.OpType.Add)
        ps = [p for p in m.decompose() if p.volume() >= 3.0]
        if not ps: continue
        m = M.Manifold.batch_boolean(ps, M.OpType.Add)
        c_ = rgb[r].astype(float) / 255; 부 = DD.색부류(c_[None])[0]; 밝 = 부 != 3
        주부류 = np.bincount(부[밝]).argmax() if 밝.any() else 3
        색 = np.median(c_[부 == 주부류], 0)
        주색 = np.asarray(부품[주인][1], float)
        if DD.색부류(주색[None, None])[0, 0] == 주부류: 색 = 주색     # 같은 부류면 주인 색 그대로 — 원화 중앙값은 주인 색과 조금 달라 가짜 색 경계가 생긴다(발톱)
        이름 = "돌출%02d_%s" % (len(목록) + 1, 주인)
        목록.append(이름); 결과["부품"][이름] = dict(파일=이름 + ".stl", 색=색.round(3).tolist(), 주인=주인, 넓이mm2=round(넓, 1), 멀리mm=round(멀, 1),
                                               중심xz=[round(float(xmm.mean()), 1), round(float(zmm.mean()), 1)], y=[round(float(yc), 1), round(float(T), 1)])
        fn = os.path.join(OUT, 이름 + ".stl"); C.메시(m).export(fn); wt = trimesh.load(fn).is_watertight
        for 양 in (0.03, 0.06, 0.10):
            if wt: break
            부채나누기(m, 양).export(fn); wt = trimesh.load(fn).is_watertight
        결과["부품"][이름].update(닫힘=bool(wt), 부피mm3=round(m.volume(), 1), 무게g_PLA=round(m.volume() * 1.24e-3, 2))
        log(이름, "넓이 %.0f · 멀리 %.1f · y %.1f±%.1f · %.2f g · 닫힘 %s" % (넓, 멀, yc, T / 2, m.volume() * 1.24e-3, wt))
    json.dump(결과, open(os.path.join(OUT, "부품.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log("돌출 %d · %.1f g" % (len(목록), sum(v["무게g_PLA"] for v in 결과["부품"].values())))

if __name__ == "__main__":
    main()
