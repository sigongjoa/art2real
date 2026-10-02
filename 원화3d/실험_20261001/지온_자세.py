# -*- coding: utf-8 -*-
"""샘플 메크 머리를 원래 그림 자세로: 총을 핀 축(x) 둘레로 돌려 총구(좁은 끝)가 앞(+y)을 향하게. 앞 = +y 는 투구 다섯 방향 렌더에서 앞판(깎은 정수리 · 띠 두 줄)으로 확인."""
import os, json, numpy as np, trimesh
O = r"G:\art2real\원화3d\out\샘플\메크머리_CC0\지온"; 자리 = json.load(open(os.path.join(O, "자리.json"), encoding="utf-8"))
def 총구(p):
    c = p.centroid; ax = np.linalg.svd(p.vertices - c, full_matrices=False)[2][0]; t = (p.vertices - c) @ ax
    a = [p.section(plane_origin=c + ax * s, plane_normal=ax) for s in (t.min() + 0.1 * np.ptp(t), t.max() - 0.1 * np.ptp(t))]
    A = [sum(q.area for q in s.to_2D()[0].polygons_full) if s is not None else 0 for s in a]
    return ax if A[1] < A[0] else -ax          # 좁은 끝 쪽
각도 = {}
for k in ("투구_가운데", "핀_왼", "핀_오른", "총_왼", "총_오른"):
    p = trimesh.load(os.path.join(O, f"조립_{k}.obj"), force="mesh")
    if k.startswith("총"):
        m = 총구(p); my = np.array([0, m[1], m[2]]); my /= np.linalg.norm(my)
        ang = np.arctan2(np.cross(my, [0, 1, 0])[0], my @ [0, 1, 0])        # x 축 둘레 각
        piv = np.array(자리["붙는자리"][k.replace("_", "/")])
        p.apply_transform(trimesh.transformations.rotation_matrix(ang, [1, 0, 0], piv)); 각도[k] = round(float(np.degrees(ang)), 1)
        assert 총구(p) @ [0, 1, 0] > 0.95, k                                     # 총구가 앞
    p.export(os.path.join(O, f"자세_{k}.obj"))
json.dump(각도, open(os.path.join(O, "자세.json"), "w", encoding="utf-8")); print("핀 축 둘레 회전", 각도)
