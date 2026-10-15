# 판정기준54 데이터 — 부품 1 만마다 정답 메시 표면 점 2,048 개(짓기.정규메시 틀 · float16) · 조각 없이 한 번 · 실패는 0 점(ok=False) · 10-15
import json, numpy as np
from multiprocessing import Pool
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/"
def 하나(p):
    try:
        import trimesh
        v, f, H = J.정규메시(p); m = trimesh.Trimesh(v, f, process=False); q, _ = trimesh.sample.sample_surface(m, 2048, seed=54); return q.astype(np.float16), True
    except Exception: return np.zeros((2048, 3), np.float16), False
if __name__ == "__main__":
    L = json.load(open(O + "목록.json", encoding="utf-8"))
    with Pool(4, maxtasksperchild=200) as pool: R = pool.map(하나, L, chunksize=16)
    P = np.stack([r[0] for r in R]); ok = np.array([r[1] for r in R]); np.savez(O + "표면점54.npz", P=P, ok=ok); print("부품", len(P), "실패", int((~ok).sum()))
