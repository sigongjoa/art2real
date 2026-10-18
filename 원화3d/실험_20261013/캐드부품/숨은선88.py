# 숨은선 데이터 — 위(+z 에서) · 앞(+y) · 옆(+x) 128² 광선이 지나는 면 전부(list_intersections) · 둘째 이후 면에 데이터.py 와 같은 선 규칙 · 보이는 선과 겹치면 뺌 · 10-19
# 사용자 10-19 「숨은선 데이터부터 만들어」 — 지금 데이터(데이터.py · 데이터_앞옆.py)는 첫 면(t_hit)만 봐서 실선뿐 · GPT 에는 실선 · 점선 삼면도를 요청하면 됨
# 사용(venv · ART_MEM_GB=12): 숨은선88.py 시험 → 막힌 구멍 상자 확인 · 숨은선88.py → out/설명/캐드부품/숨은선88.npz (HX · HF · HS uint8 · 목록.json 순서)
import sys, json, numpy as np
from multiprocessing import Pool
N = 128; O = "G:/art2real/out/설명/캐드부품/"; K = 6   # 광선마다 최대 6 면
def 선규칙(zz, S):   # 높이 지도(클수록 보는 쪽에 가까움) · 맞은 곳 → 테 ∪ 끊김(> .03) ∪ 꺾임(> .004) — 데이터.py · 데이터_앞옆.py 와 같은 문턱
    import cv2
    gx, gy = np.abs(np.diff(zz, axis=0, append=zz[-1:])), np.abs(np.diff(zz, axis=1, append=zz[:, -1:]))
    cx, cy = np.abs(np.diff(zz, 2, axis=0, prepend=zz[:1], append=zz[-1:])), np.abs(np.diff(zz, 2, axis=1, prepend=zz[:, :1], append=zz[:, -1:]))
    s8 = S.astype(np.uint8); 테 = (s8 - cv2.erode(s8, np.ones((3, 3), np.uint8))) > 0
    return 테 | (((gx > .03) | (gy > .03) | (cx > .004) | (cy > .004)) & S)
def 그리기(v, f):   # 메시 → [(보이는 선, 숨은선) × 위 · 앞 · 옆] bool
    import open3d as o3d
    sc = o3d.t.geometry.RaycastingScene(); sc.add_triangles(o3d.core.Tensor(np.asarray(v, np.float32)), o3d.core.Tensor(np.asarray(f, np.uint32)))
    u = (np.arange(N) + .5) / N * 1.1 - .55; A, B = np.meshgrid(u, -u); out = []
    for 가, 세, 깊 in ((0, 1, 2), (0, 2, 1), (1, 2, 0)):   # 위: 가로 x · 세로 y · +z 에서 / 앞: x · z · +y 에서 / 옆: y · z · +x 에서
        r = np.zeros((N, N, 6), np.float32); r[..., 가] = A; r[..., 세] = B; r[..., 깊] = 1.0; r[..., 3 + 깊] = -1
        q = sc.list_intersections(o3d.core.Tensor(r.reshape(-1, 6))); t = q["t_hit"].numpy(); ri = q["ray_ids"].numpy().astype(np.int64); 면 = np.full((N * N, K), np.inf, np.float32)
        if len(t):
            o = np.lexsort((t, ri)); t, ri = t[o], ri[o]; 새 = np.concatenate([[True], (ri[1:] != ri[:-1]) | (np.diff(t) > 1e-5)]); t, ri = t[새], ri[새]   # 모서리에서 겹친 맞음 하나로
            처 = np.concatenate([[True], ri[1:] != ri[:-1]]); 순 = np.arange(len(ri)) - np.maximum.accumulate(np.where(처, np.arange(len(ri)), 0)); k_ = 순 < K; 면[ri[k_], 순[k_]] = t[k_]
        면 = 면.reshape(N, N, K); 맞 = np.isfinite(면); 보 = 선규칙(np.where(맞[..., 0], -면[..., 0], -3.), 맞[..., 0]); 숨 = np.zeros((N, N), bool)
        for k in range(1, K):
            if not 맞[..., k].any(): break
            숨 |= 선규칙(np.where(맞[..., k], -면[..., k], -3.), 맞[..., k])
        out.append((보, 숨 & ~보))
    return out
def 하나(p):
    try:
        import trimesh; m = trimesh.load(p, force="mesh"); e = m.extents; ax = int(np.argmin(e)); order = [i for i in range(3) if i != ax] + [ax]
        v = (m.vertices - m.bounds.mean(0))[:, order] / e.max(); return [np.packbits(h) for _, h in 그리기(v, m.faces)]
    except Exception: return [np.packbits(np.zeros((N, N), bool))] * 3
def 시험():   # 정답 아는 모양: 상자 .6 × .6 × .3 안에 숨은 빈 방 .3 × .2 × .1(면 뒤집은 상자 · 불리언 안 씀 — trimesh 차집합은 엔진이 없어 빈 메시) → 위 · 앞에서 빈 방 윤곽은 숨은선에만
    import trimesh
    겉 = trimesh.creation.box((.6, .6, .3)); 속 = trimesh.creation.box((.3, .2, .1)); 속.invert(); m = trimesh.util.concatenate([겉, 속])
    (위보, 위숨), (앞보, 앞숨), _ = 그리기(m.vertices, m.faces); g = (np.arange(N) + .5) / N * 1.1 - .55; 칸 = 1.1 / N
    yy, xx = np.mgrid[0:N, 0:N]; X, Y = g[xx], -g[yy]; 안 = (np.abs(X) <= .15 + 칸) & (np.abs(Y) <= .1 + 칸); 테 = 안 & ~((np.abs(X) <= .15 - 1.5 * 칸) & (np.abs(Y) <= .1 - 1.5 * 칸))
    assert 위숨[테].mean() > .6 and 위보[테].mean() < .1 and 위숨[~안].sum() == 0, (위숨[테].mean(), 위보[테].mean(), 위숨[~안].sum()); assert 앞숨.sum() > 20, 앞숨.sum()
    print("시험 통과 · 위 숨은선이 빈 방 테 덮음 %.2f · 보이는 선 %.2f · 빈 방 밖 숨은선 %d · 앞 숨은선 화소 %d" % (위숨[테].mean(), 위보[테].mean(), 위숨[~안].sum(), 앞숨.sum()))
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "시험": 시험(); sys.exit()
    L = json.load(open(O + "목록.json", encoding="utf-8"))
    with Pool(6, maxtasksperchild=200) as pool: R = pool.map(하나, L, chunksize=20)
    풀 = lambda b: np.unpackbits(b)[:N * N].reshape(N, N).astype(np.uint8)
    np.savez_compressed(O + "숨은선88.npz", HX=np.stack([풀(r[0]) for r in R]), HF=np.stack([풀(r[1]) for r in R]), HS=np.stack([풀(r[2]) for r in R])); print("ok", len(R), "숨은선 있는 부품", sum(int(풀(r[0]).any() or 풀(r[1]).any() or 풀(r[2]).any()) for r in R))
