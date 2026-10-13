# 로드맵 2(사용자 「ㄱㄱ」 10-13) — 실제 CAD 부품(Fusion 360 Gallery · AutoMate 부품 STL)으로 「위에서 본 선 그림 ↔ 화소마다 정답」 데이터셋
# venv python 데이터.py [개수=10000] → out/설명/캐드부품/데이터.npz · 목록.json · 예시.png
# 부품마다: 가장 얇은 축을 위로(판 모양 부품이 많다) → 위에서 광선 128² → 정답: 0 바깥 · 1 윗면 · 2 관통 · 3 들어감(+ 깊이 비율)
# 선 그림: 바깥 윤곽 + 높이 끊김 + 꺾임(기존 준비.선 과 같은 규칙) · 시험 = 조립 폴더 이름 해시로 10 % (같은 조립 부품이 학습 · 시험에 갈리지 않게)
import os, sys, json, hashlib, numpy as np
from multiprocessing import Pool
PARTS = "G:/art2real/원화3d/out/레퍼런스/CAD조립/parts/"; O = "G:/art2real/out/설명/캐드부품/"; os.makedirs(O, exist_ok=True)
N = 128; 문턱 = .03   # 들어감 = 윗면보다 높이의 3 % 넘게 낮음

def 하나(p):
    try:
        import trimesh, open3d as o3d, cv2
        m = trimesh.load(p, force="mesh")
        if len(m.faces) < 50 or len(m.faces) > 300000: return None
        e = m.extents; ax = int(np.argmin(e)); order = [i for i in range(3) if i != ax] + [ax]   # 가장 얇은 축 → Z
        v = (m.vertices - m.bounds.mean(0))[:, order] / e.max(); H = float(e[ax] / e.max())
        if H < .02: return None
        sc = o3d.t.geometry.RaycastingScene(); sc.add_triangles(o3d.core.Tensor(v.astype(np.float32)), o3d.core.Tensor(m.faces.astype(np.uint32)))
        u = (np.arange(N) + .5) / N * 1.1 - .55; X_, Y_ = np.meshgrid(u, -u); ray = np.zeros((N, N, 6), np.float32); ray[..., 0], ray[..., 1], ray[..., 2], ray[..., 5] = X_, Y_, 1.0, -1
        t = sc.cast_rays(o3d.core.Tensor(ray.reshape(-1, 6)))["t_hit"].numpy().reshape(N, N); S = np.isfinite(t)
        if S.sum() < 200: return None
        z = np.where(S, 1.0 - t, np.nan); top = np.nanmax(z); d = np.where(S, (top - z) / max(H, 1e-6), 0)   # 윗면에서 얼마나 내려갔나(높이 비율)
        s8 = S.astype(np.uint8); cs, _ = cv2.findContours(s8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); 밖 = np.zeros_like(s8); cv2.drawContours(밖, cs, -1, 1, -1); 밖 = 밖 > 0
        Y = np.zeros((N, N), np.uint8); Y[밖] = 1; Y[밖 & ~S] = 2; Y[S & (d > 문턱)] = 3
        zz = np.where(S, z, top - H)   # 선 그림: 바깥 윤곽 + 높이 끊김 + 꺾임
        gx, gy = np.abs(np.diff(zz, axis=0, append=zz[-1:])), np.abs(np.diff(zz, axis=1, append=zz[:, -1:]))
        cx, cy = np.abs(np.diff(zz, 2, axis=0, prepend=zz[:1], append=zz[-1:])), np.abs(np.diff(zz, 2, axis=1, prepend=zz[:, :1], append=zz[:, -1:]))
        밖8 = 밖.astype(np.uint8); 테 = (밖8 - cv2.erode(밖8, np.ones((3, 3), np.uint8))) > 0; 구테 = (s8 - cv2.erode(s8, np.ones((3, 3), np.uint8))) > 0
        L = 테 | 구테 | (((gx > .03) | (gy > .03) | (cx > .004) | (cy > .004)) & S)
        return L.astype(np.uint8), Y, np.where(Y == 3, d, 0).astype(np.float16), H
    except Exception: return None

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
    폴더 = sorted(f for f in os.listdir(PARTS) if os.path.isdir(PARTS + f)); 전부 = [(f, PARTS + f + "/" + s) for f in 폴더 for s in sorted(os.listdir(PARTS + f)) if s.lower().endswith(".stl")]
    rng = np.random.default_rng(30); 고름 = [전부[i] for i in rng.permutation(len(전부))[: int(n * 1.3)]]   # 걸러질 것을 감안해 1.3 배
    print("전체 부품", len(전부), "· 고른 후보", len(고름), flush=True)
    with Pool(6) as pool: R = pool.map(하나, [p for _, p in 고름], chunksize=20)
    ok = [(g, r) for g, r in zip(고름, R) if r is not None][:n]
    X = np.stack([r[0] for _, r in ok]); Y = np.stack([r[1] for _, r in ok]); D = np.stack([r[2] for _, r in ok]); Hs = np.array([r[3] for _, r in ok], np.float32)
    시험 = np.array([int(hashlib.md5(g[0].encode()).hexdigest(), 16) % 10 == 0 for g, _ in ok])
    np.savez_compressed(O + "데이터.npz", X=X, Y=Y, D=D, H=Hs, 시험=시험); json.dump([g[1] for g, _ in ok], open(O + "목록.json", "w", encoding="utf-8"), ensure_ascii=False)
    c = np.bincount(Y.ravel(), minlength=4) / Y.size
    print("만듦 %d (학습 %d · 시험 %d) · 화소 비율 바깥 %.2f 윗면 %.2f 관통 %.3f 들어감 %.3f · 깎을 것 있는 부품 %.0f%%" % (len(ok), (~시험).sum(), 시험.sum(), *c, 100 * np.mean([(y >= 2).sum() > 30 for y in Y])))
