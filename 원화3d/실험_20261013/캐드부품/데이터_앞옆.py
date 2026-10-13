# 판정기준31 ② — 같은 부품 1만(목록.json 순서)에서 앞(+Y 쪽에서 −Y 로) · 옆(+X 쪽에서 −X 로) 선 그림 128² · 데이터.py 와 같은 정규화 · 같은 선 규칙 · 10-13
# venv python 데이터_앞옆.py → out/설명/캐드부품/데이터_앞옆.npz (F · S uint8)
import json, numpy as np
from multiprocessing import Pool
N = 128; O = "G:/art2real/out/설명/캐드부품/"
def 선그림(t, S):   # 광선 맞은 거리 t → 바깥 윤곽 + 거리 끊김 + 꺾임
    import cv2
    zz = np.where(S, -t, -3.0); s8 = S.astype(np.uint8)
    gx, gy = np.abs(np.diff(zz, axis=0, append=zz[-1:])), np.abs(np.diff(zz, axis=1, append=zz[:, -1:]))
    cx, cy = np.abs(np.diff(zz, 2, axis=0, prepend=zz[:1], append=zz[-1:])), np.abs(np.diff(zz, 2, axis=1, prepend=zz[:, :1], append=zz[:, -1:]))
    테 = (s8 - cv2.erode(s8, np.ones((3, 3), np.uint8))) > 0
    return (테 | (((gx > .03) | (gy > .03) | (cx > .004) | (cy > .004)) & S)).astype(np.uint8)
def 하나(p):
    try:
        import trimesh, open3d as o3d
        m = trimesh.load(p, force="mesh"); e = m.extents; ax = int(np.argmin(e)); order = [i for i in range(3) if i != ax] + [ax]
        v = (m.vertices - m.bounds.mean(0))[:, order] / e.max()
        sc = o3d.t.geometry.RaycastingScene(); sc.add_triangles(o3d.core.Tensor(v.astype(np.float32)), o3d.core.Tensor(m.faces.astype(np.uint32)))
        u = (np.arange(N) + .5) / N * 1.1 - .55; A, Bz = np.meshgrid(u, -u)   # 가로 = 그 면의 가로축 · 세로 = Z(위가 큼)
        out = []
        for 가로, 깊축 in ((0, 1), (1, 0)):   # 앞: 가로 X · Y 방향으로 쏨 / 옆: 가로 Y · X 방향으로 쏨
            r = np.zeros((N, N, 6), np.float32); r[..., 가로] = A; r[..., 2] = Bz; r[..., 깊축] = 1.0; r[..., 3 + 깊축] = -1
            t = sc.cast_rays(o3d.core.Tensor(r.reshape(-1, 6)))["t_hit"].numpy().reshape(N, N); S = np.isfinite(t); out.append(선그림(np.where(S, t, 0), S))
        return out
    except Exception: return [np.zeros((N, N), np.uint8)] * 2
if __name__ == "__main__":
    L = json.load(open(O + "목록.json", encoding="utf-8"))
    with Pool(6) as pool: R = pool.map(하나, L, chunksize=20)
    np.savez_compressed(O + "데이터_앞옆.npz", F=np.stack([r[0] for r in R]), S=np.stack([r[1] for r in R])); print("ok", len(R), "빈 것", sum(int(r[0].sum() == 0) for r in R))
