# 얇은 판 채점 후보 비교 — 정답 자기 · 한 칸 밀림(x · z) · 여섯 방향 정답 깊이 칸 깎기(층 내림 · 천장과 같은 것)
# M0 48³ 칸 가운데(지금) · M1 부분 점유(4³ 초표본 → 48³ 비율 · Σmin/Σmax) · M2 표면(F@τ=칸 · Chamfer/칸) · M3 칸 가운데 96³ · 192³
import sys, json, time, numpy as np
sys.path.insert(0, "G:/art2real/원화3d/실험_20261013/캐드부품")
import 짓기 as J, 여섯방향 as S6
O = "G:/art2real/out/설명/캐드부품/"; 칸48 = 1.1 / 48

def 점유(v, f, n):   # J.점유_메시 와 같은 선 교차 · 홀수 기둥만 그 기둥 칸 가운데를 compute_occupancy(전체 n³ 대신)
    import open3d as o3d
    g = (np.arange(n) + .5) / n * 1.1 - .55; sc = o3d.t.geometry.RaycastingScene(); sc.add_triangles(o3d.core.Tensor(np.asarray(v, np.float32)), o3d.core.Tensor(np.asarray(f, np.uint32)))
    X, Y = np.meshgrid(g, g, indexing="ij"); r = np.zeros((n * n, 6), np.float32); r[:, 0], r[:, 1], r[:, 2], r[:, 5] = X.ravel(), Y.ravel(), 1.0, -1
    Lr = sc.list_intersections(o3d.core.Tensor(r)); sp = Lr["ray_splits"].numpy(); t = Lr["t_hit"].numpy(); q = np.zeros((n, n, n), bool); 홀 = []
    for k in range(n * n):
        z = np.sort(1.0 - t[sp[k]:sp[k + 1]]); z = z[np.r_[True, np.diff(z) > 1e-6]] if len(z) else z; i, j = divmod(k, n)
        if len(z) % 2 == 0:
            for a, b in zip(z[0::2], z[1::2]): q[i, j] |= (g >= a) & (g <= b)
        else: 홀.append((i, j))
    if 홀:
        P = np.array([[g[i], g[j], zz] for i, j in 홀 for zz in g], np.float32)
        o = sc.compute_occupancy(o3d.core.Tensor(P), nsamples=9).numpy().reshape(len(홀), n) > .5
        for (i, j), row in zip(홀, o): q[i, j] = row
    return q

def 깊이표(층, 반):   # 방향마다 (r, h, 깎을 깊이 128²) — 여섯방향.층 과 같은 내림(층 번호가 이미 내림 · 17 = 통째)
    out = []
    for n, k in enumerate(S6.방향):
        h = float(반[n]); 단 = 2 * h / S6.층수; out.append((S6.R(*S6.방향[k]), h, np.where(층[n] == 17, 2 * h + .1, 층[n] * 단)))
    return out

def 깎기안(P, 표, 상자, 여유=0.0):   # 점 P(M,3) 가 칸 깎기 결과 안인가 · 상자 = (lo, hi) 틀 대신(세 윤곽 틀은 여섯 깊이에 거의 포함)
    q = np.all((P >= 상자[0] - 여유) & (P <= 상자[1] + 여유), 1)
    for r, h, 깊 in 표:
        L = P @ r; x = np.clip(np.round((L[:, 0] + .55) / S6.칸 - .5).astype(int), 0, S6.N - 1); y = np.clip(np.round((-L[:, 1] + .55) / S6.칸 - .5).astype(int), 0, S6.N - 1)
        q &= L[:, 2] <= h - 깊[y, x] + 여유
    return q

def 깎기칸(표, 상자, n):
    g = ((np.arange(n) + .5) / n * 1.1 - .55).astype(np.float32); out = np.zeros((n, n, n), bool)
    for i in range(n):   # 한 판씩(메모리)
        P = np.stack(np.meshgrid(g[i:i + 1], g, g, indexing="ij"), -1).reshape(-1, 3); out[i] = 깎기안(P, 표, 상자).reshape(n, n)
    return out

def 깎기표면(표, 상자):   # 깊이 지도 화소마다 첫 맞음 점 → 나머지 방향에 안 깎인 것만(보이는 표면) · 여유 1e-3
    g = (np.arange(S6.N) + .5) * S6.칸 - .55; U, V = np.meshgrid(g, -g); 점 = []
    for r, h, 깊 in 표:
        m = 깊 < 2 * h; L = np.stack([U[m], V[m], h - 깊[m]], -1); 점.append(L @ r.T)
    P = np.concatenate(점) if 점 else np.zeros((0, 3)); return P[깎기안(P, 표, 상자, 1e-3)]

def IoU(a, b): return float((a & b).sum() / max((a | b).sum(), 1))
def 부분IoU(a, b):
    n = a.shape[0] // 48; fa = a.reshape(48, n, 48, n, 48, n).mean((1, 3, 5)); fb = b.reshape(48, n, 48, n, 48, n).mean((1, 3, 5)); return float(np.minimum(fa, fb).sum() / max(np.maximum(fa, fb).sum(), 1e-9))
def 표면(A, B, τ=칸48):   # A 정답 표면 점 · B 시험 표면 점 → (F@τ, Chamfer/칸)
    from scipy.spatial import cKDTree
    if len(B) == 0 or len(A) == 0: return (0.0, float("nan"))
    da = cKDTree(B).query(A)[0]; db = cKDTree(A).query(B)[0]; 재 = (da < τ).mean(); 정 = (db < τ).mean()
    return (float(2 * 재 * 정 / max(재 + 정, 1e-9)), float((da.mean() + db.mean()) / 2 / 칸48))

def 하나(job):
    p, 층, 반, 틀칸 = job; t0 = time.time()
    try:
        import trimesh
        v, f, H = J.정규메시(p); m = trimesh.Trimesh(v, f, process=False); 표 = 깊이표(층, 반); 상자 = (v.min(0) - 1e-4, v.max(0) + 1e-4)
        rng = np.random.default_rng(0); 샘 = lambda: trimesh.sample.sample_surface(m, 20000, seed=int(rng.integers(1 << 30)))[0]
        밀 = {"자기": np.zeros(3), "밀림x": np.array([칸48, 0, 0]), "밀림z": np.array([0, 0, 칸48])}
        occ = {n: {"정답": 점유(v, f, n)} for n in (48, 96, 192)}
        for k, d in 밀.items():
            if k != "자기":
                for n in occ: occ[n][k] = 점유(v + d, f, n)
            else:
                for n in occ: occ[n][k] = occ[n]["정답"]
        for n in occ: occ[n]["깎기"] = 깎기칸(표, 상자, n)
        g48 = (np.arange(48) + .5) / 48 * 1.1 - .55; P48 = np.stack(np.meshgrid(g48, g48, g48, indexing="ij"), -1).reshape(-1, 3)
        깎틀48 = 틀칸 & 깎기안(P48, 표, (np.full(3, -9.0), np.full(3, 9.0))).reshape(48, 48, 48)   # 천장 그대로(틀칸) — 영역53 열 0 과 맞춰 보기
        A = 샘(); 표점 = {"자기": 샘(), "밀림x": 샘() + 밀["밀림x"], "밀림z": 샘() + 밀["밀림z"], "깎기": 깎기표면(표, 상자)}
        out = {"H": float(H), "부피": float(abs(m.volume)) if m.is_watertight else None, "칸48수": int(occ[48]["정답"].sum()), "천장틀": IoU(깎틀48, occ[48]["정답"])}
        for k in ("자기", "밀림x", "밀림z", "깎기"):
            F, C = 표면(A, 표점[k])
            out[k] = {"M0_48": IoU(occ[48][k], occ[48]["정답"]), "M1_부분": 부분IoU(occ[192][k], occ[192]["정답"]), "M2_F": F, "M2_CD칸": C,
                      "M3_96": IoU(occ[96][k], occ[96]["정답"]), "M3_192": IoU(occ[192][k], occ[192]["정답"])}
        out["초"] = time.time() - t0; return out
    except Exception as e: return {"실패": type(e).__name__ + " " + str(e)[:80]}

if __name__ == "__main__":
    from multiprocessing import Pool
    d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; del d
    L = json.load(open(O + "목록.json", encoding="utf-8")); 범 = json.load(open(O + "범위46.json")); a = np.load(O + "영역53.npy")
    z = np.load(O + "데이터51.npz"); 풀 = lambda b: np.unpackbits(b)[:48 ** 3].reshape(48, 48, 48).astype(bool)
    낮 = list(np.nonzero(a[:, 0] < .5)[0]); 나머지 = np.nonzero(a[:, 0] >= .5)[0]; 무 = list(np.random.default_rng(0).choice(나머지, 100, replace=False))
    고른 = [int(x) for x in 낮 + 무]
    if len(sys.argv) > 1: 고른 = 고른[:int(sys.argv[1])]
    ii = [te[범[k]] for k in 고른]; 층 = z["층"][ii]; 반 = z["반"][ii]; 틀 = z["틀"][ii]; del z   # npz 는 꺼낼 때마다 통째로 풀린다 — 한 번만
    jobs = [(L[i], 층[n], 반[n], 풀(틀[n])) for n, i in enumerate(ii)]; del 층
    with Pool(2, maxtasksperchild=10) as pool: R = pool.map(하나, jobs, chunksize=1)
    for k, r in zip(고른, R): r["k"] = k; r["천장53"] = float(a[k, 0]); r["무리"] = "89" if a[k, 0] < .5 else "100"
    json.dump(R, open("결과.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0); print("끝", sum("실패" in r for r in R), "실패")
