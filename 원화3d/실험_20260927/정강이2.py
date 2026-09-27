# -*- coding: utf-8 -*-
"""EG 정강이 반쪽 둘째 판 — 실루엣 부풀리기 대신 하위 도형 다섯의 합 (2026-09-27).

    python 정강이2.py -> out/키트/EG_RX78/정강이/정강이.stl · 결과.json (정강이_그림.py 로 그림)

첫 판(정강이.py)은 옆 실루엣을 부풀려 「덩어리」가 됐다. 실물 = 또렷한 도형의 조합:
  ① 바닥판: 윤곽을 민 평판(겉면 평평 · 가장자리만 r 0.02 L 둥글림) · 뒤는 비움(벽 0.025 L)
  ② 종아리 돔: 물방울 윤곽 판 — 경계 단차 0.008 L(또렷한 선) + 가운데로 0.03 L 부푼 곡면
  ③ 무릎 원판: r 0.058 L · 0.015 L 솟음 · 일자 홈
  ④ 발목 탭: v < 0.14 는 두께 0.6 배(한 단 낮음) · 축 구멍 관통
  ⑤ 옆 브래킷: 오른쪽 v 0.70~0.77 작은 상자(연결부)
깊이 값(두께 · 단차 · 돔 높이)은 여전히 가정 — 사진에 없다."""
import os, sys, json, numpy as np, trimesh, manifold3d as M
from scipy import ndimage
from matplotlib.path import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 정강이 as S1, 방패 as B
from 메시출력 import 부채나누기

L = S1.L; D = S1.D; OUT = S1.OUT
반두께, 벽, 가장r, 돔단차, 돔높이, 원판높이, 탭몫 = 0.10, 0.025, 0.02, 0.008, 0.030, 0.015, 0.6
탭v = 0.14; 브래킷 = (0.135, 0.195, 0.70, 0.77)

def 판x(poly, x0, x1): return S1.기둥x(np.asarray(poly, float) * L, x0, x1)

def 짓기():
    g = np.load(os.path.join(D, "정강이_정답.npz")); mask = S1.매끈마스크(g["겉"]); H, W = mask.shape
    P = S1.다각형(mask); a0, t = 반두께 * L, 벽 * L
    # ① 바닥판 + ④ 탭 단
    바닥 = 판x(P, 0.0, a0)
    탭자름 = S1.기둥x(np.array([(-1, -0.1), (1, -0.1), (1, 탭v), (-1, 탭v)]) * L, 탭몫 * a0, a0 + 1)
    바닥 = 바닥 - 탭자름
    안 = M.CrossSection([B.반시계(P * L).tolist()]).offset(-t, M.JoinType.Round).extrude(a0 - t + 1.0).transform(np.array([[0, 0, 1, -1.0], [1, 0, 0, 0], [0, 1, 0, 0]], float))
    안 = 안 - S1.기둥x(np.array([(-1, -0.1), (1, -0.1), (1, 탭v + 0.02), (-1, 탭v + 0.02)]) * L, -2, a0 + 2)     # 탭은 속 찬 판
    바닥 = 바닥 - 안
    # ② 돔 판 (경계 단차 + 곡면)
    돔윤곽 = S1.잘게(S1.물방울)
    돔 = 판x(돔윤곽, a0 - 0.2, a0 + 돔단차 * L).refine_to_length(0.5)
    yy, xx = np.mgrid[0:H, 0:W]; uu = (xx + 0.5 - W / 2) / H; vv = 1 - (yy + 0.5) / H
    안쪽 = Path(돔윤곽).contains_points(np.c_[uu.ravel(), vv.ravel()]).reshape(H, W)
    dd = ndimage.gaussian_filter(ndimage.distance_transform_edt(안쪽) / H, 3.0); dmax = float(dd.max())
    def 부풀(V):
        top = V[:, 0] > a0 + 0.5 * 돔단차 * L
        d = S1.표본(dd, (H, W), V[:, 1] / L, V[:, 2] / L); k = np.sqrt(np.clip(1 - (1 - np.clip(d / dmax, 0, 1)) ** 2, 0, 1))
        return np.c_[V[:, 0] + top * 돔높이 * L * k, V[:, 1], V[:, 2]]
    돔 = 돔.warp_batch(부풀)
    # ③ 무릎 원판 + 일자 홈
    c = S1.무릎원; 원판 = 판x(S1.원(c[:2], c[2], 48), a0 - 0.2, a0 + 원판높이 * L)
    홈 = 판x(np.array([(c[0] - 0.045, c[1] - 0.007), (c[0] + 0.045, c[1] - 0.007), (c[0] + 0.045, c[1] + 0.007), (c[0] - 0.045, c[1] + 0.007)]), a0 + 0.006 * L, a0 + 1)
    원판 = 원판 - 홈
    # ⑤ 옆 브래킷
    u0, u1, v0, v1 = 브래킷; 브 = 판x(np.array([(u0, v0), (u1, v0), (u1, v1), (u0, v1)]), 0.3 * a0, 0.9 * a0)
    m = 바닥 + 돔 + 원판 + 브
    m = m - 판x(S1.원(S1.발목구멍[:2], S1.발목구멍[2]), -1, a0 + 1)
    # 가장자리 둥글림: 겉면(x ≈ 바닥 윗면)에서 윤곽 가까이만 살짝 내린다
    거리 = ndimage.distance_transform_edt(mask) / H
    m = m.refine_to_length(0.6)
    def 둥글(V):
        d = S1.표본(거리, (H, W), V[:, 1] / L, V[:, 2] / L); 위 = np.clip((V[:, 0] - 0.5 * a0) / (0.5 * a0), 0, 1)
        return np.c_[V[:, 0] - 위 * 가장r * L * (1 - np.sqrt(np.clip(1 - (1 - np.clip(d / 가장r, 0, 1)) ** 2, 0, 1))), V[:, 1], V[:, 2]]
    return m.warp_batch(둥글), P

if __name__ == "__main__":
    m, P = 짓기(); g = m.to_mesh(); tm = trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False)
    fn = os.path.join(OUT, "정강이.stl"); tm.export(fn); 닫힘 = bool(trimesh.load(fn).is_watertight)
    for 양 in (0.02, 0.04, 0.08):
        if 닫힘: break
        부채나누기(m, 양).export(fn); 닫힘 = bool(trimesh.load(fn).is_watertight)
    tm = trimesh.load(fn); 모 = ndimage.binary_fill_holes(S1.옆실루엣(tm))
    결과 = dict(판="둘째(도형 다섯)", L_mm=L, 닫힘=닫힘, 부피mm3=round(m.volume(), 1), 무게g=round(m.volume() * 1.24e-3, 2), 크기mm=np.round(tm.extents, 1).tolist(),
              가정=dict(반두께=반두께, 벽=벽, 돔단차=돔단차, 돔높이=돔높이, 원판높이=원판높이, 탭몫=탭몫))
    for 라벨, 이름 in (("짓는 데 쓴 부품", "정강이"), ("held-out(거울 짝 부품)", "정강이_짝")):
        s1, _ = S1.맞춤(S1.정답(이름), 모); 결과[라벨] = dict(옆실루엣IoU=round(s1, 4))
    json.dump(결과, open(os.path.join(OUT, "결과.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(결과, ensure_ascii=False, indent=1))
