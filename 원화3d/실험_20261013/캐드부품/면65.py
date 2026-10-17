# 판정기준65 — 선 그림 영역마다 평면 → 2 차 곡면 → RANSAC 평면 여러 장으로 깊이 층을 맞춤(기울기 · 휨으로 나누기) → 같은 깎기 · 대조는 판0 그대로 · 10-17
# 사용(venv · ART_MEM_GB=8): 면65.py [일꾼=4] [QUICK] → out/설명/캐드부품/면65/ · 결과판정65.json
import sys, os, json, numpy as np
from multiprocessing import Pool
from scipy.ndimage import label
import 영역64 as R4
O = "G:/art2real/out/설명/캐드부품/"; D = O + "면65/"; os.makedirs(D, exist_ok=True); 문턱, 조각, 안쪽 = .7, 30, 1.0
def 맞춤(x, y, z, 차):   # 최소제곱 · 2 번 깎아 다시(오차 2 층 넘는 점 빼고)
    A = np.stack([x, y, np.ones_like(x)] + ([x * x, x * y, y * y] if 차 == 2 else []), 1).astype(float); w = np.ones(len(z), bool)
    for _ in range(2):
        c = np.linalg.lstsq(A[w], z[w], rcond=None)[0]; r = z - A @ c; w = np.abs(r) <= 2
        if w.sum() < A.shape[1] + 2: break
    return A @ c, float(np.sqrt(np.mean((z - A @ c)[w] ** 2))) if w.any() else 99.
def 랜삭(x, y, z, rng):   # 평면 여러 장 — 최대 4 장 · 각 장 안쪽 연결 덩어리 ≥ 조각 화소만 받음
    out = np.full(len(z), np.nan); 남 = np.ones(len(z), bool)
    for _ in range(4):
        ix = np.nonzero(남)[0]
        if len(ix) < 조각: break
        best = None
        for _ in range(60):
            s = rng.choice(ix, 3, replace=False); A = np.stack([x[s], y[s], np.ones(3)], 1)
            if abs(np.linalg.det(A)) < 1e-6: continue
            c = np.linalg.solve(A, z[s]); 안 = 남 & (np.abs(x * c[0] + y * c[1] + c[2] - z) <= 안쪽)
            if best is None or 안.sum() > best[1].sum(): best = (c, 안)
        if best is None or best[1].sum() < 조각: break
        _, 안 = best; f, _ = 맞춤(x[안], y[안], z[안], 1); out[안] = f; 남 &= ~안
    return out
def 면묶기(층, 선, seed=0):
    L, n = label(~선); out = 층.astype(float).copy(); rng = np.random.default_rng(seed)
    for r in range(1, n + 1):
        m = L == r; v = 층[m]; 통 = (v == 17).mean()
        if 통 > .8: out[m] = 17; continue
        if 통 > .2 or m.sum() < 6: continue
        yy, xx = np.nonzero(m); z = v.astype(float); 안 = v != 17
        for 차 in (1, 2):
            f, e = 맞춤(xx[안], yy[안], z[안], 차)
            if e <= 문턱: break
        if e > 문턱: f = 랜삭(xx[안].astype(float), yy[안].astype(float), z[안], rng)
        g = z.copy(); g[안] = np.where(np.isnan(f), z[안], f); out[m] = g
    return np.clip(np.round(out), 0, 17).astype(np.uint8)
def 어긋(층, 선):   # 평평함 — 영역마다 평면 맞춤에서 1 층 넘게 벗어난 화소 비율(통째 칸 뺌)
    L, n = label(~선); 다 = 전 = 0
    for r in range(1, n + 1):
        m = (L == r) & (층 != 17)
        if m.sum() < 6: continue
        yy, xx = np.nonzero(m); f, _ = 맞춤(xx, yy, 층[m].astype(float), 1); 다 += (np.abs(층[m] - f) > 1).sum(); 전 += m.sum()
    return 다 / max(전, 1)
def 하나(job):
    k, p, 층, 선, 반, 틀b, 정b = job
    import trimesh, 짓기 as J, 평가51나 as E, 천장쪼개기52 as C, 자63 as A
    풀 = lambda b: np.unpackbits(b)[:48 ** 3].reshape(48, 48, 48).astype(bool)
    묶 = np.stack([면묶기(층[d], 선[d], d) for d in range(6)]); 틀, 정 = 풀(틀b), 풀(정b)
    v = C.깎(틀, E.지도(묶, 반), 48, True, [float(x) for x in 반])
    try:
        vv, ff, _ = J.정규메시(p); 점 = trimesh.sample.sample_surface(trimesh.Trimesh(vv, ff, process=False), A.점수, seed=0)[0]; F = A.F(A.칸표면(v, 1), 점)
    except Exception: F = np.nan
    return [F, float((v & 정).sum() / max((v | 정).sum(), 1)), 어긋(층[0], 선[0]), 어긋(묶[0], 선[0])], np.packbits(v)
if __name__ == "__main__":
    시 = np.load(O + "데이터.npz")["시험"]; te = np.nonzero(시)[0]; 범 = json.load(open(O + "범위46.json")); 예부 = te[범]
    P = np.load(O + "학습51나_판0전체/예측.npy", mmap_mode="r"); 입 = np.load(O + "입력51.npy", mmap_mode="r"); z = np.load(O + "데이터51.npz"); 반, 틀, 정 = z["반"], z["틀"], z["정답"]
    L = json.load(open(O + "목록.json", encoding="utf-8")); 쓸 = range(8) if "QUICK" in sys.argv else range(len(예부))
    일 = [(k, L[예부[k]], np.array(P[범[k]]), np.array(입[예부[k], :, 0]) > 0, 반[예부[k]], 틀[예부[k]], 정[예부[k]]) for k in 쓸]
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 4, maxtasksperchild=20) as pool: 출 = pool.map(하나, 일, chunksize=2)
    R = np.array([o[0] for o in 출], float); V4 = np.load(O + "영역64/값.npy")[: len(R)]
    if "QUICK" in sys.argv: print(np.round(np.c_[V4[:, 0], V4[:, 1], R], 3)); sys.exit()
    np.save(D + "값.npy", R); np.save(D + "칸.npy", np.stack([o[1] for o in 출])); R0 = np.nan_to_num(R); c0 = np.nan_to_num(V4[:, 0]); 망 = int((R0[:, 0] < c0 - .05).sum())
    결과 = {"712 F 대조": float(c0.mean()), "712 F 판정64 묶기": float(np.nan_to_num(V4[:, 1]).mean()), "712 F 면 맞춤": float(R0[:, 0].mean()), "712 IoU 대조": float(np.nan_to_num(V4[:, 2]).mean()), "712 IoU 면 맞춤": float(R0[:, 1].mean()),
          "평평함 대조": float(R0[:, 2].mean()), "평평함 면 맞춤": float(R0[:, 3].mean()), "F 0.05 넘게 떨어진 부품": 망, "F 오른 부품(+0.01)": int((R0[:, 0] > c0 + .01).sum()), "실패": int(np.isnan(R[:, 0]).sum()),
          "판정": {"F ≥ 대조 + 0.005": bool(R0[:, 0].mean() >= c0.mean() + .005), "평평함 절반": bool(R0[:, 3].mean() <= R0[:, 2].mean() / 2), "망침 ≤ 50": 망 <= 50}}
    json.dump(결과, open("결과판정65.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(결과, ensure_ascii=False, indent=1))
