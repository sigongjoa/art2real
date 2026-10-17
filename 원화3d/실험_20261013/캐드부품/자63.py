# 판정기준63 — 새 자: 표면 F-score@1 칸 · 정답 = 메시 표면 점 · 답 = 48³ 칸 → 마칭 큐브 표면 점 · 10-17
# 사용(venv · ART_MEM_GB=8): 자63.py [일꾼=4] → out/설명/캐드부품/자63.npy(712 × 열) · 결과판정63.json
import sys, json, numpy as np
from multiprocessing import Pool
import os
O = "G:/art2real/out/설명/캐드부품/"; n = 48; 칸 = 1.1 / n; τ = 칸 * float(os.environ.get("TAU", 1)); 점수 = 20000   # TAU = 칸 배수(판정은 1 · 0.5 는 참고)
판들 = ["판0예측", "HF", "H"]; 열 = ["반 칸 옮긴 정답", "정답 칸", "틀"] + 판들
풀 = lambda b: np.unpackbits(b)[:n ** 3].reshape(n, n, n).astype(bool)
def 칸표면(v, rng):   # 칸 [i,j,k] 중심 = (i+.5)/n*1.1-.55 — 짓기.점유_메시 와 같은 좌표
    import trimesh; from skimage.measure import marching_cubes
    if v.sum() == 0: return None
    vs, fs, _, _ = marching_cubes(np.pad(v, 1).astype(np.float32), .5); vs = (vs - 1 + .5) / n * 1.1 - .55
    return trimesh.sample.sample_surface(trimesh.Trimesh(vs, fs, process=False), 점수, seed=rng)[0]
def F(a, b):   # a 답 점 · b 정답 점
    from scipy.spatial import cKDTree
    if a is None or b is None: return 0.0
    p = (cKDTree(b).query(a, distance_upper_bound=τ)[0] <= τ).mean(); r = (cKDTree(a).query(b, distance_upper_bound=τ)[0] <= τ).mean()
    return float(2 * p * r / (p + r)) if p + r else 0.0
def 하나(job):
    k, p, 칸들 = job
    try:
        import trimesh, 짓기 as J
        v, f, _ = J.정규메시(p); 정 = trimesh.sample.sample_surface(trimesh.Trimesh(v, f, process=False), 점수, seed=0)[0]
        옮 = np.mean([F(정 + np.eye(3)[a] * 칸 / 2, 정) for a in range(3)])
        return [옮] + [F(칸표면(풀(b), 1 + i), 정) for i, b in enumerate(칸들)]
    except Exception as ex: return [np.nan] * len(열)
if __name__ == "__main__":
    z = np.load(O + "데이터51.npz"); z = {"정답": z["정답"], "틀": z["틀"]}; 시 = np.load(O + "데이터.npz")["시험"]; L = json.load(open(O + "목록.json", encoding="utf-8"))
    예부 = np.nonzero(시)[0][json.load(open(O + "범위46.json"))]; P = {m: np.load(O + "학습58_%s/예측.npy" % m) for m in 판들}
    일 = [(k, L[i], [z["정답"][i], z["틀"][i]] + [P[m][k] for m in 판들]) for k, i in enumerate(예부)]
    if "QUICK" in sys.argv: 일 = 일[:8]
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 4, maxtasksperchild=20) as pool: R = np.array(pool.map(하나, 일, chunksize=4))
    if "QUICK" in sys.argv: print(np.round(R, 3)); sys.exit()
    np.save(O + "자63%s.npy" % os.environ.get("TAU", ""), R); R0 = np.nan_to_num(R)
    t = np.load(O + "학습58_H/부피IoU.npy")[:, 1]; 어 = t < .5; 거 = np.load(O + "거름62.npy"); from scipy.ndimage import binary_erosion
    얇 = np.array([not binary_erosion(풀(z["정답"][i])).any() for i in 예부]) & 어
    묶 = {"712": np.ones(len(R), bool), "어려운 217": 어, "얇은 124": 얇, "거른 450": 거, "거른 어려운 67": 거 & 어}
    결과 = {g: {c: round(float(R0[m, j].mean()), 3) for j, c in enumerate(열)} for g, m in 묶.items()}; 결과["실패(nan)"] = int(np.isnan(R[:, 0]).sum())
    결과["자 감사"] = {"반 칸 내성 ≥ 0.95": bool(min(결과[g]["반 칸 옮긴 정답"] for g in 묶) >= .95), "칸 표현 천장 712": 결과["712"]["정답 칸"], "틀 < 58": bool(결과["712"]["틀"] < 결과["712"]["판0예측"])}
    json.dump(결과, open("결과판정63%s.json" % ("_TAU" + os.environ["TAU"] if "TAU" in os.environ else ""), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(결과, ensure_ascii=False, indent=1))
