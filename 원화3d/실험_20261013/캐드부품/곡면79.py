# 판정기준79 (가) — 방향별 깊이 지도를 도면 선 · 층 끊김으로 조각내고, 조각마다 평면 · 원통 · 구 · 2 차를 맞춰 연속 장으로 깎는다(칸 계단 없음) · 10-18
# 사용(venv · ART_MEM_GB=8): 곡면79.py → out/설명/캐드부품/곡면79/ 결과.json · 메시 <팔>_<k>.npz · 결과판정79.json
import sys, os, json, numpy as np
from multiprocessing import Pool
sys.path.append("G:/art2real/원화3d/실험_20261013/구멍")
O = "G:/art2real/out/설명/캐드부품/"; D = O + "곡면79/"; N = 128; G = 160; 팔들 = ["칸32", "연속정답", "단32장", "단32맞춤", "판0칸", "판0맞춤"]
def 조각(L, 층):   # 선 그림 · 층(0~32) → 조각 번호 (0 = 통째 · 선 화소도 가까운 조각에)
    from scipy import ndimage as nd
    끊 = np.zeros(층.shape, bool); a = 층.astype(int); 끊[:-1] |= np.abs(a[1:] - a[:-1]) >= 2; 끊[:, :-1] |= np.abs(a[:, 1:] - a[:, :-1]) >= 2
    벽 = (L > 0) | 끊; 쓸 = (층 < 32) & ~벽; lab, n = nd.label(쓸)
    _, (iy, ix) = nd.distance_transform_edt(lab == 0, return_indices=True); lab = np.where(층 < 32, lab[iy, ix], 0); return lab
def 맞추기(lab, d, 단, u, v):   # 조각마다 가장 단순한 곡면 · → 연속 깊이 (nan = 통째)
    from scipy import ndimage as nd
    out = np.full(d.shape, np.nan); 쓴 = {}
    for j in range(1, lab.max() + 1):
        m = lab == j; n = m.sum()
        if n == 0: continue
        U, V, Z = u[m], v[m], d[m]
        if n < 6: out[m] = Z; continue
        후 = []
        A = np.c_[U, V, np.ones(n)]; 후.append(("평면", A))
        for 이름, 가로 in (("원통u", V), ("원통v", U)):   # 축이 u(또는 v)인 원통: 단면 (가로, d) 원 맞춤 → d = c ± sqrt(r² − (가로 − a)²)
            try:
                q, *_ = np.linalg.lstsq(np.c_[가로, Z, np.ones(n)], -(가로 ** 2 + Z ** 2), rcond=None); a0, c0 = -q[0] / 2, -q[1] / 2; r2 = a0 ** 2 + c0 ** 2 - q[2]
                s = r2 - (가로 - a0) ** 2
                if r2 > 0 and (s >= 0).all(): 후.append((이름, (a0, c0, r2, 가로)))
            except Exception: pass
        후.append(("2차", np.c_[U, V, np.ones(n), U * U, V * V, U * V]))
        골 = None
        for 이름, A in 후:
            if isinstance(A, tuple):
                a0, c0, r2, 가로 = A; s = np.sqrt(r2 - (가로 - a0) ** 2); z = np.where(np.abs(c0 - s - Z) < np.abs(c0 + s - Z), c0 - s, c0 + s)
            else: z = A @ np.linalg.lstsq(A, Z, rcond=None)[0]
            if np.sqrt(np.mean((z - Z) ** 2)) <= .6 * 단: 골 = (이름, z); break
        if 골 is None:   # 조각 안 매끄럽게(정규화 합성곱)
            w = m.astype(float); s = nd.gaussian_filter(np.where(m, d, 0), 1.5) / np.maximum(nd.gaussian_filter(w, 1.5), 1e-6); 골 = ("매끈", s[m])
        out[m] = 골[1]; 쓴[골[0]] = 쓴.get(골[0], 0) + int(n)
    return out, 쓴
def 장메시(위들, 반):   # 위들[k] = 지역 w 의 표면(N × N · nan = 통째) → 연속 장 marching cubes
    import 여섯방향 as S6; from scipy.ndimage import map_coordinates; from skimage.measure import marching_cubes
    Δ = 1.1 / G; g3 = (np.arange(G) + .5) * Δ - .55; P = np.stack(np.meshgrid(g3, g3, g3, indexing="ij"), -1).reshape(-1, 3).astype(np.float32); f = np.full(len(P), np.inf, np.float32)
    for (k, 방), 위, h in zip(enumerate(S6.방향), 위들, 반):
        loc = P @ S6.R(*S6.방향[방]).astype(np.float32); 바닥 = -h - .05
        px = (loc[:, 0] + .55) / S6.칸 - .5; py = (-loc[:, 1] + .55) / S6.칸 - .5
        s = map_coordinates(np.nan_to_num(위, nan=바닥).astype(np.float32), [py, px], order=1, mode="constant", cval=바닥); f = np.minimum(f, s - loc[:, 2])
    f = f.reshape(G, G, G)
    if f.max() <= 0: return None
    vs, fs, _, _ = marching_cubes(np.pad(f, 1, constant_values=-1), 0); return (vs - 1) * Δ + g3[0], fs
def 메시F(v, f, gv, gf, τ=1.1 / 48):   # → [F 1 칸, F 반 칸, 법선 오차 평균 °, 15° 넘는 몫]
    import trimesh; from scipy.spatial import cKDTree
    A = trimesh.Trimesh(v, f, process=False); B = trimesh.Trimesh(gv, gf, process=False)
    a, ia = trimesh.sample.sample_surface(A, 20000, seed=0); b, ib = trimesh.sample.sample_surface(B, 20000, seed=0); da, ja = cKDTree(b).query(a); db = cKDTree(a).query(b)[0]; o = []
    for t in (τ, τ / 2): p = (da <= t).mean(); r = (db <= t).mean(); o.append(float(2 * p * r / max(p + r, 1e-9)))
    각 = np.degrees(np.arccos(np.clip(np.abs((A.face_normals[ia] * B.face_normals[ib][ja]).sum(1)), 0, 1))); return o + [float(각.mean()), float((각 > 15).mean())]
def 하나(job):
    k, i, p, 층정, 층판, 칸정, 칸판, 반, 선, 그림 = job
    import 짓기 as J, 여섯방향 as S6, 재투영78 as R, 입력51 as I
    gv, gf, _ = J.정규메시(p); 깊 = S6.깊이지도(gv, gf); 방 = list(S6.방향); u = np.tile(S6.g, (N, 1)); v = -u.T; out = {}; 쓴 = {}
    def 층위(층, 맞춤):   # 층 → 지역 w 표면 지도들
        위들 = []
        for j, h in enumerate(반):
            단 = 2 * h / 32; d = np.where(층[j] == 32, np.nan, 층[j] * 단)
            if 맞춤:
                d, c = 맞추기(조각(선[j], 층[j]), np.nan_to_num(d), 단, u, v); [쓴.__setitem__(x, 쓴.get(x, 0) + y) for x, y in c.items()]
            위들.append(h - d)
        return 위들
    메 = {"칸32": R.칸메시(np.unpackbits(칸정)[:48 ** 3].reshape(48, 48, 48).astype(bool)), "판0칸": R.칸메시(np.unpackbits(칸판)[:48 ** 3].reshape(48, 48, 48).astype(bool)),
          "연속정답": 장메시([깊[d] for d in 방], 반), "단32장": 장메시(층위(층정, False), 반), "단32맞춤": 장메시(층위(층정, True), 반), "판0맞춤": 장메시(층위(층판, True), 반)}
    for 팔, m in 메.items():
        if m is None: out[팔] = [0., 0., 90., 1., 0.]; continue
        vv, ff = m; 다 = R.그리기(vv, ff); out[팔] = 메시F(vv, ff, gv, gf) + [float(np.mean([R.점수(a, g > 0, I._채움(g))[2] for a, g in zip(다, 그림)]))]
        np.savez_compressed(D + "%s_%d.npz" % (팔, k), v=np.asarray(vv, np.float32), f=np.asarray(ff, np.int32))
    print(k, {a: [round(x, 3) for x in b] for a, b in out.items()}, flush=True); return k, out, 쓴
if __name__ == "__main__":
    os.makedirs(D, exist_ok=True); 시 = np.load(O + "데이터.npz")["시험"]; te = np.nonzero(시)[0]; 범 = json.load(open(O + "범위46.json")); 예부 = te[범]; 거 = np.load(O + "거름62.npy")
    ks = np.random.default_rng(79).choice(np.nonzero(거)[0], int(os.environ.get("NUM", 20)), replace=False); L = json.load(open(O + "목록.json", encoding="utf-8"))
    층32 = np.load(O + "층32.npy", mmap_mode="r"); P = np.load(O + "학습69_판0/예측.npy", mmap_mode="r"); 입 = np.load(O + "입력51.npy", mmap_mode="r"); 반 = np.load(O + "데이터51.npz")["반"]
    C정 = np.load(O + "천장32/칸.npy", mmap_mode="r"); C판 = np.load(O + "학습69_판0/칸.npy", mmap_mode="r"); X = np.load(O + "데이터.npz")["X"]; e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"], e["S"]
    일 = [(int(k), int(예부[k]), L[예부[k]], np.array(층32[예부[k]]), np.array(P[범[k]]), np.array(C정[k]), np.array(C판[k]), 반[예부[k]], np.array(입[예부[k], :, 0]), (X[예부[k]], F[예부[k]], S[예부[k]])) for k in ks]
    with Pool(4, maxtasksperchild=5) as pool: R_ = pool.map(하나, 일, chunksize=1)
    평 = {팔: [round(float(np.mean([r[1][팔][j] for r in R_])), 4) for j in range(5)] for 팔 in 팔들}; 쓴 = {}
    for r in R_:
        for a, b in r[2].items(): 쓴[a] = 쓴.get(a, 0) + b
    결 = {"부품": [int(k) for k in ks], "팔별 [메시 F 1 칸, 메시 F 반 칸, 법선 오차 °, 15° 넘는 몫, 다시 그린 선 F(참고)]": 평, "맞춘 곡면 화소 몫": {a: round(b / max(sum(쓴.values()), 1), 3) for a, b in 쓴.items()}}
    결["판정"] = {"감사 연속정답 F ≥ 0.95 · 15° 몫 ≤ 0.05": bool(평["연속정답"][0] >= .95 and 평["연속정답"][3] <= .05),
                "(가) 천장": bool(평["단32맞춤"][3] <= 평["칸32"][3] * .7 and 평["단32맞춤"][0] >= 평["칸32"][0] - .005),
                "(가) 실제": bool(평["판0맞춤"][3] <= 평["판0칸"][3] * .7 and 평["판0맞춤"][0] >= 평["판0칸"][0] - .005)}
    json.dump({"요약": 결, "부품별": {str(r[0]): r[1] for r in R_}}, open(D + "결과.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); json.dump(결, open("결과판정79.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(결, ensure_ascii=False, indent=1))
