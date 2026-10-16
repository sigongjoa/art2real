# 판정기준56 입력 — 위 · 앞 · 옆 세 방향의 숨은선 128² (도면의 점선 자리) · 데이터.py · 데이터_앞옆.py 와 같은 정규화 · 같은 광선 · 같은 선 규칙 · 10-16
# 숨은선 = 광선을 벗겨 2 번째 이후로 맞은 면들(깊이 벗기기 · 최대 층 6)의 윤곽 + 높이 끊김(꺾임 규칙은 뺌) − 보이는 선(+ 1 화소 번짐)
# 10-16 고침: 꺾임 규칙까지 쓰면 곡면 뒤쪽(9806 나사 이음 안쪽)이 빨간 덩어리로 칠해졌다(층애니 · 규칙비교.jpg) → 끊김만
# 사용(venv): 숨은선.py [시작 끝] → out/설명/캐드부품/숨은선.npz (HX · HF · HS uint8 · 목록.json 순서) · 숨은선.py 시험 <i…> → 그림만
import sys, json, numpy as np
from multiprocessing import Pool
from 데이터_앞옆 import 선그림
def 끊김선(t, S):   # 선그림 에서 꺾임(2 차 차분)만 뺀 것
    import cv2
    zz = np.where(S, -t, -3.0); s8 = S.astype(np.uint8)
    gx, gy = np.abs(np.diff(zz, axis=0, append=zz[-1:])), np.abs(np.diff(zz, axis=1, append=zz[:, -1:]))
    return (((s8 - cv2.erode(s8, np.ones((3, 3), np.uint8))) > 0) | (((gx > .03) | (gy > .03)) & S)).astype(np.uint8)
N = 128; O = "G:/art2real/out/설명/캐드부품/"; 층수 = 6; 틈 = 1e-4
def 벗기기(sc, r):   # r (N, N, 6) → 층마다 (t, 맞음) · t 는 처음 원점에서 잰 거리
    import open3d as o3d
    o, d = r[..., :3].copy(), r[..., 3:]; 누 = np.zeros((N, N), np.float32); 산 = np.ones((N, N), bool); out = []
    for _ in range(층수):
        rr = np.concatenate([o, d], -1).astype(np.float32); t = sc.cast_rays(o3d.core.Tensor(rr.reshape(-1, 6)))["t_hit"].numpy().reshape(N, N)
        S = np.isfinite(t) & 산; t = np.where(S, t, 0)
        if not S.any(): break
        out.append((np.where(S, 누 + t, 0), S)); 산 = S; 누 = np.where(S, 누 + t + 틈, 누); o = np.where(S[..., None], o + d * (t + 틈)[..., None], o)
    return out
def 하나(p):
    try:
        import trimesh, open3d as o3d, cv2
        m = trimesh.load(p, force="mesh"); e = m.extents; ax = int(np.argmin(e)); order = [i for i in range(3) if i != ax] + [ax]
        v = (m.vertices - m.bounds.mean(0))[:, order] / e.max()
        sc = o3d.t.geometry.RaycastingScene(); sc.add_triangles(o3d.core.Tensor(v.astype(np.float32)), o3d.core.Tensor(m.faces.astype(np.uint32)))
        u = (np.arange(N) + .5) / N * 1.1 - .55; A, B = np.meshgrid(u, -u); out = []
        위 = np.zeros((N, N, 6), np.float32); 위[..., 0], 위[..., 1], 위[..., 2], 위[..., 5] = A, B, 1.0, -1   # 데이터.py 와 같은 광선
        광선들 = [위]
        for 가로, 깊축 in ((0, 1), (1, 0)):   # 데이터_앞옆.py 와 같은 광선
            r = np.zeros((N, N, 6), np.float32); r[..., 가로] = A; r[..., 2] = B; r[..., 깊축] = 1.0; r[..., 3 + 깊축] = -1; 광선들.append(r)
        for r in 광선들:
            L = 벗기기(sc, r); 보 = 선그림(*L[0]) if L else np.zeros((N, N), np.uint8); 숨 = np.zeros((N, N), bool)
            for t, S in L[1:]: 숨 |= 끊김선(t, S) > 0
            out.append((숨 & ~(cv2.dilate(보, np.ones((3, 3), np.uint8)) > 0)).astype(np.uint8))
        return out
    except Exception as ex: return [np.zeros((N, N), np.uint8)] * 3 + [type(ex).__name__]
if __name__ == "__main__":
    L = json.load(open(O + "목록.json", encoding="utf-8"))
    if sys.argv[1:2] == ["시험"]:
        import cv2; from PIL import Image
        d = np.load(O + "데이터.npz"); X = d["X"]; e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"], e["S"]; 줄 = []
        for i in map(int, sys.argv[2:]):
            h = 하나(L[i]); 칸 = []
            for 보, 숨 in zip((X[i], F[i], S[i]), h[:3]):
                c = np.full((N, N, 3), 255, np.uint8); c[보 > 0] = (40, 40, 50); c[숨 > 0] = (220, 50, 50); 칸.append(np.pad(c, ((2, 2), (2, 2), (0, 0)), constant_values=200))
            줄.append(np.concatenate(칸, 1)); print(i, "보이는", int(X[i].sum() + F[i].sum() + S[i].sum()), "숨은", [int(x.sum()) for x in h[:3]], h[3:] or "")
        Image.fromarray(np.concatenate(줄, 0)).resize((3 * 132 * 2, len(줄) * 132 * 2), Image.NEAREST).save(O + "숨은선_시험.png"); sys.exit()
    a, b = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, len(L))
    with Pool(6, maxtasksperchild=200) as pool: R = pool.map(하나, L[a:b], chunksize=20)
    실 = [r[3] for r in R if len(r) > 3]
    np.savez_compressed(O + "숨은선_%05d.npz" % a, HX=np.stack([r[0] for r in R]), HF=np.stack([r[1] for r in R]), HS=np.stack([r[2] for r in R])); print("ok", a, b, "실패", len(실), set(실))
    assert len(실) < (b - a) // 50, "실패가 2 % 넘음 — 환경부터 본다"
