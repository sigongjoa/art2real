# -*- coding: utf-8 -*-
"""납작하게 누운 출력 부품에서 공(볼) · 소켓 중심 찾기 — 표면 법선 투표(허프). 10-07 Dummy 13 조립용.
python 관절찾기.py <stl> [...] → 부품마다 (종류 · 반지름 · 중심 xyz · 표)"""
import sys, numpy as np, trimesh
def joints(m, rs=np.arange(1.25, 4.76, 0.25), cell=0.3, k=6):
    p, fi = trimesh.sample.sample_surface_even(m, 40000, seed=0); n = m.face_normals[fi]
    out = []
    for kind, sgn in (("공", -1), ("소켓", +1)):
        best = {}
        for r in rs:
            c = p + sgn * r * n; key = np.round(c / cell).astype(int)
            u, cnt = np.unique(key, axis=0, return_counts=True)
            for kk, cc in zip(map(tuple, u[cnt > 25]), cnt[cnt > 25]):
                s = cc / (r * r)   # 넓이로 나눔(큰 구가 이기지 않게)
                if s > best.get(kk, (0,))[0]: best[kk] = (s, r, cc)
        cand = sorted(((s, r, cc, np.array(kk) * cell) for kk, (s, r, cc) in best.items()), key=lambda t: -t[0])
        keep = []
        for s, r, cc, c in cand:
            if all(np.linalg.norm(c - q[3]) > 3 for q in keep): keep.append((s, r, cc, c))
            if len(keep) == k: break
        out += [(kind, round(float(r), 2), np.round(c, 1).tolist(), int(cc)) for s, r, cc, c in keep]
    return out
if __name__ == "__main__":
    import os
    for f in sys.argv[1:]:
        m = trimesh.load(f, force="mesh"); m.apply_translation(-m.bounds[0])   # 상자 왼쪽 아래를 0 으로
        print(os.path.basename(f), np.round(m.extents, 1))
        for j in joints(m): print("   ", j)
