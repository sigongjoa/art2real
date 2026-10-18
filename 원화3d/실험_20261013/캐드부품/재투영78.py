# 판정기준78 시험 — 만든 3D 에서 위 · 앞 · 옆 선 그림을 다시 뽑아 입력 선 그림과 맞댄다(정답 없이도 잴 수 있음) · 10-18
# 깎은 48³ → marching cubes → Taubin 10 → 위(+z 에서) · 앞(+y) · 옆(+x) 128² 광선 → 데이터_앞옆.선그림(데이터.py 와 같은 선 규칙) → 1 화소 허용 정밀 · 재현 · F(전체 선 · 안쪽 선)
# 사용(venv · ART_MEM_GB=8): 재투영78.py <정답 | 천장32 | 판0 | 선> → out/설명/캐드부품/재투영78/<팔>.npy (712 × 3 방향 × [정밀, 재현, F, 안정밀, 안재현, 안F])
#                          재투영78.py 실제 <칸.npy> <그림.png> <겹침.png> → 실제 그림 하나 점수 + 겹친 그림(초록 둘 다 · 빨강 그림만 · 파랑 3D 만)
import sys, os, json, numpy as np
from multiprocessing import Pool
O = "G:/art2real/out/설명/캐드부품/"; N = 128; 뷰 = [(0, 1, 2), (0, 2, 1), (1, 2, 0)]   # (가로축, 세로축, 쏘는 축) — 위 · 앞 · 옆 · 세로는 위가 큼(행 = −세로)
풀 = lambda b: np.unpackbits(b)[:48 ** 3].reshape(48, 48, 48).astype(bool)
def 칸메시(v):
    import trimesh; from skimage.measure import marching_cubes
    vs, fs, _, _ = marching_cubes(np.pad(v, 1).astype(np.float32), .5); m = trimesh.Trimesh((vs - .5) / 48 * 1.1 - .55, fs, process=False); trimesh.smoothing.filter_taubin(m, iterations=10); return m.vertices, m.faces
def 그리기(v, f):   # 메시 → [위, 앞, 옆] 선 그림 (N, N) bool — 데이터.py · 데이터_앞옆.py 와 같은 배치
    import open3d as o3d, 데이터_앞옆 as DA
    sc = o3d.t.geometry.RaycastingScene(); sc.add_triangles(o3d.core.Tensor(np.asarray(v, np.float32)), o3d.core.Tensor(np.asarray(f, np.uint32)))
    u = (np.arange(N) + .5) / N * 1.1 - .55; A, B = np.meshgrid(u, -u); out = []
    for 가, 세, 깊 in 뷰:
        r = np.zeros((N, N, 6), np.float32); r[..., 가] = A; r[..., 세] = B; r[..., 깊] = 1.0; r[..., 3 + 깊] = -1
        t = sc.cast_rays(o3d.core.Tensor(r.reshape(-1, 6)))["t_hit"].numpy().reshape(N, N); S = np.isfinite(t); out.append(DA.선그림(np.where(S, t, 0), S) > 0)
    return out
def 점수(p, t, 채):   # 1 화소 허용 · 채 = 입력 채운 윤곽(안쪽 = 3×3 침식)
    import cv2; K = np.ones((3, 3), np.uint8); d = lambda a: cv2.dilate(a.astype(np.uint8), K) > 0; 안 = cv2.erode(채.astype(np.uint8), K) > 0; r = []
    for a, b in ((p, t), (p & 안, t & 안)):
        if not a.any() and not b.any(): r += [1., 1., 1.]; continue   # 둘 다 선 없음 = 맞음
        pr = (a & d(b)).sum() / max(a.sum(), 1); re = (b & d(a)).sum() / max(b.sum(), 1); r += [pr, re, 2 * pr * re / max(pr + re, 1e-9)]
    return r
def 하나(job):
    k, 팔, 칸b, p, 그림 = job
    try:
        import 짓기 as J, 입력51 as I
        if 팔 != "정답" and not 풀(칸b).any(): return [[0.] * 6] * 3   # 빈 3D = 선 하나도 못 그림(0 점)
        v, f = J.정규메시(p)[:2] if 팔 == "정답" else 칸메시(풀(칸b)); 다 = 그리기(v, f)
        return [점수(a, g > 0, I._채움(g)) for a, g in zip(다, 그림)]
    except Exception as e: print("실패", k, e, flush=True); return [[np.nan] * 6] * 3
if __name__ == "__main__":
    sys.path.append("G:/art2real/원화3d/실험_20261013/구멍")
    if sys.argv[1] == "실제":
        import cv2, 실제76 as R, 입력51 as I; v = np.load(sys.argv[2]); X, F, S, _ = R.그림셋(sys.argv[3]); 다 = 그리기(*칸메시(v)); 그 = (X, F, S)
        s = [점수(a, g > 0, I._채움(g)) for a, g in zip(다, 그)]; 판 = []
        for a, g in zip(다, 그):
            g = g > 0; c = np.full((N, N, 3), 255, np.uint8); c[g & ~a] = (220, 50, 50); c[a & ~g] = (60, 120, 200); c[a & g] = (40, 160, 80); 판.append(cv2.resize(c, (384, 384), interpolation=cv2.INTER_NEAREST))
        cv2.imencode(".png", np.concatenate(판, 1)[..., ::-1])[1].tofile(sys.argv[4]); print(json.dumps({"F 위 · 앞 · 옆": [round(x[2], 3) for x in s], "안F": [round(x[5], 3) for x in s], "평균 F": round(float(np.mean([x[2] for x in s])), 3)}, ensure_ascii=False)); sys.exit()
    팔 = sys.argv[1]; D = O + "재투영78/"; os.makedirs(D, exist_ok=True)
    시 = np.load(O + "데이터.npz")["시험"]; te = np.nonzero(시)[0]; 범 = json.load(open(O + "범위46.json")); 예부 = te[범]; L = json.load(open(O + "목록.json", encoding="utf-8"))
    X = np.load(O + "데이터.npz")["X"]; e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"], e["S"]
    칸 = None if 팔 == "정답" else np.load(O + ("천장32/칸.npy" if 팔 == "천장32" else "학습69_%s/칸.npy" % 팔), mmap_mode="r")
    일 = [(k, 팔, None if 칸 is None else np.array(칸[k]), L[i], (X[i], F[i], S[i])) for k, i in enumerate(예부)]
    with Pool(4, maxtasksperchild=40) as pool: R = np.array(pool.map(하나, 일, chunksize=4), float)
    np.save(D + 팔 + ".npy", R); 거 = np.load(O + "거름62.npy"); m = np.nanmean(R[거], (0,)); print(팔, "450 방향 평균 F %.3f · 안F %.3f" % (np.nanmean(R[거][:, :, 2]), np.nanmean(R[거][:, :, 5])), "· 방향별 F", np.round(m[:, 2], 3).tolist(), "· 실패", int(np.isnan(R[:, 0, 0]).sum()), flush=True)
    if 팔 == "정답": assert np.nanmean(R[거][:, :, 2]) >= .95, "자가 틀림 — 정답 메시 재투영이 입력과 안 맞음"
