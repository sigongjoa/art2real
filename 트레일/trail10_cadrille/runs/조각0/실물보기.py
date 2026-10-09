# -*- coding: utf-8 -*-
"""실물 메시 → 6 방향 실루엣 · 깊이 (조각.보기 와 같은 규약) — open3d 광선 (점유 격자 없이 · 메모리 작음 · 10-09)
메시는 단위 상자 규약([0,1]³ · 긴 변 1 · 가운데 0.5) 이어야 한다"""
import numpy as np

def 실물보기(m, n):
    import open3d as o3d
    sc = o3d.t.geometry.RaycastingScene(); sc.add_triangles(o3d.core.Tensor(m.vertices.astype(np.float32)), o3d.core.Tensor(m.faces.astype(np.uint32)))
    u = (np.arange(n) + .5) / n * 1.1 - .05; A, B = np.meshgrid(u, u, indexing="ij"); S, D = [], []
    for ax in range(3):
        o = [i for i in range(3) if i != ax]
        for fl in (False, True):
            org = np.zeros((n, n, 3), np.float32); dr = np.zeros((n, n, 3), np.float32)
            org[..., o[0]], org[..., o[1]] = A, B; org[..., ax] = 1.2 if fl else -0.2; dr[..., ax] = -1 if fl else 1
            t = sc.cast_rays(o3d.core.Tensor(np.concatenate([org, dr], -1).reshape(-1, 6)))["t_hit"].numpy().reshape(n, n)
            hit = np.isfinite(t); w = (1.2 - t) if fl else (-0.2 + t)            # 맞은 곳의 세계 좌표(그 축)
            d = (w + .05) / 1.1; d = (1 - d) if fl else d                          # 격자 칸 비율 = 보기의 z
            S.append(hit.astype(np.float32)); D.append(np.where(hit, d, 1.0).astype(np.float32))
    return np.stack(S), np.stack(D)

if __name__ == "__main__":   # 자기 검사: 합성 정답 부품의 SDF 보기와 광선 보기가 거의 같다
    import sys, json, torch, trimesh
    sys.path.insert(0, ".")
    from 조각 import 정답칸, 점유, 격자, 보기
    from 평가 import 메시
    n = 48; Q = json.load(open("정답/0001.json", encoding="utf-8"))
    m = 메시(Q); m.apply_scale(.5); m.apply_translation([.5] * 3)   # [-1,1] → 단위 상자
    Sr, Dr = 실물보기(m, n); P, C, S = 정답칸(Q, 12)
    Ss, Ds = 보기(점유(격자(n, "cpu")[None], P[None], C[None], S[None], .005), n)
    ds, dd = np.abs(Sr - Ss[0].numpy()).mean(), np.abs(Dr - Ds[0].numpy()).mean()
    print("실루엣 차 %.3f · 깊이 차 %.3f" % (ds, dd)); assert ds < .05 and dd < .05   # 경계 한 칸 계단 차이(3 %) — 축이 뒤집히면 20 % 넘음
    print("ok")
