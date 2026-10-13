# 로드맵 2 — 지도(0 바깥 · 1 윗면 · 2 관통 · 3 들어감 + 깊이 비율) → CadQuery: 바깥 윤곽을 높이 H 로 밀고 · 관통은 뚫고 · 들어감은 깊이 층(0.1 단위)마다 덩어리째 깎음 · 부피 IoU(48³) · 10-13
import numpy as np, cv2
N = 128; 칸 = 1.1 / N
def 화(x, y): return (-.55 + (x + .5) * 칸, .55 - (y + .5) * 칸)   # 화소 → 세계(데이터.py 의 광선 격자와 같음)
def 꼬임(q):   # 닫힌 다각형의 변끼리 건너는 곳 수 — 0 이어야 CAD 면이 된다(기능0/도구.py 와 같음 · 꼬인 윤곽은 OCC 불리언이 메모리를 끝없이 잡음 10-11)
    n = len(q); o = lambda u, v, w: (v[0] - u[0]) * (w[1] - u[1]) - (v[1] - u[1]) * (w[0] - u[0])
    return sum(o(q[i], q[(i + 1) % n], q[j]) * o(q[i], q[(i + 1) % n], q[(j + 1) % n]) < 0 and o(q[j], q[(j + 1) % n], q[i]) * o(q[j], q[(j + 1) % n], q[(i + 1) % n]) < 0
               for i in range(n) for j in range(i + 2, n) if not (i == 0 and j == n - 1))
def 다각(mask):
    cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); out = []
    for c in cs:
        if cv2.contourArea(c) < 3: continue
        for e in (.8, .5, .3, 1.2, 2, 3):   # 꼬이면 버리지 않고 줄임 정도를 바꿔 다시(판정기준32) — 0.8 에서 되던 것은 그대로
            p = cv2.approxPolyDP(c, e, True)[:, 0, :]
            if 3 <= len(p) <= 200:
                q = [화(x, y) for x, y in p]
                if not 꼬임(q): out.append(q); break   # 끝까지 꼬이거나 꼭짓점 200 넘으면 버림
    return out
def 몸통53(그림, H):   # 판정기준33 — 몸통은 53 편 윤곽바탕(그림 물붓기 · 가장 큰 바깥 윤곽 · 원 판정 · 1.5 줄이기) · → (고체, 경로)
    import sys, cadquery as cq
    sys.path.insert(0, "G:/art2real/원화3d/실험_20261013/구멍"); import 윤곽바탕 as W
    _, c = W.바깥(그림); f = W.맞추기(c)
    if f[0] == "원": (x, y), r = f[1], f[2]; cx, cy = 화(x, y); return cq.Workplane("XY").center(cx, cy).circle(r * 칸).extrude(H).translate((0, 0, -H / 2)), "원"
    for i, e in enumerate((1.5, 1.0, .5, 2.5, 4)):   # 꼬이면 줄임 정도를 바꿔 다시 — 끝까지 꼬이면 볼록 껍질(경로를 세어 찍는다)
        p = cv2.approxPolyDP(c.reshape(-1, 1, 2).astype(np.float32), e, True)[:, 0, :]; q = [화(x, y) for x, y in p]
        if 3 <= len(q) <= 300 and not 꼬임(q): return cq.Workplane("XY").polyline(q).close().extrude(H).translate((0, 0, -H / 2)), "다각" if i == 0 else "다시 줄임"
    q = [화(x, y) for x, y in cv2.convexHull(c.astype(np.float32))[:, 0, :]]; return cq.Workplane("XY").polyline(q).close().extrude(H).translate((0, 0, -H / 2)), "볼록 껍질"
def 짓기(Y, D, H, 덩어리깊이=False, 그림=None):   # 그림: 주면 몸통은 몸통53(그림) · Y 는 관통 · 들어감에만   # 덩어리깊이: 들어감 덩어리(4 이웃)마다 깊이 하나(중앙값) — 판정기준31 ①
    import cadquery as cq
    if 그림 is not None: return 깎기(몸통53(그림, H)[0], Y, D, H, 덩어리깊이)
    밖 = Y > 0; ps = 다각(밖)
    if not ps: return None
    s = None
    for p in ps:
        try:
            b = cq.Workplane("XY").polyline(p).close().extrude(H).translate((0, 0, -H / 2)); s = b if s is None else s.union(b)
        except Exception: pass
    if s is None: return None
    return 깎기(s, Y, D, H, 덩어리깊이)
def 깎기(s, Y, D, H, 덩어리깊이):   # 몸통 s 에 관통 · 들어감을 깎는다
    import cadquery as cq
    for p in 다각(Y == 2):
        try: s = s.cut(cq.Workplane("XY").polyline(p).close().extrude(H + .2).translate((0, 0, -H / 2 - .1)))
        except Exception: pass
    if 덩어리깊이:
        n, lab = cv2.connectedComponents((Y == 3).astype(np.uint8), connectivity=4)
        for i in range(1, n):
            m = lab == i; dz = min(float(np.median(D[m])), .98) * H
            if dz < .01 * H: continue
            for p in 다각(m):
                try: s = s.cut(cq.Workplane("XY").polyline(p).close().extrude(dz + .05).translate((0, 0, H / 2 - dz)))
                except Exception: pass
        return s
    층 = np.clip(np.round(np.where(Y == 3, D, 0) / .1), 0, 10).astype(int)
    for k in range(1, 11):
        for p in 다각((Y == 3) & (층 == k)):
            dz = min(k * .1, .98) * H
            try: s = s.cut(cq.Workplane("XY").polyline(p).close().extrude(dz + .05).translate((0, 0, H / 2 - dz)))
            except Exception: pass
    return s
def 점유_메시(v, f, n=48):
    import open3d as o3d
    sc = o3d.t.geometry.RaycastingScene(); sc.add_triangles(o3d.core.Tensor(np.asarray(v, np.float32)), o3d.core.Tensor(np.asarray(f, np.uint32)))
    g = (np.arange(n) + .5) / n * 1.1 - .55; P = np.stack(np.meshgrid(g, g, g, indexing="ij"), -1).reshape(-1, 3).astype(np.float32)
    return sc.compute_occupancy(o3d.core.Tensor(P)).numpy().reshape(n, n, n) > .5
def 점유_캐드(s, n=48):
    vs, ts = s.val().tessellate(0.005, 0.2); return 점유_메시([(q.x, q.y, q.z) for q in vs], ts, n)
def 정규메시(p):   # 데이터.py 와 같은 변환
    import trimesh
    m = trimesh.load(p, force="mesh")
    if len(m.faces) > 150000: raise ValueError("면이 너무 많음")   # 10-13 평가 메모리 — 큰 메시는 건너뜀(0 점으로 셈)
    e = m.extents; ax = int(np.argmin(e)); order = [i for i in range(3) if i != ax] + [ax]
    return (m.vertices - m.bounds.mean(0))[:, order] / e.max(), m.faces, float(e[ax] / e.max())
def 부피IoU(job):   # (stl 경로, Y, D[, 덩어리깊이[, 그림]]) → (IoU, 바탕만 IoU) · 그림을 주면 (IoU, 바탕만, 몸통 경로)
    p, Y, D = job[:3]; 덩 = job[3] if len(job) > 3 else False; 그림 = job[4] if len(job) > 4 else None
    if 그림 is not None:
        try:
            v, f, H = 정규메시(p); 정 = 점유_메시(v, f); 몸, 길 = 몸통53(그림, H); s = 깎기(몸, Y, D, H, 덩)
            r = lambda q: float((q & 정).sum() / max((q | 정).sum(), 1)); return (r(점유_캐드(s)), r(점유_캐드(몸)), 길)
        except Exception as e: return (0.0, 0.0, "실패 " + type(e).__name__)
    try:
        v, f, H = 정규메시(p); 정 = 점유_메시(v, f); s = 짓기(Y, D, H, 덩); s0 = 짓기(np.where(Y > 0, 1, 0), D * 0, H)
        r = lambda q: float((q & 정).sum() / max((q | 정).sum(), 1))
        return (r(점유_캐드(s)) if s is not None else 0.0, r(점유_캐드(s0)) if s0 is not None else 0.0)
    except Exception: return (0.0, 0.0)
