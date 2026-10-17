# 판정기준69 데이터 — 부품마다 정답 메시 첫 맞음 깊이 → 32 단계 층(0~31 · 32 = 통째) · 반높이는 데이터51 의 「반」 그대로 · 10-17
# 사용(venv · ART_MEM_GB=8): 데이터69.py [일꾼=4] → out/설명/캐드부품/층32.npy (부품 × 6 × 128² uint8 · 실패 부품은 32)
import sys, json, numpy as np
from multiprocessing import Pool
O = "G:/art2real/out/설명/캐드부품/"; K = 32
def 하나(job):
    p, 반 = job
    try:
        import 짓기 as J, 여섯방향 as S6
        v, f, _ = J.정규메시(p); 지 = S6.깊이지도(v, f); out = []
        for d, h in zip(S6.방향, 반):
            h = float(h); dd = np.where(np.isnan(지[d]), 2 * h + .1, h - 지[d]); q = np.floor(np.clip(dd, 0, None) / (2 * h / K) + 1e-6)
            out.append(np.where(dd > 2 * h, K, np.clip(q, 0, K - 1)).astype(np.uint8))
        return np.stack(out)
    except Exception: return np.full((6, 128, 128), K, np.uint8)
if __name__ == "__main__":
    z = np.load(O + "데이터51.npz"); 반, ok = z["반"], z["ok"]; L = json.load(open(O + "목록.json", encoding="utf-8")); n = len(ok)
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 4, maxtasksperchild=50) as pool: R = pool.map(하나, [(L[i], 반[i]) for i in range(n)], chunksize=8)
    R = np.stack(R); np.save(O + "층32.npy", R)
    old = z["층"]; 맞 = (np.minimum(R // 2, 16) == np.where(old == 17, 16, old))[ok].mean(); print("부품", n, "· 16 단계와 일치(32 → 16 으로 내렸을 때) %.3f" % 맞)
